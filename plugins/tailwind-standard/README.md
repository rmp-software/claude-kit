# tailwind-standard

RMP's hard-won **Tailwind v4 + design-token styling standard**, made to travel
with the tooling — instead of being re-authored in every repo's `CLAUDE.md` /
`app_spec.txt`. **Tailwind v4 is the only hard requirement;** **shadcn is an
auto-detected, optional layer** on top.

## The problem

The styling standard (tokens are the utility vocabulary, no `var()` in a
className, no raw hex, arbitraries reserved for runtime bridges — and, where
shadcn is present, buy commodity UI / build the domain, primitives from one
shared package) keeps getting re-typed into each repo's docs and drifting
between them. A skill + hooks let it ship once and apply everywhere Tailwind v4
is present.

shadcn can't exist without Tailwind, but a repo can use Tailwind v4 + tokens
**without** shadcn — those repos should still get the token discipline, but NOT
the shadcn-specific rules (which would false-positive, e.g. warning on a
legitimate direct radix import in a no-shadcn project). So Tailwind v4 gates the
standard, and the shadcn layer activates only when shadcn is also detected.

## The standard

A token is a **utility**, not a `var()`; spacing follows the **scale**;
arbitraries are reserved for **runtime bridges**. The Tailwind-core invariants:

- **NO design-token `var(--…)` inside a className.** Write `text-fg-3` /
  `bg-surface` / `border-border` / `text-h4`, never `text-[color:var(--fg-3)]` /
  `bg-[var(--surface)]`. A token missing a utility is a gap to fix in `@theme`,
  not a reason to reach for `[var(--…)]`.
- **Tokens are the utility vocabulary; no raw hex in a className.** Hex literals
  belong only in the token CSS source.
- **`[var(--…)]` / inline-style vars are reserved for runtime bridges only** —
  per-render computed values (drag coords, measured/`%`/`clamp()` dims, animation
  offset, alpha-blended `rgba()`). A finite enumerable set is NOT a bridge: map
  it to a static className lookup.
- **Spacing/size follows the scale;** snap `[NNpx]` to a step only on an exact
  match (no nearest-step rounding); genuine off-scale values stay documented
  arbitraries.

When the repo **also uses shadcn**, the standard adds: **buy commodity UI**
(modal/drawer/toast/dialog/focus/animation), **build the domain**; app code
imports the shadcn **primitive** (your `components/ui`, or a shared UI package in
a monorepo), **never radix directly**; shadcn alias utilities stay internal to
the primitives layer. The shared-UI-package boundary (a new primitive goes into
the shared package, apps don't keep their own `components/ui`) is a **monorepo-
only** convention — in a single-app project a local `components/ui` is the
correct home.

The full guide lives in the **`tailwind-standard` skill**.

## How it's enforced (three layers)

1. **SessionStart hook → injects a short pointer, Tailwind-gated.** It cheaply
   detects whether the repo uses Tailwind v4 (a `tailwindcss` major ≥ 4 /
   `@tailwindcss/postcss` dep, or an `@import "tailwindcss"`). On Tailwind it
   injects the **token-core invariants** + a "load the skill" pointer; **off
   Tailwind (or on any ambiguity) it stays silent.** It detects shadcn
   independently (a `components.json` / `class-variance-authority` /
   `tailwind-merge` / `cn()` signal) and **appends the shadcn paragraph only when
   shadcn is present.** Monorepo-aware: from an app dir it also scans the repo
   root so a shared UI package's shadcn signal is seen.
2. **On-demand skill → the full guide.** `tailwind-standard` holds the complete
   standard (tiers, the no-`var()` rule with right/wrong snippets, the
   runtime-bridge exception, scale-snapping, `cn()`, and a grep-able compliance
   checklist split into an always-Tailwind group and a shadcn-only group). It
   triggers on UI/styling/Tailwind/shadcn work.
3. **PreToolUse hook → non-blocking lint backstop.** On `Write`/`Edit`/`MultiEdit`
   to UI-ish files it scans the incoming text for the banned patterns. The
   Tailwind-core checks (`[color:var(--…)]`, a token `var()` in a colour/bg/border
   bracket utility, raw hex in a className) **always fire.** The **direct-radix
   import check is shadcn-gated** — it fires only when the file's repo actually
   uses shadcn (a no-shadcn repo may use radix legitimately, so on a
   negative/ambiguous detection it's skipped), and only when the file is **not a
   primitives file**. The primitives dir is **detected per-repo** — it reads a
   `components.json` `aliases.ui` segment and also exempts common fallback
   segments (`/components/ui/`, `/ui/src/ui/`, `/src/components/ui/`,
   `/packages/ui/src/`, `/packages/ui/components/`) — so the check works for a
   plain Next.js shadcn app (`@/components/ui`) and any turborepo layout alike,
   not just one hardcoded path. Importing your own primitives
   (`@/components/ui/*`) is correct and never flagged. It warns with the file, the
   snippet, and the fix; the write always proceeds; Claude self-corrects.

## Install

This plugin ships in the **claude-kit** marketplace:

```
/plugin marketplace add rmp-software/claude-kit
/plugin install tailwind-standard@claude-kit
```

## Notes

- Hooks are dependency-free Python 3 (no `jq`, no pip installs) and never block
  or crash a session on failure — worst case they stay silent. Detection lives in
  a shared `hooks/_detect.py` both hooks import.
- The PreToolUse matchers are intentionally tight (favour false negatives over
  false positives); each warning explicitly notes that a genuine runtime bridge
  is allowed and should be ignored. Warnings are advisory, not enforced.
- The SessionStart hook stays **silent off Tailwind** — it injects only when
  Tailwind v4 is detected, and the shadcn paragraph appears only when shadcn is
  also present, so neither shows up where it doesn't apply.
