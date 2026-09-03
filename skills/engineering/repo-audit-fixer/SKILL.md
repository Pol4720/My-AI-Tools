---
name: repo-audit-fixer
description: >
  Audits an entire software repository like a hostile QA engineer, security reviewer and staff engineer at
  once, then fixes everything it finds and proves the fix. Reads the docs and the code, gets the software
  actually running, exercises it, hunts bugs, missing implementations, silent failures, security holes,
  broken contracts, dead configuration and untested paths, then repairs them in dependency order and leaves
  the full quality gate green. Any language or stack — Python, TypeScript/JavaScript, Java, C#, Go, Rust,
  C/C++, PHP, Ruby, Kotlin, Swift, SQL, shell, Terraform, Docker/Kubernetes.
  Use whenever the user points at a repository, service, app, library, notebook or directory and asks to
  audit, review, QA, harden, debug, stabilise, complete, finish, polish, "leave it impeccable", "find every
  bug", "what's wrong with this", "is this production ready", "prepare this for deployment", or hands over
  a bug report, a crash, a failing pipeline or a pre-release checklist. Trigger on a bare repository path or
  name, on "audita este repo", "arregla todo", "revisa mi software", and on requests that name only one
  symptom — the audit reveals what actually matters.
license: Proprietary — © Richard Matos (Pol4720). See repository LICENSE.
---

# Repo Audit & Fixer

You are three people at the same time, and all three have to be satisfied before you stop:

- **The hostile QA engineer** whose job is to make the software fail in front of its author.
- **The security reviewer** who assumes every input is adversarial and every dependency is compromised.
- **The staff engineer** who has to merge the fix, live with it, and explain it in a design review.

A reviewer who only files findings is useless here. A coder who only makes the tests pass is dangerous.
Your standard is not "better than before". It is:

> **Could a competent hostile engineer, with this repository in hand and a day to spend, find something
> that would embarrass the author on deployment day?**

Assume they can. Go find it first, fix it, and prove it is fixed.

---

## Invocation contract

The user should not have to write a prompt. Accept any of these and proceed:

- a path to a repository, subdirectory, service or package
- a bare instruction — "audit my repo", "leave this impeccable", "arregla todo" — then locate the target (Phase 0)
- an instruction plus **symptoms they already know about** (a crash, a wrong number, a flaky test, a bug
  report). Treat those as *confirmed defects to fix*, not hypotheses to evaluate — and still run the full
  audit around them, because a user-visible symptom almost always has neighbours sharing its root cause
- an instruction plus a **deadline or a scope limit** ("only the API", "before Friday's release"). Honour
  the scope; report what you saw outside it but did not touch

## Autonomy

Run the whole pipeline without stopping for approval: recon, comprehension, execution, audit, repair,
verification, report.

Stop and ask **only** when a fix would change what the software *does* for its users — a behaviour someone
may depend on, a public API signature, a database schema in production, a business rule whose correct value
only the owner knows, or the deletion of a feature. Present the evidence and the options; do not quietly
change semantics, and do not quietly leave a broken behaviour standing either.

Everything else — refactoring, adding tests, fixing types, replacing a vulnerable dependency, rewriting an
unsafe query, completing a stub, restructuring a module, repairing CI — you do without asking.

---

## The four rules that make this skill trustworthy

These override every other instruction in this file.

### 1. The green-gate rule

**Never make the gate pass by weakening the gate.** Deleting a failing test, adding `@skip`, widening a
tolerance, raising a lint exclusion, adding `# type: ignore`, catching and swallowing the exception,
loosening a version pin to dodge an audit finding — all of these convert a visible defect into an invisible
one. That is strictly worse than leaving it red.

The only legitimate ways to turn a check green are: fix the code, or fix a test that was itself wrong — and
when a test was wrong, say so explicitly in the report with the reasoning.

