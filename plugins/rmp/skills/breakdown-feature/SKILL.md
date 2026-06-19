---
name: breakdown-feature
description: Use after `/rmp:brainstorming` to turn a design doc at `docs/specs/<slug>.md` into a breakdown of tasks with test steps — either as a parent Linear issue + child sub-issues (Linear mode) or as a `## Tasks` checklist in the spec (local mode, no tracker needed). Asks which up front and writes the choice to the spec frontmatter.
user-invocable: true
---

You take a feature spec and turn it into a structured breakdown: one **parent** representing the whole feature, and N **tasks** for each discrete deliverable, each with test steps baked in so `/work-iteration` can verify against them.

**Linear is optional.** The breakdown lives in one of two trackers, chosen per feature:

- **Linear mode** — a parent Linear issue + child sub-issues. Durable, linkable, multi-person. Needs a Linear MCP + `.linear_features.json`.
- **Local mode** — a `## Tasks` checklist appended to the spec file (`docs/specs/<slug>.md`). Zero extra dependencies; ideal for simpler/solo features where Linear is overhead. State lives in the checkboxes.

Generic across projects — don't hardcode team names or project names. Read context from the spec, `CLAUDE.md`, and (in Linear mode) Linear.

## Read first

1. The spec at `docs/specs/<slug>.md` (user may pass the slug as an argument; if not, list specs and ask)
2. `/CLAUDE.md` for any team conventions
3. In **Linear mode only**: `.linear_features.json` at repo root (project-wide Linear config — see Schema below). If missing, set it up before continuing.

## `.linear_features.json` schema

This file holds project-wide Linear context (NOT per-feature). Per-feature state lives in the spec file's frontmatter.

```json
{
  "team_key": "RMP",
  "team_id": "<uuid>",
  "features_project_id": "<uuid>",
  "features_project_name": "<project-name>"
}
```

## Workflow

### 1. Resolve the spec

If user invoked `/breakdown-feature <slug>`, read `docs/specs/<slug>.md`. Otherwise list files in `docs/specs/`, ask which one.

Read the spec. If status frontmatter is anything other than `draft` or unset, warn the user and ask whether to proceed (a breakdown may already exist).

### 2. Choose the tracker

