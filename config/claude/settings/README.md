# Claude Code settings

Templates for `settings.json`, the file through which the Claude Code **harness** — not
Claude — is configured. This distinction matters: anything that must happen automatically
(a formatter after every edit, a blocked command, an environment variable) is a hook or a
permission rule here. Asking Claude to remember it does not work reliably; a hook does.

| File | Copy to | Committed? |
|---|---|---|
| [`settings.user.json`](settings.user.json) | `~/.claude/settings.json` | Personal, all projects |
| [`settings.project.json`](settings.project.json) | `<project>/.claude/settings.json` | **Yes** — the whole team gets it |
| — | `<project>/.claude/settings.local.json` | **No** — gitignored, machine-specific only |

Precedence runs lowest to highest down that table: a project setting overrides a personal
one, and a local setting overrides both.

## The one rule

**No secrets in any of these files.** Two of the three are committed, and the third is one
`git add -f` away from being committed. API keys, tokens and passwords belong in the
environment or in a secret manager. The `deny` lists in both templates block Claude from
reading `.env` files and private keys for the same reason.

## What the templates set

**`settings.user.json`** — pre-approves read-only commands and the common test/lint
invocations so routine work does not stop for a permission prompt, and denies
force-pushes, hard resets and reads of credential files. It also carries a
commented-out hook example (`_hooks_example`) showing the shape of a
format-on-edit hook.

**`settings.project.json`** — allows the project's own gate commands so an audit can run
the checks without asking, and denies history rewriting. It also states, deliberately,
that `Reports/` must stay committed when the project is audited with `repo-audit-fixer`:
the accumulated audit history is what lets a later audit recognise a returning defect as a
regression instead of a fresh discovery.

## Editing these

Use the built-in **`update-config`** skill rather than hand-editing — it knows the schema,
the hook event names, and the shape of the JSON each event receives:

> Add a hook that runs `ruff format` after every Python file edit.

And the **`fewer-permission-prompts`** skill builds an allowlist from what you have
actually been approving, which produces a better list than guessing.

## Verifying a change took effect

Settings are read when a session starts. After editing, start a new session and check with
`/config`, or ask Claude to read the resolved settings. A hook that silently does not fire
is worse than no hook — if you add one, test it once deliberately.
