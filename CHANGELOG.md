# Changelog

Notable changes to this workspace. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning is date-based, because a workspace is not a released library.

## [Unreleased]

## [2026-09-16] — Description length fix; connector inventory refresh

### Fixed

- **`repo-audit-fixer`: `description` exceeded claude.ai's own skill-upload limit.**
  claude.ai's skill validator rejects a `description` over 1024 characters; this skill's
  was 1169. The skill was correct and useful in every way that mattered locally —
  `scripts/validate_skills.py` passed it clean — and still could not be uploaded, because
  this repository's own length check was set to 4000, far looser than the platform it was
  meant to guard. Tightened the description to 1004 characters, preserving both trigger
  halves (what it does, when to use it, in English and Spanish), and corrected
  `MAX_DESCRIPTION` in the validator to 1024 so the same gap cannot reopen silently.
  Verified by re-running the skill through the official `skill-creator` packager, which now
  reports the package valid.

### Changed

- `config/claude/inventory/connectors.json` refreshed against the live account: added
  ChEMBL, BioRender, Owkin, Synapse.org and the account's own GitHub connector (23
  connectors total, up from 18); recorded that Cloudflare Developer Platform, Owkin and
  Synapse.org need re-authorisation (`needs_reconnect` — each worked once and the grant has
  since lapsed), and that the Monte Carlo connection attempt was started and left
  incomplete.
- `config/claude/recommendations/connectors.md` updated to match: the four newly connected
  bio-research connectors (three working, one — Owkin plus Synapse.org — needing a second
  authorisation pass) make that recommendation's plugin-bundled connector story redundant
  for this account.
- `docs/03-manual-setup-checklist.md`, `docs/01-repository-architecture.md`, `README.md`
  and `config/claude/README.md` updated to the current connector and skill counts.

## [2026-09-03] — Initial workspace

The repository goes from empty to a complete, declared workspace.

### Added — skills

- **`repo-audit-fixer`** (engineering) — new. Audits a repository as a hostile QA engineer,
  security reviewer and staff engineer at once, fixes what it finds, and proves each fix.
  Ten phases from recon through to a compiled LaTeX report; twelve independent audit lenses
  run in parallel; a dedicated phase for hunting implementations that were never written.
  Governed by four overriding rules — green-gate, reproduce-first, no-cosmetics,
  honest-ledger.
  - 8 reference playbooks: audit lenses, defect taxonomy, incompleteness hunting,
    per-language and per-stack playbooks, verification, tooling catalog, report spec
  - 5 standard-library scripts: `repo_recon.py`, `incompleteness_scan.py`,
    `run_toolchain.py`, `findings.py`, `build_report.py`
  - LaTeX report template compiling to zero errors and zero warnings in English and
    Spanish, plus narrative and folder-README templates
  - Deliverable: `Reports/audit-YYYY-MM-DD-HHMM/` inside the audited repository, never
    overwritten, so audits accumulate into a history and a returning defect is recognised
    as a regression
- **`q1-paper-auditor`** (research) — vendored from the account, authored 2026-08-14
- **`thesis-auditor-fixer`** (research) — vendored from the account, authored 2026-05-18

### Added — configuration

- `config/claude/inventory/` — declarative snapshot of 18 connectors, 11 skills and the
  plugin state, with what each is for and whether it can be restored from a file
- `config/claude/settings/` — Claude Code `settings.json` templates for user and project
  scope, with a read-only allowlist and a deny list covering force-push, hard reset and
  credential files
- `config/claude/mcp/` — project `.mcp.json` template for servers the claude.ai connector
  directory does not offer
- `config/claude/recommendations/` — reasoned proposals for 4 plugins, 5 connectors and
  4 skills worth writing, plus what to deliberately skip

### Added — tooling and documentation

- `scripts/validate_skills.py` — front matter, name/directory agreement, description
  length, referenced-file existence, script health, and a committed-secret scan
- `scripts/install_skills.sh` — symlink or copy installation, per-skill or whole-set, with
  a refusal to overwrite anything it did not create
- `docs/` — getting started, repository architecture, skill authoring guide, manual setup
  checklist, workspace profile
- `templates/skill/` — scaffold for the next skill
- CI on four Python versions; issue and pull request templates; `.gitignore`,
  `.gitattributes`, `.editorconfig`

### Notes

- Anthropic's built-in skills are **not** vendored. They are recorded by name in
  `config/claude/inventory/skills.json` so the workspace is described completely, and
  remain enabled per account.
- No credential of any kind is committed. The inventory records which services are
  connected, never how to authenticate to them.