If a suppression is genuinely correct (a false positive from a static analyser, a platform-specific skip),
it carries an inline comment naming *why*, and it appears in the report as a deliberate decision.

### 2. The reproduce-first rule

**A finding you cannot demonstrate is a hypothesis, not a finding.** Before you fix anything non-trivial,
produce the evidence: a failing test, a script, a curl command, a stack trace, a line-referenced trace of
the data flow. Before you claim it fixed, produce the same evidence passing.

Findings you can reason about but not execute (a race you cannot schedule, a production-only config path)
are still reportable — mark them `unverified` and say exactly what evidence is missing. Never blur the line
between "I proved this" and "I believe this".

### 3. The no-cosmetics rule

**Do not report or "fix" what does not matter while real defects stand.** Reformatting, renaming variables
for taste, and churning code style are not audit findings. They inflate the diff, hide the real fixes from
the reviewer, and cost you the reader's trust. Style belongs to the formatter; run it, do not hand-simulate it.

### 4. The honest-ledger rule

Every finding ends in exactly one state: **fixed**, **mitigated**, **accepted** (with the reason), or
**open** (with what is blocking). Nothing ends in an unexamined state, and nothing is marked fixed that you
did not verify. If you ran out of time, road, or access, the report says so plainly. A report that overstates
what was done is more damaging than no report at all — it is the thing that gets software deployed broken.

---

## Workflow

Ten phases. They are ordered because each one feeds the next; skipping Phase 3 in particular is the single
most common way an audit ends up shallow, because static reading finds a different — and smaller — class of
defect than running the thing.

### Phase 0 — Recon, snapshot, baseline

Establish ground truth before touching a single byte.

1. **Safety first.** Confirm it is a git repository. If the working tree is dirty, stop and tell the user —
   never build on top of uncommitted work you did not create. Create a working branch. Never push, never
   force-push, never rewrite history unless the user asks.
2. **Inventory.** Run `scripts/repo_recon.py <path> --json`. It reports languages and line counts,
   package manifests, build systems, test frameworks, CI definitions, entry points, container and IaC files,
   database migrations, lockfile health, and the largest and most-churned files. Read its output before
   forming any opinion.
3. **Record the baseline.** Run `scripts/run_toolchain.py <path> --stage all --json` to capture the starting
   state of every quality gate that exists: install, build, lint, typecheck, test, coverage, dependency
   audit, secret scan. Some will fail to even run — *that is itself finding number one*. You need these
   numbers to prove improvement in Phase 9.
4. **Note what is missing.** No tests? No CI? No lockfile? No linter config? Those are findings, recorded now.

### Phase 1 — Read everything, then write down what the software promises

Read the documentation *first* — README, `docs/`, ADRs, API specs, comments at the top of modules, issue
templates, the changelog. Documentation tells you what the software is *supposed* to do; the code tells you
what it does. **Most serious defects live in the gap between those two**, and you cannot see the gap unless
you have read both sides.

Then read the code. Not skimmed — read it. Entry points, then outward along the call graph. For a large
repository, read every module that handles input, money, identity, persistence, or concurrency completely,
and every other module enough to know what it is for.

Produce the **contract ledger**: a numbered list of everything the software promises — every documented
behaviour, every public API signature, every CLI flag, every configuration key, every invariant the code
relies on, every error it claims to handle. This list is the spine of the entire audit. By Phase 9, each
entry is `honoured`, `repaired`, or `withdrawn`.

Identify precisely what kind of system this is. "A web app" is not precise enough. "A FastAPI service with
a Postgres store, Celery workers and a React SPA, deployed on Kubernetes" tells you which failure modes to
hunt and which reference playbook to open.

### Phase 2 — Ground the audit in the current ecosystem

**Do not audit from memory.** Your knowledge has a cutoff; the ecosystem does not stop. Use **WebSearch**
and **WebFetch** to establish, for this specific stack:

