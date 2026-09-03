# Verification playbook — Phase 8

Repair is a claim. This phase turns the claim into evidence. An audit whose report says "fixed" without proof
is worth less than no audit, because it manufactures confidence.

---

## The four questions every fix must answer

For each finding marked `fixed`:

1. **Did I reproduce it before?** Evidence of the defect, captured — a failing test, a trace, a wrong output,
   an exit code, a screenshot.
2. **Does the regression test fail on the old code?** Not "does it pass now" — *does it fail then*. This is
   the step everyone skips and it is the only one that proves the test tests anything.
3. **Does the whole suite still pass?** A fix that breaks something else is a trade, not a fix.
4. **Did I fix the cause or the instance?** If the root cause spans several call sites, are all of them fixed?
   Search the repository for the pattern again, after the fix, and confirm zero remaining.

### Proving a regression test is real

```bash
git stash                     # or: git stash push -- <the fixed source files>
<run only the new test>       # MUST fail
git stash pop
<run only the new test>       # MUST pass
```

If step two passes, the test does not exercise the defect. Rewrite it. Record the two outcomes as evidence.

For a whole-suite version of the same idea, mutate deliberately: invert a condition you just fixed and confirm
a test goes red. If nothing goes red, the branch is untested regardless of what the coverage number says.

---

## The gate

Run every stage that exists, both at Phase 0 (baseline) and here (final). `scripts/run_toolchain.py` detects
and runs them; record both results in `findings.json` under `gate`.

| Stage | Passing means |
|---|---|
| `install` | A clean dependency install from the lockfile succeeds, offline-reproducibly where possible |
| `build` | Compiles/bundles from a clean state with no warnings introduced |
| `lint` | Zero errors; warnings not increased; no new suppressions |
| `typecheck` | Zero errors; no new `any`/`ignore`/`unchecked` casts |
| `test` | All pass; nothing skipped without a written reason; three consecutive runs agree |
| `coverage` | Not decreased; every line changed in this audit is covered |
| `audit` | No known-vulnerable dependency whose vulnerable path is reachable |
| `secrets` | No credential in the tree or in the commits this audit added |
| `docs` | Every command in the README executes successfully |

**No stage may be made to pass by weakening it.** Compare the configuration files at Phase 0 and Phase 8: if
a lint rule, a coverage threshold, a strictness flag or a test selector changed, that change must be a
deliberate, justified finding — not a silent adjustment. Diff them explicitly and put the diff in the report.

---

## Beyond the gate

The gate is the floor. These find what it cannot.

**Flakiness.** Run the suite three times. Then run it with a shuffled order (`pytest -p no:randomly --random-order`,
`jest --randomize`, `go test -shuffle=on`). Order-dependence means tests share state, and shared state means at
least one of them is not testing what it claims.

**Race detection.** `go test -race`, `-fsanitize=thread`, Java concurrency stress, or simply hammering the
endpoint with concurrent requests and checking invariants afterwards. Run this whenever Phase 4's L5 lens
produced anything at all.

**Property-based testing.** For pure transformation functions — parsers, serialisers, validators, calculators,
anything with a round trip. Hypothesis (Python), fast-check (JS), quickcheck (Rust/Go), jqwik (Java). One
property test explores more of the input space than twenty hand-written cases, and it *finds* the boundary
case rather than making you guess it. Round trips (`decode(encode(x)) == x`) and invariants (sorting preserves
length and multiset) are the highest-yield properties.

**Fuzzing.** For any parser or binary format handler. `atheris`, `cargo fuzz`, `go-fuzz`, libFuzzer. Even a
short run finds crashes on malformed input.

**Sanitizers.** For native code, re-run the whole suite under ASan and UBSan. This is not optional for C/C++.

**Load and limits.** Whatever the software's scale claim is, exercise it at that scale and one order of
magnitude beyond. Watch memory across a long run — flat is correct, monotonically rising is a leak.

**Clean-room build.** Build the deployment artifact from a fresh clone in a fresh container with no cache.
A build that only works on a warm machine is a deployment-day failure with a delay fuse.

**The stranger test.** Follow the README exactly, as literally as a machine, from an empty directory. Every
place you must improvise is a `DOC` finding.

---

## What a real quality gate looks like

If the repository has no enforced gate, building one is part of the audit's deliverable. The minimum that is
worth having, wired into CI and **blocking** the merge:

```
install (from lockfile)  →  lint  →  typecheck  →  test + coverage  →  build  →  dependency audit  →  secret scan
```

with:

- the **same commands** available locally as a single task-runner target, so contributors can reproduce CI;
- **no `continue-on-error`** on any of these stages;
- **branch protection** requiring them;
- **pinned tool versions** (a gate whose behaviour drifts is not a gate);
- a **pre-commit hook** for the fast stages, as a convenience — never as the enforcement point, because hooks
  are skippable.

A repository with a real gate stays fixed. A repository fixed once without a gate regresses, and the next
audit finds the same findings — which is exactly what the `Reports/` history will show you.

---

## Closing the loop

Before writing the report:

1. Every finding has a `state`, and every `fixed` has `evidence` **and** `verification`.
2. Every contract-ledger entry from Phase 1 is `honoured`, `repaired` or `withdrawn`.
3. `scripts/findings.py --validate` passes — it enforces the schema and refuses a ledger with unexamined
   entries or a `fixed` finding lacking verification.
4. The gate numbers in the report are the numbers the tools actually printed. Do not round, do not estimate,
   do not report a coverage figure you did not measure.
5. Re-read your own diff as a hostile reviewer. Anything you would object to in someone else's PR, fix now.

Then, and only then, Phase 9.
