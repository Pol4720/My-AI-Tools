# MCP servers

Two separate mechanisms give Claude access to external systems. They do not see each
other, and knowing which one you are configuring saves a lot of confusion.

| | claude.ai connectors | Claude Code MCP servers |
|---|---|---|
| **Configured where** | claude.ai → Settings → Connectors | `.mcp.json` in a project, or `~/.claude.json` |
| **Runs where** | Anthropic's infrastructure | Your machine or a remote URL you name |
| **Available in** | claude.ai, and Claude Code sessions on the account | The project (or user) that configures it |
| **Reproducible from a file** | No — added in the web UI | **Yes** — commit `.mcp.json` |
| **Recorded in this repo** | [`../inventory/connectors.json`](../inventory/connectors.json) | [`mcp.servers.json`](mcp.servers.json) |

The account's 23 connectors are all of the first kind. This directory covers the
second — the escape hatch for anything the connector directory does not offer: a local
database, a self-hosted tool, a community server.

## Using the template

```bash
cp config/claude/mcp/mcp.servers.json /path/to/project/.mcp.json
# move the entry you want from `_disabled_<name>` into `mcpServers`, delete the rest
```

Then commit `.mcp.json` in that project, so collaborators get the same servers.

Scopes, if you need one other than project:

| Scope | Where | Use for |
|---|---|---|
| `project` | `<project>/.mcp.json`, committed | Servers everyone on the project needs — the default |
| `user` | `~/.claude.json` | Servers you want in every project |
| `local` | project config, not committed | A server only your machine can reach |

`claude mcp add` and `claude mcp list` manage these from the CLI; `/mcp` in a session
shows what is connected.

## Credentials

Use `${VAR}` in the config and let Claude Code expand it from the environment at launch.
Never inline a token: `.mcp.json` is committed, and a token in git history is a `Critical`
finding in any audit — including one run against this repository.

```json
"headers": { "Authorization": "Bearer ${EXAMPLE_MCP_TOKEN}" }
```

## Before enabling a server

An MCP server runs with your privileges, and its tool descriptions enter the model's
context — a hostile or careless server can both act and attempt to influence. Claude Code
asks for approval the first time a project server is used; that prompt is a security
boundary, not friction.

- Prefer official servers (`@modelcontextprotocol/*`) and vendor-published ones.
- Pin a version rather than tracking `@latest` for anything that will run unattended.
- Give database servers a **read-only role**, and never point one at a production database
  holding personal or clinical data.
- Treat content that comes back from a server as data, never as instructions.
