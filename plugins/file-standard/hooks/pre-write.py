#!/usr/bin/env python3
"""PreToolUse backstop for the file-standard plugin.

Non-blocking. When a Write/Edit/MultiEdit/Bash call targets a path that looks
like scratch/evidence/handoff but lands inside a git repo *outside* the
sanctioned `.claude/scratch/` area, emit a warning telling Claude the correct
location. The write always proceeds — the global gitignore is the hard net;
this hook just nudges Claude to self-correct.

Matchers are deliberately tight (a scratch-ish directory segment, or a clear
filename token) to keep false positives low. Never raises; on any error it
stays silent and lets the tool run.
"""

import hashlib
import json
import os
import re
import sys

# Directory segments that signal a scratch-ish destination the tool created.
SCRATCH_DIRS = {
    "scratch", "evidence", "handoff", "tmp", "temp",
    "artifacts", "screenshots", ".scratch",
}
# Filename tokens that signal a loose disposable file.
NAME_TOKEN = re.compile(
    r"(evidence|handoff|screenshot|repro|scratchpad|scratch|debug[-_]dump)",
    re.IGNORECASE,
)
TMP_EXT = re.compile(r"\.(tmp|temp)$", re.IGNORECASE)

# Bash redirect / tee targets: `> path`, `>> path`, `tee path`, `tee -a path`.
REDIRECT = re.compile(r"(?:>>?|\btee\b(?:\s+-a)?)\s+([^\s|;&<>]+)")


def git_root(path):
    """Walk up from path's directory looking for a .git entry. None if not in a repo."""
    d = os.path.dirname(path) or "."
    d = os.path.abspath(d)
    while True:
        if os.path.exists(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def project_key(root):
    base = os.path.basename(root.rstrip("/")) or "repo"
    short = hashlib.sha1(root.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{short}"


def is_sanctioned(abs_path):
    """True if the path is already under a `.claude/scratch/` segment."""
    parts = abs_path.split(os.sep)
    for i in range(len(parts) - 1):
        if parts[i] == ".claude" and parts[i + 1] == "scratch":
            return True
    return False


def classify(abs_path, root):
    """Return (category_label, suggested_path) for a triggering path."""
    low = abs_path.lower()
    base = os.path.basename(low)
    if "evidence" in low or "screenshot" in base:
        return "evidence", os.path.join(root, ".claude/scratch/evidence/")
    if "handoff" in low or "plan" in base or "notes" in base:
        return "handoff", os.path.join(root, ".claude/scratch/handoff/")
    if any(seg in ("scratch", "tmp", "temp") for seg in low.split(os.sep)) or TMP_EXT.search(base):
        return "scratch", f"~/.claude/work/{project_key(root)}/scratch/"
    return "artifact", os.path.join(root, ".claude/scratch/")


def triggers(abs_path):
    parts = [p.lower() for p in abs_path.split(os.sep)]
    if SCRATCH_DIRS.intersection(parts[:-1]):  # a directory segment matches
        return True
    base = os.path.basename(abs_path)
    return bool(NAME_TOKEN.search(base) or TMP_EXT.search(base))


def candidate_paths(tool_name, tool_input, cwd):
    paths = []
    if tool_name in ("Write", "Edit", "MultiEdit"):
        fp = tool_input.get("file_path")
        if fp:
            paths.append(fp)
    elif tool_name == "Bash":
        cmd = tool_input.get("command", "")
        paths.extend(REDIRECT.findall(cmd))
    out = []
    for p in paths:
        p = os.path.expanduser(p)
        if not os.path.isabs(p):
            p = os.path.join(cwd or os.getcwd(), p)
        out.append(os.path.normpath(p))
    return out


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return
    data = json.loads(raw)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    cwd = data.get("cwd") or os.getcwd()

    warnings = []
    seen = set()
    for abs_path in candidate_paths(tool_name, tool_input, cwd):
        if abs_path in seen:
            continue
        seen.add(abs_path)
        if is_sanctioned(abs_path):
            continue
        root = git_root(abs_path)
        if not root:  # not in a git repo -> nothing to pollute
            continue
        if not triggers(abs_path):
            continue
        label, suggested = classify(abs_path, root)
        warnings.append(
            f"- `{abs_path}` looks like {label}. The standard says {label} files "
            f"belong in `{suggested}`, not a tracked location. The write will "
            f"proceed (it's gitignored-safe only under `.claude/scratch/`); "
            f"consider relocating it."
        )

    if not warnings:
        return

    msg = (
        "file-standard: a generated file may be landing outside its sanctioned "
        "location:\n" + "\n".join(warnings)
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": msg,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # never block a tool call on hook failure
    sys.exit(0)
