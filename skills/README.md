# Skills

The four skills authored by [Pol4720](https://github.com/Pol4720), grouped by domain.

| Skill | Domain | Does |
|---|---|---|
| [`repo-audit-fixer`](engineering/repo-audit-fixer/) | engineering | Audits a repository as a hostile QA engineer, security reviewer and staff engineer, fixes everything found, proves each fix, delivers a LaTeX audit report |
| [`q1-paper-auditor`](research/q1-paper-auditor/) | research | Reviews a paper as a demanding Q1 referee, verifies every number against the data and code, repairs LaTeX to zero warnings, writes the response letter |
| [`thesis-auditor-fixer`](research/thesis-auditor-fixer/) | research | The same standard for a CS/SE thesis in LaTeX — exact corrections, not just critique |
| [`lsc-asesor`](business/lsc-asesor/) | business | Advisory engine for La Subasta Cubana: pre-qualification, cost modelling, comparison spreadsheets, client PDFs |

## Installing

```bash
../scripts/install_skills.sh              # all of them, symlinked
../scripts/install_skills.sh repo-audit-fixer
../scripts/install_skills.sh --copy       # copy instead of symlink
```

`~/.claude/skills/` is flat, so the installer flattens the domain grouping. Claude Code
discovers skills by the presence of `SKILL.md`, not by path.

## Anatomy

```
<skill-name>/
├── SKILL.md          required · front matter + the instructions
├── references/       loaded on demand, when a phase calls for it
├── scripts/          deterministic work — cheaper and more reliable than prose
└── assets/           templates the skill copies into a project
```

**Progressive disclosure** is the organising idea: `SKILL.md` carries the workflow and the
judgement, `references/` carries the depth, and Claude opens a reference when the phase
needs it rather than on every invocation.

**Anything deterministic belongs in `scripts/`.** A script does the same thing every time,
in a fraction of the tokens, and its output is evidence rather than assertion.

## What is not here

Anthropic's built-in skills — `pdf`, `xlsx`, `docx`, `pptx`, `skill-creator`,
`canvas-design`, `import-memory`, `morning` — are **not** vendored. They are Anthropic's,
they update upstream, and a stale copy that looked authoritative would be worse than none.
They are recorded by name in
[`../config/claude/inventory/skills.json`](../config/claude/inventory/skills.json) and
enabled per account.

## Adding one

Read [`../docs/02-skill-authoring-guide.md`](../docs/02-skill-authoring-guide.md), start
from [`../templates/skill/`](../templates/skill/), and run
`python3 ../scripts/validate_skills.py` before committing.

A skill that has never been run on real work is a draft.
