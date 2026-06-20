# file-standard

A company-wide standard for **where Claude-generated files live**, so tools and
agents stop inventing ad-hoc locations — and so scratch never leaks into a git
tree.

## The problem

Skills, subagents, and tools routinely create files (evidence, handoffs, scratch,
debug dumps) and each one picks its own location. Inside a git repo that means
junk gets staged and committed. This plugin makes placement deterministic and
keeps tracked trees clean by construction.

## The standard

| Category    | What it is                                            | Where it goes |
|-------------|-------------------------------------------------------|---------------|
| **scratch** | throwaway working files, intermediate output          | `~/.claude/work/<project>/scratch/` — **outside the repo, always** |
| **evidence**| screenshots, logs, test runs proving something worked | `<repo>/.claude/scratch/evidence/` — in-repo, gitignored |
| **handoff** | plans, notes, specs passed between agents/sessions    | `<repo>/.claude/scratch/handoff/` — in-repo, gitignored |
| **deliverable** | output the user explicitly asked to keep          | the path the user specified — committed normally |

- `<project>` = `<basename>-<shorthash>` of the repo/cwd absolute path, so two
  repos named `app` never collide.
- **Not in a git repo?** There's no tree to pollute — evidence and handoff fall
  back to `~/.claude/work/<project>/` too.
- Only `.claude/scratch/` is gitignored; the rest of `.claude/` (committed
  config) is untouched. Don't put disposable artifacts elsewhere under `.claude/`.

## How it's enforced (three layers)

1. **SessionStart hook → injects the standard** as session context, so every
   session and every subagent that inherits it follows the rules. No per-machine
   CLAUDE.md edit required — the standard travels with the plugin.
2. **SessionStart hook → ensures the global gitignore** contains `.claude/scratch/`
   (creating/setting `~/.config/git/ignore` only if needed). A leak becomes
   physically uncommittable in every repo on the machine. Idempotent; reports
   once when it makes a change.
3. **PreToolUse hook → non-blocking backstop.** On `Write`/`Edit`/`MultiEdit`
   and `Bash` redirects, if a scratch/evidence/handoff path lands in a git repo
   outside `.claude/scratch/`, it warns with the correct path. The write still
   proceeds; Claude self-corrects.

## Install

This plugin ships in the **claude-kit** marketplace:

```
/plugin marketplace add rmp-software/claude-kit
/plugin install file-standard@claude-kit
```

## Notes

- Hooks are dependency-free Python 3 (no `jq`, no pip installs) and never block
  or crash a session on failure — worst case they stay silent.
- The PreToolUse matchers are intentionally tight (a scratch-ish directory
  segment or a clear filename token) to keep false positives low; warnings are
  advisory, not enforced.
