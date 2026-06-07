---
name: spec-feature
description: Use when planning a new feature that's bigger than a one-PR change. Walks the user through writing a feature spec to `docs/specs/<slug>.md` using a structured template, grounded in the project's existing conventions (CLAUDE.md, `app_spec.txt`, prior specs). Output is the input for `/breakdown-feature` and `/work-iteration`.
user-invocable: true
---

You help the user write a feature spec — a durable, committed planning document that's the source of truth for what's being built and how it'll be verified. Specs live at `docs/specs/<slug>.md` and are designed to be read by humans, future Claude sessions, and downstream skills (`/breakdown-feature`, `/work-iteration`, `/continue-feature`).

## Read first — project context

Always load before drafting:

1. `/CLAUDE.md` (project conventions, branch policy, copy rules)
2. `/app_spec.txt` if present (the canonical surface spec — match its voice and section style)
3. `docs/specs/*.md` if present (prior specs to match tone and avoid repeating decisions)

This skill is generic — it doesn't know what kind of project this is. Always derive voice, language, and conventions from the files above. **Never assume pt-BR / specific tech stack / specific domain unless the project files confirm it.**

## Workflow

### 1. Confirm the feature with the user

Before writing anything, get a 1-paragraph problem statement from the user. If they gave one already, restate it back: "So you want to ___ because ___. Acceptance is when ___." Wait for confirmation.

Ask one or two clarifying questions ONLY if the answer would shape the spec's structure (e.g. "is this user-facing or internal-only?"). Do not interrogate.

### 2. Pick a slug

Derive a kebab-case slug from the feature name. Examples: `photo-capture-v2`, `judge-onboarding`, `bracket-share-link`. Confirm with user if ambiguous.

Spec path: `docs/specs/<slug>.md`. If `docs/specs/` doesn't exist, create it.

### 3. Draft the spec

Use the template below. Fill what you can from the problem statement and project context. Leave honest TODOs for what you need from the user — don't invent details. Sections in the template are ordered for skim-readability: a contributor should be able to read just *Overview* and *Acceptance criteria* to know what's being built.

**Spec template:**

```markdown
---
slug: <kebab-case-slug>
status: draft
created: <YYYY-MM-DD>
linear_project_id:
linear_parent_issue:
feature_branch:
---

# <Feature name>

## Overview

1–2 paragraphs. What is this, who uses it, why now. Plain language — no jargon a new contributor wouldn't know.

## Problem / motivation

What breaks today, what's missing, what does this unblock. Link to incident reports, user feedback, or Linear issues if available.

## Scope

**In scope:**
- bullet
- bullet

**Out of scope (explicit cuts):**
- bullet (so we don't argue about it later)
- bullet

## Surfaces affected

Which pages, routes, APIs, or CLI commands change. Mark new vs modified. Example:
- `app/dashboard/judges/page.tsx` — new
- `app/api/judges/route.ts` — modified (add POST)
- `lib/bracket.ts` — modified (handle judge count)

## Data model

New tables/columns, migrations needed, indices. Skip this section if no DB change.

```sql
-- example
ALTER TABLE events ADD COLUMN judges_count INT NOT NULL DEFAULT 3;
```

## API surface

New routes, request/response shape, error cases. Skip if no API change.

```
POST /api/events/:id/judges
Body: { name: string, email: string }
Response: { id: string, name: string, email: string }
Errors: 409 if email exists, 422 on validation
```

## UI / Copy

Key strings in the project's primary language (check `CLAUDE.md` / `app_spec.txt` for the project's copy locale). New components needed. Layout sketch in ASCII or words.

## Acceptance criteria

Testable assertions. Format: "Given X, when Y, then Z." These map 1:1 to test steps in Linear sub-issues — so write them precisely.

- [ ] Given an authenticated organizer, when they POST /api/judges with valid body, then a judge row is created and 201 is returned
- [ ] Given …

## Risks / open questions

What could go wrong, what needs a human decision, what depends on other in-flight work.

## Breakdown sketch (optional)

If you already have a sense of how this breaks into tasks, list them here. `/breakdown-feature` will use this as a starting point. Otherwise leave empty.

- Schema migration + types
- API route POST /api/judges
- Judge list UI
- …
```

### 4. Write the file

Use the Write tool. Do not run any other tools to "verify" the file — Write either succeeds or errors loudly.

### 5. Confirm and hand off

After writing, summarize in 3 lines:
- What's in the spec
- What's still TODO (any sections the user needs to fill)
- Next step: `/breakdown-feature <slug>` to create Linear issues, or edit `docs/specs/<slug>.md` further first

## What this skill does NOT do

- Create Linear issues (that's `/breakdown-feature`)
- Write code (that's `/work-iteration`)
- Pick a tech stack or design (those come from the project's existing files)
- Commit the spec file (the user does that, or they invoke `/commit` after)

## Style notes for the spec text itself

- Keep it short. A good spec is 1–2 screens of markdown. If it's longer, the feature should probably be split.
- Specify behavior, not implementation. Acceptance criteria > "use library X".
- Honest TODOs are better than invented details. If you don't know what the user wants, write `TODO: confirm with user — ___` and move on.
- Match the voice of `CLAUDE.md` / existing specs. Don't introduce a new tone.
