# Audit — <repository> — <YYYY-MM-DD HH:MM UTC>

One screen, for someone scrolling the repository on a phone. Everything else is in
[`audit.pdf`](./audit.pdf).

**Verdict.** <One or two sentences: would it have failed in front of its users, and does it now.>

**Deployment recommendation.** <ready / ready with conditions (name them) / not ready (name the blockers)>

## Counts

| Severity | Before | Fixed | Mitigated | Accepted | Open |
|---|---|---|---|---|---|
| Critical |  |  |  |  |  |
| Major    |  |  |  |  |  |
| Minor    |  |  |  |  |  |
| Advisory |  |  |  |  |  |

## The three that mattered

1. **F-0xx — <title>.** <One sentence on the cause and the consequence.>
2. **F-0xx — <title>.**
3. **F-0xx — <title>.**

## Quality gate

| Stage | Before | After |
|---|---|---|
| install |  |  |
| build |  |  |
| lint |  |  |
| typecheck |  |  |
| test |  |  |
| coverage |  |  |
| audit |  |  |
| secrets |  |  |

## Still open

<Count, and the one-line reason for each. If none: "None.">

## Not examined

<What was out of scope or unreachable, and why. If nothing: "Nothing — the full repository was audited.">

---

| | |
|---|---|
| Commit audited | `<sha>` |
| Commit delivered | `<sha>` |
| Branch | `<branch>` |
| Ledger | [`findings.json`](./findings.json) |
| Evidence | [`evidence/`](./evidence/) |
