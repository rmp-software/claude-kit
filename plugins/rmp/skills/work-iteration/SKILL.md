---
name: work-iteration
description: Use to execute one sub-issue from a feature breakdown — picks the next pending sub-issue under a spec's parent Linear issue, manages the feature branch + sub-PR, dispatches a coding subagent to implement, then an adversarial Sonnet reviewer subagent. Enforces evidence gates (tsc, dev server, screenshot/test) and caps retries at 3.
user-invocable: true
---

You execute exactly one sub-issue under a feature's Linear parent — implementing, reviewing, committing, and opening a PR into the feature branch. You orchestrate; the actual code-writing and code-reviewing happen in **separate subagents** with isolated context. This separation is intentional and based on Anthropic's harness-design findings: agents reviewing their own work systematically overclaim quality.

## When to use

After `/breakdown-feature` has created the issue tree. Each invocation handles one sub-issue.

## Read first

1. The spec at `docs/specs/<slug>.md` (slug from user argument; if not provided, list specs with status `planned` or `in-progress` and ask)
2. Spec frontmatter — must have `linear_parent_issue` and `feature_branch` set. If not, abort and tell user to run `/breakdown-feature` first.
3. `/CLAUDE.md` for branch policy, test commands, copy rules
4. `.linear_features.json` for Linear team/project IDs

## Workflow

### Step 1 — Identify the next sub-issue

Run `mcp__plugin_linear_linear__get_issue` on the parent (from spec frontmatter). Pull its sub-issues. Pick the first one in `Todo` state (lowest sort order if multiple).

If none are Todo:
- All Done → tell the user the feature is complete; suggest opening the umbrella PR from `feature/<slug>` → main
- Some In Progress → ask user whether to resume one or move past

Record: `<issue-identifier>` (e.g. `RMP-100`), `<issue-title>`, `<issue-description>` (with test steps).

### Step 2 — Branch management

Make sure we're on the right branch:

```bash
git fetch origin
# Ensure feature branch exists locally and is current
if ! git show-ref --verify --quiet refs/heads/feature/<slug>; then
  git checkout -b feature/<slug> origin/main
else
  git checkout feature/<slug>
  git pull origin feature/<slug> 2>/dev/null || true  # may not exist on remote yet
fi
# Create sub-branch off feature
# Use a HYPHEN, not a slash, between <slug> and <issue-id>: git refs can't be both
# a file and a directory at the same path. `feature/<slug>` as a branch blocks
# `feature/<slug>/<issue-id>` from being created. Hyphen avoids the collision.
git checkout -b feature/<slug>-<issue-identifier-lowercase>
```

**Never branch directly off main for a sub-issue.** Always off the feature branch.

### Step 3 — Mark the issue In Progress in Linear

Use `mcp__plugin_linear_linear__save_issue` with `stateId` for the team's "In Progress" workflow state. Look it up via `mcp__plugin_linear_linear__list_issue_statuses` if you don't have it cached.

### Step 4 — Dispatch the coding subagent

Use the `Agent` tool. Subagent type: `general-purpose` (broadest tool access). Use the session's default model — don't pin a version.

Prompt structure (compose with full context — the subagent has no conversation history):

