# Audit lenses — Phase 4

One pass finds one class of defect, because attention is singular. Each lens below is a different engineer
with a different obsession. Run them as **independent subagents in parallel**, give each one only its own
brief, then merge and deduplicate. Verify every finding yourself before it enters the ledger — a subagent's
finding is a lead, not a fact.

A lens is done when it can answer its **exit question** with evidence.

---

## L1 · Correctness

**Obsession:** the code computes the wrong answer and nobody notices.

Hunt: off-by-one in slicing, indexing and loop bounds · integer division and truncation where a float was
meant · float equality and accumulated error · rounding applied twice or at the wrong step · division with
no zero guard · empty-collection aggregations (`mean([])`, `max([])`, `sum/len`) · unit and scale mismatches
(ms vs s, bytes vs KB, percent vs fraction, cents vs dollars) · timezone-naive datetimes crossing a boundary
· DST and leap-day arithmetic · locale-dependent parsing (`,` vs `.` decimals, `%d/%m` vs `%m/%d`) · string
comparison where a numeric one was meant · mutable default arguments · aliasing where a copy was intended ·
shallow copy of a nested structure · operator precedence, especially mixed `and`/`or`/`not` · inverted
boolean conditions · `sort` without a stable key where order matters · silent truncation on cast or column
width.

**Exit question:** for every function that transforms data, can I name its correct output on the empty
input, the single-element input, the boundary input, and the maximum input — and does it produce that?

---

## L2 · Security

**Obsession:** the attacker is already inside the input.

Hunt, mapped to OWASP and CWE (see `defect-taxonomy.md`):

- **Injection** — string-built SQL, shell via `system`/`exec`/`popen` with interpolation, template injection
  (SSTI), NoSQL operator injection, LDAP/XPath, regex built from user input (ReDoS), header/CRLF injection,
  log injection.
- **AuthN/AuthZ** — missing authorisation check on a route that has authentication (the classic IDOR: the
  handler trusts the ID in the request), authorisation enforced in the UI but not the API, JWT with
  `alg: none` or an unverified signature, token expiry unchecked, session fixation, missing CSRF token on a
  state-changing form, privilege check before rather than after a redirect.
- **Secrets** — credentials, keys, tokens or connection strings in source, config, tests, fixtures, CI files,
  Dockerfiles, notebooks or **git history**; `.env` committed; a default password that ships.
- **Crypto** — MD5/SHA-1 for anything security-bearing, unsalted or fast password hashing (use argon2/bcrypt/
  scrypt), ECB mode, a static or reused IV, `random` instead of `secrets`/`crypto.randomBytes` for tokens,
  home-made crypto, disabled certificate verification (`verify=False`, `rejectUnauthorized: false`).
- **Deserialisation & parsing** — `pickle`, `yaml.load`, Java native deserialisation, XML without external
  entity resolution disabled (XXE), zip/tar extraction without path checks (zip-slip).
- **Web surface** — reflected/stored/DOM XSS, `dangerouslySetInnerHTML`/`v-html`/`innerHTML` with untrusted
  data, open redirect, permissive CORS (`*` with credentials), missing security headers, cookies without
  `HttpOnly`/`Secure`/`SameSite`.
- **SSRF & path traversal** — a URL or filename from the user reaching a fetch or an open, without an
  allowlist and without normalising `..`.
- **Information leakage** — stack traces or SQL in a production error response, debug mode on by default,
  verbose 500s, secrets or PII in logs, a timing oracle in a credential comparison (use a constant-time compare).
- **Supply chain** — an unpinned or floating dependency, an install script in a transitive package, a typo-
  squatted name, a lockfile that disagrees with the manifest, an unverified curl-to-shell in a Dockerfile.
- **Denial of service** — unbounded request body, unbounded pagination, no rate limit, unbounded recursion,
  a quadratic algorithm on user-controlled size, an unbounded in-memory cache.

**Exit question:** for every input that crosses the trust boundary, can I name where it is validated, where
it is escaped, and for whose authority it is checked?

---

## L3 · Failure modes & resilience

**Obsession:** everything downstream is about to break, and this code has no plan.

