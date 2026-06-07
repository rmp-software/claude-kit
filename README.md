# claude-kit

RMP Software's company-wide [Claude Code](https://claude.com/claude-code) tooling — a
plugin marketplace of shared skills, agents, and harnesses installable across every repo.

## Install

```
/plugin marketplace add rmp-software/claude-kit
/plugin install rmp@claude-kit
```

## Plugins

| Plugin | Invoke as | What it does |
|--------|-----------|--------------|
| [`rmp`](plugins/rmp) | `/rmp:<skill>` | Spec-driven feature harness (spec → Linear breakdown → adversarial implement/review with evidence gates) + a generic, spec-driven compliance reviewer. |

See each plugin's README for skills, agents, and dependencies.

## Layout

```
claude-kit/
├── .claude-plugin/
│   └── marketplace.json        # marketplace manifest
└── plugins/
    └── rmp/
        ├── .claude-plugin/plugin.json
        ├── skills/             # /rmp:spec-feature, breakdown-feature, work-iteration, …
        ├── agents/             # code-reviewer, spec-compliance-reviewer
        ├── templates/          # app_spec.template.txt
        └── README.md
```

## Adding a plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json`.
2. Add `skills/`, `agents/`, `commands/`, and/or `hooks/` under it.
3. Register it in `.claude-plugin/marketplace.json`.
4. Open a PR. After merge, `/plugin marketplace update claude-kit` picks it up.

## License

MIT — see [LICENSE](LICENSE).
