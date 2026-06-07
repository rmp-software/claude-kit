# rmp — RMP Feature Harness

Company-wide Claude Code plugin for spec-driven feature development. Skills invoke as
`/rmp:<name>`.

## What's in it

### Skills (the harness)

| Skill | Use it to |
|-------|-----------|
| `/rmp:spec-feature` | Write a committed feature spec to `docs/specs/<slug>.md`. |
| `/rmp:breakdown-feature` | Turn a spec into a Linear parent issue + child sub-issues with test steps. |
| `/rmp:work-iteration` | Implement one sub-issue: coder subagent → adversarial reviewer(s) → evidence gates → sub-PR. Has an autonomous "run the whole feature" mode. |
| `/rmp:continue-feature` | Resume a feature across sessions — reports progress and the next task. |
| `/rmp:critique` | Standalone adversarial review of a diff/PR/files. No spec or Linear needed. |

Typical flow: `spec-feature` → `breakdown-feature` → `work-iteration` (repeat) →
`continue-feature` to pick back up. `critique` is standalone.

### Agents

| Agent | Role |
|-------|------|
| `rmp:code-reviewer` | Independent, adversarial **correctness** reviewer for a diff. Read-only. |
| `rmp:spec-compliance-reviewer` | Audits user-facing diffs against the **target app's own** `app_spec.txt` `<compliance_rules>` + `CLAUDE.md`. Carries no built-in app knowledge — every rule comes from the spec. Read-only. |

### Templates

- `templates/app_spec.template.txt` — the standardized application spec. Copy it to an
  app's root as `app_spec.txt` and fill it in. The `<compliance_rules>` block is what
  `rmp:spec-compliance-reviewer` enforces, so make those rules **checkable** (verbatim
  strings, allowlists, `grep=` patterns, "never" lists).

## Dependencies

Hard requirements for the full harness:

- **A Linear MCP** — `breakdown-feature`, `work-iteration`, and `continue-feature` create
  and read Linear issues. The skills reference tools under a `linear` MCP; if your Linear
  MCP exposes different tool names, the skill adapts at runtime, but a Linear MCP must be
  connected. Project-wide Linear context lives in `.linear_features.json` at the repo root
  (the skills scaffold it on first run).
- **A browser MCP** (Playwright, Chrome DevTools, or equivalent) — `work-iteration`'s
  evidence gates require browser-driven verification. `curl`/`wget` is explicitly rejected.

Optional:

- **`pr-review-toolkit` plugin** — enables the specialized `silent-failure-hunter` and
  `type-design-analyzer` reviewers in `work-iteration` and `critique`. Without it, the
  bundled `rmp:code-reviewer` covers correctness review.

`spec-feature` and `critique` work with no Linear/browser dependency.

## Conventions this harness assumes

It's opinionated. It expects a project that uses:

- Specs at `docs/specs/<slug>.md`, with status + Linear IDs in frontmatter.
- Linear as the issue tracker.
- A git flow of `feature/<slug>` branches with per-sub-issue sub-PRs into the feature
  branch (never directly to `main`).
- Browser-evidence gates (screenshot/network capture under `.playwright-mcp/`).
- An `app_spec.txt` following `templates/app_spec.template.txt` for spec-compliance review.

Projects that don't use Linear can still use `spec-feature` and `critique` standalone.

## Install

```
/plugin marketplace add rmp-software/claude-kit
/plugin install rmp@claude-kit
```

Then in any repo: `/rmp:spec-feature`, `/rmp:critique`, etc.
