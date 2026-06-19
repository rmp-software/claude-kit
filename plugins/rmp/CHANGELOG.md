# Changelog

Notable changes to the `rmp` plugin. Versions track the `version` field in
`.claude-plugin/plugin.json`; bump it on every release so the marketplace re-pulls.

## 0.4.0

Promotes the harness operating conventions that had been living in per-machine memory into
the shipped plugin — specialized-agent routing, parallel batch execution, and the merge/fork
boundaries are now standard behavior, not tribal knowledge.

### Added

- **7 specialized agents** (stack-agnostic, genericized from real use): `principal-engineer`,
  `code-refactor-master`, `code-architecture-reviewer`, `plan-reviewer`, `refactor-planner`,
  `auto-error-resolver`, `documentation-architect`, `web-research-specialist`. They derive
  conventions from the target project's `CLAUDE.md`/`app_spec.txt`; a project's own same-named
  agent overrides the plugin's.
- **`enforce-specialized-agent` PreToolUse hook** (`hooks/hooks.json` + `hooks/enforce-specialized-agent.sh`):
  denies any `general-purpose` subagent dispatch and names the role-appropriate substitute.
  Applies repo-wide once installed. Requires `jq`.

### Changed

- **work-iteration — specialized-agent routing.** Coders are now `principal-engineer` /
  `code-refactor-master`; the evidence verifier and correctness gate are `rmp:code-reviewer`;
  added an optional `code-architecture-reviewer` as a third parallel reviewer for structural
  diffs. All `general-purpose` dispatches removed.
- **work-iteration — parallel batch execution (autonomous mode).** File-disjoint sub-issues
  run in concurrent batches (≤3 coders); foundation first, whole-app gate last; baseline
  screenshots before edits; one authoritative `tsc` + browser pass per batch. Batch coders
  edit + grep only (no dev server, no commit) to avoid shared-tree races.
- **work-iteration — integration policy asked up front** (sub-PR auto-merge / stacked PRs /
  umbrella-only); the umbrella `feature→main` PR is never auto-merged. **Cross-cutting
  architecture forks pause for the human** even mid-autonomous-run.
- **work-iteration / critique — reviewer diff fix:** use `git diff feature/<slug>` instead of
  `git diff feature/<slug>...HEAD`. The coder never commits, so the commit-range form was
  empty — reviewers were diffing nothing.
- **critique — new reviewer flavors:** architecture and first-principles deep-dive; parallel
  multi-flavor dispatch.

### Renamed

- **`spec-feature` → `brainstorming`.** The feature front door is now `/rmp:brainstorming`
  (same name as `superpowers:brainstorming`, which it wraps). Its description asserts it as
  THE entry point for starting a feature in an rmp project, so the router stops defaulting to
  plain `superpowers:brainstorming` (which would land the spec in the wrong place and hand off
  to `writing-plans`). Chain is now `brainstorming → breakdown-feature → work-iteration`.

### Linear is now optional

- **Two tracker modes, chosen per feature.** `/breakdown-feature` asks **Linear or local** up
  front and writes `tracker:` to the spec frontmatter. **Local mode** writes a `## Tasks`
  checklist into the spec (`[ ]`/`[~]`/`[x]` = todo/in-progress/done, with PR refs appended) —
  no Linear MCP, no `.linear_features.json`, zero extra deps. Good for simpler/solo features.
- **All three lifecycle skills are mode-aware.** `breakdown-feature` materializes to Linear or
  the checklist; `work-iteration` reads the next task and updates state in either backend (same
  implement → verify → review → sub-PR machinery); `continue-feature` reports progress from
  either. Local task IDs are a stable kebab of the task title, so branch naming + resumption
  work cross-session without Linear.
- **README/dependencies updated:** Linear moved from hard requirement to optional; the full
  spec → breakdown → iterate loop now runs with no tracker dependency.

### Dependency

- The enforce hook requires `jq` on PATH.

## 0.3.0

