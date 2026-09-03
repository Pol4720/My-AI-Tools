## What changed

<!-- One or two sentences. What is different after this PR. -->

## Why

<!-- The problem this solves. If it fixes a defect, say what was broken and what the root
     cause was — not just the symptom. A reader six months from now needs the reason more
     than the description. -->

## Type

- [ ] New skill
- [ ] Change to an existing skill
- [ ] Configuration / inventory update
- [ ] Documentation
- [ ] Tooling (scripts, CI)
- [ ] Fix

## Verification

<!-- What you actually ran. Not what you intended to run. -->

- [ ] `python3 scripts/validate_skills.py` passes
- [ ] `./scripts/install_skills.sh --list` still resolves every skill
- [ ] Bundled scripts run: `python3 <script> --help`

**If this touches a skill:**

- [ ] Triggered it in a fresh session **without naming it** — it fired
- [ ] Described a *related but different* task — it did **not** fire
- [ ] Ran it end to end on real work

**If this adds or changes a skill:**

- [ ] `config/claude/inventory/skills.json` updated
- [ ] `README.md` skill table updated
- [ ] `CHANGELOG.md` updated

## Checks

- [ ] No credential, token, key or connection string is committed
- [ ] No personal, clinical or client data, including in fixtures
- [ ] Commits are atomic and their messages explain the *why*
- [ ] Authored by Pol4720; no tool or assistant appears as author, co-author, or in the branch name
