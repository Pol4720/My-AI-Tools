# Skill authoring guide

How to write a skill for this repository that actually triggers, actually works, and still
works six months from now.

The fastest route is the enabled **`skill-creator`** skill — it scaffolds, and it runs
evals, which is the only honest way to find out whether a description triggers. This guide
covers the judgement `skill-creator` cannot make for you.

---

## Before writing: is a skill the right shape?

| Situation | Right tool |
|---|---|
| A repeatable process with judgement in it, that you will run again | **A skill** |
| Something that must happen automatically on every edit or command | **A hook** in `settings.json` — Claude cannot be relied on to remember; the harness can |
| A fact you want Claude to know about one project | **`CLAUDE.md`** in that project |
| A deterministic transformation | **A script**, possibly inside a skill |
| A one-off | Just ask |

The test that matters: **would a generic tool already do this well?** Every skill in this
repository exists because the answer was no — because it encodes a *standard*, not just a
procedure. If a built-in already covers it, use the built-in.

---

## Front matter

```yaml
---
name: repo-audit-fixer
description: >
  What it does, in one or two sentences. Then: when to use it — the situations, the
  phrasings a user would actually type, in every language they would type them in.
license: Proprietary — © Richard Matos (Pol4720). See repository LICENSE.
---
```

`name`: lowercase, hyphenated, matching the directory, at most 64 characters.

`description`: **the most important line in the skill.** It is the only thing Claude sees
when deciding whether to load it, and a skill that does not trigger does not exist.

Write it in two halves:

1. **What it does** — concrete, not aspirational. "Audits an entire repository as a hostile
   QA engineer, then fixes what it finds and proves the fix" beats "helps with code
   quality".
2. **When to use it** — the trigger surface. Every phrasing a user might reach for, in
   every language they use. `repo-audit-fixer` names "audit", "QA", "harden", "is this
   production ready", *"audita este repo"*, *"arregla todo"*, and a bare repository path,
   because all of those are things that get typed.

Two failure modes, both common:

- **Too narrow** → the skill never fires, and you end up invoking it by name every time,
  which defeats the point.
- **Too broad** → it fires on unrelated work and gets in the way. Worse than too narrow,
  because it erodes trust in every skill.

Name the boundary explicitly when there is a near neighbour. `q1-paper-auditor` and
`thesis-auditor-fixer` overlap; each says which is which.

---

## Body

Keep `SKILL.md` under ~500 lines. Past that, the instructions that matter get buried and
every invocation pays for the excess.

The structure that has worked here:

1. **Identity and standard.** Who Claude is being, and what "done" means. Concretely —
   "could a hostile engineer find something that would embarrass the author on deployment
   day" gives a bar to clear; "be thorough" does not.
2. **Invocation contract.** What inputs to accept, so the user never has to write a prompt.
3. **Autonomy.** What to do without asking, and the narrow set of things worth interrupting
   for. Be specific about the second: a skill that asks too often is abandoned, and one that
   never asks makes decisions that were not its to make.
4. **The rules that make it trustworthy.** The two or three inviolable ones, stated as
   overriding everything else. `repo-audit-fixer` has four — the green-gate rule, the
   reproduce-first rule, the no-cosmetics rule, the honest-ledger rule. These are what stop
   a skill optimising for looking successful.
5. **The workflow.** Ordered phases, each saying *why* it comes where it does.
6. **Deliverables.** Exact format, exact location.
7. **Bundled resources.** A table naming each reference and the phase that calls for it.
8. **What finishing looks like.** A checklist you can actually verify against.

Write in the imperative, addressed to Claude. Explain *why* an instruction exists whenever
the reason is not obvious — an instruction with a reason survives edge cases the author did
not foresee, and one without it gets applied where it does not fit.

---

## References

`references/*.md`, one topic each, loaded on demand.

This is progressive disclosure and it is the main lever on a skill's cost: `SKILL.md`
carries the workflow and the judgement, references carry the depth. Claude opens
`language-playbooks.md` when it needs Rust specifics, not before.

Name each reference in `SKILL.md` with the phase that calls for it — the validator checks
that every path referenced in backticks actually exists.

---

## Scripts

**Anything deterministic goes in a script.** Not because prose cannot describe it, but
because a script does it identically every time, in a fraction of the tokens, and its
output is evidence rather than assertion.

House rules:

- Python 3, **standard library only** — no dependency means it runs anywhere.
- `--help` and, where output feeds another step, `--json`.
- A module docstring saying what it does and how it is used.
- Exit codes that mean something: 0 success, 1 findings/failure, 2 usage error.
- **Fail loudly.** A script that silently returns nothing when it cannot do its job is the
  exact defect class these skills exist to find.

`python3 scripts/validate_skills.py` runs `--help` on every bundled script. A script that
crashes there is a broken skill, and CI will say so.

---

## Assets

Templates the skill copies into a user's project: a LaTeX template, a config scaffold, a
document skeleton. Keep them complete and runnable — an asset that needs hand-editing
before it works is half an asset.

---

## Testing — the part that is usually skipped

A skill that has never been run on real work is a draft.

1. **Validate.** `python3 scripts/validate_skills.py --skill skills/<domain>/<name>`
2. **Trigger test.** In a fresh session, describe the task **without naming the skill**. If
   it does not fire, the description is wrong — fix the description, not your phrasing.
3. **Negative trigger test.** Describe a *related but different* task. If it fires anyway,
   the description is too broad.
4. **Run it end to end** on something real. Every skill in this repository found a bug in
   its own scripts this way — a syntax error the validator caught had been sitting
   unnoticed until then.
5. **Eval it.** `skill-creator` runs eval suites with variance analysis — the only way to
   know a description triggers reliably rather than once.

---

## Adding it to this repository

```bash
cp -r templates/skill skills/<domain>/<name>
# write SKILL.md, references, scripts
python3 scripts/validate_skills.py
./scripts/install_skills.sh <name>
# use it on something real, fix what breaks
```

Then:

- [ ] Add an entry to `config/claude/inventory/skills.json` under `owned`
- [ ] Add a row to the skill table in `README.md`
- [ ] Add a line to `CHANGELOG.md`
- [ ] Commit atomically, with a message saying what the skill does and why it exists

---

## Maintenance

Skills rot in specific ways. Re-read a skill when:

- A tool it names changes its interface, or is replaced.
- A phase of its workflow keeps being skipped in practice — either the phase is wrong or
  the instruction is unclear.
- You find yourself correcting the same thing on every run — that correction belongs in the
  skill.
- It stops triggering, or starts triggering on the wrong things.

The last one is the most common and the least noticed. If you have started invoking a skill
by name out of habit, its description has stopped working.
