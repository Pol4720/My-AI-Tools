<div align="center">

# My AI Tools

**The Claude workspace of [Richard Matos (@Pol4720)](https://github.com/Pol4720) — declared, versioned and reproducible.**

Skills that encode a standard · configuration that can be rebuilt · documentation that says what it cannot do

</div>

---

An AI workspace is usually invisible: a set of skills, connectors and settings that live in
someone's account, cannot be inspected, cannot be shared, and vanish with the account.

This repository makes that workspace an artifact — **versioned, reviewable, and rebuildable
on a new account in about twenty-five minutes**, including an honest account of the parts a
file can never rebuild.

## Quick start

```bash
git clone https://github.com/Pol4720/My-AI-Tools.git
cd My-AI-Tools
./scripts/install_skills.sh          # symlink every skill into ~/.claude/skills/
python3 scripts/validate_skills.py   # confirm all three are healthy
```

Start a new Claude Code session and, without naming any skill:

> Audit this repository and fix everything you find.

Full walkthrough: [`docs/00-getting-started.md`](docs/00-getting-started.md).

## The skills

| Skill | Domain | What it does |
|---|---|---|
| [**`repo-audit-fixer`**](skills/engineering/repo-audit-fixer/) | engineering | Audits a repository as a hostile QA engineer, security reviewer and staff engineer at once — then fixes everything and proves each fix. Delivers a LaTeX audit report. |
| [**`q1-paper-auditor`**](skills/research/q1-paper-auditor/) | research | Reviews a paper like a demanding Q1 referee, verifies every number against the data and code, repairs LaTeX to zero warnings, writes the response letter. |
| [**`thesis-auditor-fixer`**](skills/research/thesis-auditor-fixer/) | research | The same standard for a CS/SE thesis in LaTeX — exact corrections, not just critique. |

### `repo-audit-fixer` in a paragraph

Point it at a repository. It reads the documentation and the code, **builds the software
and runs it**, drives hostile inputs through every surface, reviews the result through
twelve independent lenses in parallel, hunts the implementations that were never written,
verifies every claim the software makes about itself, repairs everything in dependency
order, and proves each fix with a regression test demonstrated to fail on the pre-fix code.

It is governed by four rules that override everything else in it:

> **The green-gate rule.** Never make a check pass by weakening the check.
> **The reproduce-first rule.** A finding you cannot demonstrate is a hypothesis.
> **The no-cosmetics rule.** Do not report style while real defects stand.
> **The honest-ledger rule.** Every finding ends fixed, mitigated, accepted or open — with evidence for each fix and a reason for each non-fix.

The deliverable lands inside the audited repository:

```
Reports/audit-YYYY-MM-DD-HHMM/
├── audit.pdf        compiled clean — zero errors, zero warnings
├── audit.tex        rendered from the ledger, so the prose cannot drift from the counts
├── findings.json    the machine-readable ledger, schema-validated
├── evidence/        reproductions, traces, before/after output
└── README.md        one screen for someone who will not open the PDF
```

Never overwritten. Repeated audits accumulate, which is what lets a returning defect be
recognised as a **regression** rather than rediscovered as news.

## Layout

```
skills/            engineering · research
config/claude/     inventory · settings · mcp · recommendations
docs/              getting started · architecture · authoring · setup · profile
scripts/           install_skills.sh · validate_skills.py
templates/skill/   scaffold for the next skill
```

Why it is shaped this way: [`docs/01-repository-architecture.md`](docs/01-repository-architecture.md).

## The configuration half

[`config/claude/`](config/claude/) declares the workspace: eighteen MCP connectors, the
enabled skills, the plugins, the Claude Code settings and hooks — what each is for, and
whether it can be restored from a file.

That last distinction is the point. **Owned skills, settings and project MCP servers are
reproducible from this repository. claude.ai connectors, plugins and built-in skills are
not** — each needs a human at a browser holding credentials that must never live in git.
So rather than pretending otherwise,
[`docs/03-manual-setup-checklist.md`](docs/03-manual-setup-checklist.md) is an ordered,
checkable list of exactly those steps, and
[`config/claude/recommendations/`](config/claude/recommendations/) argues for what to add
next and what to deliberately skip.

**No credential of any kind is in this repository.** These files record *which* services
are connected, never *how* to authenticate to them. CI scans for committed secrets on
every push.

## Quality gate

Every push runs [`scripts/validate_skills.py`](scripts/validate_skills.py) across four
Python versions. It checks that each skill's front matter parses, that `name` matches its
directory, that `description` is substantial enough to trigger, that every file referenced
in `SKILL.md` exists, that every bundled script parses and runs `--help`, and that nothing
resembling a credential is committed.

```bash
python3 scripts/validate_skills.py           # all skills
python3 scripts/validate_skills.py --skill skills/engineering/repo-audit-fixer
```

## Contributing

Sole authorship: **Pol4720**. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for commit
conventions, and [`docs/02-skill-authoring-guide.md`](docs/02-skill-authoring-guide.md) for
how to write a skill that actually triggers.

## Licence

[`LICENSE`](LICENSE) — © 2026 Richard Matos (Pol4720). All rights reserved.
