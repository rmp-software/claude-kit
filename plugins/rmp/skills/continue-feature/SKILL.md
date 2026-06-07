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
2. Spec frontmatter for `linear_parent_issue` and `feature_branch`
3. `/CLAUDE.md` for branch policy

## Workflow

### Step 1 — Resolve the spec

If user invoked `/continue-feature <slug>`, read that. Otherwise:
- List `docs/specs/*.md`
- Show with status from frontmatter
- Filter to `planned` and `in-progress` by default; user can expand to `draft` if they want
- Ask which to resume

If the spec has `status: draft` or empty Linear frontmatter, tell the user it hasn't been broken down — suggest `/breakdown-feature <slug>` instead.

### Step 2 — Pull Linear state

Run `mcp__plugin_linear_linear__get_issue` on the parent (from frontmatter). Pull its sub-issues with current state and assignee.

Compute:
- Total sub-issues
- Done count
- In Progress count (and which one — likely has an open sub-branch)
- Todo count
- Blocked / Canceled count

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
Parent issue: <identifier> · status <state>
Progress: <done>/<total> sub-issues complete

Done:
  - <id> <title>
  - …

In progress:
  - <id> <title> (PR #<n> open, branch feature/<slug>/<id>)  [if any]

Next up:
  - <id> <title>

Branch state: feature/<slug> · <N> commits ahead of main · clean | dirty
```

### Step 5 — Offer next step

Based on state, recommend ONE next action:

- All sub-issues done → "Open umbrella PR `feature/<slug>` → main with `/commit-push-pr` (or `gh pr create --base main`)."
- A sub-issue is In Progress with an open PR → "Review/merge #<n>, or work on a different sub-issue."
- Todos remain and no In Progress → "Run `/work-iteration <slug>` to tackle next: <id>."
- Branch is dirty → "Uncommitted changes on `<current branch>` — stash or commit before proceeding."
- Branch is behind main → "Pull main into `feature/<slug>` before continuing."

Wait for the user's confirmation before doing anything. This skill is read-only by default — its job is orientation, not action.

## Things to never do

- **Never auto-trigger `/work-iteration`.** Always wait for explicit user confirmation. Surprise automation breaks user trust.
- **Never make assumptions about state.** If Linear and the spec disagree (e.g. parent is Done but spec status is `in-progress`), surface the conflict — don't pick one silently.
- **Never modify the spec frontmatter from this skill.** Updates happen in `/work-iteration` (per sub-issue) and at feature completion (manually or via `/breakdown-feature` if re-scoping).