Hunt: bare `except:` / `catch (Exception)` / `catch {}` that swallows · an error logged and then execution
continuing as if nothing happened · a network call with no timeout (the single most common production hang)
· retries with no ceiling, no backoff, no jitter · retry on a non-idempotent operation · a file, socket,
cursor, lock or transaction not closed on the error path (no `with`/`defer`/`try-finally`/`using`) · cleanup
only on the success path · partial writes with no atomicity (write-then-rename, or a transaction) · a failed
step leaving the system in a state no code can recover from · no circuit breaker on a dependency that will be
down · unbounded queues and unbounded memory growth · missing graceful shutdown, so in-flight work is lost ·
a health check that returns 200 while the dependency it depends on is unreachable · an assertion used for
runtime validation in a build where assertions are stripped.

**Exit question:** for each external dependency (database, HTTP service, disk, queue, clock), what does the
code do when it is slow, when it is down, and when it returns something malformed?

---

## L4 · Data integrity & persistence

**Obsession:** the data will be silently wrong forever, and no backup will help because the corruption is committed.

Hunt: read-modify-write without a transaction or optimistic lock (lost update) · "check then act" across a
network boundary · a missing unique constraint behind an application-level uniqueness check · missing foreign
keys, or `ON DELETE` behaviour nobody chose · nullable columns the code assumes are non-null · a migration
with no `down`, or one that is not idempotent, or one that locks a large table without warning · a migration
that changes a type in a way that truncates · schema drift between the migrations and the ORM models · N+1
queries · an unindexed column in a `WHERE`, `JOIN` or `ORDER BY` on a table that will grow · float used for
money · a timestamp stored without a timezone · encoding mismatch between application and column ·
soft-delete filtering forgotten in one query out of ten · a cache with no invalidation path · a cache key
that omits a variable the value depends on.

**Exit question:** if the process is killed at any single point in this write path, what is left in the store,
and can the system recover from it?

---

## L5 · Concurrency & time

**Obsession:** it works until two things happen at once.

Hunt: shared mutable state without a lock · a lock held across an I/O call · lock ordering that can deadlock
· `async` function called without `await` (a silently discarded coroutine) · blocking I/O inside an event
loop · `useEffect`/subscription without cleanup · a `setState` after unmount · a race between initialisation
and first use · double-submit with no idempotency key · a scheduled job with no overlap guard · time
assumptions: monotonic vs wall clock, `now()` called twice in one operation and expected to be equal, a
timeout compared against a clock that can jump · thread-unsafe library used from multiple threads · signal
handling that is not async-safe.

**Exit question:** which of these operations can run twice concurrently, and what happens if they do?

---

## L6 · Contracts, interfaces & compatibility

**Obsession:** the caller believed the signature.

Hunt: a function that returns a different type on the error path than the signature promises · `None`/`null`
returned where a caller does not check · an exception type raised that no caller handles and no docstring
mentions · an API response that does not match its OpenAPI/JSON schema/TypeScript type · a required field
added to a request without a version bump · an enum value added that old clients will not recognise · a
default changed silently · a breaking change with no major version bump · a public symbol removed with no
deprecation period · inconsistent error shapes across endpoints of the same API · pagination that is not
stable under concurrent insert · a header the client must send that is documented nowhere.

**Exit question:** what is the exhaustive set of things this function or endpoint can return or raise, and
does every caller handle each one?

---

## L7 · Tests & verifiability

**Obsession:** the green checkmark is a lie.

Hunt: a test with no assertion · a test that asserts only "did not raise" · a test that mocks the very unit
under test · over-mocking such that the test passes even if the implementation is deleted · tests coupled to
each other by shared state or execution order · a test that depends on the wall clock, the network, the
filesystem layout, or a random seed it does not set · `skip`/`xfail`/`@Ignore` with no reason and no ticket ·
a snapshot test updated blindly · a test asserting the current buggy behaviour (so the bug is now pinned) ·
whole branches of the domain with no coverage — especially error paths, which is where coverage is always
thinnest · no test for the bug the user reported · coverage measured but not enforced · assertions on
implementation details rather than behaviour, making refactoring impossible.

**Exit question:** if I introduce the bug this test is named for, does the test fail? (Try it — mutate the
code and watch. That is the only honest answer.)

