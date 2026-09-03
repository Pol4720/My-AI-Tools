# `.claude/` — active project configuration

This directory is the **integrated, live** Claude Code configuration for this repository,
assembled from the templates in [`config/claude/`](../config/claude/). Opening the repo in
Claude Code activates everything the repo provides — its skills, its settings, and its MCP
servers — with no manual copy step.

| File | Activated from | What it does |
|---|---|---|
| `settings.json` | `config/claude/settings/settings.project.json` | Project permissions (allow the repo's own gate commands; deny history rewrites and secret reads) and `env`. |
| `skills/*` | `config/claude/` + `scripts/install_skills.sh` | Relative symlinks so Claude Code discovers all three owned skills as project skills. |
| `../.mcp.json` | `config/claude/mcp/mcp.servers.json` | Project MCP servers. Only the credential-free `playwright` server is enabled. |

The `settings.json` here mirrors the committed template but is tuned for this repository:
its gate is `python3 scripts/validate_skills.py`, so that command and the skill scripts'
toolchain (`pytest`, `ruff`, `mypy`, `latexmk`) are pre-approved.

## What is intentionally not here

- **`settings.local.json`** — machine-specific overrides. Gitignored; create your own.
- **claude.ai connectors, plugins, built-in skills** — these cannot be rebuilt from a file.
  Follow [`docs/03-manual-setup-checklist.md`](../docs/03-manual-setup-checklist.md).

## Never in this directory

No API key, token, connection string or password. The `.mcp.json` uses `${VAR}` for any
credential, expanded from the environment at launch — never inlined into the committed file.