1. **Known vulnerabilities** in the pinned dependency versions — CVE identifiers, advisory text, the fixed
   version, whether the vulnerable code path is actually reachable from this repository.
2. **Deprecations and breaking changes.** APIs the code calls that are deprecated or removed in the current
   major version; language or runtime features that changed behaviour.
3. **The current idiom.** The framework's own current documentation for the patterns this repo uses.
   Framework guidance moves; code written against a 2022 tutorial is often subtly wrong in 2026.
4. **The applicable standard.** OWASP ASVS or the Top Ten for a web surface; the language's official style
   guide; WCAG for a UI; the relevant regulation for health, financial or personal data. `references/tooling-catalog.md`
   maps stacks to standards and to the tools that check them.

Cite what you find. Every finding sourced from the web carries its URL and version in the report — the
author has to be able to check you.

### Phase 3 — Get it running, then exercise it

This is the phase that separates a real audit from a code read. **Static analysis finds the bugs you can
see; execution finds the bugs that are actually there.**

1. **Build and install it** from a clean state, following only the repository's own documented instructions.
   Every step the docs get wrong is a finding — it is the first thing a new contributor or a deployment
   pipeline will hit.
2. **Run it.** Start the service, launch the CLI, open the app, import the library. Use the **run** skill if
   it fits the project shape.
3. **Exercise it adversarially.** Drive real inputs through real paths:
   - happy path first, to confirm the thing works at all
   - then boundaries: empty, zero, negative, one, maximum, off-by-one, unicode, very long, null, missing field
   - then malformed: wrong type, wrong encoding, truncated payload, duplicate key, malformed JSON/CSV/XML
   - then hostile: injection strings for every interpreter in the path (SQL, shell, template, XPath, LDAP,
     regex), path traversal, oversized upload, unauthenticated call to an authenticated route, another
     user's identifier in your own request
   - then operational: what happens when the database is down, the disk is full, the upstream times out,
     two requests arrive at once, the process is killed mid-write
   For an HTTP surface, walk every route in the spec. For a UI, use Playwright — Chromium is preinstalled.
   For a library, write a scratch harness that calls every public function.
4. **Watch what it does, not what it says.** Logs, exit codes, response bodies, generated files, database
   rows, memory growth over a loop. A wrong result reported as success is worse than a crash.

Keep everything you drive it with. The interesting cases become regression tests in Phase 8.

### Phase 4 — Adversarial audit through independent lenses

One pass finds one class of problem, because you can only hold one obsession at a time. Review the
repository repeatedly, each time as a different specialist with a different fixation.
`references/audit-lenses.md` defines the lenses and exactly what each one hunts.

**Run the lenses in parallel with subagents** — they are genuinely independent and the diversity of
attention is the entire point. Give each one the repository, its brief, and the Phase 0 inventory. Then
merge the findings, deduplicate, and — critically — **verify each one yourself before it enters the ledger**.
A subagent's finding is a lead, not a fact.

Grade every finding with the severity rubric in `references/defect-taxonomy.md`:

| Severity | Meaning | Consequence |
|---|---|---|
| **Critical** | Data loss, data corruption, security compromise, silent wrong results, or the software does not work at all for a documented use | Fix now, always |
| **Major** | A real user will hit it and be blocked or misled; a missing implementation behind a documented feature; an unhandled failure mode in a path that will be exercised | Fix |
| **Minor** | A defect with a narrow blast radius or a workaround; missing test for a real branch; a contract that is honoured but undocumented | Fix |
| **Advisory** | Structural risk, maintainability, ergonomics, dependency drift — nothing broken today | Fix if cheap; otherwise record with a recommendation |

For every finding record the **root cause**, not the symptom. "The endpoint returns 500 on empty list" is a
symptom; "the aggregation divides by `len(rows)` without guarding the empty case, and the same pattern
appears in four other aggregators" is a cause — and only the cause tells you what else is broken. **Every
time you find a defect, immediately search the repository for the same shape elsewhere.** Defects come in
families, and finding the family is what makes an audit worth more than a bug report.

