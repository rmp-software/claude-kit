#!/usr/bin/env python3
"""SessionStart hook for the file-standard plugin.

Two jobs, both best-effort and non-fatal:
  1. Inject the file-placement standard into the session as additionalContext,
     so every session (and every subagent that inherits it) knows where
     tool-generated files belong.
  2. Idempotently ensure the machine's global gitignore covers
     `.claude/scratch/`, so in-repo scratch/evidence/handoff can never be
     committed even if the convention is ignored.

The hook must never break session start: every step is wrapped, and on any
failure we still emit valid JSON (at minimum the standard text).
"""

import json
import os
import subprocess
import sys

IGNORE_PATTERN = ".claude/scratch/"
DEFAULT_EXCLUDES = os.path.expanduser("~/.config/git/ignore")

STANDARD = """\
# File-placement standard (claude-kit: file-standard)

When you create a file that is NOT source code the user asked you to write,
place it by category. Do not invent ad-hoc locations.

| Category    | What it is                                             | Where it goes |
|-------------|--------------------------------------------------------|---------------|
| scratch     | throwaway working files, intermediate output           | ~/.claude/work/<project>/scratch/  (OUTSIDE the repo, always) |
| evidence    | screenshots, logs, test runs proving something worked  | <repo>/.claude/scratch/evidence/   (in-repo, gitignored) |
| handoff     | plans, notes, specs passed between agents/sessions     | <repo>/.claude/scratch/handoff/    (in-repo, gitignored) |
| deliverable | output the user explicitly asked to keep               | the path the user specified (committed normally) |

Rules:
- `<project>` = "<basename-of-repo-or-cwd>-<shorthash-of-its-abs-path>".
- If the working directory is NOT a git repo, there is no tree to pollute:
  evidence and handoff fall back to ~/.claude/work/<project>/ as well.
- Never write scratch/evidence/handoff into a tracked location. The in-repo
  home for them is always `.claude/scratch/` (which is gitignored globally).
- `.claude/scratch/` is ignored; the rest of `.claude/` (config) is not — do
  not put disposable artifacts anywhere else under `.claude/`.
- Deliverables are the exception: put them where the user wants them.
"""


def ensure_global_gitignore():
    """Make sure the global gitignore contains IGNORE_PATTERN.

    Returns a short human note if a change was made, else None. Never raises.
    """
    try:
        excludes = subprocess.run(
            ["git", "config", "--global", "core.excludesfile"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()

        created_config = False
        if not excludes:
            excludes = DEFAULT_EXCLUDES
            subprocess.run(
                ["git", "config", "--global", "core.excludesfile", excludes],
                capture_output=True, text=True, timeout=5,
            )
            created_config = True

        path = os.path.expanduser(excludes)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        existing = ""
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                existing = fh.read()

        # Already covered? (match the exact pattern line, ignoring whitespace)
        if any(line.strip() == IGNORE_PATTERN for line in existing.splitlines()):
            return None

        with open(path, "a", encoding="utf-8") as fh:
            if existing and not existing.endswith("\n"):
                fh.write("\n")
            fh.write("# claude-kit file-standard: in-repo agent scratch\n")
            fh.write(IGNORE_PATTERN + "\n")

        where = f"{excludes} (newly set as core.excludesfile)" if created_config else excludes
        return f"Added `{IGNORE_PATTERN}` to your global gitignore at {where}."
    except Exception:
        return None


def main():
    context = STANDARD
    note = ensure_global_gitignore()
    if note:
        context += "\n# Setup note (one-time)\n" + note + "\n"

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Last-resort fallback: still deliver the standard, never crash startup.
        try:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": STANDARD,
                }
            }))
        except Exception:
            pass
    sys.exit(0)
