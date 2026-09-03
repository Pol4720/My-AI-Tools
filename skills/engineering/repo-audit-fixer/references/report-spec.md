# Audit report specification — Phase 9

The report is the audit's durable artifact. Long after the branch is merged and the conversation is gone, this
is what tells the author — or a colleague, or a regulator, or the author in two years — what was wrong, what
was done, and what remains.

---

## Location and naming — a hard requirement

```
<repo>/Reports/audit-YYYY-MM-DD-HHMM/
├── audit.tex          LaTeX source
├── audit.pdf          compiled output, zero errors and zero warnings
├── findings.json      the machine-readable ledger
├── README.md          one-screen summary for someone who will not open the PDF
└── evidence/          reproductions, before/after outputs, logs, gate transcripts, screenshots
```

- `Reports/` sits at the repository root. **Create it if it does not exist.**
- If the repository already uses a different casing (`reports/`, `REPORTS/`), follow the repository's
  existing convention rather than creating a second directory.
- The folder name uses the audit's **start** timestamp, UTC, minute precision. Optionally append a short slug
  when several audits in a day target different scopes: `audit-2026-09-03-1540-api-surface`.
- **Never overwrite or delete a previous audit folder.** The point of the timestamp is accumulation: a
  project audited three times has three folders, and the diff between them is itself information.
- Add `Reports/` to nothing — it is committed. If the repository's `.gitignore` would exclude it, that is a
  finding, and the report is the first thing to un-ignore.

## Reading the history first

Before writing, open the most recent previous audit in `Reports/`, if one exists:

- Findings previously `open` or `accepted` are your **starting backlog** — carry them forward with their
  original ID and note whether they moved.
- A finding previously `fixed` that has returned is a **regression**, and per `defect-taxonomy.md` it is
  `Critical` regardless of its intrinsic severity — the process failure is the real finding.
- The gate numbers from the previous audit go in this report's trend table.

---

## Language and tone

Write in **the language the user is speaking**. Spanish request → Spanish report. The template supports both.

The tone is a technical audit, not a performance review:

- **Factual.** "The aggregation divides by the row count with no empty guard" — not "unfortunately the code
  is quite fragile here".
- **Attributed to code, not to people.** Never name a contributor as the cause of a defect.
- **Quantified.** Counts, line numbers, versions, before/after numbers. A report of adjectives is unusable.
- **Honest about limits.** A section that says what you could not check is worth more than one that implies
  you checked everything.
- **No congratulation.** Do not open by praising the codebase and do not close by celebrating the fixes. The
  reader wants the findings.

---

## Required structure

The template `assets/audit-report-template.tex` implements this. Sections marked **required** always appear,
even when empty — an empty "Open issues" section that says "none" is information.

### Front matter (required)
Title, repository name and remote, audited commit SHA (before) and delivered commit SHA (after), branch,
audit date and duration, auditor, scope statement, and the environment (OS, language runtime versions, tool
versions). Reproducibility starts here.

### 1 · Executive verdict (required)
**One page maximum.** Written for someone who will read nothing else and may have to decide whether to ship.

- Would this repository have failed in front of its users as it stood? Yes or no, then why.
- Does it now? Yes or no, then what remains.
- The single most serious finding, in two sentences.
- The severity count table, before and after.
- A one-line deployment recommendation: *ready*, *ready with conditions* (name them), or *not ready* (name the
  blockers).

### 2 · Scope and method (required)
What was audited and what was not, explicitly. Which phases ran. Which lenses were applied. Which tools ran
and which were unavailable. How the software was exercised in Phase 3 — this paragraph is what makes the
audit credible, because it shows the findings came from running the thing and not only from reading it.

### 3 · The system as found (required)
A short technical portrait: architecture, languages and line counts, dependencies, entry points, the state of
the test suite and CI at Phase 0. Two or three paragraphs plus the recon table. A reader six months from now
needs this to interpret everything else.

### 4 · Findings (required)
The core. Ordered by severity, then by category. Each finding is a numbered subsection carrying, in this order:

| Field | Content |
|---|---|
| Identifier & title | `F-014 — Empty result set divides by zero in coverage aggregation` |
| Severity · Category · Confidence · State | The four badges |
| Location | File and line for every affected site, not just the first |
| Symptom | What is observably wrong |
| Root cause | The mechanism. **Not the symptom restated.** |
| Impact | Who is affected, under what conditions, and how badly |
| Evidence | The reproduction — a path into `evidence/`, a command, a trace |
| Correction | What was changed, and why this way rather than the alternatives |
| Verification | The regression test, and the proof it fails on the pre-fix code |
| References | CVE, CWE, standard clause, or the documentation URL that settles it |

`accepted` and `open` findings replace *Correction* and *Verification* with **Recommendation** (what should be
done) and **Reason** (why it was not done here). Never omit them — a finding with no disposition is the
failure mode this format exists to prevent.

### 5 · Completeness ledger (required)
The Phase 1 contract ledger, as a table: every documented promise → `honoured` / `repaired` / `withdrawn`,
with evidence. This is the section that answers *"is the software finished?"*, and it is the one most reports
lack.

### 6 · Verification and quality gate (required)
The before/after table for every gate stage, with the real numbers. Explicitly state whether any gate
configuration changed and why. Include the flakiness result, the clean-room build result, and the coverage
delta on changed lines.

### 7 · Open issues and risks (required)
Everything not fixed, each with what is blocking it and what it would take. Plus risks that are not defects:
an unmaintained dependency, a design that will not scale past a stated point, a single point of failure. This
section is the author's to-do list — make it actionable, with an effort estimate on each item.

### 8 · Recommendations (required)
Ordered by value, not by severity. Prevention over repair: the gate that would have caught this class, the
test that should exist, the abstraction that would make the defect family impossible rather than merely
absent. Each recommendation names the defect family it closes.

### Appendices (as applicable)
Full tool output; the exercise matrix from Phase 3 (input → expected → observed → verdict); the SBOM; the
complete diff statistics; the commit list.

---

## Figures

Two charts earn their place; more is decoration.

1. **Severity distribution, before and after** — a grouped bar chart.
2. **Findings by category** — a horizontal bar chart, sorted, showing where the defects concentrated.

Add a third only if the repository has audit history: **findings over time** across the `Reports/` folders.

Load the **dataviz** skill before drawing any of them. Generate them as PDF or PGF so they are vector in the
document, write them into the audit folder, and never hand-place a number into a caption that the chart's
data does not support.

---

## The machine-readable ledger

`findings.json` is the source of truth; `audit.tex` is rendered from it by `scripts/build_report.py`. This
ordering matters: it means the narrative cannot drift from the counts, and it means a future audit can diff
against this one programmatically.

Validate before rendering:

```bash
python3 scripts/findings.py --validate Reports/audit-<ts>/findings.json
python3 scripts/build_report.py --audit-dir Reports/audit-<ts> --lang es
```

`findings.py --validate` refuses a ledger containing a finding with no `state`, a `fixed` finding with no
`verification`, an `accepted` finding with no `reason`, or a `critical` finding at `reported` confidence.
Those refusals are the honest-ledger rule enforced by a program rather than by good intentions.

## Compilation

The PDF must build with **zero errors and zero warnings**. `latexmk -pdf` (or `pdflatex` ×3 for the table of
contents and references). Undefined references, overfull boxes and missing figures are all defects in a
document whose entire subject is defects.

If no LaTeX toolchain is available in the environment: ship `audit.tex`, ship a faithful Markdown rendering
alongside it, and state plainly in `README.md` that the PDF was not compiled here and what command produces
it. Do not ship nothing, and do not claim a PDF exists that does not.

## The folder README

One screen. The verdict, the severity counts before and after, the three findings that mattered most, the
gate delta, and the count of open issues — with a pointer to the PDF for everything else. Written for someone
scrolling the repository on a phone.