```
You are implementing one sub-issue of a feature for [project-name from CLAUDE.md].

=== Project context ===
Read these files before touching anything:
1. /CLAUDE.md
2. docs/specs/<slug>.md
3. Any files mentioned in the issue's "Surfaces affected" section

=== The sub-issue ===
ID: <identifier>
Title: <title>
Description (includes acceptance criteria and test steps):
<full description body>

=== Your task ===
1. Read the project context.
2. Implement the change. Match existing patterns in `app/` (or equivalent source dir). Use existing primitives — don't create new abstractions unless the issue requires it.
3. Run the test steps from the issue description literally — every step must produce its claimed outcome.
4. Run the project's verification gates:
   - `npx tsc --noEmit` (or the project's type-check command from CLAUDE.md) — must exit 0
   - Boot the dev server (the command from CLAUDE.md) — must serve without error
   - **Browser-based verification is mandatory.** Use a real browser tool (Playwright MCP, Chrome DevTools MCP, Puppeteer — any tool that drives a real browser). **Never use `curl`, `wget`, or other shell-based HTTP requests as evidence** — they miss auth/cookies/CSP/CSRF and return misleading green checks on rendered error pages.
   - For UI work: navigate to the page, exercise the new behavior in the UI, take a screenshot. Save to `.playwright-mcp/<issue-id>-<step>.png`.
   - For API work: drive the UI that calls the route (preferred), OR call the route via `fetch()` from the browser console using `mcp__playwright__browser_evaluate` / `mcp__plugin_chrome-devtools-mcp_chrome-devtools__evaluate_script`, OR capture the request via `browser_network_requests` / `list_network_requests`. Always inside a browser context.
   - For server-only changes (migrations, jobs, internal libs with no HTTP surface): exercise the change through a page that triggers it via the browser, OR write a temporary script that the test runner executes. No raw shell HTTP either way.
   - **Evidence artifact paths (strict):** EVERY artifact you write — screenshots, evidence JSON, network logs — MUST live under `.playwright-mcp/` and be named `<issue-id>-<label>.<ext>` (e.g. `.playwright-mcp/rmp-110-evidence.json`). That directory is gitignored; the repo root is NOT. A bare relative filename (e.g. `evidence.json`) resolves to the repo root and pollutes the working tree — do not do this. When a tool only accepts a filename (some screenshot tools default to their own output dir), still pass a path beginning `.playwright-mcp/`. Before you finish, run `ls .playwright-mcp/<issue-id>-*` to confirm every artifact landed there, and `git status --short` to confirm you left NO new files at the repo root.
5. Report back with:
   - Files changed (paths only)
   - Evidence artifacts (paths to screenshots, command outputs)
   - Any test step that did NOT pass and why
   - Any acceptance criteria you could not verify and why

DO NOT commit. DO NOT push. DO NOT create a PR. Stop after evidence is gathered.

If you cannot complete the task (missing dependency, ambiguous requirement, contradicts existing code), STOP and report what you found. Do not invent or skip steps.
```

### Step 5 — Verify the evidence

Before invoking the reviewer, double-check what the coding agent reported:

- Read each evidence artifact path it cited — confirm the files exist.
- Run `git diff` and review the actual changes — they must match what the agent claimed to change.
- Run `npx tsc --noEmit` yourself once more. If it errors, do not proceed.
- **Sweep stray evidence files.** Run `git status --short` and check for any new files at the repo root (or outside `.playwright-mcp/`) that are clearly evidence artifacts — coding subagents sometimes write `*-evidence.json` / `*.png` to cwd despite instructions. Move them into `.playwright-mcp/` (`mv <file> .playwright-mcp/`) so the working tree stays clean and they don't get committed. Only the actual source changes should remain staged for the sub-PR.

If anything is missing or fabricated, treat it as a retry (go to Step 7 with a coder retry, not a reviewer round).

### Step 6 — Dispatch the adversarial reviewer(s)

Two review axes run as **separate subagents**: a correctness reviewer (always) and a spec-compliance reviewer (when the diff touches user-facing surfaces). Both must clear before Step 7's APPROVE.

**Dispatch them CONCURRENTLY when both apply** — put both `Agent` calls in a *single message* so they run in parallel. They're independent and you block on both before deciding the verdict, so sequential dispatch just doubles the wall-clock for no benefit. (Only the correctness reviewer runs for purely backend diffs.) Wait for both, then consolidate their findings into one verdict and, if retrying, one combined coder retry.

**6a — Correctness reviewer (always).** Use the `Agent` tool. Subagent type: `rmp:code-reviewer` (bundled with this plugin). **Pass `model: "sonnet"`** to override the default, so a different model than the coder reviews the work — different model, different blind spots. (Optional: if you have the `pr-review-toolkit` plugin installed and the diff is error-handling-heavy or type-heavy, also dispatch its `silent-failure-hunter` / `type-design-analyzer`.)

Reviewer prompt — adversarial framing:

