# rmp — RMP Feature Harness

Company-wide Claude Code plugin for spec-driven feature development. Skills invoke as
`/rmp:<name>`.

## What's in it

### Skills (the harness)

| Skill | Use it to |
|-------|-----------|
| `/rmp:brainstorming` | **The feature front door.** Brainstorm a feature (wraps `superpowers:brainstorming`) and commit the design doc to `docs/specs/<slug>.md`. Supersedes plain `superpowers:brainstorming` in rmp projects. |
| `/rmp:breakdown-feature` | Turn a spec into a breakdown with test steps — Linear parent + sub-issues, or a local `## Tasks` checklist (asks which). |
| `/rmp:work-iteration` | Implement one task: coder subagent → adversarial reviewer(s) → evidence gates → sub-PR. Autonomous "run the whole feature" mode runs file-disjoint tasks in parallel batches. Works in either tracker mode. |
| `/rmp:continue-feature` | Resume a feature across sessions — reports progress and the next task. |
| `/rmp:critique` | Standalone adversarial review of a diff/PR/files. No spec or Linear needed. |

Typical flow: `brainstorming` → `breakdown-feature` → `work-iteration` (repeat) →
`continue-feature` to pick back up. `critique` is standalone.

### Agents

Specialized subagents the harness routes to **by role** — the harness never dispatches the
generic `general-purpose` agent (a shipped hook enforces this; see *Harness conventions*).

**Review gates** (read-only):

| Agent | Role |
|-------|------|
| `rmp:code-reviewer` | Independent, adversarial **correctness** reviewer for a diff — also serves as `work-iteration`'s evidence verifier. Read-only. |
| `rmp:spec-compliance-reviewer` | Audits user-facing diffs against the **target app's own** `app_spec.txt` `<compliance_rules>` + `CLAUDE.md`. Carries no built-in app knowledge — every rule comes from the spec. Read-only. |
| `rmp:code-architecture-reviewer` | Optional third reviewer for architecture-heavy diffs — system integration, module/package fit, boundary violations. Read-only. |

**Workers** (feed the gates / utility roles):

| Agent | Role |
|-------|------|
| `rmp:principal-engineer` | First-principles implementer — the default coder for new code. |
| `rmp:code-refactor-master` | Pure restructuring / file-moves with dependency tracking. |
| `rmp:auto-error-resolver` | Clears a red build (tsc/build errors) before review. |
| `rmp:plan-reviewer` | Reviews a plan before implementation for gaps/risks. |
| `rmp:refactor-planner` | Produces a phased refactor plan with risk assessment. |
| `rmp:web-research-specialist` | Multi-source web research for debugging/solutions. |
| `rmp:documentation-architect` | Creates/updates docs for a feature or system. |

All are **stack-agnostic** — they derive conventions from the target project's `CLAUDE.md` /
`app_spec.txt`, not from any built-in framework assumptions. A project that ships its own
same-named agent overrides the plugin's.

### Templates

- `templates/app_spec.template.txt` — the standardized application spec. Copy it to an
  app's root as `app_spec.txt` and fill it in. The `<compliance_rules>` block is what
  `rmp:spec-compliance-reviewer` enforces, so make those rules **checkable** (verbatim
  strings, allowlists, `grep=` patterns, "never" lists).

## Dependencies

Hard requirements for the full harness:

- **A browser MCP** (Playwright, Chrome DevTools, or equivalent) — `work-iteration`'s
  evidence gates require browser-driven verification. `curl`/`wget` is explicitly rejected.
- **`superpowers` plugin** — `/rmp:brainstorming` delegates its dialogue to
  `superpowers:brainstorming`. Install superpowers for `/rmp:brainstorming` to work.
- **`jq`** — the `enforce-specialized-agent` hook needs it on PATH.

Optional:

- **A Linear MCP** — **Linear is optional.** `/breakdown-feature` asks per feature whether to
  track in Linear or **locally** (a `## Tasks` checklist in the spec — zero extra deps).
  In Linear mode, `breakdown-feature` / `work-iteration` / `continue-feature` create and read
  Linear issues; the skills reference tools under a `linear` MCP and adapt to different tool
  names at runtime. Project-wide Linear context lives in `.linear_features.json` at the repo
  root (scaffolded on first run). In **local mode** none of this is needed.
- **`pr-review-toolkit` plugin** — enables the specialized `silent-failure-hunter` and
  `type-design-analyzer` reviewers in `work-iteration` and `critique`. Without it, the
  bundled `rmp:code-reviewer` covers correctness review.

The whole harness runs **with no Linear** (local-tracker mode); `brainstorming` and `critique`
have no Linear/browser dependency at all.

## Conventions this harness assumes

It's opinionated. It expects a project that uses:

- Specs at `docs/specs/<slug>.md`, with `tracker` + status (+ Linear IDs in Linear mode) in frontmatter.
- A task tracker — **Linear or a local `## Tasks` checklist in the spec** (chosen per feature at breakdown).
- A git flow of `feature/<slug>` branches with per-task sub-PRs into the feature
  branch (never directly to `main`).
- Browser-evidence gates (screenshot/network capture under `.playwright-mcp/`).
- An `app_spec.txt` following `templates/app_spec.template.txt` for spec-compliance review.

The full spec → breakdown → iterate loop works **without Linear** in local-tracker mode;
`brainstorming` and `critique` are standalone regardless.

## Harness conventions (how it operates)

These are baked into the skills + a shipped hook, so the behavior is standard across every
repo that installs the plugin — not tribal knowledge:

- **Specialized agents only — never `general-purpose`.** Every subagent dispatch routes by
  role (see *Agents*). The plugin ships a `PreToolUse` hook (`hooks/enforce-specialized-agent.sh`,
  matcher `Agent|Task`) that **denies** a `general-purpose` dispatch and names the substitute.
  This applies repo-wide once installed, not only inside the harness skills. Requires `jq`.
- **Parallel batches, lean orchestrator.** In autonomous mode, `work-iteration` runs
  file-disjoint sub-issues in concurrent batches (≤3 coders), delegates all bulky
  reading/verification to subagents, and keeps only one-line summaries in its own context.
  Foundation issues go first; the whole-app gate goes last.
- **Batch coders edit + grep only** (no dev server, no commit) to avoid `.next`/port/staging
  races in the shared tree; one authoritative `tsc` + browser-screenshot pass runs per batch.
- **Merge boundary.** Sub-PRs merge into `feature/<slug>` (per an integration policy asked
  once, up front); the umbrella `feature/<slug>` → `main` PR is **always the human gate** —
  never auto-merged.
- **Consult on cross-cutting forks.** Even mid-autonomous-run, a decision with monorepo-wide
  or multi-app blast radius pauses for the human; per-slice details don't.
- **Reviewers diff `git diff feature/<slug>`** (not `...HEAD`) — the coder doesn't commit, so
  a commit-range diff would be empty.

## Install

```
/plugin marketplace add rmp-software/claude-kit
/plugin install rmp@claude-kit
```

Then in any repo: `/rmp:brainstorming`, `/rmp:critique`, etc.
