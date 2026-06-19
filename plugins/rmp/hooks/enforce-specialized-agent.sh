#!/usr/bin/env bash
# PreToolUse hook (matcher: Agent|Task), shipped by the rmp plugin.
# The rmp harness bans the generic `general-purpose` subagent — every dispatch must use a
# specialized agent (a different model/persona from the caller has different blind spots,
# and the harness skills route by role). Reads the PreToolUse payload on stdin and DENIES
# only when .tool_input.subagent_type == "general-purpose"; every other dispatch is allowed
# (emits `{}` = no opinion). Requires `jq` on PATH. See the rmp README "Harness conventions".
exec jq -c '
  if .tool_input.subagent_type == "general-purpose" then
    {
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: "The rmp harness bans the generic general-purpose subagent. Substitute a specialized agent and re-dispatch by role: rmp:principal-engineer (new code) or rmp:code-refactor-master (pure restructuring) for implementation; rmp:code-reviewer for correctness review/evidence verification; rmp:spec-compliance-reviewer for UI/copy/spec compliance; rmp:code-architecture-reviewer for architecture/system-integration; rmp:auto-error-resolver for a red build; rmp:plan-reviewer / rmp:refactor-planner for planning; rmp:web-research-specialist for research; rmp:documentation-architect for docs. If none fits, pick the closest specialized agent rather than general-purpose."
      }
    }
  else {} end'
