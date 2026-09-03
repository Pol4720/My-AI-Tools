# Account inventory

A declarative snapshot of the Claude workspace of **Pol4720 (Richard Matos)**, captured
**2026-09-03** from the live account.

The point of this directory is reconstruction. If the account is lost, a second account is
opened, or a colleague wants the same environment, everything needed to rebuild it is
recorded here — plus, in [`../../../docs/03-manual-setup-checklist.md`](../../../docs/03-manual-setup-checklist.md),
an explicit list of the steps that only a human can perform.

| File | Records |
|---|---|
| [`connectors.json`](connectors.json) | Every MCP connector installed on the account, its purpose, its auth mode, and what it is used for |
| [`skills.json`](skills.json) | Skills, split into **owned** (source lives in this repository) and **builtin** (Anthropic's, enabled per account) |
| [`plugins.json`](plugins.json) | Plugins enabled on the account, and the marketplaces visible to it |

## What is and is not reproducible from these files

| | Reproducible from a file? | How |
|---|---|---|
| **Owned skills** | Yes | `./scripts/install_skills.sh`, or upload to claude.ai |
| **Claude Code settings & hooks** | Yes | Copy from [`../settings/`](../settings/) |
| **Project MCP servers (Claude Code)** | Yes | Copy [`../mcp/mcp.servers.json`](../mcp/mcp.servers.json) to `.mcp.json` |
| **claude.ai connectors** | **No** | Each is added in the web UI; OAuth ones need an interactive login |
| **claude.ai plugins** | **No** | Installed from a marketplace in the web UI |
| **Built-in skills** | **No** | Toggled per account under Settings → Capabilities |

The three "No" rows are exactly what the manual setup checklist covers. Nothing about
them is secret — they simply require a human at a browser, holding credentials that must
never live in a repository.

## Keeping the snapshot honest

These files are a record of a moment, and they go stale silently. Refresh them whenever
the workspace changes — a connector added, a plugin enabled, a skill written — and update
`captured_at` in the same commit. A stale inventory is worse than none, because it will be
trusted.

Ask Claude, in a session that has the account tools available:

> Refresh `config/claude/inventory/` against the live account and tell me what changed.

## Deliberately not recorded here

- **Credentials of any kind** — API keys, OAuth tokens, session cookies, connection
  strings. These files describe *which* services are connected, never *how* to
  authenticate to them.
- **Personal or client data** reachable through a connector.
- **Anthropic's own skill sources.** They are enabled per account, updated upstream, and
  are not this repository's to redistribute.
