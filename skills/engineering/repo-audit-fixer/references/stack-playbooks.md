# Stack playbooks — Phases 3–7

Architecture-shaped failure modes. Identify the shape in Phase 1, then read the matching section. A project
is usually several of these at once.

---

## HTTP API / backend service

**Exercise it (Phase 3).** Walk every route. If there is an OpenAPI spec, drive from the spec and treat any
route not in the spec — or in the spec but not implemented — as a `CONTRACT` finding.

For each route, in this order: happy path · missing required field · wrong type · extra unexpected field ·
empty string, empty array, `null` · a very long string · unicode and emoji · a number at and beyond the
boundary · malformed JSON · no `Content-Type` · no authentication · authentication for a *different* user
whose ID appears in your request · the same request twice, concurrently · a payload of 100 MB.

**Hunt**

- **Authorisation per route.** Authentication proves *who*; authorisation proves *whether*. The endemic bug is
  a handler that authenticates and then trusts the resource ID in the path. Check every route individually —
  audit findings here are almost never uniform.
- **Input validation at the boundary**, in one place, with a schema — not scattered through handlers.
- **Error contract.** One error shape across the API. No stack traces or SQL in responses. Correct status
  codes (a 200 with `{"error": ...}` breaks every client's error handling).
- **Timeouts on every outbound call**, and a total request budget.
- **Idempotency** for anything that creates or charges; an idempotency key honoured on retry.
- **Rate limiting and body size limits** — absent by default in most frameworks.
- **CORS**: `*` with credentials is a vulnerability, not a config choice.
- **Pagination**: bounded page size, stable ordering, a documented maximum.
- **N+1** in every list endpoint — the default failure of every ORM.
- **Transactions** spanning exactly the operations that must be atomic; nothing slow inside one.
- **Health vs readiness** — a health check that does not check dependencies causes traffic to be routed to a
  broken instance.
- **Graceful shutdown** — draining in-flight requests on SIGTERM, or every deployment drops requests.
- **Logging** with a request ID, and no secrets or PII in it.

---

## Frontend / SPA

**Exercise it.** Use Playwright (Chromium is preinstalled). Drive: first load with a cold cache, a slow
network, an offline network, a 500 from the API, an empty dataset, a very large dataset, a session that
expires mid-flow, back/forward navigation, a deep link, a page reload mid-form, and a double-click on every
submit button.

**Hunt**

- **The four states.** Every view that loads data needs success, loading, empty and error. The last three are
  routinely missing — that is an `INCOMPL` finding each.
- **Double submission** — no disabled state, no idempotency, so the user creates two orders.
- **XSS** via `innerHTML` / `dangerouslySetInnerHTML` / `v-html` / bypassed sanitisation.
- **Secrets in the bundle** — an API key or a private endpoint in client-side code. Everything shipped to the
  browser is public.
- **Authorisation in the UI only** — hiding a button is not access control; confirm the API refuses too.
- **Effect cleanup and stale closures** (see `language-playbooks.md`).
- **Accessibility** — labels, alt text, focus management, keyboard reachability, contrast, `aria-live` for
  async updates, focus trap in a modal, colour as the sole meaning carrier. WCAG 2.2 AA is the bar.
- **Form validation** duplicated client-side without a server-side counterpart.
- **Bundle size and unbounded lists** rendered without virtualisation.
- **Uncaught errors** with no error boundary — one component crashes the whole app to a white screen.

---

## Data / ML / scientific computing

This is where a wrong answer is most likely to be believed, so the correctness bar is highest.

**Hunt**

- **Data leakage** — the single most damaging defect in ML code. Scaling, imputation, feature selection or
  encoding fitted on the full dataset before the split; target-derived features; a group (patient, site,
  household) split across train and test; time-series split at random rather than chronologically.
- **Reproducibility** — no seed, or a seed set for one library and not the others; non-deterministic GPU ops;
  no environment pin; a data version nobody records.
- **The split** — no held-out test set, or a test set used repeatedly for model selection (which turns it into
  a validation set and invalidates the reported score).
- **Metrics** — accuracy on an imbalanced target; a threshold chosen on test data; no confidence interval;
  averaging AUCs across folds instead of pooling; a metric computed on a different subset than the one
  described.
- **Missing data** — silent `dropna` changing the cohort; imputation not documented; missingness that is
  informative treated as random.
- **Pipeline integrity** — a merge that silently duplicates rows (**assert the row count before and after
  every join**); an index misalignment; a dtype coerced to `object`; a category mapping applied to the wrong
  column; units mixed between sources.
- **Numbers in the report** — hand-typed rather than generated. The durable fix is to emit results to a file
  the document reads, so the two cannot diverge.
- **Notebooks** — see `language-playbooks.md`. Out-of-order execution invalidates everything below it.
- **Privacy** (`PRIV`) — identifiers in fixtures, logs, error payloads or committed sample data; an export
  path with no de-identification. In clinical and epidemiological repositories this is `Critical`.
- **Statistical validity** — the test's assumptions checked; multiple comparisons corrected; a causal claim
  from an observational design; a confidence interval computed for a metric it does not apply to.

---

## CLI tools

Exercise: no arguments · `--help` · `--version` · every documented flag · an unknown flag · conflicting flags ·
a missing required argument · a nonexistent input file · a file with no read permission · piped stdin · no
stdin on a TTY · a very large input · interruption with Ctrl-C mid-write · running twice concurrently in the
same directory.

Hunt: exit code 0 on failure (breaks every script that calls it) · errors written to stdout instead of stderr,
corrupting pipelines · a partially written output file left behind after an error · no atomic write
(write-temp-then-rename) · progress output that breaks when not a TTY · colour codes emitted when piped · a
destructive action with no `--dry-run` and no confirmation · a config file precedence order that is
undocumented or inconsistent · a `--force` that also disables the safety checks it should not.

---

## Mobile

Hunt: work on the main thread · a leak from a retained context/delegate/listener · state lost on rotation or
process death · no offline handling and no retry on reconnect · permissions requested without a rationale and
without handling denial · secrets in the app bundle or in shared preferences/`UserDefaults` · certificate
handling weakened for a test environment and shipped · deep links accepted without validation · background
work with no constraints draining battery · a minimum OS version claimed but an API used that is newer.

---

## Infrastructure as code, containers, CI/CD

**Docker.** A floating `:latest` base tag · running as root · secrets in build args or baked into a layer
(they persist in the image history even if deleted later) · `COPY . .` with no `.dockerignore`, shipping
`.git` and `.env` · `apt-get install` with no version pins and no cache cleanup · no `HEALTHCHECK` · a single
huge layer · no non-root `USER` · unnecessary capabilities.

**Kubernetes.** No resource requests/limits · no liveness/readiness distinction · secrets as plain env vars ·
`hostPath` mounts · a privileged container · no `PodDisruptionBudget` for a service that must stay up · an
`imagePullPolicy` that pins nothing · no network policy.

**Terraform / IaC.** A storage bucket or database publicly readable · a security group open to `0.0.0.0/0` ·
unencrypted storage or unencrypted backups · state file committed or stored unencrypted · secrets in
variables with no `sensitive = true` · no lifecycle protection on a stateful resource · IAM policies with `*`.

**CI/CD.** The pipeline runs different commands than the documentation says (so local green ≠ CI green) ·
`continue-on-error` on a quality gate · a step pinned to a mutable tag or branch rather than a SHA · secrets
echoed into logs · a workflow triggered by `pull_request_target` that checks out and executes untrusted code ·
no branch protection requiring the checks · a deployment with no rollback path · no dependency-audit stage.

---

## Desktop / Electron

`nodeIntegration: true` with remote content (full RCE) · `contextIsolation: false` · loading remote URLs into
a privileged window · no auto-update signature verification · IPC handlers accepting arbitrary paths or
commands from the renderer · secrets in the packaged app.

---

## Monorepos & multi-package repositories

Hunt: a package importing another's internals rather than its public entry point · a circular dependency
between packages · version drift of a shared dependency between packages · one package's tests silently not
running in CI · a shared config that one package overrides in a way nobody knows about · a build order that
works only by accident · a change in a base package with no way to know which dependents it breaks.

Practical move: enumerate the packages from the workspace manifest, then check that **every** one appears in
the CI matrix. A package that CI does not build is a package that is broken.

---

## Legacy code with no tests

The special case. You cannot safely fix what you cannot verify, and you cannot verify without tests.

The order that works:

1. **Get it running and pin the current behaviour.** Write *characterisation tests* — tests that assert what
   the code does today, bugs included. They are not correctness tests; they are a safety net.
2. **Find the seams.** The smallest change that lets you inject a dependency or call a unit in isolation.
3. **Only then fix**, one defect at a time, watching the characterisation tests.
4. **When a characterisation test encodes a bug**, changing it is part of the fix — and the report says which
   tests were changed and why. This is the one legitimate case for editing an existing passing test, and it
   must be visible.

Do not begin a broad refactor of untested legacy code during an audit. Fix the defects, add the tests, and
record the refactor as an `Advisory` finding with a concrete proposal.
