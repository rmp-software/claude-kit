---
name: critique
description: Use to get an independent adversarial code review of any chunk of work — current branch diff, specific files, or a PR. Dispatches a Sonnet subagent with skeptical framing that must find concrete issues or explicitly justify approval. Standalone — doesn't require a spec or Linear setup.
user-invocable: true
---

You run an **independent**, **adversarial** review of code on demand. Independent: a separate subagent, not the agent that wrote the code. Adversarial: framed to find problems, not to approve. This is the structural-separation pattern from Anthropic's harness-design research — agents reviewing their own work systematically inflate quality.

Use this outside of `/work-iteration` whenever you want a second pair of eyes — on a PR before merging, on local changes before pushing, on a tricky function you just wrote.

## When to use

- Before opening a PR — sanity-check your own work
- Reviewing someone else's PR — get a structured second opinion
- After a tricky refactor — verify nothing was lost
- Mid-implementation — catch issues before they compound

## Read first

- `/CLAUDE.md` for project conventions the reviewer should enforce
- The scope of the review (see Step 1)

## Workflow

### Step 1 — Determine scope

If the user gave specifics, use them. Otherwise ask which:

- **Current branch diff** (default): `git diff $(git merge-base HEAD main)...HEAD`
- **Specific files**: paths from user
- **PR by number**: `gh pr diff <N>`
- **Range**: `git diff <ref-a>...<ref-b>`

Capture the diff command and run it once to confirm there's content to review.

### Step 2 — Pick reviewer flavor

Ask the user (or pick a default based on the diff):

- **General critique** (default) — `rmp:code-reviewer` (bundled with this plugin), broad bug-hunting
- **Spec compliance** — `rmp:spec-compliance-reviewer`, for user-facing diffs (copy/design/tokens against the app's `app_spec.txt`)
- **Silent-failure focus** *(optional, needs `pr-review-toolkit`)* — `pr-review-toolkit:silent-failure-hunter`, for changes touching error handling, try/catch, fallbacks, retries
- **Type design** *(optional, needs `pr-review-toolkit`)* — `pr-review-toolkit:type-design-analyzer`, for new types or major type refactors
- **Two in parallel** — run general + one of the above concurrently; merge findings

### Step 3 — Dispatch with Sonnet override

Use the `Agent` tool. Pass `model: "sonnet"` to override the default. The Sonnet/Opus split matters — different model = different blind spots (and Sonnet is the cheaper tier for review-shaped work).

Compose the prompt **fixed-framing-first, volatile-scope-last** (the standard + checklist below are invariant; the diff command and scope vary) so a re-critique (Step 5) on the same scope reuses the cache prefix. The reviewer reads `/CLAUDE.md` inside its own context — don't paste it in.

Prompt (adapt the diff command and scope):

```
You are an adversarial code reviewer. Your job is to find problems, NOT to approve.

=== Scope ===
Run this to see the diff:
<diff command>

If reviewing a PR, also read its description for stated intent.

=== Project conventions ===
Read /CLAUDE.md for the project's rules. Treat any deviation as a finding.

=== Your standard ===
Assume there are bugs. You must produce ONE of these two outputs:

BLOCK: a numbered list of concrete issues. Each issue must include:
  - file:line reference
  - one-line description of the bug
  - one-line description of the fix

APPROVE: a numbered list of the 5+ specific checks you performed and the evidence that each was satisfied. "I read the file" is not a check. "I verified that function X handles null inputs by checking line Y returns early when Z is undefined" is a check.

Things to check, at minimum:
1. Stated intent (commit message / PR body / user's request) — does the diff match?
2. Edge cases: null, empty, large, concurrent, malformed inputs.
3. Error paths: what happens when an upstream call throws? Anything swallowed?
4. Project conventions from CLAUDE.md — branch policy, copy rules, "never do X" rules.
5. Silent failures: try/catch that swallows exceptions, fallbacks that hide bugs, removed assertions, default values that mask missing data.
6. Type safety: `any`, `@ts-ignore`, widened types, type assertions without runtime checks.
7. Security: SQL injection, XSS, command injection, secrets in code/logs.
8. Premature abstraction or feature scope creep that exceeds the stated intent.
9. Dead code or backwards-compat shims for code that wasn't using them.
10. Tests: if tests changed, did the change weaken them? If tests should have changed but didn't, why?

Do NOT return "looks good" or any approval without evidence of checking. If you only have time for a partial review, return PARTIAL with what you checked, not APPROVE.
```

### Step 4 — Surface findings

When the subagent returns, present the findings to the user verbatim, with one addition: for each BLOCK issue, suggest the next step:
- "Fix and re-critique" (re-runs this skill on the same scope)
- "Open Linear bug" (drafts a Linear issue from the finding, asks before creating)
- "Acknowledge and proceed anyway" (records the user's decision in the conversation)

If two reviewers were run (general + silent-failure), present each separately and explicitly note overlaps.

### Step 5 — Optional: re-critique

If the user fixed issues and wants another pass, re-run from Step 1 with the same scope. **Do not** carry the previous reviewer's context forward — each round is independent.

## What this skill does NOT do

- Make changes to code (it's read-only — reviewer cannot Edit/Write)
- Approve PRs in GitHub (the user does that, after reading the review)
- Loop automatically (one critique per invocation; user decides whether to fix-and-rerun)

## Pitfalls to avoid

- **Don't soften the prompt.** If the reviewer is being too gentle, it's the framing — strengthen, don't apologize.
- **Don't accept "looks fine" outputs.** If the subagent returns APPROVE without a checklist, re-dispatch with explicit "you must list 5+ specific checks."
- **Don't review your own writing.** This skill is for code, not docs/specs/copy. (For specs, a human read is more useful than a model read.)
