#!/usr/bin/env python3
"""SessionStart hook for the tailwind-standard plugin.

One job, best-effort and non-fatal: when the session's repo uses Tailwind v4,
inject a SHORT pointer to the RMP styling standard as additionalContext so every
session (and inheriting subagent) knows the hard invariants before it edits UI,
and knows to pull the full guide from the `tailwind-standard` skill.

Tailwind v4 is the ONLY hard requirement — a repo can use Tailwind v4 + tokens
without shadcn, and those repos still get the token-discipline rules. shadcn is
an OPTIONAL layer: when it's also detected, an extra paragraph about the
buy-commodity / shared-primitive boundary is appended. Off-Tailwind → silent.

Detection is cheap, bounded, and wrapped (see `_detect.py`): on ANY error or
ambiguity it returns (False, False) and the hook stays silent. The hook must
never break session start.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _detect import detect_stack

# Always injected when Tailwind v4 is detected.
TAILWIND_CORE = """\
# Tailwind v4 styling standard (claude-kit: tailwind-standard)

This repo styles with Tailwind v4 `@theme` tokens. Before writing or editing UI,
follow the RMP styling standard — invoke the `tailwind-standard` skill for the
full guide. Hard invariants:
- NO design-token `var(--…)` inside a className. A token is a utility:
  `text-fg-3` / `bg-surface` / `border-border` / `text-h4`, NEVER
  `text-[color:var(--fg-3)]` / `bg-[var(--surface)]`. A token missing a utility
  is a gap to fix in `@theme`, not a reason to reach for `[var(--…)]`.
- Tokens are the utility vocabulary; no raw hex in a className.
- Arbitrary `[var(--…)]` / inline-style vars are reserved for RUNTIME BRIDGES only
  (per-render computed values: drag coords, measured/%/clamp() dims, animation
  offset, alpha-blended rgba()). A finite enumerable set is NOT a runtime bridge —
  map it to a static className lookup.
- Spacing/size follows the scale; snap `[NNpx]` to a scale step only on an EXACT
  match (no nearest-step rounding); genuine off-scale values stay documented arbitraries."""

# Appended only when shadcn is also detected. The leading blank line makes it
# read as a continuation of the TAILWIND_CORE bullet list.
SHADCN_LAYER = """

- shadcn layer (this repo uses shadcn): buy commodity UI (modal/drawer/toast/
  dialog/focus/animation), build the domain. Primitives come from the shared UI
  package; apps NEVER import radix/shadcn directly. shadcn alias utilities
  (`bg-background`, `text-muted-foreground`) stay internal to the UI package's
  `src/ui/**`; app code uses the house neutrals."""


def session_cwd():
    try:
        raw = sys.stdin.read()
        if raw.strip():
            data = json.loads(raw)
            cwd = data.get("cwd")
            if cwd and os.path.isdir(cwd):
                return cwd
    except Exception:
        pass
    return os.getcwd()


def main():
    cwd = session_cwd()
    tailwind, shadcn = detect_stack(cwd)
    if not tailwind:
        # Off-Tailwind (or ambiguous) — stay silent. Emit nothing.
        return
    pointer = TAILWIND_CORE + (SHADCN_LAYER if shadcn else "")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": pointer,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never break session start; on any failure, stay silent.
        pass
    sys.exit(0)