If the spec frontmatter already has `tracker:` set, use that (the user already chose; don't re-ask). Otherwise ask once with `AskUserQuestion`:

> "Track this feature in **Linear** (parent + sub-issues) or **locally** (a `## Tasks` checklist in the spec)? Local needs no Linear setup — good for simpler/solo features."

Default suggestion: **Linear** if `.linear_features.json` exists at the repo root, otherwise **local**. Write the choice to the spec frontmatter (`tracker: linear` or `tracker: local`) immediately, so `/work-iteration` and `/continue-feature` follow the same mode without re-asking.

The drafting (Step 3) and the user-review (Step 4) are identical in both modes — only the materialization (Step 5) differs.

### 3. Ensure Linear project exists — **Linear mode only** (skip in local mode)

Read `.linear_features.json`. If missing or incomplete:

a. Run `mcp__plugin_linear_linear__list_teams` and pick the user's team. If multiple, ask. Capture `team_id` and `team_key`.

b. Run `mcp__plugin_linear_linear__list_projects` filtered to the team. Look for a project that fits "features for this codebase" — match against patterns like `<repo-name> Features`, `<repo-name>` (if no bug-fix variant exists), or similar.

c. If no suitable project exists, ask the user: "No features project found for this team. Create a new project named `<suggested-name>`?" — suggested name should be the repo's project name from `CLAUDE.md` (e.g. "Crema Arena Features") or derived from the package.json name.

d. If they approve, create with `mcp__plugin_linear_linear__save_project`. Capture `project_id` + `project_name`.

e. Write `.linear_features.json` with the captured fields.

### 4. Draft the breakdown (both modes)

The spec is a free-form brainstorming design doc: rmp YAML frontmatter followed by markdown sections (headings, prose, lists — whatever the design dialogue produced). There is no fixed XML schema; read the markdown by meaning, not by tag. The one section you can rely on is **Acceptance criteria** (`/rmp:brainstorming` requires it) — find that heading and use its checkboxes verbatim.

**The feature parent:**
- Title: the feature name (the doc's H1/title, or derive from the slug)
- Summary: 3–5 lines + the Acceptance criteria list copied verbatim from the spec. (In Linear mode this becomes the parent issue's description; in local mode the spec file *is* the parent record, so you don't restate it.)

**The tasks** — one per discrete deliverable. Sources, in order of preference:

1. If the design doc has an explicit breakdown / tasks / milestones / components section, use those items as the starting list.
2. Otherwise, infer the natural units of work from the design — one task per component, surface, endpoint, migration, or phase the design describes. Group by what can be built and verified independently.

If the design is too thin to yield any concrete deliverables, stop and tell the user — suggest they flesh out the spec (re-run `/rmp:brainstorming`) before breaking it down.

Each task MUST carry:
- A one-line summary (its title)
- Its **acceptance criteria** — pull the relevant rows from the spec's Acceptance criteria section
- Its **test steps** — concrete steps that prove the task is done (e.g. "1. Run `npx tsc --noEmit` — exits 0. 2. Visit `/judges`, click 'Add', fill form, submit — judge appears in list.")

Aim for tasks that are 2–8 hours of work each. Ones bigger than that should be split; ones smaller can be combined.

### 5. Review with the user (both modes)

Show the proposed parent + task list as a numbered markdown list. **Stop and wait for approval.** Offer to:
- Edit a specific task's title / acceptance criteria / test steps
- Add a task
- Remove a task
- Reorder
- Merge two

Loop until the user says "create them" / "looks good" or equivalent.

### 6. Materialize the breakdown

**6a — Linear mode.** Create issues: parent first, capture its ID, then children with `parentId` set to the parent's ID.

Use `mcp__plugin_linear_linear__save_issue` for each. Required fields:
- `teamId` (from `.linear_features.json`)
- `projectId` (from `.linear_features.json`)
- `title`
- `description` (markdown — include the `## Acceptance criteria` and `## Test steps` blocks)
- For children: `parentId`

Capture all returned identifiers (`identifier` like "RMP-99" and `id` UUID).

**6b — Local mode.** Append a `## Tasks` section to the spec file (`docs/specs/<slug>.md`) — this is the durable task record; there is no Linear. Use this exact shape so `/work-iteration` and `/continue-feature` can parse and update it:

```markdown
## Tasks

- [ ] <Task title>
  - AC: <acceptance criterion(s) for this task>
  - Test: <test step(s) that prove it's done>
- [ ] <Task title>
  - AC: …
  - Test: …
```

Checkbox states are the contract: `[ ]` todo, `[~]` in progress, `[x]` done. `/work-iteration` flips them and appends the merge/commit ref to a done line (e.g. `- [x] Schema + types — PR #41`). Order the list in dependency order (foundation tasks first, whole-app gate last) — `/work-iteration` walks it top-to-bottom.

### 7. Update spec frontmatter (both modes)

Edit the spec file's YAML frontmatter:
```yaml
status: planned
tracker: <linear | local>   # the choice from Step 2
feature_branch: feature/<slug>
# Linear mode only:
linear_project_id: <features_project_id>
linear_parent_issue: <parent identifier, e.g. RMP-99>
```
In local mode leave `linear_project_id` / `linear_parent_issue` empty.

### 8. Report

Tell the user:
- **Linear mode:** parent issue link/identifier + the sub-issue identifiers (bulleted)
- **Local mode:** the count of tasks written to the spec's `## Tasks` section
- Spec frontmatter updated (`tracker`, `status: planned`, `feature_branch`)
- Next step: `/work-iteration <slug>` to start the first task, OR commit the spec change first

## Constraints

- **Never materialize without explicit user approval of the list** (Step 5). No "I'll just create them and let you adjust." Applies to both Linear issues and the local `## Tasks` write.
- **Don't lose work** if Linear MCP fails mid-create (Linear mode). If a child creation errors, surface it; offer to retry. Don't leave the spec frontmatter half-updated.
- **Don't create duplicates.** Before re-running, check for an existing breakdown: in Linear mode a set `linear_parent_issue`; in local mode an existing `## Tasks` section. If found, warn and offer to skip / update existing / start fresh.
- **Don't add nested sub-sub-issues.** Exactly two levels: parent + tasks. (Local mode: a flat checklist; sub-bullets are AC/Test, not nested tasks.)
- **Test steps must be runnable.** Each test step is a command, a UI click sequence, or an assertion that something appears. No vague "verify it works."
