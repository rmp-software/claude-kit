#!/usr/bin/env python3
"""PreToolUse backstop for the tailwind-standard plugin.

Non-blocking write-time lint. When a Write/Edit/MultiEdit targets a UI-ish file
and the incoming text contains a banned styling pattern, emit an advisory
warning naming the file, the offending snippet, and the correct alternative. The
write always proceeds — this is a nudge, not a gate.

Matchers are deliberately TIGHT (favour false negatives over false positives,
like file-standard). We flag only high-signal violations:
  1. `[color:var(--…)]` arbitrary utilities (the clearest violation).
  2. a design-token `var(--…)` inside a bracket utility on a color/bg/border/
     fill/stroke/ring/shadow prefix (so positional/size runtime bridges like
     `left-[var(--puck-x)]` / `h-[var(--pad-h)]` do NOT trip it).
  3. a raw hex colour inside a `className` / `class=` string.
  4. an app importing `radix-ui` / `@radix-ui/*` / a shadcn registry path from a
     file that is NOT under a shared UI package's `src/ui/**` (advisory) —
     SHADCN-GATED: this check fires ONLY when the file's repo actually uses
     shadcn. A Tailwind-only (no-shadcn) repo may use radix legitimately, so if
     detection is negative or ambiguous we favour the false-negative and skip it.

Checks 1–3 are Tailwind core and always fire. Never raises; on any error it
stays silent and lets the tool run.
"""

import functools
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _detect import detect_stack

# --- File scoping -------------------------------------------------------------
# Only lint files where these patterns are meaningful. .tsx/.jsx are the core;
# .css/.ts are handled conservatively (only the hex-in-class check is risky
# there, so we keep the className checks scoped to JSX-bearing extensions).
JSX_EXT = (".tsx", ".jsx")
SOURCE_EXT = (".tsx", ".jsx", ".ts", ".mts", ".cts")

# --- Pattern 1: [color:var(--…)] arbitrary utility ---------------------------
COLOR_VAR_RE = re.compile(r"\[color:var\(--[^)]+\)\]")

# --- Pattern 2: token var() in a color-ish bracket utility -------------------
# Tight prefix list so size/position bridges (left-, top-, h-, w-, max-w-,
# translate-, inset-, basis-, flex-, gap-, text-[length:…]) are NOT flagged.
COLORISH_PREFIXES = (
    "bg", "text", "border", "fill", "stroke", "ring", "shadow",
    "from", "via", "to", "decoration", "outline", "caret", "accent",
    "divide", "placeholder",
)
COLORISH_VAR_RE = re.compile(
    r"\b(?:" + "|".join(COLORISH_PREFIXES) + r")-\[var\(--[^)]+\)\]"
)