---

## L8 · Build, dependencies & supply chain

**Obsession:** it works on this machine.

Hunt: no lockfile, or a lockfile out of sync with the manifest · floating version ranges on a runtime
dependency · a dependency that is unmaintained, deprecated, or has a known CVE · two versions of the same
library resolved into one build · a dev dependency imported by production code · a native dependency with no
documented system requirement · a build that depends on network access at an unexpected point · a Docker
image built on a floating `:latest` base, running as root, with build secrets baked into a layer, or with the
whole build context copied in · missing `.dockerignore` · CI that does not run the same commands as the docs
· CI that continues on failure · a step pinned to a mutable action reference · no reproducible build path.

**Exit question:** from an empty machine with only the repository, does the documented command produce a
working artifact — and would it still, six months from now?

---

## L9 · Observability & operability

**Obsession:** it is 3am and production is broken.

Hunt: an error path with no log · logs with no context (no request ID, no user, no input identifier) ·
secrets or PII written to logs · `print`/`console.log` used as logging · no log levels, or everything at
`INFO` · no metrics on the paths that matter (latency, error rate, queue depth, saturation) · no health or
readiness endpoint · configuration that cannot be inspected at runtime · no way to reproduce a user's report
from what is recorded · alerting on symptoms nobody can act on · a stack trace lost by re-raising without the
cause (`raise X` instead of `raise X from e`).

**Exit question:** given only the logs and metrics this software emits, could I diagnose each Critical
finding I have already made?

---

## L10 · Performance & resources

**Obsession:** it is fine at ten rows.

Hunt: an algorithm that is quadratic or worse on user-controlled input · a query inside a loop (N+1) · a full
scan where an index was intended · loading an entire file, table or response into memory · no streaming for
large payloads · a regex with catastrophic backtracking · repeated recomputation of an invariant inside a
loop · a connection opened per request instead of pooled · a synchronous call blocking a request path that
could be deferred · unbounded caches and unbounded concurrency · a memory leak from a listener, a closure, or
a growing global · a container with no memory limit next to code that assumes there is one.

**Exit question:** what is the input size at which this becomes unusable, and is that size reachable?

---

## L11 · Maintainability, structure & readability

**Obsession:** the next person, in six months, at speed.

Hunt: duplicated logic that has already drifted between copies (the dangerous kind — one copy has the bug
fix and one does not) · a function doing five things · a module with no single responsibility · a circular
import · business logic in a controller, a template, or a migration · a magic number with no name · dead
code and unreferenced files · configuration hard-coded into logic · an abstraction with exactly one
implementation and three layers · inconsistent naming for the same concept · comments that contradict the
code · a public API surface far larger than needed.

**Exit question:** to change the software's most likely next requirement, how many files must be edited, and
does anything enforce that all of them are?

---

## L12 · Documentation, UX & accessibility

**Obsession:** the person who has never seen this before.

Hunt: a README whose install steps do not work · an example that does not run · a documented flag that does
not exist · an undocumented required environment variable · no statement of what the software is for · error
messages that name an internal identifier instead of what the user should do · error messages that leak
internals · no validation feedback in the UI · form controls with no label, images with no alt text, an
interaction reachable only by mouse, colour as the only carrier of meaning, contrast below WCAG AA, focus
order that jumps · text that cannot be translated because it is concatenated · a destructive action with no
confirmation and no undo.

**Exit question:** can a competent stranger install it, run it, make it do its main job, and recover from
their first mistake, using only what is in the repository?

---

## Merging the lenses

Lenses overlap by design. When merging:

1. **Deduplicate by root cause, not by symptom.** Three lenses reporting three symptoms of one missing
   validation is *one* finding with three consequences — that framing is more useful to the author.
2. **Take the highest severity** any lens assigned, then re-justify it yourself against the rubric.
3. **Look for the family.** If two lenses independently found the same *shape* of defect in different
   modules, sweep the whole repository for that shape before moving on. This is where an audit earns its keep.
4. **Discard what you cannot support.** A finding you could not reproduce and cannot trace in the source does
   not go in the ledger as a finding; if it still worries you, it goes in the report's "worth watching"
   section, labelled as unverified.
