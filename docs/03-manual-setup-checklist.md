# Manual setup checklist

Everything a file cannot do for you.

This is the companion to [`config/claude/`](../config/claude/): that directory records
what the workspace *has*; this one is the ordered list of the steps that require a human
at a browser, because they involve logging into external platforms with credentials that
must never live in a repository.

**Use this when:** setting up a second Claude account, onboarding a colleague onto the same
workspace, or rebuilding after losing access.

**Time:** about 25 minutes for the whole list. Ten if you only do Part 1.

---

## Part 0 — Automatic (no browser needed)

Do this first; it needs nothing but the repository.

```bash
git clone https://github.com/Pol4720/My-AI-Tools.git
cd My-AI-Tools
./scripts/install_skills.sh          # symlinks every skill into ~/.claude/skills/
python3 scripts/validate_skills.py   # confirms all four are healthy

cp config/claude/settings/settings.user.json ~/.claude/settings.json
```

- [ ] Skills installed and validated
- [ ] `~/.claude/settings.json` in place
- [ ] New Claude Code session started (settings load at session start)

Everything below this line needs you.

---

## Part 1 — Essential (do these)

### 1.1 Enable the built-in skills · claude.ai → Settings → Capabilities

No external login. Eight to enable:

- [ ] `skill-creator` — needed to author or edit any skill
- [ ] `pdf` — the paper auditors depend on it for reading reference PDFs
- [ ] `xlsx` — collaborator data arrives this way
- [ ] `docx`
- [ ] `pptx`
- [ ] `canvas-design`
- [ ] `import-memory`
- [ ] `morning`

### 1.2 Upload the owned skills · claude.ai → Settings → Capabilities → Skills

Only if you want them on claude.ai as well as in Claude Code. Zip each directory and
upload:

- [ ] `skills/engineering/repo-audit-fixer`
- [ ] `skills/research/q1-paper-auditor`
- [ ] `skills/research/thesis-auditor-fixer`

### 1.3 Connect the research connectors · claude.ai → Settings → Connectors

**No login required** — connect and they work:

- [ ] PubMed
- [ ] bioRxiv
- [ ] Clinical Trials
- [ ] Open Targets
- [ ] PopHIVE
- [ ] ICD-10 Codes
- [ ] CMS Coverage

### 1.4 Connect the OAuth connectors

Each opens a login window for that platform. **You must have an account on each service.**

| Connector | Log in with | Needed for |
|---|---|---|
| [ ] Hugging Face | HF account | Model and dataset discovery |
| [ ] Notion | Notion workspace | Notes, project tracking |
| [ ] Consensus | Consensus account | Evidence synthesis |
| [ ] Elicit | Elicit account | Systematic reviews |
| [ ] Scholar Gateway | account | Citation verification |
| [ ] Demographic and Health Surveys | DHS account (free registration) | Population health indicators |
| [ ] Figma | Figma account | Design context, diagrams |
| [ ] Canva | Canva account | Figures, presentation material |
| [ ] Cloudflare Developer Platform | Cloudflare account | Workers, D1, R2, KV |

### 1.5 Install the plugins · claude.ai → Settings → Plugins

Marketplace: `knowledge-work-plugins`. Rationale in
[`config/claude/recommendations/plugins.md`](../config/claude/recommendations/plugins.md).

- [ ] `engineering` — code review, debug, testing strategy, tech debt, architecture
- [ ] `security-guidance` — hooks that catch vulnerabilities as code is written
- [ ] `data` — statistical analysis, data validation, SQL
- [ ] `bio-research` — Nextflow, scientific problem selection

> `security-guidance` installs `PreToolUse`/`PostToolUse`/`Stop` hooks, so it inspects code
> as you work. That is what makes it useful — worth knowing before you enable it.

---

## Part 2 — Recommended (as the need arises)

Full reasoning in
[`config/claude/recommendations/connectors.md`](../config/claude/recommendations/connectors.md).

- [ ] **Microsoft 365** — already half-installed on the account but not authenticated.
      Connect it if institutional documents live in SharePoint / OneDrive / Outlook. Highest
      value of anything on this list for DICEI work.
- [ ] **Sentry** — once something is deployed and instrumented. It is the half of
      `repo-audit-fixer` that tells you which findings reached real users.
- [ ] **Linear** — a home for the `open` findings an audit produces. Try Notion first; it
      is already connected and may be enough.
- [ ] **Supabase** — if a project uses it. Gives the audit skill the real schema.
- [ ] **Vercel** — if a project deploys there.
- [ ] **Google Drive** — for collaborator files.
- [ ] **Remove Monte Carlo** — installed, never authenticated, needs a tenant that does
      not exist. Removing it keeps the connector list honest.

---

## Part 3 — Per-machine, per-project

- [ ] `cp config/claude/settings/settings.project.json <project>/.claude/settings.json` in
      each project that needs it, and commit it.
- [ ] `cp config/claude/mcp/mcp.servers.json <project>/.mcp.json` where a local database or
      self-hosted tool is needed — see [`config/claude/mcp/README.md`](../config/claude/mcp/README.md).
- [ ] Export any `${VAR}` referenced by `.mcp.json` in your shell profile. **Never** inline
      a token into the committed file.

---

## Part 4 — Verification

Do not skip this. A half-configured workspace fails quietly.

- [ ] `python3 scripts/validate_skills.py` → 4 skills valid
- [ ] In a fresh Claude session: *"List my enabled skills, plugins and connectors."*
      Compare against [`config/claude/inventory/`](../config/claude/inventory/).
- [ ] Trigger a skill without naming it — e.g. *"audit this repository"* should reach
      `repo-audit-fixer`. If it does not, the description needs work; use `skill-creator`.
- [ ] Update `config/claude/inventory/*.json` to match what you actually installed, set
      `captured_at`, and commit. **The checklist is not finished until the inventory is
      true again.**

---

## What can never be automated, and why

Everything in Parts 1.3 through 2 is an OAuth grant: you authorising Anthropic's
infrastructure to act on your behalf against a third party. That authorisation is designed
to require a human, with credentials, at a browser — no file, script or agent can produce
it, and any tool claiming otherwise would be asking for your password.

This is not a limitation to work around. It is the boundary that makes the rest safe. What
this repository can do — and does — is make the manual part short, ordered, and impossible
to forget a step of.
