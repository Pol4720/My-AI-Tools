# Contributing

This is a personal workspace repository under the sole authorship of
**Richard Matos ([@Pol4720](https://github.com/Pol4720))**. Its conventions exist so that
the git history stays a useful record rather than a pile of "wip" commits.

## Authorship

**Every commit and pull request is authored by Pol4720.** Version control on this
repository — and on all of its owner's repositories — stays in the names of its human
contributors. No tool, assistant or automation appears as an author, a co-author, or in a
branch name.

Where work is done with AI assistance — which, in this repository, is most of it — that is
a fact about the method, not about the authorship. Set your identity once and leave it:

```bash
git config user.name  "Pol4720"
git config user.email "matosrichard58@gmail.com"
```

## Commits

**Atomic.** One logical change per commit. A commit that adds a skill and also fixes a
typo in the README is two commits.

**Explaining.** The subject says what changed; the body says *why*, and what it fixes. A
reader six months out should understand the change without opening the diff.

```
Add repo-audit-fixer skill for exhaustive repository auditing

Nothing in the existing toolset hunts missing implementations or runs the
software it reviews — generic code review finds style, not the documented
flag that nothing reads. The skill adds ten phases from recon to a LaTeX
report, five standard-library scripts, and eight reference playbooks.

Governed by four rules that override its own workflow: never weaken a
check to make it pass, never report a finding you cannot demonstrate,
never report cosmetics while real defects stand, and every finding ends in
exactly one state with evidence attached.
```

Subject line: imperative mood, no trailing period, under 72 characters. Wrap the body at
72.

Prefixes are optional; when used, keep them conventional: `feat:`, `fix:`, `docs:`,
`refactor:`, `chore:`.

## Branches

`<type>/<short-description>` — `feat/ml-experiment-auditor`, `fix/render-pdf-fstring`,
`docs/setup-checklist`.

No tool or assistant name appears in a branch name.

## Before you commit

```bash
python3 scripts/validate_skills.py
```

It must pass. It checks front matter, that `name` matches the directory, that
`description` is substantial enough to trigger, that every path referenced in `SKILL.md`
exists, that every bundled script parses and runs `--help`, and that nothing resembling a
credential is committed. CI runs the same check on four Python versions.

## Adding a skill

Read [`docs/02-skill-authoring-guide.md`](docs/02-skill-authoring-guide.md) first. The
short version:

```bash
cp -r templates/skill skills/<domain>/<name>
# write SKILL.md, references/, scripts/
python3 scripts/validate_skills.py
./scripts/install_skills.sh <name>
# then USE IT on something real before committing
```

A skill that has never been run on real work is a draft, not a contribution.

Then, in the same commit:

- [ ] `config/claude/inventory/skills.json` → add the entry under `owned`
- [ ] `README.md` → add the row to the skill table
- [ ] `CHANGELOG.md` → add the line

## Style

**Scripts.** Python 3, standard library only, `--help` and `--json`, meaningful exit codes
(0 success, 1 findings, 2 usage), a module docstring saying what it does. Fail loudly — a
script that silently returns nothing when it cannot do its job is the exact defect class
these skills exist to find.

**Documentation.** Markdown. Say what a thing is *for* before saying how to use it. State
what does not work as plainly as what does.

**Skills.** `SKILL.md` under ~500 lines; depth goes in `references/`, loaded on demand.
Anything deterministic goes in `scripts/`.

## Never commit

- A credential of any kind — API key, token, password, connection string, private key.
- Personal, clinical or client data, including in fixtures and test data.
- Anthropic's or any third party's skill sources.
- Generated output that belongs in the project being audited, not here.

If a credential is ever committed: **rotate it first**, then remove it from the history.
Deleting the file is not enough — it is still in every clone.