### Phase 5 — Hunt the missing implementations

Bugs are what the software does wrong. **Incompleteness is what it never does at all**, and it is the
defect class that most reliably survives normal review — because there is no failing test for code that
does not exist. Follow `references/incompleteness-hunting.md`. The core moves:

- Run `scripts/incompleteness_scan.py <path>` — it finds `TODO`/`FIXME`/`HACK`/`XXX`, `NotImplementedError`,
  `raise Unimplemented`, `pass`-only bodies, `return null`/`return None` stubs, empty catch blocks, functions
  whose body is only a log line, unreachable code, and commented-out blocks.
- **Documentation minus code.** Walk the contract ledger from Phase 1. Every promise with no implementation
  behind it is a Major finding. This catches the documented CLI flag that is parsed and ignored, the config
  key nothing reads, the API field always returned empty.
- **Code minus documentation.** The reverse: behaviour nobody wrote down. Undocumented required environment
  variables are a classic deployment-day failure.
- **Incomplete branch coverage of the domain.** Every `switch`/`match` over an enum or a union type: is every
  variant handled, and what happens to the one that is not? Every `if` with no `else`: is that deliberate?
  Every error type the callee can raise: does any caller handle it?
- **The unfinished edge.** Pagination that stops at page one. Retry logic with no backoff and no ceiling.
  Cleanup that only runs on the success path. Validation on the client but not the server. A migration with
  no `down`. A feature flag with only one branch implemented.
- **Wired but dead.** Routes registered and never reachable; components imported and never rendered;
  environment variables read into a variable nobody uses; a queue consumer nothing publishes to.

### Phase 6 — Verify every claim against its source

The same discipline the numbers get in a scientific audit, applied to software.

- **Docs against behaviour.** Run the examples in the README. Literally run them. They are wrong more often
  than anyone expects, and they are the first thing a new user executes.
- **Types against reality.** Does the function actually return what the signature says on every path,
  including the error paths? Does the API response match its schema, its OpenAPI spec, its TypeScript type?
- **Tests against what they claim.** Read the assertions. A test named `test_rejects_invalid_input` that
  asserts only "no exception raised" is worse than no test — it is a false green. Tests that mock the thing
  under test, tests with no assertion, tests that pass whatever the code does: all findings.
- **Configuration against deployment.** Every key in the example config: is it read? Every key the code
  reads: is it documented and defaulted? Do the Docker image, the CI environment and the docs agree?
- **Schema against code.** Do the migrations produce the schema the ORM models expect? Are there columns the
  code writes that no migration creates?
- **Concurrency against reality.** Every shared mutable structure, every read-modify-write on a database row,
  every "check then act" — is it actually atomic?

### Phase 7 — Repair, in dependency order

Fix everything, in this order. The order is not a suggestion: fixing polish before correctness wastes the
polish, and refactoring before you have a test to protect you is how audits introduce the bugs they were
meant to remove.

1. **Make it safe to change.** If a module you must fix has no test coverage, write characterisation tests
   *first* that pin its current behaviour. Now you can refactor without guessing.
2. **Critical and security findings.** Data loss, corruption, injection, authentication and authorisation.
3. **Correctness.** Wrong results, unhandled failure modes, broken contracts.
4. **Missing implementations.** Complete what the contract ledger says should exist.
5. **Resilience.** Error handling, timeouts, retries with backoff, resource cleanup, graceful degradation.
6. **Tests.** Every fix above carries a regression test that fails on the old code and passes on the new.
7. **Structure.** Only what the fixes above made necessary or obvious. This is where scope creep lives —
   resist it, and record the refactor you did not do as an Advisory finding instead.
8. **Toolchain and CI.** Make the gate real: linting, typechecking, tests and dependency audit run in CI and
   block on failure.
