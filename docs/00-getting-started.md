# Getting started

Five minutes to a working setup.

## 1. Install the skills

```bash
git clone https://github.com/Pol4720/My-AI-Tools.git
cd My-AI-Tools
./scripts/install_skills.sh
```

Symlinks each skill into `~/.claude/skills/`, so editing a skill here is live in Claude
Code immediately, with git as the single source of truth. Use `--copy` on a machine where
this repository will not stay checked out, and `--target <dir>` for a project-scoped
install.

## 2. Confirm they are healthy

```bash
python3 scripts/validate_skills.py
```

Expect four skills, one warning about `openpyxl` (a documented dependency of `lsc-asesor`,
not installed by default). Anything else is a real problem.

## 3. Start a new session

Skills load at session start. Then, without naming any skill:

> Audit this repository and fix everything you find.

`repo-audit-fixer` should pick it up. If it does not, the description needs work — see
[`02-skill-authoring-guide.md`](02-skill-authoring-guide.md).

## 4. Optionally, the settings

```bash
cp config/claude/settings/settings.user.json ~/.claude/settings.json
```

Pre-approves read-only commands and the common test/lint invocations so routine work
stops asking; denies force-pushes, hard resets, and reads of `.env` files and private
keys. Read it before copying — it is a starting point, not a mandate.

---

## What each skill is for

### `repo-audit-fixer` — engineering

Point it at a repository and it audits, fixes and proves. Ten phases: recon, comprehension,
ecosystem research, **actually running and exercising the software**, adversarial review
through twelve independent lenses, a hunt for missing implementations, verification of every
claim, repair in dependency order, proof, and a LaTeX report.

```
Audit ~/projects/my-service and leave it impeccable.
Audita este repo — encuentra todos los bugs y arréglalos.
Is this production ready?
```

**Deliverable:** `Reports/audit-YYYY-MM-DD-HHMM/` — `audit.pdf`, `audit.tex`,
`findings.json`, `evidence/` and a one-screen `README.md`, inside the audited repository.
Never overwritten, so repeated audits accumulate into a history.

Not a linter. It builds the software, runs it, drives hostile inputs through it, and every
fix carries a regression test proven to fail on the pre-fix code.

### `q1-paper-auditor` — research

A demanding Q1 referee that also does the repairs. Verifies every number against the data
and the code, checks the literature is current, repairs LaTeX to zero warnings, keeps
language versions in parity, and writes a response letter when reviewer comments are
supplied.

```
Audit my paper before I submit it.
Here are the reviewer comments — address them.
```

### `thesis-auditor-fixer` — research

The same standard for a CS / Software Engineering thesis in LaTeX. Produces exact
corrections — rewritten paragraphs, fixed LaTeX, corrected citations — not just a critique.

```
Review chapter 3 of my thesis.
```

### `lsc-asesor` — business

Advisory engine for La Subasta Cubana: pre-qualification, total-cost modelling, comparison
spreadsheets, client PDFs. Needs
`pip install requests beautifulsoup4 openpyxl pillow playwright`.

---

## Where to go next

| | |
|---|---|
| Why the repository is shaped this way | [`01-repository-architecture.md`](01-repository-architecture.md) |
| Writing your own skill | [`02-skill-authoring-guide.md`](02-skill-authoring-guide.md) |
| Rebuilding the whole workspace on a new account | [`03-manual-setup-checklist.md`](03-manual-setup-checklist.md) |
| What this workspace optimises for, and why | [`04-workspace-profile.md`](04-workspace-profile.md) |
| What is installed today | [`../config/claude/inventory/`](../config/claude/inventory/) |
| What to add next | [`../config/claude/recommendations/`](../config/claude/recommendations/) |

## Troubleshooting

**A skill does not trigger.** Start a new session — skills load at session start. If it
still does not, the `description` is the problem, not your phrasing.

**`install_skills.sh` says "skip".** Something already exists at that path in
`~/.claude/skills/` that this script did not create. It will not delete work it does not
own; remove it yourself, or install elsewhere with `--target`.

**The audit PDF does not build.** The report needs `latexmk` or `pdflatex`
(`texlive-latex-base`, `texlive-latex-recommended`, `texlive-latex-extra`, `lmodern`; add
`texlive-lang-spanish` for Spanish reports). Without them the skill ships `audit.tex` plus
a Markdown rendering and says so — it will not claim a PDF that does not exist.

**A bundled script fails.** Run it directly: `python3 skills/<domain>/<name>/scripts/<x>.py --help`.
Every script is standard-library only except `lsc-asesor`'s, which document their
dependencies.
