---
name: breakdown-feature
description: Use after `/spec-feature` to turn a spec file at `docs/specs/<slug>.md` into a parent Linear issue + child sub-issues with test steps in their descriptions. Detects or creates the project's features Linear project. Writes Linear IDs back into the spec's frontmatter.
user-invocable: true
---

You take a feature spec and turn it into a structured Linear breakdown: one **parent issue** representing the whole feature, and N **child sub-issues** for each discrete deliverable. Sub-issues get test steps baked into their descriptions so `/work-iteration` can verify against them.

Generic across projects — don't hardcode team names or project names. Read context from the spec, `CLAUDE.md`, and Linear.

## Read first

1. The spec at `docs/specs/<slug>.md` (user may pass the slug as an argument; if not, list specs and ask)
2. `.linear_features.json` at repo root (project-wide Linear config — see Schema below). If missing, set it up before continuing.
3. `/CLAUDE.md` for any team conventions

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

Read the spec. If status frontmatter is anything other than `draft` or unset, warn the user and ask whether to proceed (issues may already exist).

### 2. Ensure Linear project exists

Read `.linear_features.json`. If missing or incomplete:

a. Run `mcp__plugin_linear_linear__list_teams` and pick the user's team. If multiple, ask. Capture `team_id` and `team_key`.

b. Run `mcp__plugin_linear_linear__list_projects` filtered to the team. Look for a project that fits "features for this codebase" — match against patterns like `<repo-name> Features`, `<repo-name>` (if no bug-fix variant exists), or similar.

c. If no suitable project exists, ask the user: "No features project found for this team. Create a new project named `<suggested-name>`?" — suggested name should be the repo's project name from `CLAUDE.md` (e.g. "Crema Arena Features") or derived from the package.json name.

d. If they approve, create with `mcp__plugin_linear_linear__save_project`. Capture `project_id` + `project_name`.

e. Write `.linear_features.json` with the captured fields.

### 3. Draft the issue tree

**Parent issue:**
- Title: spec's H1 (e.g. "Photo Capture v2")
- Description: a 3–5 line summary + link to the spec file (`docs/specs/<slug>.md`) + the Acceptance criteria list copied verbatim from the spec
- Labels: `feature` if the team has one (check via `list_issue_labels`)
- Priority: ask user or default to Medium

**Child sub-issues** — one per discrete deliverable. Sources, in order of preference:

1. If the spec has a `## Breakdown sketch` section, use those bullets as the starting list.
2. Otherwise, draft from `## Surfaces affected` + `## Data model` + `## API surface` + `## UI / Copy` — one issue per natural unit of work.

Each child issue's description MUST contain:
- A one-line summary
- A `## Acceptance criteria` block — pull the relevant rows from the spec's acceptance list
- A `## Test steps` block — concrete steps that prove the issue is done (e.g. "1. Run `npx tsc --noEmit` — exits 0. 2. Visit `/judges`, click 'Add', fill form, submit — judge appears in list.")

Aim for sub-issues that are 2–8 hours of work each. Ones bigger than that should be split; ones smaller can be combined.

### 4. Review with the user

Show the proposed parent + sub-issue list as a numbered markdown list. **Stop and wait for approval.** Offer to:
- Edit a specific issue's title / description
- Add an issue
- Remove an issue
- Reorder
- Merge two

Loop until user says "create them" or equivalent.

### 5. Create in Linear

Order: parent first, capture its ID, then children with `parentId` set to the parent's ID.

Use `mcp__plugin_linear_linear__save_issue` for each. Required fields:
- `teamId` (from `.linear_features.json`)
- `projectId` (from `.linear_features.json`)
- `title`
- `description` (markdown)
- For children: `parentId`

Capture all returned identifiers (`identifier` like "RMP-99" and `id` UUID).

### 6. Update spec frontmatter

Edit the spec file's YAML frontmatter to fill in:
```yaml
status: planned
linear_project_id: <features_project_id>
linear_parent_issue: <parent identifier, e.g. RMP-99>
feature_branch: feature/<slug>
```

### 7. Report

Tell the user:
- Parent issue link/identifier
- Number of sub-issues created (and their identifiers as a bulleted list)
- Spec frontmatter updated
- Next step: `/work-iteration <slug>` to start the first sub-issue, OR commit the spec change first

## Constraints

- **Never create issues without explicit user approval of the list.** No "I'll just create them and let you adjust."
- **Don't lose work** if Linear MCP fails mid-create. If a child creation errors, surface it; offer to retry. Don't leave the spec frontmatter half-updated.
- **Don't create duplicates.** If the spec frontmatter already has `linear_parent_issue` set, warn before re-running and offer to skip / update existing / create new with a `(v2)` suffix.
- **Don't add nested sub-sub-issues.** This skill creates exactly two levels: parent + children.
- **Test steps must be runnable.** Each test step is a command, a UI click sequence, or an assertion that something appears. No vague "verify it works."
