# Repository architecture

Why this repository is laid out the way it is. Read this before adding to it.

## The layout

```
My-AI-Tools/
├── skills/                 the assets — everything else serves these
│   ├── engineering/
│   │   └── repo-audit-fixer/
│   ├── research/
│   │   ├── q1-paper-auditor/
│   │   └── thesis-auditor-fixer/
│   └── business/
│       └── lsc-asesor/
├── config/claude/          the workspace, declared
│   ├── inventory/          what the account has today
│   ├── settings/           Claude Code settings.json templates
│   ├── mcp/                project MCP server template
│   └── recommendations/    what to add next, and why
├── docs/                   how to use, extend and rebuild all of it
├── scripts/                install and validate
├── templates/skill/        scaffold for the next skill
└── .github/workflows/      CI that runs the validator on every push
```

## The three decisions that shape it

### 1. Skills are grouped by domain, not by type

`skills/engineering/`, `skills/research/`, `skills/business/`. The alternative — a flat
`skills/` directory — works fine at four skills and stops working at fifteen, and
renaming directories later breaks every symlink an install script has created.

Domain grouping also carries information: a skill's location tells you the standards it
should hold itself to. Anything under `research/` is expected to treat citation integrity
and reproducibility as first-class; anything under `engineering/` is expected to run the
software it audits.

Claude Code discovers skills by the presence of `SKILL.md`, not by path, so the grouping
costs nothing at runtime. `scripts/install_skills.sh` flattens it when installing, because
`~/.claude/skills/` is flat.

### 2. Configuration is declarative, and honest about what it cannot do

`config/claude/` records the workspace as data. Some of it can be applied by a script;
most of it cannot, because OAuth grants require a human at a browser.

Rather than pretending otherwise, the split is explicit: the inventory says what exists,
the templates say what can be copied, and
[`docs/03-manual-setup-checklist.md`](03-manual-setup-checklist.md) is an ordered list of
what only you can do. A setup guide that silently omits the manual half is how a workspace
ends up half-configured and failing quietly.

### 3. Only owned skills are vendored

`skills/` holds the four skills authored by Pol4720 and nothing else.

Anthropic's built-in skills — `pdf`, `xlsx`, `docx`, `pptx`, `skill-creator`,
`canvas-design`, `import-memory`, `morning` — are **not** copied here. They are Anthropic's,
they update upstream, and a vendored copy would go stale while looking authoritative. They
are *recorded* in [`config/claude/inventory/skills.json`](../config/claude/inventory/skills.json)
so the workspace is described completely, and enabled per account.

## Anatomy of a skill

```
<skill-name>/
├── SKILL.md          required · front matter + the instructions themselves
├── references/       loaded on demand, when a phase calls for it
├── scripts/          deterministic work — always cheaper and more reliable than prose
└── assets/           templates and files the skill copies into a project
```

The design principle is **progressive disclosure**. `SKILL.md` carries the workflow and
the judgement; `references/` carries the depth. Claude reads a reference file when the
phase needs it, not before. A skill that puts everything in `SKILL.md` wastes context on
every invocation and buries the instructions that matter.

The corollary: **anything deterministic belongs in `scripts/`**. Scanning a tree for stubs,
validating a JSON schema, rendering LaTeX — a script does these identically every time,
and its output is evidence. Prose asking Claude to do the same thing is slower, more
expensive and less reliable.

## Conventions

**Scripts** are Python 3, standard library only, with `--help` and `--json`. No dependency
means the skill works in any environment. `--json` means one script can feed another.
The validator enforces that every script parses and runs `--help`.

**References** are Markdown, one topic each, named for what they contain. `SKILL.md` names
each one and says which phase calls for it.

**Descriptions** — the `description` in the front matter is the single most important line
in a skill, because it decides whether the skill ever triggers. Say what it does *and when
to use it*, include the words a user would actually type, in both languages if the skill is
used in both. See [`02-skill-authoring-guide.md`](02-skill-authoring-guide.md).

## What does not belong here

- **Credentials of any kind.** Both settings templates deny reading `.env` files and
  private keys; the validator scans for committed secrets on every push.
- **Anthropic's skill sources.** Not ours to redistribute.
- **Project data.** This repository holds tools, not the material they operate on.
- **A skill that has never been run.** Validate it, then use it on something real, then
  commit it.
