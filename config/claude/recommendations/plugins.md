# Recommended plugins

None are enabled on the account today. These are the ones from the
`knowledge-work-plugins` marketplace that fit the work in
[`docs/04-workspace-profile.md`](../../../docs/04-workspace-profile.md) — scientific
software engineering, vaccine and epidemiology projects, ML, and academic writing.

**How to install.** claude.ai → Settings → Plugins → browse the marketplace → Install.
In Claude Code, `/plugin` opens the same catalogue. No login beyond the Claude account is
needed for the plugin itself; individual MCP servers a plugin bundles may need their own.

Ordered by value for this account.

---

## 1. `engineering` — install first

**Why.** It is the daily-driver bundle for the work that fills most of these repositories,
and it composes with `repo-audit-fixer` rather than competing with it: the audit skill is
the deep, once-per-milestone pass; these are the small ones you run constantly.

| Skill | Use |
|---|---|
| `engineering:code-review` | A review pass on a diff before pushing |
| `engineering:debug` | Structured debugging of a specific failure |
| `engineering:testing-strategy` | Deciding what to test, at which level |
| `engineering:tech-debt` | Prioritising debt with effort estimates |
| `engineering:architecture` | Architecture decision records |
| `engineering:system-design` | Design work before implementation |
| `engineering:documentation` | Technical documentation |
| `engineering:incident-response` | When something is broken in production |
| `engineering:deploy-checklist` | Pre-deployment verification |
| `engineering:standup` | Progress summaries from recent activity |

**Bundled MCP servers:** github (already available in Claude Code), linear, atlassian,
notion (already connected), slack, datadog, pagerduty, asana, gmail, google-calendar.
Each is optional and separately authenticated — install the plugin, connect only what
you actually use.

---

## 2. `security-guidance` — install second

**Why.** It closes the loop that `repo-audit-fixer` opens. The audit skill finds
vulnerabilities during a deliberate audit; this plugin catches them at the moment code is
written, through hooks that run on every edit and every commit. Prevention beats a later
audit finding, and its coverage (injection, XSS, SSRF, hard-coded secrets, and 25+ other
classes) maps directly onto the `SEC-*` categories in the audit taxonomy.

Note its reach: it installs `PreToolUse`/`PostToolUse`/`Stop` hooks, so it inspects code
as you work. That is the point, and it is worth knowing before you enable it.

---

## 3. `data`

**Why.** Statistical analysis, dataset validation and SQL are recurring work across
`mortality-ami-predictor`, `vax-SPIRAL-CB`, `Hybrid-Modeling` and `climaXtreme`.
`data:validate-data` in particular targets the defect class that does the most damage in
research code: a data-integrity problem that produces a plausible wrong number.

| Skill | Use |
|---|---|
| `data:statistical-analysis` | Descriptive statistics, trends, outliers |
| `data:validate-data` | Data-quality checks before analysis |
| `data:explore-data` | Profiling an unfamiliar dataset |
| `data:sql-queries`, `data:write-query` | Query authoring and optimisation |
| `data:create-viz`, `data:build-dashboard` | Visualisation and dashboards |

Its bundled MCP servers (BigQuery, Databricks, Snowflake, Amplitude) are enterprise
warehouses — skip them unless one is actually in use.

---

## 4. `bio-research`

**Why.** Life-sciences R&D tooling that overlaps the DICEI / Instituto Finlay work. Most
valuable here is `bio-research:nextflow-development` if any pipeline work is on the
horizon, and `scientific-problem-selection` for framing.

Its MCP bundle includes PubMed, bioRxiv, Consensus, Clinical Trials and Open Targets —
**all five are already connected on this account**, so the plugin adds skills rather than
new connections. Benchling, BioRender, ChEMBL, Synapse and Wiley are additional.

---

## Considered and not recommended

| Plugin | Why not |
|---|---|
| `design` | Overlaps the built-in `dataviz` and `canvas-design`, plus the Figma connector already present. Add only if UI work becomes regular. |
| `product-management`, `operations`, `marketing`, `finance`, `customer-support` | Business-function bundles with little overlap with this account's work. `operations:runbook` and `operations:risk-assessment` are the only individually interesting pieces. |
| `cockroachdb`, `unity`, `twilio-developer-kit` | Excellent, but vendor-specific to stacks not in use here. Install if that changes. |
| `brightdata-plugin`, `nimble`, `tavily` | Web scraping and search. `WebSearch`/`WebFetch` already cover the research needs, and these are commercial services requiring their own API keys. |
| `miro`, `bigdata-com`, `searchfit-seo`, `common-room` | Outside this account's work. |

---

## After installing

Record what was actually installed in
[`../inventory/plugins.json`](../inventory/plugins.json) and commit that change. In a
Claude session:

> List my enabled plugins and update `config/claude/inventory/plugins.json` to match.
