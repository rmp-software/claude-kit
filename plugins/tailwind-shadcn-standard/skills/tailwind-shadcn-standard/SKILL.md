---
name: tailwind-shadcn-standard
description: The RMP styling standard for Tailwind v4 + shadcn + design-token codebases. Use BEFORE writing or editing any UI — components, screens, styling, className work, choosing a primitive, adding a token, or reviewing styling. Covers the @theme token vocabulary, the no-var()-in-className rule, buy-commodity-build-domain, the shared UI primitive boundary, the runtime-bridge exception, scale-snapping, and a grep-able compliance checklist.
---

# Tailwind v4 + shadcn styling standard

How to style in a Tailwind v4 + shadcn + design-token codebase. The tokens are
the utility vocabulary; primitives are bought, not hand-rolled; the domain is
built. This is generalized — wherever it says "the shared UI package", "the
tokens package", or "the app's `@theme`", read your repo's actual names
(e.g. `@crivelo/ui`, `@crivelo/tokens`, `apps/<app>/app/*-theme.css`).

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

### shadcn alias utilities stay internal

shadcn's primitives use alias utilities (`bg-background`, `text-muted-foreground`,
`bg-primary`). Those are **internal to the shared UI package's `src/ui/**`** —
the place that wraps shadcn/radix. **App and feature code uses the house
neutrals** (`bg-surface`, `text-fg`), not the shadcn aliases.

## 3. Buy commodity UI, build the domain

Don't re-implement a solved interaction. **Buy** the commodity — modal, drawer,
toast, dialog, focus-trap, animation — from an established library. **Build** the
domain — the bespoke product logic and screens. The commodity is a liability to
hand-roll; the domain is the product.

The toolkit:
- **shadcn primitives** for commodity UI.
- **`cn()`** (clsx + tailwind-merge) for conditional/variant classes via
  className lookups (`Record<status, classes>`), never an inline `style` ternary.
- **`motion`** (`motion/react`) for animation, gated on `prefers-reduced-motion`.
  No new manual `setInterval` animation loops; no new `@keyframes` authored in
  component (`.tsx`/`.ts`) code — keyframes live in `.css` sources.

### The shared UI package is the single source of truth for primitives

- **Apps NEVER import `radix-ui` / `@radix-ui/*` / shadcn registry paths
  directly.** Every primitive is imported from the shared UI package
  (`<pkg>/button`, `<pkg>/dialog`, …).
- A primitive that **doesn't exist yet is added TO the shared package**, never
  kept in an app's scope.
- An app MAY add a thin **wrapper** that imports a shared primitive and extends
  it (restyle, add variants/props, bigger sizes). A wrapper imports the shared
  base — it is an extension, **not a new primitive**. Decide case-by-case:
  generally-useful change → push it into the shared primitive; app-specific look
  → app-local wrapper.
- The only file that wraps radix/shadcn directly is the shared UI package's own
  `src/ui/**`.

```tsx
import { Button } from "@crivelo/ui/button";   // ✅ from the shared package
import * as Dialog from "@radix-ui/react-dialog"; // ❌ radix direct in an app
```

## 4. The runtime-bridge exception

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

## 5. Scale-snapping and arbitraries

Spacing/size follows the **scale** (`gap-2.5`, `p-4`, `rounded-md`). **Snap a
`[NNpx]` to a scale step ONLY on an exact match** — never nearest-step rounding.
Genuinely off-scale one-offs stay documented arbitraries (`min-h-[44px]`,
`max-w-[1060px]`, an odd font size). An intentionally-unpromoted token (e.g. a
focus ring kept as `ring-[var(--focus-ring)]`) is a documented arbitrary, not a
violation — but it's the exception, declared in the spec.

## 6. Inline `style` is a last resort

Only for what cannot be a utility: computed dimensions (progress-bar fill width),
SVG geometry, state-driven transforms. With `motion`, animation rarely needs a
manual `style`. No `var(--…)` inside a `style` prop except a true runtime bridge
(a custom property carrying a per-render JS value).

## Compliance checklist

Grep-able banned patterns (the canonical ruleset for both the lint backstop and
the spec-compliance reviewer). Each is a violation **unless** the documented
exception applies.

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
- `from ['"]@?radix-ui` (and `@/components/ui/*` shadcn registry paths) — an app
  importing radix/shadcn directly. Import from the shared UI package instead.
  EXEMPT: the shared UI package's own `src/ui/**`.
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