```
You are an adversarial code reviewer. Your job is to find problems, NOT to approve.

=== Scope of review ===
Branch: feature/<slug>-<issue-identifier-lowercase>
Diff against: feature/<slug>
Run: `git diff feature/<slug>...HEAD`

=== Context ===
Sub-issue being implemented:
Title: <title>
Description (with acceptance criteria and test steps):
<full description body>

Spec: docs/specs/<slug>.md
Project conventions: /CLAUDE.md

=== Your standard ===
Assume there are bugs. You must find at least 3 concrete issues OR explicitly show what you checked and why none exist.

Check, at minimum:
1. Each acceptance criterion line-by-line — is it actually true in the diff?
2. Each test step — does the code support it actually passing? Don't trust the implementer's claim; reason from the code.
3. Edge cases: null/empty inputs, concurrency, error paths, what happens when an upstream call fails.
4. Project conventions from CLAUDE.md — branch policy, copy rules, "never do X" rules.
5. Silent failures: try/catch that swallows, fallbacks that hide bugs, removed assertions.
6. Type safety: anywhere `any` was introduced, `@ts-ignore` was used, or types were widened.
7. Pre-existing tests: any that this change breaks (don't run them — reason from the diff).

=== Output ===
Return one of:
- BLOCK: with a numbered list of concrete issues, each with a file:line reference and a one-line description of the fix needed.
- APPROVE: with a numbered list of the 5+ specific checks you performed and what you saw that satisfied each.

Do NOT return "looks good" or any variant. Approval requires evidence of checking, not absence of obvious bugs.
```

**6b — Spec-compliance reviewer (user-facing diffs only).** If the diff touches user-facing surfaces — UI/component/copy files, or changes the shape of a live/polled endpoint — ALSO dispatch the `rmp:spec-compliance-reviewer` agent (Subagent type: `rmp:spec-compliance-reviewer`; it pins `model: sonnet` itself). It audits the contracts the correctness reviewer doesn't, reading them from the **touched app's own** `app_spec.txt` `<compliance_rules>` + `CLAUDE.md`: copy/locale, casing, prescribed strings, design tokens, fonts/assets, feedback-UI primitives, and live-surface reachability. Because it derives every rule from the app's spec, it works for any app that follows the RMP app_spec template. Pass it the same branch/diff + the sub-issue's UI/Copy acceptance criteria. Skip it for purely backend sub-issues (schema, internal libs, API logic with no response-shape or copy change).

Treat a `BLOCKER` from the spec-compliance reviewer exactly like a correctness BLOCK (Step 7 retry path). `WARN`/`NIT` are non-blocking but should be reported and, if cheap, folded into the same retry.

