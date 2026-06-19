---
name: brainstorming
description: THE front door for starting any feature in an rmp-harness project — use for "let's build X", "start/plan a new feature", "brainstorm a feature", or before entering plan mode for feature work. Runs the same collaborative brainstorming dialogue as superpowers:brainstorming, but lands the design doc at `docs/specs/<slug>.md` with rmp frontmatter and hands off to `/rmp:breakdown-feature` (NOT superpowers writing-plans). In an rmp project this SUPERSEDES `superpowers:brainstorming` — prefer it whenever brainstorming a feature, so the spec lands where the harness expects.
user-invocable: true
---

You help the user turn a feature idea into a committed design doc — the source of truth for what's being built and how. The exploration and design work is delegated to the **`superpowers:brainstorming`** skill; this skill only adapts its output so the rest of the rmp harness (`/breakdown-feature`, `/work-iteration`, `/continue-feature`) can consume it.

The design doc lives at `docs/specs/<slug>.md` (NOT brainstorming's default `docs/superpowers/specs/` location) and carries rmp YAML frontmatter on top of brainstorming's free-form markdown body.

## What to do

### 1. Run the brainstorming session

Invoke the `superpowers:brainstorming` skill and follow it as written — explore project context, ask questions one at a time, propose 2–3 approaches, present the design in sections, get the user's approval. That skill owns the conversation; don't reinvent it here.

### 2. Apply these two overrides to brainstorming's defaults

Brainstorming has two terminal steps you MUST override for the rmp harness:

**Override A — output location and frontmatter.** When brainstorming reaches "Write design doc", do NOT write to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`. Instead:

- Derive a kebab-case `<slug>` from the feature name (e.g. `photo-capture-v2`, `judge-onboarding`). Confirm it with the user if ambiguous.
- Write the design doc to `docs/specs/<slug>.md`. Create `docs/specs/` if it doesn't exist.
- Prepend this exact YAML frontmatter block (the downstream skills parse these keys — keep the names and leave the Linear fields empty):

  ```yaml
  ---
  slug: <kebab-case-slug>
  status: draft
  created: <YYYY-MM-DD>
  tracker:            # set by /breakdown-feature — linear | local
  linear_project_id:  # linear mode only
  linear_parent_issue: # linear mode only
  feature_branch:
  ---
  ```

  Leave `tracker` empty — `/breakdown-feature` asks the user whether to track the feature in Linear or locally (a `## Tasks` checklist appended to this spec) and fills it in. Don't pick a tracker here.

- The body below the frontmatter is brainstorming's free-form design markdown — keep its sections as the dialogue produced them. There is **no required XML structure**; write whatever best captures the design.
- One requirement for the body: it MUST contain a clear, testable **Acceptance criteria** section (a `## Acceptance criteria` heading with "Given X, when Y, then Z" checkboxes). `/breakdown-feature` turns these into the test steps baked into each Linear sub-issue, so write them precisely. If the brainstormed design didn't surface acceptance criteria, add them before writing the file.

Run brainstorming's spec self-review and user-review gate against this file at `docs/specs/<slug>.md`.

**Override B — handoff.** Brainstorming's terminal step is "invoke the writing-plans skill". Do NOT do that. The rmp harness's next step is **`/breakdown-feature <slug>`** (which creates the Linear parent + sub-issues), then `/work-iteration`. Don't invoke `writing-plans`, `frontend-design`, or any implementation skill.

### 3. Confirm and hand off

After the file is written and the user has reviewed it, summarize in ~3 lines:
- What's in the design
- Anything still open / TODO the user needs to resolve
- Next step: `/breakdown-feature <slug>` to create Linear issues, or edit `docs/specs/<slug>.md` further first

## What this skill does NOT do

- Run the brainstorming dialogue itself — that's `superpowers:brainstorming`. This skill is the rmp adapter around it.
- Create Linear issues (that's `/breakdown-feature`)
- Write code or implementation plans (that's `/work-iteration`; do NOT invoke `writing-plans`)
- Pick a tech stack or design unilaterally (those come out of the brainstorming dialogue + the project's existing files)
- Commit anything beyond the design doc brainstorming commits (the user drives the rest)

## Notes

- Match the project's voice: brainstorming explores `CLAUDE.md`, `app_spec.txt`, and prior `docs/specs/*.md` as context. Don't assume a locale, stack, or domain the project files don't confirm.
- Keep the design focused. If brainstorming reveals the feature is really several independent subsystems, decompose first (brainstorming covers this) and write one spec per sub-feature, each with its own `<slug>`.