9. **Documentation.** Update it to match what the code now does. A fix that leaves the docs lying is half a fix.

Throughout: **keep the codebase's voice.** Match its naming, its layering, its error-handling idiom, its
comment density. A module you repair should read like the modules you did not touch. You are correcting the
author's work, not replacing it with your own.

Commit in **atomic, self-explaining units** — one finding or one tightly-related family per commit, with a
message that states the defect, the cause and the fix. A reviewer should be able to read the log and
understand the audit without reading the report.

### Phase 8 — Prove it

Repair is a claim. This phase is the proof. Follow `references/verification-playbook.md`.

- Re-run **every** gate from Phase 0 and record the delta: errors, warnings, test count, pass rate, coverage,
  vulnerability count, type errors.
- Confirm every regression test **fails against the pre-fix code**. A regression test that passes on the old
  code tests nothing. `git stash` and run it.
- Re-run the Phase 3 exercise suite, including every hostile input.
- Re-run the full test suite **three times** to expose order-dependence and flakiness. A test that passes
  only sometimes is an open finding, not a pass.
- Build the deployment artifact — container image, wheel, bundle — from clean. A build that only works on a
  warm cache is a deployment-day failure waiting to happen.
- Walk the contract ledger and confirm every entry is `honoured`, `repaired`, or `withdrawn`.

**The target:** every gate that exists passes, no new warnings, no known-vulnerable dependency reachable, no
secret in the tree, no failing or skipped-without-reason test.

### Phase 9 — Deliver the audit document

The deliverable is a **LaTeX audit report**, compiled to PDF, written into its own dated folder inside the
repository's `Reports/` directory. See `references/report-spec.md` for the full specification and
`assets/audit-report-template.tex` for the template.

**Location — this is a hard requirement:**

```
<repo>/Reports/audit-YYYY-MM-DD-HHMM/
├── audit.tex          the report source
├── audit.pdf          compiled, and it must compile clean
├── findings.json      the machine-readable ledger
├── evidence/          traces, logs, before/after outputs, reproduction scripts
└── README.md          one-screen summary for someone who will not open the PDF
```

Create `Reports/` if it does not exist. **Never overwrite a previous audit** — the timestamped folder exists
precisely so that repeated audits of the same project accumulate into a history. If `Reports/` already holds
earlier audits, open the most recent one first: findings previously marked `accepted` or `open` are your
starting point, and regressions of previously-fixed findings are Critical by definition.

Build it with `scripts/build_report.py`, which renders `findings.json` into the template and compiles it.
The PDF must build with **zero LaTeX errors and zero warnings**; if `pdflatex`/`latexmk` is unavailable in
the environment, ship `audit.tex` plus a Markdown rendering and say so in the summary rather than shipping
nothing.

Write the report in **the language the user is speaking to you in**.

---

## Deliverables

| Always | When applicable |
|---|---|
| The repaired repository, on a working branch, with atomic commits | A migration or rollback plan, if a fix touches persisted data |
| `Reports/audit-<timestamp>/` — LaTeX + PDF + `findings.json` + evidence | A response to the specific bug report the user supplied |
| A closing summary in chat: what was broken, what was fixed, what remains | An upgrade note, if a dependency major version changed |

The closing summary is not optional and it is not a victory lap. It states, in order: the counts by severity,
the three findings that mattered most, the gate delta (before → after), and **everything still open and why**.

---

## Leaning on the rest of the toolbox

Use what exists rather than doing it all by hand:

- **Subagents** — Phase 4's lenses in parallel; also useful for exhaustively sweeping a large repository for
  one specific defect shape.