**Judge each finding against the breakdown — do not blindly comply.** The reviewers see only one sub-issue's diff; they lack the cross-issue plan and will sometimes flag a "missing X" or "dead code Y" that is *deliberately* a sibling sub-issue's scope (e.g. a constant/payload field added here but consumed two issues later, or "the duration chart isn't implemented" when that's a separate issue). Verify the objection against `docs/specs/<slug>.md` + the Linear breakdown: if it's genuinely out-of-scope-by-design, **reject it with a one-line rationale** (and say so in the PR/Linear note) rather than pulling the work forward. Conversely, when two reviewers disagree (e.g. one wants font-mono, the app_spec mandates it), the spec-compliance reviewer's spec-derived ruling wins. As orchestrator you own the verdict — the reviewers inform it. Also: a finding you can fully verify yourself from the diff (a one-line copy/type fix) can be confirmed and merged without burning another full review round on it.

### Step 7 — Handle the verdict

**If BLOCK:** (a `BLOCKER` from *either* the correctness or spec-compliance reviewer)

Tell the user what either reviewer found, in a tight summary. Ask whether to:
- (a) Dispatch the coder again to address the feedback (counts as 1 retry)
- (b) Manually intervene
- (c) Abandon this sub-issue

If (a), increment the retry counter. **Cap retries at 3.** On the 4th cycle, automatically pick (b) and surface to the user — do not loop further. The retry coder prompt should include both reviewers' full feedback verbatim plus the original prompt.

(In **Autonomous mode**, skip the question: a BLOCK auto-selects (a) until the cap; the 3rd consecutive BLOCK on one sub-issue HALTS the loop — see *Autonomous mode*.)

**If APPROVE:** (correctness APPROVE **and**, when run, spec-compliance with no `BLOCKER`)

Proceed to Step 8.

### Step 8 — Commit and PR

Stage exactly the files the coder reported. Commit message:

```
<conventional-prefix>(<scope>): <issue title in sentence case>

<issue identifier>
Resolves the sub-issue: <one-line description>

Co-Authored-By: Claude <noreply@anthropic.com>
```

The conventional prefix follows the project's existing log style (run `git log --oneline -10` to check — `feat:`, `fix:`, `chore:` etc.).

Push the sub-branch:
```bash
git push -u origin feature/<slug>-<issue-identifier-lowercase>
```

Open a PR from the sub-branch into the **feature branch** (NOT main):
```bash
gh pr create --base feature/<slug> --title "<title>" --body "$(cat <<'EOF'
## What
<one-line description>

## Linear
<issue-identifier>

## Evidence
- <evidence path 1>
- <evidence path 2>

## Adversarial review
<reviewer's APPROVE block — the list of specific checks>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### Step 9 — Update Linear

- Sub-issue → state "In Review" (or whatever state matches "PR open" in this team's workflow). Add a comment with the PR URL.
- Parent issue: add a comment summarizing progress (e.g. "Sub-issue RMP-100 done — N/M complete").

### Step 10 — Report back to the user

3–5 lines:
- Sub-issue ID + title (done)
- PR URL
- Reviewer's APPROVE checklist (so the user can see what was actually verified)
- Retries used (if any) and a one-line summary of what changed during retries
- Next step: another `/work-iteration <slug>` for the next sub-issue, or open the umbrella PR if this was the last

## Autonomous mode (iterate-all)

Triggered when the user asks to run the whole feature unattended (e.g. `/work-iteration <slug> --auto`, "iterate automatically", "run the rest while I sleep"). Instead of one sub-issue, loop the Steps 1–9 workflow over **all** `Todo` sub-issues in dependency order, merging each sub-PR into the **feature branch** as you go. No questions between issues — the decision policy below replaces every "ask the user" prompt.

**Per-issue cycle (unchanged):** coder subagent → correctness reviewer (+ spec-compliance reviewer for user-facing diffs) → on dual-APPROVE: commit, push, sub-PR into `feature/<slug>`, **merge it** (`gh pr merge --squash --delete-branch`), mark Linear Done, next. On BLOCK: auto-retry the coder with verbatim feedback.

**HALT the entire loop and write the morning report when ANY of these fire** (do nothing further — leave it for the human):

1. **3 reviews blocked on one sub-issue.** A sub-issue that reaches its 3-retry cap without a dual-APPROVE. Because sub-issues form a dependency chain, a stuck one blocks everything downstream — so halt, don't skip.
2. **Critical path / hard stop:** an irreversible or destructive action; a decision the spec does not settle (ambiguity the coder would have to invent); an evidence gate that retries can't satisfy (e.g. dev server won't boot, migration fails); or anything that would **touch `main` or production**.
3. **Migration safety:** schema/migration sub-issues run **dev-only**, against a local/dev database (enforced by the project's DB-safety hook, if it has one). NEVER run a production migration or touch the prod database autonomously.

**Boundaries that always hold in autonomous mode:**
- **Never open or merge the umbrella `feature/<slug>` → `main` PR.** Stop after the last sub-issue merges into the feature branch and leave that PR for the human — especially when the feature includes a migration (prod isn't auto-migrated).
- Merging **sub-PRs into the feature branch** is allowed autonomously; merging anything into `main` is not.
- The dual-review separation and all evidence gates still apply to every issue — autonomy lowers the *interaction* bar, never the *verification* bar.

**Progress + report:** keep a running log (sub-issue → APPROVE/retries/PR URL). Linear `Done` state is the durable record. On halt or completion, post one consolidated report: issues completed (with PR URLs + each reviewer's APPROVE checklist), where it stopped and exactly why, retries used, and the single next action for the human (usually: review the merged feature branch, run the prod migration, then open the umbrella PR).

## Things to never do

- **Never commit code the reviewer BLOCKED.** No "the issues are small, I'll fix in next PR."
- **Never open or merge the umbrella PR into `main` in autonomous mode.** The feature→main merge is always a human step.
- **Never push to main.** Sub-PRs target the feature branch.
- **Never let the same agent both code and review.** The Sonnet reviewer is non-negotiable structural separation.
- **Never invent evidence.** If a screenshot path is claimed, you must `ls` it and confirm size > 0.
- **Never accept `curl` / `wget` / shell HTTP as verification.** Browser-driven verification only. If the coding subagent reports curl output as evidence, treat it as missing evidence and require a browser-based check.
- **Never skip the verification gates** (tsc + browser check) because "the change is small."
- **Never silently increase the retry cap.** 3 is the cap. After that, the human takes over.
- **Never bypass git hooks** (no `--no-verify`). If a hook fails, that's signal — investigate.

## Evidence gates — minimum bar

A sub-issue cannot pass to commit unless ALL of these are present in the conversation:

1. Git diff visible (run `git diff feature/<slug>...HEAD` and confirm output looks right)
2. `npx tsc --noEmit` (or project equivalent) — exit 0, output captured
3. Dev server boot check — confirmed via a browser navigation to the dev URL (Playwright/Chrome DevTools), NOT curl. The page must load without console errors that didn't exist before.
4. **Browser-driven verification of the change** (hard block — no exceptions):
   - For UI: at least one screenshot in `.playwright-mcp/` with size > 0 showing the new behavior in a real browser
   - For API: at least one network request captured via `browser_network_requests` / `list_network_requests`, OR a browser-evaluated `fetch()` result in the conversation
   - `curl`/`wget` output does NOT satisfy this gate, even if the response looks correct
5. Reviewer APPROVE block with ≥5 specific checks

If any is missing, you cannot proceed to Step 8.

### UI / visual verification — hard-won specifics

These come from real failures; bake them into the coder prompt AND check them yourself when you read the screenshots (the jank check is yours too, not just the reviewer's):

- **Test at the phone viewport, not desktop/tablet** (e.g. 393×852 / a phone `devices[...]` profile). For mobile-first apps the phone is the real surface; defer to the project's CLAUDE.md if it names a size. When the app is iOS-sensitive, also verify on **WebKit (iPhone-emulated)**, not just Chromium.
- **Visual jank is a blocker, not a nit.** "Not broken but janky" — misalignment, overflow, clipped/over-wrapped text, cramped spacing, labels colliding/clipping at the right edge, jumpy/unsettled charts — fails the gate even when the feature functions. Actually *look* at the screenshot; a green assertion is not a passing render.
- **Disable chart/animation for screenshots.** Recharts (and similar) animate from 0; a headless capture catches them mid-animation and bars/lines look absent even though the data is in the DOM. Set `isAnimationActive={false}` (also kills "jumpy chart" jank). If a value is "in the DOM but not painted," suspect animation before suspecting a real bug.
- **Dynamic colors: no `var(--…)` inside an inline `style`** (a common CLAUDE.md rule). Tailwind JIT only generates classes whose *literal* strings appear in source, so `bg-[${dynamicVar}]` silently produces nothing — use a STATIC class lookup (`Record<Key, "bg-[var(--token-a)]" | ...>`) or a CSS-custom-property pattern. Recharts `fill`/`stroke` as a `var(--…)` SVG *attribute* (not a `style` object) is fine.
- **Playwright MCP server CWD may be the repo's PARENT**, so screenshot/`fetch`-dump artifacts can land outside the repo (or at the repo root). Always have the coder write under `.playwright-mcp/<issue-id>-*`, then in Step 5 sweep both the repo root AND the parent dir and move strays in. Confirm `git status` shows only source changes.
- **For deterministic UI verification, seed a fixture first.** Whatever's in the dev DB won't reliably exercise empty/edge/threshold states. Seed a representative dataset (dev-only, guarded against non-local `DATABASE_URL`) before the browser checks — and prefer a committed fixture if a later sub-issue builds the e2e harness.
- **e2e assertions must bite.** Page-global `getByText` often matches unrelated surfaces (lists, tooltips) → tautological. Scope to the component under test, assert real *values* (counts/deltas), not just that labels exist, and prove it by mutating the fixture to confirm the assertion goes red.

## Cross-session resumption

If the user invokes this skill on a sub-issue that already has an open PR (check via `gh pr list --head feature/<slug>-<issue-identifier-lowercase>`), do NOT re-implement. Instead, report the PR status and ask whether they want to:
- View the open PR
- Pick a different sub-issue
- Force-restart (delete branch + PR — confirm before doing this)
