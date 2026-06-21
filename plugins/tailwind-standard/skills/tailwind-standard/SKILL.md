---
name: tailwind-standard
description: The RMP Tailwind v4 token-discipline styling standard, with an optional shadcn-primitive layer. Use BEFORE writing or editing any UI — components, screens, styling, className work, adding a token, choosing a primitive, or reviewing styling. Covers the @theme token vocabulary, the no-var()-in-className rule, no raw hex, the runtime-bridge exception, scale-snapping, `cn()`, and a grep-able compliance checklist. The shadcn layer (buy-commodity-build-domain, the primitives-wrap-radix boundary, aliases-stay-internal) applies only when the repo uses shadcn; its shared-UI-package rule is a monorepo-only convention.
---

# Tailwind v4 styling standard

How to style in a Tailwind v4 `@theme` token codebase. The tokens are the utility
vocabulary; spacing follows the scale; arbitraries are reserved for runtime
bridges. Tailwind v4 is the only thing this standard requires. If the repo ALSO
uses shadcn, the **shadcn layer** at the bottom applies on top (commodity UI is
bought, the domain is built, app code imports the shadcn primitive — never radix
directly). This is generalized — wherever it says "the tokens package" or "the
app's `@theme`", read your repo's actual names (e.g. `@crivelo/tokens`,
`apps/<app>/app/*-theme.css`); the primitives live wherever your shadcn
`aliases.ui` points (`@/components/ui` single-app, a shared `@org/ui` package in a
monorepo). The shared-UI-package boundary is a **monorepo-only** convention,
called out as such below.

## 1. Design-system tiers

Two tiers of design tokens, both registered as Tailwind v4 `@theme` utilities:

- **Tier 1 — the neutral house.** Shipped by the tokens package: semantic
  neutrals (`surface`, `fg`, `border`), the named type scale (`text-h1` … `text-body`),
  spacing/radius/shadow. No product accent. This is the shared foundation.
- **Tier 2 — the app accent/palette.** Each app brings its own accent + extra
  ramps in an app-local `@theme` source (e.g. `app/<app>-theme.css`): the brand
  colour, raw ramp steps, app-specific warning/signature shadows.

Both tiers land in `@theme`, so **every token has a bare utility class**. There
is no `tailwind.config.ts` in v4 — the CSS entry is `@import "tailwindcss"`, then
the foundation + token sources, and `@theme` turns the raw `--*` variables into
utilities (`bg-surface`, `text-fg-3`, `bg-espresso-800`, `text-warning`).

## 2. Tokens ARE the utility vocabulary

Style with semantic utility classes. **A token is a utility, NOT a `var()`.**

```tsx
// ✅ right — the registered utility
<div className="bg-surface text-fg-3 border-border rounded-md shadow-live-halo" />

// ❌ wrong — a token var() smuggled into a className arbitrary
<div className="bg-[var(--surface)] text-[color:var(--fg-3)]" />
```

**A token missing a utility is a gap to fix in `@theme`, not a reason to reach
for `[var(--…)]`.** If you need `text-fg-3` and it isn't registered, add it to
the `@theme` source — don't write `text-[color:var(--fg-3)]`.

**No raw hex in a className** (or anywhere in app/component code). Hex literals
belong ONLY in the token CSS source files (the definition layer). Everywhere
else, colour comes from a token utility.

```tsx
<div className="bg-espresso-800" />          // ✅
<div className="bg-[#1a1a1a]" />             // ❌ raw hex in a className
```

## 3. The runtime-bridge exception

`[var(--…)]` / inline-style vars are reserved for **runtime bridges only**: a
value **computed per render from JS** that no static utility can express —

- drag/pointer coordinates (`left-[var(--puck-x)]`),
- measured / `%` / `clamp()` dimensions (`width: ${pct}%`, `max-w-[var(--mw)]`),
- animation offsets,
- alpha-blended `rgba()` carried on a custom property (`bg-[var(--bar)]`),
- a `text-[length:var(--title-size)]` driven by a measured size.

**A finite, enumerable set is NOT a runtime bridge.** If the value is one of a
known list (status → colour, size → class), map it to a **static className
lookup** with `cn()`, not a `var()`.