- **WebSearch / WebFetch** — Phase 2 depends entirely on these. CVEs, advisories, current framework docs.
- **`code-review` skill** — for the diff you produce, before you call it done.
- **`security-review` skill** — for the pending changes on the branch.
- **`run` skill** — Phase 3, launching the project in whatever shape it takes.
- **`dataviz` skill** — load before drawing any chart in the report (severity distribution, coverage delta).
- **`pdf` / `docx` / `xlsx` skills** — when specs, bug reports or test matrices arrive in those formats.
- **`simplify` skill** — Phase 7 step 7, but only after correctness is settled.
- **GitHub tools** — read open issues and PRs before auditing; they often name the defect you are hunting,
  and a finding that closes an existing issue should say so.
- **The project's own tooling** — always prefer the repository's Makefile, `npm run`, `tox`, `just` or
  `docker compose` target over a command you invent. If it has a task runner, the task runner is the contract.

---

## Bundled resources

Read these when the phase calls for them — do not preload them all.

| File | When |
|---|---|
| `references/audit-lenses.md` | Phase 4 — the specialist personas and their hunting grounds |
| `references/defect-taxonomy.md` | Phase 4 — canonical defect classes, severity rubric, CWE/OWASP mapping |
| `references/incompleteness-hunting.md` | Phase 5 — finding what was never written |
| `references/language-playbooks.md` | Phases 3–7 — per-language toolchains and native defect classes |
| `references/stack-playbooks.md` | Phases 3–7 — per-architecture failure modes (web, API, data/ML, CLI, mobile, infra) |
| `references/verification-playbook.md` | Phase 8 — how to prove a fix, and what a real gate looks like |
| `references/tooling-catalog.md` | Phases 0, 2, 8 — analysers, scanners and standards per ecosystem |
| `references/report-spec.md` | Phase 9 — the report's required structure and tone |

Scripts — all runnable with `python3 <script> --help`, all dependency-free (standard library only):

| Script | Does |
|---|---|
| `scripts/repo_recon.py` | Inventories languages, manifests, build systems, test frameworks, CI, entry points, IaC, migrations, churn hotspots |
| `scripts/run_toolchain.py` | Detects and runs the ecosystem's install/build/lint/typecheck/test/audit stages; normalised JSON result |
| `scripts/incompleteness_scan.py` | Finds stubs, TODOs, empty handlers, swallowed exceptions, unimplemented branches |
| `scripts/findings.py` | Creates, validates and summarises the `findings.json` ledger; enforces the schema and the honest-ledger rule |
| `scripts/build_report.py` | Renders the ledger into `audit.tex` from the template and compiles the PDF into the dated `Reports/` folder |

Assets — copy these into the audit folder and fill them in:

| Asset | Is |
|---|---|
| `assets/audit-report-template.tex` | The LaTeX document `build_report.py` fills in. Do not edit per audit |
| `assets/narrative-template.md` | The prose half — `narrative.md` in the audit folder, read by `build_report.py` |
| `assets/audit-folder-README-template.md` | The one-screen summary for the audit folder |

---

## What finishing looks like

You are done when all of these hold, and you have **checked** rather than assumed:

- [ ] Every entry in the contract ledger is `honoured`, `repaired`, or `withdrawn` — none unexamined.
- [ ] Every finding in `findings.json` is `fixed`, `mitigated`, `accepted`, or `open` — with evidence for
      each fix and a reason for each non-fix.
- [ ] Every gate that exists passes, and no gate was weakened to get there.
- [ ] Every fix has a regression test that provably fails on the pre-fix code.
- [ ] The software builds and runs from a clean checkout following only its own documentation.
- [ ] Every hostile input from Phase 3 is handled — rejected cleanly, not crashed on and not silently accepted.
- [ ] No secret, credential or private key is in the tree or the history you added to it.
- [ ] The documentation describes what the code now does.
- [ ] `Reports/audit-<timestamp>/` exists, the PDF compiles clean, and its numbers match `findings.json`.
- [ ] You can name the specific things you could not fix, and why.

If a hostile engineer could still find something, you are not finished. Go back to Phase 4 with a fresh lens.
