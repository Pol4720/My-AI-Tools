# Workspace profile

Who this workspace is for and what it is optimised around. Every design decision in this
repository — which skills exist, which connectors matter, which defect categories are
escalated to Critical — follows from what is written here. Read it before proposing a
change to any of them.

---

## The owner

**Richard Matos** — [@Pol4720](https://github.com/Pol4720) · Computer Scientist ·
[CV](https://pol4720.github.io/CV/)

Work sits across three areas that rarely share a toolchain, which is exactly why a
deliberate workspace is worth building:

1. **Scientific software engineering** — building the systems that produce research
   results, not only analysing the results.
2. **Vaccine safety, epidemiology and clinical research** — with
   [DICEI, Instituto Finlay de Vacunas](https://github.com/DICEI-Instituto-Finlay-de-Vacunas).
3. **Academic writing and publication** — LaTeX theses and Q1-target papers.

Working languages: **Spanish and English**. Deliverables are frequently bilingual, and
parity between language versions is a real requirement, not a nicety — both paper skills
treat divergence between versions as a defect.

## The project landscape

Drawn from the account's repositories, and the reason the tooling is shaped as it is.

| Area | Representative repositories | What the tooling must handle |
|---|---|---|
| **Health & epidemiology** | `esavi-report`, `vax-SPIRAL-CB`, `dicei-sgec`, `regulatory-documentation`, `Simmunity` | Personal and clinical data, regulatory expectations, audit trails, de-identification on **every** export path |
| **ML & prediction** | `mortality-ami-predictor`, `Hybrid-Modeling`, `ML_tool`, `BCW-Project` | Data leakage, reproducibility, honest metrics, seeds, split integrity |
| **Data & simulation** | `climaXtreme`, `Discrete-Event-Simulation-Project`, `Clinical-Trial-DB-Design` | Numerical correctness, schema design, scale |
| **Systems & compilers** | `HULK-Compiler-RS`, `DistriSearch`, `Microprocesador-32-bits`, `FTP-Final-Project-` | Memory safety, concurrency, protocol correctness, parser robustness |
| **Applications** | `smart-travel-agent`, `tour-guide-cuba`, `logistic_app`, `LSC`, `FinlAI`, `AuditSoft`, `IATools` | Web and API surfaces, auth, deployment |
| **Academic** | Theses and papers in LaTeX | Zero-warning builds, citation integrity, cross-language parity |

Polyglot by necessity: **Python, TypeScript/JavaScript, Rust, C#, SQL, LaTeX**, with
Docker and CI around them. This is why `repo-audit-fixer` carries per-language and
per-stack playbooks instead of assuming one ecosystem.

## What the workspace optimises for

### 1. Nothing ships broken

The stated motivation for `repo-audit-fixer` was plain: *deploying software and having
defects found afterwards is embarrassing.* So the audit skill is built around finding them
first, and around a rule that a green gate obtained by weakening the gate is worse than a
red one.

### 2. Finished, not merely working

Incompleteness — the documented flag nothing reads, the branch that was never written, the
error path with no handler — survives normal review because there is no failing test for
code that does not exist. Phase 5 of the audit skill exists entirely for this class, and
it is the phase most likely to surprise.

### 3. Correctness above all, because the domain demands it

In vaccine-safety and clinical-prediction software, a **silently wrong number** outranks a
crash. A crash gets noticed; a wrong number reaches a report, a paper, or a decision. The
defect taxonomy escalates silent failure by one severity level for exactly this reason,
and treats personal or clinical identifiers reaching a log, a fixture or an export as
`Critical` rather than `Minor`.

### 4. Evidence, not assertion

Both the paper auditors and the repository auditor share one discipline: every claim traces
to something checkable — a number to its source, a fix to a test that fails without it.
"Probably fine" is not a state any ledger in this workspace accepts.

### 5. Written down, so it survives

An audit that lives in a chat log is gone next week. Audit reports go into
`Reports/audit-<timestamp>/`, committed, accumulating — so a defect that returns is
recognisable as a **regression** rather than rediscovered as news.

## Why these particular skills

| Skill | Exists because |
|---|---|
| `repo-audit-fixer` | Generic code review finds style. Nothing generic hunts missing implementations, runs the software adversarially, and proves each fix. |
| `q1-paper-auditor` | A referee who only complains does not help; the skill both finds and fixes, and verifies every number against the data and the code. |
| `thesis-auditor-fixer` | The same standard for a CS/SE thesis, where LaTeX and citation integrity carry as much weight as the argument. |

The common thread: **each was written because a generic tool did not encode the standard
being applied.** That is the test for whether the next one is worth writing — see
[`config/claude/recommendations/skills.md`](../config/claude/recommendations/skills.md) for
four candidates.

## Conventions this workspace assumes

- **`Reports/`** at a repository root holds audit output, one timestamped folder per audit,
  never overwritten, always committed.
- **LaTeX** is the format for anything formal — audit reports included.
- **Spanish or English**, following whatever language the conversation is in.
- **Atomic commits** with a message stating the defect, the cause and the fix.
- **Sole authorship: Pol4720.** Version control on these repositories stays in the names of
  their human contributors — see [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