```tsx
// ✅ runtime bridge — coord computed every render
<div className="left-[var(--puck-x)]" style={{ "--puck-x": `${x}px` }} />

// ❌ enumerable set faked as a bridge — use a static lookup instead
const tone = { win: "text-success", loss: "text-warning" }[status];
```

Note the colour-vs-position distinction the lint backstop relies on:
`bg-[var(--…)]` / `border-[var(--…)]` on a **colour** prefix is suspect (likely a
token that should be a utility); `left-`/`top-`/`h-`/`w-`/`translate-` bridges
are positional/size and legitimately dynamic.

## 4. Scale-snapping and arbitraries

Spacing/size follows the **scale** (`gap-2.5`, `p-4`, `rounded-md`). **Snap a
`[NNpx]` to a scale step ONLY on an exact match** — never nearest-step rounding.
Genuinely off-scale one-offs stay documented arbitraries (`min-h-[44px]`,
`max-w-[1060px]`, an odd font size). An intentionally-unpromoted token (e.g. a
focus ring kept as `ring-[var(--focus-ring)]`) is a documented arbitrary, not a
violation — but it's the exception, declared in the spec.

## 5. `cn()` for conditional/variant classes

Conditional and variant classes go through **`cn()`** (clsx + tailwind-merge) as
className lookups (`Record<status, classes>`), never an inline `style` ternary.
A finite set maps to static classes; `cn()` merges them deterministically.

## 6. Inline `style` is a last resort

Only for what cannot be a utility: computed dimensions (progress-bar fill width),
SVG geometry, state-driven transforms. No `var(--…)` inside a `style` prop except
a true runtime bridge (a custom property carrying a per-render JS value).

---

## shadcn layer (only when the repo uses shadcn)

Everything below applies ONLY in a repo that uses shadcn. A Tailwind-v4-only repo
without shadcn skips this section entirely — it may import radix directly and
legitimately. The first sub-sections are **universal** (any shadcn setup,
single-app or monorepo); the last one — a shared UI package owning primitives —
is a **monorepo-only** convention, labelled as such.

### Buy commodity UI, build the domain

Don't re-implement a solved interaction. **Buy** the commodity — modal, drawer,
toast, dialog, focus-trap, animation — from an established library. **Build** the
domain — the bespoke product logic and screens. The commodity is a liability to
hand-roll; the domain is the product.

The toolkit:
- **shadcn primitives** for commodity UI.
- **`motion`** (`motion/react`) for animation, gated on `prefers-reduced-motion`.
  No new manual `setInterval` animation loops; no new `@keyframes` authored in
  component (`.tsx`/`.ts`) code — keyframes live in `.css` sources.

### Primitives wrap radix — app code imports the primitive, NOT radix (universal)

This holds in **any** shadcn setup, single-app or monorepo:

- **App/feature code NEVER imports `radix-ui` / `@radix-ui/*` directly.** It
  imports the shadcn **primitive**, which is the file that wraps radix.
- The primitives live **wherever your shadcn `aliases.ui` points** — typically
  `@/components/ui` in a single app, or a shared `@org/ui` package in a monorepo.
  That alias dir is the one place radix is wrapped directly.
- A primitive that **doesn't exist yet is generated/added to the primitives
  layer** (`npx shadcn add …`, or hand-authored in the primitives dir) — it is
  **not** hand-rolled with raw radix in app code.

```tsx
// ✅ single-app shadcn — import your own primitive
import { Button } from "@/components/ui/button";
// ❌ radix direct in app/feature code — wrap it in a primitive instead
import * as Dialog from "@radix-ui/react-dialog";
```

### shadcn alias utilities stay internal (universal)

shadcn's primitives use alias utilities (`bg-background`, `text-muted-foreground`,
`bg-primary`). Those stay **internal to the primitives layer** (your `aliases.ui`
dir — the place that wraps shadcn/radix). **App and feature code uses the house
token utilities** (`bg-surface`, `text-fg`), not the shadcn aliases.

### Monorepo convention — a shared UI package owns the primitives (monorepo-only)

