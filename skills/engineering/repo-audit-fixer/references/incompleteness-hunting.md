# Hunting missing implementations — Phase 5

Bugs are what the software does wrong. **Incompleteness is what it never does at all.** It is the defect
class that most reliably survives normal review, because there is no failing test for code that does not
exist, no stack trace for a branch that was never written, and no lint warning for a promise nobody kept.

This is also the class the user cares about most when they say *"completador"* — finish what was started.

---

## The five sources of incompleteness

### 1. Abandoned work — the markers

Start here because it is cheap. Run:

```bash
python3 scripts/incompleteness_scan.py <repo> --json
```

It finds `TODO` / `FIXME` / `HACK` / `XXX` / `WIP` / `TEMP` / `for now` / `later`, `NotImplementedError`,
`todo!()`, `unimplemented!()`, `panic("not implemented")`, `throw new UnsupportedOperationException`,
`raise NotImplemented`, bodies that are only `pass` / `...` / `return null` / `return None` / `{}`, empty
`catch` blocks, functions whose body is a single log statement, and large commented-out blocks.

Then do the part the script cannot: **triage every hit.**

- Is there a *caller* that will reach it? A stub nobody calls is `Advisory`. A stub behind a documented
  feature is `Major`. A stub behind an authorisation check is `Critical`.
- Does the `TODO` describe a correctness problem or a nicety? "TODO: handle the timezone" is a bug report the
  author filed against themselves.
- How old is it? `git log -S` on the line tells you. A three-year-old `TODO: temporary` is permanent, and
  should be either implemented or deleted with the workaround documented.

Do not "fix" markers by deleting them. Implement, or convert into a tracked issue with the consequence stated.

### 2. Documentation minus code — the broken promises

This is the highest-yield source, and the reason Phase 1 builds the contract ledger.

Walk the ledger. For every promise, find the code that keeps it:

| Promise | Where it hides | The classic failure |
|---|---|---|
| A documented CLI flag | argument parser | parsed into a variable nothing reads |
| A documented config key | config loader | never read, or read and defaulted over |
| A documented API field | serializer / schema | always returns `null`, `[]` or a constant |
| A documented environment variable | env access | read but never used, or used only in one of two code paths |
| A documented error behaviour | error handling | the error is raised but the documented recovery does not happen |
| A README feature | anywhere | implemented for one input type and not the others |
| An OpenAPI operation | router | declared in the spec, no handler registered |
| A "supported" format/platform | parser / build | one branch of a conditional was never written |

Practical method: grep for the identifier from the documentation across the whole tree, then ask *is it read,
and does anything depend on what was read?* An identifier that appears exactly once — at its definition — is
a broken promise.

### 3. Code minus documentation — the undocumented requirements

The reverse direction, and it is what breaks deployments rather than users.

- Every environment variable the code reads: is it in `.env.example`, the README, and the deployment manifest?
  A required variable with no default and no documentation is a `Major` finding — the software cannot be
  deployed by anyone who did not write it.
- Every system dependency: a binary invoked via subprocess, a native library, a font, a locale, a certificate
  bundle, a minimum runtime version.
- Every implicit precondition: a directory that must exist, a migration that must be run first, a seed script,
  an external service that must be reachable at startup.
- Every side effect a caller would not expect: a function that also writes a file, mutates its argument, or
  sends a request.

### 4. Unhandled branches of the domain — the incomplete case analysis

Where the code enumerates something, check that the enumeration is complete and that the default is deliberate.

- **Every `switch` / `match` / `if-elif` chain over an enum, a union, a status, a type tag or a country/
  language code.** Is every variant handled? Is there a `default`, and does it fail loudly or fall through
  silently? *Silent fallthrough on an unrecognised variant is a Critical finding* — it is the shape that
  produces wrong answers with no error. In languages with exhaustiveness checking (Rust `match`, TypeScript
  discriminated unions with a `never` assertion, Java sealed interfaces), turn the check on.
- **Every `if` with no `else`.** Was the else case considered? Add a comment or add the branch.
- **Every error the callee can produce.** For each function, enumerate what it can raise or return as an
  error; then check that every caller handles each one. Languages with checked errors (Go's `err`, Rust's
  `Result`) make this mechanical: search for discarded errors (`_ =`, `.unwrap()`, `let _ =`).
