# Recommended connectors

Eighteen connectors are already installed (see
[`../inventory/connectors.json`](../inventory/connectors.json)), and the research side of
the workspace is genuinely well covered — PubMed, bioRxiv, Consensus, Elicit, Scholar
Gateway, Clinical Trials, Open Targets, PopHIVE, DHS and ICD-10 is a strong set for
vaccine and epidemiology work.

The gaps are on the **engineering operations** side. These are the ones worth adding, with
the reason and the honest cost.

**How to add one.** claude.ai → Settings → Connectors → Browse → Connect. Every connector
below needs an interactive OAuth login that only the account owner can perform — see
[`docs/03-manual-setup-checklist.md`](../../../docs/03-manual-setup-checklist.md).

---

## Worth adding

### Sentry — error monitoring
**Why.** It is the missing half of `repo-audit-fixer`. The audit finds defects before
deployment; Sentry tells you which ones reached users, with the stack trace and the
frequency. A finding backed by "this fired 340 times last week" is a different
conversation from one backed by a code reading.
**Cost.** Free tier is generous. Needs a Sentry account and the SDK wired into the app.
**Prerequisite.** Only useful once something is actually deployed and instrumented.

### Linear — issue tracking
**Why.** The audit pipeline produces open findings that need to live somewhere after the
report is written. Today they live in a PDF, which nobody reopens. With Linear connected,
`open` findings become tracked issues in the same session that produces them, and the next
audit can check whether they moved.
**Cost.** Free for small teams. Needs a Linear workspace.
**Alternative.** The **Notion** connector is already installed and can carry the same
backlog with less ceremony — try that first before adding another tool.

### Supabase — Postgres, auth and storage
**Why.** Several projects here are database-backed. A direct connection lets Claude read
the real schema, which is what makes the `DATA` lens in the audit skill (schema drift,
missing constraints, missing indexes, migration correctness) work on evidence rather than
on the ORM models alone.
**Cost.** Free tier. Only relevant if Supabase is actually the database.
**For plain Postgres**, no first-party connector exists in the directory — use a
self-hosted Postgres MCP server as a Claude Code project server instead; see
[`../mcp/README.md`](../mcp/README.md).

### Vercel — deployments
**Why.** Build and deployment logs in-session. Relevant if any of the web projects deploy
there.
**Cost.** Free tier.

### Google Drive
**Why.** Institutional documents, datasets and protocols shared by collaborators arrive
this way far more often than through GitHub.
**Cost.** Free. Grants Claude read access to your Drive — scope it deliberately.

---

## Already installed, worth actually connecting

Two connectors sit on the account without being authenticated:

| Connector | Decision |
|---|---|
| **Microsoft 365** | Connect **if** DICEI / Instituto Finlay work lives in SharePoint, OneDrive or Outlook. It is the single highest-value connection for institutional work, and it is already half-installed. |
| **Monte Carlo** | Leave it. It requires a Monte Carlo tenant, and there is no sign of one. Remove it from the account to keep the list honest. |

---

## Not available in the directory

Things that would genuinely help but that no first-party connector covers today. Each can
still be added as a **Claude Code project MCP server** — see [`../mcp/README.md`](../mcp/README.md).

| Want | Status | What to do instead |
|---|---|---|
| **Zotero** (reference manager) | No directory connector | Community MCP server, or export BibTeX and let the paper auditors read the `.bib` |
| **Overleaf** | No connector, no API | Keep LaTeX in git; both paper skills already work on `.tex` files directly |
| **SonarQube / Snyk** | No directory connector | The audit skill's `tooling-catalog.md` runs the open-source equivalents (`semgrep`, `osv-scanner`, `trivy`) locally |
| **Local Postgres / MySQL** | No directory connector | Project MCP server with a read-only role |
| **REDCap** | No connector | Export and analyse; do not connect a clinical data capture system to an assistant without an institutional review |
| **Weights & Biases** | No directory connector | Community MCP server if experiment tracking becomes central |

---

## Before you connect anything

A connector grants a running session read — and often write — access to that service under
your identity. Two rules worth holding to:

1. **Connect the minimum that makes the work possible.** Every connector is standing
   access, not a one-off grant.
2. **Never connect a system holding identifiable clinical or personal data** without the
   institutional review that system's policy requires. For the DICEI / Instituto Finlay
   projects this is not a formality — de-identified exports are the right interface, and
   the audit skill treats identifiers reaching a log or an export as a Critical finding
   for exactly this reason.
