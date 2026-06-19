---
name: continue-feature
description: Use to resume work on a feature across sessions — reads the spec file + parent Linear issue state, reports progress (done vs total sub-issues), shows the next pending task, and optionally kicks off `/work-iteration` for it.
user-invocable: true
---

You orient a fresh session to a feature already in progress. The spec file and parent Linear issue are the source of truth — between them, you can reconstruct everything: what's the feature, what's done, what's next, what branch is open.

## When to use

- Coming back to a feature after a break
- Picking up a feature someone else started
- Sanity check: "where are we on `<slug>`?"

## Read first

1. Spec at `docs/specs/<slug>.md` (slug from argument; if not given, list specs with status != `draft` and ask)
2. Spec frontmatter for `tracker`, `feature_branch`, and (Linear mode) `linear_parent_issue`
3. `/CLAUDE.md` for branch policy

## Tracker mode

`/breakdown-feature` recorded `tracker:` in the frontmatter. Read it: in **`linear`** mode the task state is in Linear; in **`local`** mode it's the `## Tasks` checklist in the spec. The report (Step 4) and next-step (Step 5) are the same shape either way — only where you read progress (Step 2) differs.

## Workflow

### Step 1 — Resolve the spec

If user invoked `/continue-feature <slug>`, read that. Otherwise:
- List `docs/specs/*.md`
- Show with status from frontmatter
- Filter to `planned` and `in-progress` by default; user can expand to `draft` if they want
- Ask which to resume

If the spec has `status: draft`, or no breakdown yet (no `tracker`, and neither a `linear_parent_issue` nor a `## Tasks` section), tell the user it hasn't been broken down — suggest `/breakdown-feature <slug>` instead.

### Step 2 — Pull task state

- **Linear mode:** run `mcp__plugin_linear_linear__get_issue` on the parent (from frontmatter); pull its sub-issues with current state and assignee.
- **Local mode:** parse the spec's `## Tasks` section — `[x]` = done, `[~]` = in progress, `[ ]` = todo; read any appended PR refs.

Compute (both modes):
- Total tasks
- Done count
- In Progress count (and which one — likely has an open sub-branch)
- Todo count
- Blocked / Canceled count (Linear mode; local mode has no blocked/canceled state)

### Step 3 — Check git state

```bash
git status --short
git branch --show-current
git fetch origin
git log --oneline feature/<slug>...origin/main | head -10  # commits ahead
```

Check whether the feature branch exists locally and on remote. Check for any open sub-PR via `gh pr list --base feature/<slug>`.

### Step 4 — Report

Concise — 8–10 lines max:

```
Feature: <title> (spec: docs/specs/<slug>.md)
Tracker: linear (parent <identifier> · status <state>)  |  local (## Tasks in spec)
Progress: <done>/<total> tasks complete

Done:
  - <id/title>
  - …

In progress:
  - <id/title> (PR #<n> open, branch feature/<slug>-<id>)  [if any]

Next up:
  - <id/title>

Branch state: feature/<slug> · <N> commits ahead of main · clean | dirty
```

### Step 5 — Offer next step

Based on state, recommend ONE next action:

- All tasks done → "Open umbrella PR `feature/<slug>` → main with `/commit-push-pr` (or `gh pr create --base main`)."
- A task is In Progress with an open PR → "Review/merge #<n>, or work on a different task."
- Todos remain and no In Progress → "Run `/work-iteration <slug>` to tackle next: <id/title>."
- Branch is dirty → "Uncommitted changes on `<current branch>` — stash or commit before proceeding."
- Branch is behind main → "Pull main into `feature/<slug>` before continuing."

Wait for the user's confirmation before doing anything. This skill is read-only by default — its job is orientation, not action.

## Things to never do

- **Never auto-trigger `/work-iteration`.** Always wait for explicit user confirmation. Surprise automation breaks user trust.
- **Never make assumptions about state.** If the tracker and the spec disagree (e.g. the Linear parent is Done but spec status is `in-progress`, or `## Tasks` are all `[x]` but status isn't `done`), surface the conflict — don't pick one silently.
- **Never modify the spec from this skill.** It's read-only orientation. Task-state updates (Linear state, or `## Tasks` checkboxes) happen in `/work-iteration`; frontmatter changes happen at breakdown/completion.