- **Every state machine.** Draw it. Are all transitions implemented? What happens on an event in a state that
  does not expect it? Is there a terminal state that can be entered but not exited?
- **Every validation.** Is each field validated for presence, type, range, format *and* cross-field
  consistency? Partial validation is the usual finding — presence checked, range not.

### 5. The unfinished edges — patterns that are almost always half-built

A checklist of the shapes that are routinely started and rarely finished. Check each one that applies:

- **Pagination** — implemented for page one; no cursor stability; no total count; the last page is wrong;
  the client loop has no termination condition.
- **Retry** — no ceiling, no backoff, no jitter; retries on non-retryable errors (a 400 will never succeed);
  does not retry on the one error that is retryable.
- **Cleanup** — runs on the success path only; no `finally` / `defer` / `with`; temp files, locks, sockets,
  subprocesses and transactions leak on the error path.
- **Cancellation & shutdown** — no signal handler; in-flight work dropped; no draining; a background thread
  that never stops.
- **Migrations** — `up` written, `down` empty or wrong; not idempotent; not tested against real data; a
  backfill for existing rows was never written.
- **Validation symmetry** — enforced in the UI but not in the API; in the API but not in the database.
- **Feature flags** — one branch implemented; the off-path never tested; the flag never removed.
- **Internationalisation** — one language of strings; a hard-coded date/number format; a concatenated
  sentence that cannot be translated.
- **Permissions** — the check exists on the list endpoint and not the detail endpoint; on read and not write;
  on the API and not the background job.
- **Idempotency** — the retry story assumes it, the handler does not provide it.
- **Bulk operations** — the single-item path is complete, the batch path is a loop with no transaction and no
  partial-failure semantics.
- **Search & filtering** — one filter implemented, the rest accepted and ignored; combinations untested.
- **Export/import round trip** — export works, import of the export does not.
- **Empty, loading and error states** in a UI — the success state is built, the other three are not.
- **Timezones and units** — handled at the boundary in one direction only.

### 6. Wired but dead — the code that is never reached

The mirror image, and just as much a defect because it makes the codebase lie about itself:

- Routes registered but unreachable (shadowed by an earlier route, behind a flag that is always false).
- Components imported and never rendered; exported functions with no importer.
- Queue consumers with no publisher; publishers with no consumer.
- Configuration read into a variable nothing reads.
- Database columns and tables nothing writes or reads.
- Entire files no build includes.

Coverage data from the Phase 3 exercise run is the fastest way to find these: code that never executed while
you were driving every documented path is either dead or untested, and both are findings.

---

## Deciding what to complete

Not every gap should be filled by you. Sort each one:

| Situation | Action |
|---|---|
| The behaviour is determined — by the docs, by the contract, by symmetry with a sibling implementation, or by an obvious correct answer | **Implement it.** No question needed. |
| The gap makes something unsafe or silently wrong | **Implement the safe behaviour** (fail loudly) even if the full feature needs a decision, and record the remaining work as `open`. |
| The behaviour is a product decision — what the pricing rule is, which of two reasonable semantics is wanted, whether a feature should exist | **Ask.** Present the options and the trade-off. Do not guess a business rule. |
| The gap is real but out of scope for the audit's brief | Record as `open` with a concrete recommendation and an effort estimate. |

When you implement a gap, it gets the same treatment as a fix: a test that would fail without it, docs
updated, and a ledger entry with `category: "INCOMPL"`.

---

## The completeness sweep

Before leaving Phase 5, run one final pass and answer these out loud:

1. Does every documented feature work end to end, driven from the outside? (You ran them in Phase 3 — check
   your notes.)
2. Does every code path that can fail, fail visibly?
3. Is there any input for which the software does nothing and says nothing?
4. Is there any file, function, route, column or config key in the repository that nothing uses?
5. If I deleted every `TODO` comment, would the repository still tell the truth about itself?

Question 3 is the one to sit with. Silence is the worst failure mode, and it is what incompleteness sounds like.