**This sub-section is monorepo-specific.** It applies ONLY when a shared UI
package owns the primitives (e.g. crivelo's `@crivelo/ui`). It does **NOT** apply
to a single-app project, where a local `components/ui` is the correct home for
primitives.

- Apps **consume the shared package** and do **not** keep their own
  `components/ui`. Every primitive is imported from the shared package
  (`<pkg>/button`, `<pkg>/dialog`, …); the shared package's `src/ui/**` is the
  only place that wraps radix directly.
- A primitive that doesn't exist yet is added **INTO the shared package**, never
  kept in an app's scope.
- An app MAY add a thin **wrapper** that imports a shared primitive and extends
  it (restyle, add variants/props, bigger sizes). A wrapper imports the shared
  base — it is an extension, **not a new primitive**. Decide case-by-case:
  generally-useful change → push it into the shared primitive; app-specific look
  → app-local wrapper.

```tsx
// ✅ monorepo — import from the shared UI package, not a local components/ui
import { Button } from "@crivelo/ui/button";
// ❌ in this monorepo, an app keeping/​importing its own local primitives
import { Button } from "@/components/ui/button";
```

---

## Compliance checklist

Grep-able banned patterns (the canonical ruleset for both the lint backstop and
the spec-compliance reviewer). Each is a violation **unless** the documented
exception applies.

### Always (Tailwind core)

- `\[(color:)?var\(--` — a design-token `var(--…)` inside a className arbitrary.
  Write the registered utility (`bg-surface`, `text-fg-3`, `border-border`).
  EXEMPT: a true runtime bridge (per-render JS value), an intentionally-unpromoted
  token declared in the spec (e.g. `--focus-ring`), and the token CSS source files.
- `#[0-9a-fA-F]{3,8}` — a raw hex literal in app/component code. Style via token
  utilities. EXEMPT: the token CSS source files (the definition layer).
- `style=\{[^}]*var\(--` — a `var(--…)` inside a JSX `style` prop. EXEMPT: a true
  runtime bridge custom property, and the token CSS sources.
- `style=\{\{` (in new app/component code) — inline `style` outside the
  last-resort cases (computed dimensions, SVG geometry, state-driven transforms).

### shadcn-only (when the repo uses shadcn)

- `from ['"]@?radix-ui` — a direct `@radix-ui` / `radix-ui` import in app/feature
  code (outside the primitives dir). Import the shadcn primitive instead; the
  primitive is the file that wraps radix. EXEMPT: the primitives dir itself
  (detected via `components.json` `aliases.ui` + fallback segments like
  `/components/ui/`, `/ui/src/ui/`). Importing your OWN primitives
  (`@/components/ui/*`) is correct, NOT a violation. (Skip entirely in a no-shadcn
  repo — direct radix is fine there.)
- shadcn alias utilities (`bg-background`, `text-muted-foreground`, `bg-primary`)
  used OUTSIDE the primitives dir — app/feature code uses the house token
  utilities (`bg-surface`, `text-fg`), not the shadcn aliases.
- **Monorepo-only** (a shared UI package owns primitives, e.g. `@crivelo/ui`):
  an app importing/keeping a local `components/ui` instead of consuming the
  shared package — a new primitive goes INTO the shared package; an app may add a
  thin wrapper that extends a shared primitive. This is **not** a universal grep:
  in a single-app project a local `components/ui` is the correct home.
- `setInterval` (for animation) — new JS-driven animation. Use `motion` gated on
  `prefers-reduced-motion`. (Existing usages are grandfathered.)
- `@keyframes` in `.tsx`/`.ts` — keyframes authored in component code. Keyframes
  live in `.css` sources. EXEMPT: `.css` files, and any keyframe `motion` can't express.

## Shared-package API design (when you extend the shared UI / tokens package)

The package **absorbs complexity so consumers don't.** Push business logic,
parsing, guards, and assembly *into* the package; expose the highest-leverage
entry point, not raw building blocks each app re-wires. The test: look at what
every consumer has to write, and **push everything identical down**. Duplicated
boilerplate across apps is the smell that logic leaked out of the package — fix
it by relocating the logic, not by documenting the boilerplate. Design for N
consumers; only genuinely per-app values (the config, the brand glyph, colours)
stay app-local. Prefer a factory/handler over exposed internals when the
integration is otherwise boilerplate.
