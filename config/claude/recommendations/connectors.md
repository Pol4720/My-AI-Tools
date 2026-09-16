# Recommended connectors

Twenty-three connectors are installed (see
[`../inventory/connectors.json`](../inventory/connectors.json)), and the research side of
the workspace is genuinely well covered — PubMed, bioRxiv, Consensus, Elicit, Scholar
Gateway, Clinical Trials, Open Targets, ChEMBL, BioRender, PopHIVE, DHS and ICD-10 is a
strong set for vaccine, epidemiology and drug-discovery-adjacent work.

The gaps are on the **engineering operations** side. These are the ones worth adding, with
the reason and the honest cost.

**How to add one.** claude.ai → Settings → Connectors → Browse → Connect. Every connector
below needs an interactive OAuth login that only the account owner can perform — see
[`docs/03-manual-setup-checklist.md`](../../../docs/03-manual-setup-checklist.md).

---

## Recently added — finish authorising these

Four connectors were added to the account since the last inventory snapshot. Two came
through clean; two stalled mid-authorisation and need a second pass.

| Connector | Status | Action |
|---|---|---|
| **ChEMBL** | connected, no auth needed | Nothing — ready to use alongside Open Targets for target–compound work |
| **BioRender** | connected | Nothing — ready to use for publication and presentation figures |
| **Owkin** | `needs_reconnect` | Re-authorise at claude.ai → Settings → Connectors. The OAuth grant lapsed after the initial connection |
| **Synapse.org** | `needs_reconnect` | Same — re-authorise; the grant lapsed after the initial connection |

These four are exactly the bio-research connector set this file previously recommended
bundling through the `bio-research` plugin — they are now connected directly, which makes
that plugin's own connector story redundant for this account (its skills are still worth
having; see [`skills.md`](skills.md)).

One existing connector also needs re-authorising, unrelated to the additions above:

| Connector | Status | Action |
|---|---|---|
| **Cloudflare Developer Platform** | `needs_reconnect` | Was connected as of the last snapshot; the grant has since lapsed. Re-authorise if any project still deploys there |

And the account's own **GitHub** connector is authenticated but toggled off for chat use
(`connected_not_enabled_in_chat`) — this is separate from the Claude Code GitHub MCP server
this repository's git operations already use, so nothing here needs fixing unless you
specifically want GitHub tools available inside ordinary claude.ai conversations too.

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

Two connectors still sit on the account without a working authentication — see the
recently-added table above for the two that lapsed after working once:

| Connector | Decision |
|---|---|
| **Microsoft 365** | Connect **if** DICEI / Instituto Finlay work lives in SharePoint, OneDrive or Outlook. It is the single highest-value connection for institutional work, and it is already half-installed. |
| **Monte Carlo** | A connection attempt was started (`connect_incomplete`) and not finished. Either complete it if a Monte Carlo tenant exists, or remove the connector — a half-configured entry is worse than no entry, because it looks connected until something tries to use it. |

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
