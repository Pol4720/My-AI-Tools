# Defect taxonomy & severity rubric — Phase 4

A shared vocabulary so that findings are comparable across audits, across projects, and across time. Every
finding in `findings.json` carries a `category` from this file and a `severity` from the rubric below.

---

## Severity rubric

Severity answers one question: **what happens if this ships unfixed?** It is *not* a measure of how hard the
fix is, how clever the finding is, or how annoyed you are.

### Critical

The software loses or corrupts data, can be compromised, produces silently wrong results, or does not
perform a documented core function at all.

Decisive markers — any one of these makes it Critical:

- Data is destroyed, corrupted, or written where it cannot be recovered.
- An attacker can read or modify data belonging to someone else, execute code, or escalate privilege.
- A credential, key or token is exposed in the repository or its history.
- The software returns a **wrong answer that looks like a right answer** — no error, no warning, no log.
- A documented core feature does not work at all.
- Money, dosage, identity, safety or regulatory-reportable values are computed incorrectly.

The silent-wrong-answer case deserves emphasis: it outranks a crash. A crash is discovered. A wrong number
propagates into a decision, a paper, a report, or a patient record and is discovered much later, if ever.

### Major

A real user, on a path they will actually take, is blocked, misled, or exposed to a failure the software
should have handled.

- An unhandled failure mode in a path that *will* be exercised (network down, empty input, concurrent request).
- A documented feature that is partially implemented or works only in the happy case.
- A missing authorisation or validation check whose exploitation requires a precondition.
- A defect that produces a confusing error rather than a wrong result.
- A performance characteristic that makes the software unusable at a size that is reachable in practice.
- A test suite that provides false assurance for a critical path (a false green).

### Minor

A real defect, but with a narrow blast radius, a workaround, or a low-probability trigger.

- An edge case that only occurs on input a user is unlikely to produce.
- A missing test for a real branch that is otherwise correct.
- An inconsistency in error shape, naming or behaviour between two similar code paths.
- A contract honoured in code but undocumented.
- A log line missing where it would help diagnosis.

### Advisory

Nothing is broken today. Something makes the software riskier, harder to change, or more expensive to
operate tomorrow.

- Structural debt: duplication, a god module, a leaky abstraction.
- Dependency drift, an unmaintained package, a deprecated API still supported.
- Missing observability, missing CI stage, missing documentation for a non-public detail.
- A performance issue at a size that is not currently reachable.

**Advisory findings are still findings.** They go in the ledger with a recommendation. They are the only
class you may leave `accepted` without a blocker — and the reason must still be written down.

### The escalation rules

- **A defect family escalates.** One `Minor` instance of a pattern, found in eleven modules, is `Major`.
- **Reachability escalates.** A vulnerability in a dependency is `Advisory` if the vulnerable code path is
  unreachable from this repository, and `Critical` if it sits behind a public endpoint. *Check reachability
  before assigning — do not just copy the CVE's own CVSS score.*
- **A regression escalates.** A defect previously marked `fixed` in an earlier audit in `Reports/` that has
  come back is `Critical` regardless of its intrinsic severity, because the process that let it back is the
  real finding.
- **Silence escalates.** Any defect that fails without producing an error, a log or a non-zero exit code
  moves up one level.

---

## Category codes

Use these as the `category` field. They map onto the lenses in `audit-lenses.md`.

