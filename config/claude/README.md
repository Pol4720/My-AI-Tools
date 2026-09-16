# Claude workspace configuration

Everything needed to rebuild this Claude workspace on a new account, a new machine, or a
colleague's setup — plus an honest account of what a file cannot rebuild.

```
config/claude/
├── inventory/          what the account has today (declarative snapshot)
├── settings/           Claude Code settings.json templates
├── mcp/                Claude Code project MCP server template
└── recommendations/    what to add next, and why
```

## Start here

| I want to… | Go to |
|---|---|
| See what is currently installed | [`inventory/`](inventory/) |
| Rebuild the workspace on a new account | [`../../docs/03-manual-setup-checklist.md`](../../docs/03-manual-setup-checklist.md) |
| Configure Claude Code on a new machine | [`settings/`](settings/) |
| Add a database or a self-hosted tool | [`mcp/`](mcp/) |
| Decide what to add next | [`recommendations/`](recommendations/) |

## The reproducibility line

This is the thing worth understanding before anything else.

**Reproducible from this repository:**

- Owned skills — `./scripts/install_skills.sh`
- Claude Code settings, permissions and hooks — copy from `settings/`
- Project MCP servers — copy from `mcp/`

**Not reproducible from any file, ever:**

- claude.ai connectors. Each is added in the web UI, and fifteen of the twenty-three need an
  interactive OAuth login.
- claude.ai plugins. Installed from a marketplace in the web UI.
- Built-in Anthropic skills. Toggled per account under Settings → Capabilities.

That second list is not a gap in this repository — it is a property of how the platform
works, and it is deliberate: those grants exist behind a human at a browser holding
credentials that must never live in git. What this repository does instead is record
**exactly which ones**, **in what order**, and **why**, so the manual work takes twenty
minutes and nothing is forgotten. That is
[`docs/03-manual-setup-checklist.md`](../../docs/03-manual-setup-checklist.md).

## Never in this directory

No API key, OAuth token, session cookie, connection string, private key or password.
These files describe *which* services are connected — never *how* to authenticate to them.
Both settings templates carry `deny` rules stopping Claude from reading `.env` files and
private keys, for the same reason.

If a credential ever does land here: rotate it first, then remove it from the history.
Deleting the file is not enough.

## Keeping it current

The inventory is a record of one moment and it goes stale silently, which is worse than
being absent, because a stale inventory is still trusted. Refresh it whenever the
workspace changes, and update `captured_at` in the same commit:

> Refresh `config/claude/inventory/` against my live account and tell me what changed.
