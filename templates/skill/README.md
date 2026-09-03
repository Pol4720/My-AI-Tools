# Skill scaffold

Copy this directory to start a new skill:

```bash
cp -r templates/skill skills/<domain>/<name>
```

Then rewrite `SKILL.md` completely — the placeholders are prompts to think, not text to
keep. Delete `references/`, `scripts/` or `assets/` if the skill does not need them; an
empty directory is noise.

Read [`../../docs/02-skill-authoring-guide.md`](../../docs/02-skill-authoring-guide.md)
first. The single highest-leverage decision is the `description`: it is the only thing
Claude sees when deciding whether to load the skill, and a skill that does not trigger
does not exist.

Before committing:

```bash
python3 scripts/validate_skills.py --skill skills/<domain>/<name>
./scripts/install_skills.sh <name>
# then use it on real work, and fix what breaks
```
