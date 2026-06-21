# tailwind-shadcn-standard

RMP's hard-won **Tailwind v4 + shadcn + design-token styling standard**, made to
travel with the tooling — instead of being re-authored in every repo's
`CLAUDE.md` / `app_spec.txt`.

## The problem

The styling standard (tokens are the utility vocabulary, no `var()` in a
className, buy commodity UI / build the domain, primitives from one shared
package) keeps getting re-typed into each repo's docs and drifting between them.
A skill + hooks let it ship once and apply everywhere the stack is present.

## The standard

A token is a **utility**, not a `var()`; commodity UI is **bought**, the domain
is **built**; primitives live in **one** shared package. The hard invariants:

- **NO design-token `var(--…)` inside a className.** Write `text-fg-3` /
  `bg-surface` / `border-border` / `text-h4`, never `text-[color:var(--fg-3)]` /
  `bg-[var(--surface)]`. A token missing a utility is a gap to fix in `@theme`,
  not a reason to reach for `[var(--…)]`.
- **Tokens are the utility vocabulary; no raw hex in a className.** Hex literals
  belong only in the token CSS source.
- **Buy commodity UI** (modal/drawer/toast/dialog/focus/animation), **build the
  domain.** Primitives come from the shared UI package; apps never import
  radix/shadcn directly — a missing primitive is added *to* the package.
- **`[var(--…)]` / inline-style vars are reserved for runtime bridges only** —
  per-render computed values (drag coords, measured/`%`/`clamp()` dims, animation
  offset, alpha-blended `rgba()`). A finite enumerable set is NOT a bridge: map
  it to a static className lookup.
- **Spacing/size follows the scale;** snap `[NNpx]` to a step only on an exact
  match (no nearest-step rounding); genuine off-scale values stay documented
  arbitraries.

The full guide lives in the **`tailwind-shadcn-standard` skill**.

## How it's enforced (three layers)

1. **SessionStart hook → injects a short pointer, stack-gated.** It cheaply
   detects whether the repo uses Tailwind v4 **and** shadcn (a `tailwindcss`
   major ≥ 4 / `@tailwindcss/postcss` dep or an `@import "tailwindcss"`; plus a
   `components.json` / `class-variance-authority` / `tailwind-merge` / `cn()`
   signal). On that stack it injects the invariants + a "load the skill" pointer;
   **off-stack (or on any ambiguity) it stays silent.** Monorepo-aware: from an
   app dir it also scans the repo root so a shared UI package's shadcn signal is
   seen.
2. **On-demand skill → the full guide.** `tailwind-shadcn-standard` holds the
   complete standard (tiers, the no-`var()` rule with right/wrong snippets, the
   primitive boundary, the runtime-bridge exception, scale-snapping, and a
   grep-able compliance checklist). It triggers on UI/styling/Tailwind/shadcn work.
3. **PreToolUse hook → non-blocking lint backstop.** On `Write`/`Edit`/`MultiEdit`
   to UI-ish files it scans the incoming text for the banned patterns
   (`[color:var(--…)]`, a token `var()` in a colour/bg/border bracket utility,
   raw hex in a className, a direct radix/shadcn import outside the shared UI
   package) and warns with the file, the snippet, and the fix. The write always
   proceeds; Claude self-corrects.

## Install

This plugin ships in the **claude-kit** marketplace:

```
/plugin marketplace add rmp-software/claude-kit
/plugin install tailwind-shadcn-standard@claude-kit
```

## Notes

- Hooks are dependency-free Python 3 (no `jq`, no pip installs) and never block
  or crash a session on failure — worst case they stay silent.
- The PreToolUse matchers are intentionally tight (favour false negatives over
  false positives); each warning explicitly notes that a genuine runtime bridge
  is allowed and should be ignored. Warnings are advisory, not enforced.
- The SessionStart hook stays **silent off-stack** — it injects only when both
  Tailwind v4 and shadcn are detected, so the pointer never shows up where it
  doesn't apply.