`spec-feature` no longer drives a rigid XML template interview. It now delegates the
exploration and design to `superpowers:brainstorming` (Socratic, one-question-at-a-time,
2–3 approaches with approval gates) and adapts only the output.

### Changed

- **spec-feature — rewritten as an adapter around `superpowers:brainstorming`.** Runs the
  brainstorming dialogue, then overrides two of its terminal steps: writes the design doc
  to `docs/specs/<slug>.md` (not `docs/superpowers/specs/`) with rmp YAML frontmatter, and
  hands off to `/breakdown-feature` instead of `writing-plans`.
- **Spec format is now free-form markdown, not XML.** The brainstorming design body is kept
  as-is; the only required section is `## Acceptance criteria`. The rmp frontmatter contract
  (`slug`, `status`, `created`, `linear_project_id`, `linear_parent_issue`, `feature_branch`)
  is unchanged, so `breakdown-feature` / `work-iteration` / `continue-feature` still consume
  the spec.
- **breakdown-feature — reads the design by meaning, not by XML tag.** Pulls acceptance
  criteria from the `## Acceptance criteria` section and infers sub-issues from the design's
  components/phases.

### Dependency

- `spec-feature` now requires the `superpowers` plugin (for `superpowers:brainstorming`).

## 0.2.0

Usage optimization baked into the harness — none of it lowers the verification or
coding bar; it relocates bulky reading out of the long-running orchestrator and tiers
mechanical work down to Sonnet subagents.

### Optimized

- **work-iteration — context firewall.** The orchestrator no longer reads raw diffs,
  opens screenshots, or reruns `tsc` inline. Step 5 delegates evidence verification to a
  Sonnet subagent that returns a compact contract
  (`DIFF_MATCHES_CLAIMS / TSC / ARTIFACTS / VISUAL_JANK / STRAY_FILES / VERDICT`). This
  keeps the loop's context lean — cache reads on a growing prefix are where a long
  agentic session's cost accumulates.
- **work-iteration — jank gate moved** into the verification subagent (it reads the saved
  screenshots and judges the pixels), so the orchestrator gets a `VISUAL_JANK` verdict
  without ingesting images.
- **work-iteration — context-retention discipline.** Reviewer APPROVE blocks live in the
  PR body, sub-issue outcomes in Linear; the orchestrator keeps one compact line per
  finished sub-issue instead of verbatim transcripts.
- **work-iteration — stable-prefix prompt ordering** for subagent dispatches, so repeated
  coder/reviewer calls within a feature share the API prompt cache.
- **work-iteration — runaway visibility (autonomous mode):** track the *observable* spend
  proxies per sub-issue (retries, review rounds, dispatch count) and summarize outliers in
  the morning report, with a pointer to `/cost` for the actual token figure. The
  orchestrator logs a real token count only if its runtime surfaces subagent usage, and
  never fabricates one.
- **spec-feature — scoped prior-spec reading:** scan overviews, full-read only
  topically-adjacent specs instead of slurping every historical spec.
- **critique / code-reviewer — minor:** fixed-framing-first prompt ordering; a leading
  `VERDICT:` line for cheap consolidation (the evidence requirement is unchanged).

### Changed (mildly breaking)

- **Feature-spec format normalized to the `app_spec.txt` XML structure.** `spec-feature`
  now emits YAML frontmatter + an `<feature_specification>` XML body (`<overview>`,
  `<surfaces_affected>`, `<api_surface>`, `<acceptance_criteria>`, `<breakdown_sketch>`, …)
  instead of markdown `##` sections, and `breakdown-feature` parses those tags.
- **Migration:** features already broken down into Linear are unaffected —
  `work-iteration` and `continue-feature` don't parse the spec body. Only re-running
  `breakdown-feature` on a legacy markdown-format spec requires converting that spec to the
  XML tags first.

## 0.1.0

Initial release: `spec-feature` → `breakdown-feature` → `work-iteration` →
`continue-feature`, standalone `critique`, and the `code-reviewer` +
`spec-compliance-reviewer` agents.
