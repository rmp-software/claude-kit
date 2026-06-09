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
3. `docs/specs/*.md` if present — **scan, don't slurp.** List the filenames and read each one's `<overview>` (or first paragraph) to learn tone and what's already decided. Read a prior spec *in full* only when it's topically adjacent to this feature (touches the same surface/data). Reading every historical spec end-to-end is wasted context once the project has more than a handful.

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

**Spec template** — YAML frontmatter (the downstream skills parse it) followed by an XML body that mirrors `app_spec.txt`'s structure: same tag vocabulary, same prescriptive voice, scoped to one feature. Keep the frontmatter exactly as below — `/breakdown-feature` and `/continue-feature` read those keys.

```markdown
---
slug: <kebab-case-slug>
status: draft
created: <YYYY-MM-DD>
linear_project_id:
linear_parent_issue:
feature_branch:
---

<feature_specification>

  <feature_name><!-- e.g. Judge Onboarding --></feature_name>

  <overview>
    <!-- 1-2 paragraphs: what this is, who uses it, why now. Plain language —
         no jargon a new contributor wouldn't know. -->
  </overview>

  <problem>
    <!-- What breaks today, what's missing, what this unblocks. Link incident
         reports, user feedback, or Linear issues if available. -->
  </problem>

  <scope>
    <in_scope>
      <!-- - bullet -->
    </in_scope>
    <out_of_scope>
      <!-- Explicit cuts, stated so we don't argue about them later. -->
    </out_of_scope>
  </scope>

  <surfaces_affected>
    <!-- Pages, routes, APIs, or CLI commands that change. Mark new vs modified.
         (Mirrors app_spec.txt <surfaces>, scoped to this feature.)
         - `app/dashboard/judges/page.tsx` — new
         - `app/api/judges/route.ts` — modified (add POST) -->
  </surfaces_affected>

  <data_model>
    <!-- New tables/columns, migrations, indices. Omit this section if no DB change.
    ```sql
    ALTER TABLE events ADD COLUMN judges_count INT NOT NULL DEFAULT 3;
    ``` -->
  </data_model>

  <api_surface>
    <!-- New routes: request/response shape and error cases. Omit if no API change.
    POST /api/events/:id/judges
    Body: { name: string, email: string }
    Response: { id, name, email }   Errors: 409 if email exists, 422 on validation -->
  </api_surface>

  <ui_copy>
    <!-- Key strings in the project's primary language (check CLAUDE.md / app_spec.txt
         for locale + copy rules — match them exactly). New components. Layout sketch
         in ASCII or words. If the feature introduces prescribed strings that should
         hold app-wide, promote them into the app's app_spec.txt <copy_examples> so the
         spec-compliance reviewer enforces them. -->
  </ui_copy>

  <acceptance_criteria>
    <!-- Testable assertions, "Given X, when Y, then Z." These map 1:1 to the test
         steps /breakdown-feature bakes into each Linear sub-issue — write them precisely.
    - [ ] Given an authenticated organizer, when they POST /api/judges with a valid body, then a judge row is created and 201 is returned
    - [ ] Given … -->
  </acceptance_criteria>

  <risks>
    <!-- What could go wrong, what needs a human decision, what depends on other
         in-flight work. -->
  </risks>

  <breakdown_sketch>
    <!-- Optional. If you already sense how this splits into tasks, list them —
         /breakdown-feature uses this as its starting list. Otherwise leave empty.
    - Schema migration + types
    - API route POST /api/judges
    - Judge list UI -->
  </breakdown_sketch>

</feature_specification>
```

Fill what you can from the problem statement and project context; leave honest `<!-- TODO: confirm with user — … -->` comments for what you don't know. Omit `<data_model>` / `<api_surface>` / `<ui_copy>` entirely when they don't apply (a backend-only feature has no `<ui_copy>`; a frontend-only one has no `<api_surface>`) — don't leave empty stubs. The XML tags exist so `/breakdown-feature` can parse sections deterministically — keep the tag names exactly as written.

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
