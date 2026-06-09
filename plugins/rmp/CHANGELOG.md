# Changelog

Notable changes to the `rmp` plugin. Versions track the `version` field in
`.claude-plugin/plugin.json`; bump it on every release so the marketplace re-pulls.

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
- **work-iteration — cost visibility (autonomous mode):** per-sub-issue token spend in the
  running log; per-feature total + outlier flag in the morning report.
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