# --- Pattern 3: raw hex inside a className / class= string --------------------
# Find a className/class attribute value, then look for a hex literal in it.
CLASS_ATTR_RE = re.compile(
    r"""class(?:Name)?\s*=\s*(?:"([^"]*)"|'([^']*)'|\{`([^`]*)`\})"""
)
HEX_RE = re.compile(r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?(?:[0-9a-fA-F]{2})?\b")

# --- Pattern 4: direct radix/shadcn import outside the shared UI package ------
RADIX_IMPORT_RE = re.compile(
    r"""(?:import|from)\s+['"](?:radix-ui|@radix-ui/[^'"]+|@/components/ui/[^'"]+)['"]"""
)


@functools.lru_cache(maxsize=None)
def repo_uses_shadcn(scan_dir):
    """Whether the repo containing `scan_dir` uses shadcn. lru_cache'd on the
    resolved dir so repeated edits in one invocation don't rescan. On detection
    failure/ambiguity this is False (favour the false-negative on the radix check).
    """
    try:
        _, shadcn = detect_stack(scan_dir)
        return shadcn
    except Exception:
        return False


def is_ui_package_internal(abs_path):
    """True for a shared UI package's own primitive source (…/ui/src/ui/**)."""
    p = abs_path.replace("\\", "/")
    return "/ui/src/ui/" in p or p.endswith("/ui/src/ui")


def candidate_texts(tool_name, tool_input):
    """Return the incoming text blob(s) the tool is about to write."""
    texts = []
    if tool_name == "Write":
        c = tool_input.get("content")
        if isinstance(c, str):
            texts.append(c)
    elif tool_name == "Edit":
        c = tool_input.get("new_string")
        if isinstance(c, str):
            texts.append(c)
    elif tool_name == "MultiEdit":
        for edit in tool_input.get("edits", []) or []:
            c = (edit or {}).get("new_string")
            if isinstance(c, str):
                texts.append(c)
    return texts


def snippet(text, match_start, match_end, pad=24):
    lo = max(0, match_start - pad)
    hi = min(len(text), match_end + pad)
    s = text[lo:hi].replace("\n", " ").strip()
    return ("…" if lo > 0 else "") + s + ("…" if hi < len(text) else "")


BRIDGE_NOTE = (
    "If this is a genuine runtime bridge — drag coords, measured/clamp() dims, "
    "animation offset — this is allowed; ignore."
)


def lint_text(text, abs_path):
    """Return a list of (snippet, advice) findings for one text blob."""
    findings = []
    is_jsx = abs_path.lower().endswith(JSX_EXT)

    # 1. [color:var(--…)] — highest signal, any source file. (Tailwind core.)
    for m in COLOR_VAR_RE.finditer(text):
        findings.append((
            snippet(text, m.start(), m.end()),
            "A token is a utility, not a var: write `text-fg-3` / `bg-surface` / "
            "`border-border`, never `text-[color:var(--…)]`. A missing utility is "
            "a gap to fix in `@theme`. " + BRIDGE_NOTE,
        ))

    # 2. colour-ish bracket utility consuming a token var(). (Tailwind core.)
    for m in COLORISH_VAR_RE.finditer(text):
        # Avoid double-reporting the [color:var(--…)] case (already covered).
        if "[color:var(" in m.group(0):
            continue
        findings.append((
            snippet(text, m.start(), m.end()),
            "A design-token `var(--…)` in a colour/bg/border bracket utility — use "
            "the registered utility (`bg-surface`, `border-border`, `ring-ring`) "
            "instead. " + BRIDGE_NOTE,
        ))

    # 3. raw hex inside a className / class= string (JSX/className contexts only).
    #    (Tailwind core.)
    if is_jsx:
        for m in CLASS_ATTR_RE.finditer(text):
            value = m.group(1) or m.group(2) or m.group(3) or ""
            if HEX_RE.search(value):
                findings.append((
                    snippet(text, m.start(), m.end(), pad=8),
                    "Raw hex colour inside a className — colours come from `@theme` "
                    "token utilities (`bg-espresso-800`, `text-fg`), never a hex "
                    "literal. Hex belongs only in the token CSS source files.",
                ))

    # 4. direct radix/shadcn import outside the shared UI package.
    #    SHADCN-GATED: only meaningful where the repo actually uses shadcn. A
    #    Tailwind-only repo may import radix directly and legitimately, so we skip
    #    this check unless shadcn is detected (favour the false-negative).
    if abs_path.lower().endswith(SOURCE_EXT) and not is_ui_package_internal(abs_path):
        if repo_uses_shadcn(os.path.dirname(abs_path)):
            for m in RADIX_IMPORT_RE.finditer(text):
                findings.append((
                    snippet(text, m.start(), m.end(), pad=8),
                    "Apps never import `radix-ui` / shadcn directly — primitives come "
                    "from the shared UI package (e.g. `@crivelo/ui/button`). A missing "
                    "primitive is added TO that package, not the app.",
                ))

    return findings


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return
    data = json.loads(raw)
    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return
    tool_input = data.get("tool_input", {}) or {}

    file_path = tool_input.get("file_path") or ""
    if not file_path.lower().endswith(SOURCE_EXT) and not file_path.lower().endswith(".css"):
        return
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(
        data.get("cwd") or os.getcwd(), file_path
    )

    all_findings = []
    for text in candidate_texts(tool_name, tool_input):
        all_findings.extend(lint_text(text, abs_path))

    if not all_findings:
        return

    lines = [
        f"- in `{abs_path}` — `{snip}`\n  → {advice}"
        for (snip, advice) in all_findings
    ]
    msg = (
        "tailwind-standard: the incoming edit may break the styling "
        "standard (advisory; the write proceeds):\n" + "\n".join(lines)
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