| Code | Category | Typical CWE / OWASP |
|---|---|---|
| `CORR` | Correctness — wrong computation, wrong logic, wrong boundary | CWE-682, CWE-193, CWE-369 |
| `SEC-INJ` | Injection — SQL, command, template, LDAP, XPath, log, header | CWE-89, CWE-78, CWE-1336 · OWASP A03 |
| `SEC-AUTH` | Authentication & authorisation, IDOR, session, CSRF | CWE-862, CWE-639, CWE-352 · OWASP A01, A07 |
| `SEC-CRYPT` | Cryptography, hashing, randomness, TLS verification | CWE-327, CWE-330, CWE-295 · OWASP A02 |
| `SEC-SECRET` | Secrets in source, config, history or logs | CWE-798, CWE-532 |
| `SEC-XSS` | Cross-site scripting and unsafe rendering | CWE-79 · OWASP A03 |
| `SEC-SSRF` | SSRF, path traversal, unsafe file access | CWE-918, CWE-22 · OWASP A10 |
| `SEC-DESER` | Unsafe deserialisation, XXE, archive extraction | CWE-502, CWE-611 |
| `SEC-CONF` | Insecure defaults, debug mode, permissive CORS, missing headers | CWE-16 · OWASP A05 |
| `SEC-DOS` | Unbounded resource consumption, ReDoS, no rate limiting | CWE-400, CWE-1333 |
| `RESIL` | Error handling, timeouts, retries, cleanup, graceful degradation | CWE-703, CWE-772 |
| `DATA` | Persistence, transactions, constraints, migrations, cache coherence | CWE-362 |
| `CONC` | Concurrency, races, deadlocks, idempotency, time handling | CWE-362, CWE-367 |
| `CONTRACT` | API/type/schema contract violations, compatibility breaks | CWE-1059 |
| `INCOMPL` | Missing implementation — stub, unhandled branch, documented-but-absent | CWE-1071 |
| `TEST` | Missing, false, fragile or misleading tests | — |
| `BUILD` | Build reproducibility, dependencies, lockfiles, containers, CI | CWE-1104 · OWASP A06 |
| `OBS` | Logging, metrics, tracing, diagnosability | CWE-778 |
| `PERF` | Algorithmic complexity, N+1, memory, resource exhaustion | CWE-407 |
| `MAINT` | Structure, duplication, dead code, coupling, readability | — |
| `DOC` | Documentation wrong, missing, or contradicted by the code | — |
| `UX` | Usability, error messaging, destructive actions, accessibility (WCAG) | — |
| `LICENSE` | Licence incompatibility, missing attribution, missing licence file | — |
| `PRIV` | Personal data handled without basis, retained, logged or exported | — |

`PRIV` matters disproportionately in health, clinical and epidemiological software: personal or clinical
identifiers in logs, in fixtures, in test data, in error payloads, or exported without de-identification are
`Critical`, not `Minor`.

---

## Finding states

Every finding ends in exactly one of these. This is the honest-ledger rule made concrete.

| State | Meaning | Requires |
|---|---|---|
| `fixed` | The defect is gone and you demonstrated it | Evidence before and after; a regression test that fails on the old code |
| `mitigated` | The defect remains but cannot be triggered, or its impact is bounded | What the mitigation is, and what would defeat it |
| `accepted` | Deliberately not fixed | An explicit reason: out of scope, requires a product decision, cost exceeds risk. Only legitimate for `Advisory`, or when the user decided |
| `open` | Should be fixed and is not | What is blocking: missing access, missing information, needs the owner's decision, needs resources unavailable here |

Two states that do **not** exist and must never be invented: "probably fine" and "fixed (untested)".

---

## Confidence

Independent of severity. Record it.

| Confidence | Meaning |
|---|---|
| `verified` | Reproduced, or traced line by line through the source with the data flow written down |
| `inferred` | Strong reading of the code, but not executed — a race you could not schedule, a production-only path |
| `reported` | Came from a tool or a subagent, checked for plausibility, not independently reproduced |

A `Critical` finding at `reported` confidence is not yet a `Critical` finding. Raise its confidence or lower
its severity — never ship the combination.

---

## Writing a finding

Each entry in `findings.json` carries these. Terse is fine; vague is not.

```json
{
  "id": "F-014",
  "title": "Empty result set divides by zero in coverage aggregation",
  "category": "CORR",
  "severity": "critical",
  "confidence": "verified",
  "state": "fixed",
  "location": ["src/analytics/coverage.py:88", "src/analytics/uptake.py:142"],
  "symptom": "GET /coverage returns 500 when the cohort filter matches no records.",
  "root_cause": "Aggregators compute sum(values)/len(values) with no empty guard. The same shape appears in four aggregators built from the same original copy-paste.",
  "impact": "Any dashboard query for a cohort with no data fails. Two of the four sites return 0.0 instead of erroring, which is a silently wrong answer rather than a crash.",
  "evidence": "evidence/F-014-repro.sh — reproduces the 500 and the incorrect 0.0",
  "fix": "Introduced `safe_mean` returning None for the empty case; all four call sites migrated; API contract updated to return null with an explicit `insufficient_data` flag.",
  "verification": "tests/analytics/test_empty_cohort.py — fails on 8f21ac3, passes on HEAD",
  "references": ["https://cwe.mitre.org/data/definitions/369.html"]
}
```

The two fields that make a report worth reading are `root_cause` and `impact`. A finding that reports only
the symptom leaves the author to do the analysis you were meant to do.
