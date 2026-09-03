# Language playbooks — Phases 3–7

Per-language: the toolchain to run, and the defect classes native to that language. Read only the sections
that apply to the repository in front of you.

**Two rules that apply to every language.** First, prefer the repository's own task runner (`Makefile`,
`npm run`, `tox.ini`, `justfile`, `docker compose`) over a command you invent — if it has one, it *is* the
contract, and inventing your own means you tested something the CI does not. Second, tool versions matter:
check what CI uses and match it, or your green is not the pipeline's green.

---

## Python

**Toolchain**

```bash
ruff check .              # lint  (or flake8 / pylint)
ruff format --check .     # format (or black --check)
mypy .                    # types (or pyright)
pytest -q                 # tests
pytest --cov --cov-report=term-missing
pip-audit                 # dependency CVEs (or safety)
bandit -r src/            # security lint
python -W error -m ...    # surface DeprecationWarnings as failures
```

Environment: check for `pyproject.toml` (PEP 621), `setup.cfg`, `requirements*.txt`, `Pipfile`, `poetry.lock`,
`uv.lock`, `environment.yml`. A repository with `requirements.txt` and no pinned versions has no reproducible
build — that is a `BUILD` finding on its own.

**Native defect classes**

- **Mutable default arguments** (`def f(x=[])`, `def f(d={})`) — shared across calls. Classic, still common.
- **Late binding in closures** — `[lambda: i for i in range(3)]` all return 2.
- **Bare `except:`** catches `KeyboardInterrupt` and `SystemExit`. `except Exception` is the floor;
  naming the exception is correct.
- **Swallowed exceptions** — `except Exception: pass`, or `logger.error(e)` then continuing.
- **`raise X` losing the cause** — use `raise X from e` so the traceback survives.
- **Integer division** — `/` vs `//`; and `-7 // 2 == -4`, which surprises people from C.
- **Float and `Decimal`** — never `float` for money; `0.1 + 0.2 != 0.3`.
- **`datetime.now()` naive** — timezone-naive datetimes compared or stored; use `datetime.now(timezone.utc)`.
- **Mutating a collection while iterating it.**
- **`is` vs `==`** for values; works for small ints by accident, then does not.
- **Shallow `copy()`** of a nested structure; `copy.deepcopy` or a rebuild.
- **`assert` for validation** — stripped under `python -O`. Never use for runtime checks.
- **`subprocess` with `shell=True`** and interpolated input — command injection.
- **`pickle` / `yaml.load` / `eval` / `exec`** on untrusted data — RCE. `yaml.safe_load`.
- **`random`** for tokens or IDs — use `secrets`.
- **`requests` with no `timeout=`** — hangs forever. This is the most common production hang in Python.
- **Async** — a coroutine created and not awaited (silently never runs); blocking I/O inside an event loop;
  `asyncio.gather` swallowing exceptions without `return_exceptions` understood.
- **pandas** — chained assignment / `SettingWithCopyWarning`; silent `dtype` coercion to `object`; `NaN`
  propagating through comparisons; index misalignment in arithmetic; `inplace=True` behaviour; `merge`
  silently producing a cross product on duplicate keys, changing the row count. **Always assert row counts
  before and after a merge.**
- **numpy** — integer overflow in fixed-width dtypes; broadcasting producing a shape you did not intend;
  `==` on float arrays.
- **Packaging** — `__init__.py` missing so a subpackage is not installed; relative import failing outside the
  source tree; test passing only because `.` is on `sys.path`.

---

## JavaScript / TypeScript

**Toolchain**

```bash
npm ci                      # never `npm install` in an audit — ci respects the lockfile
npx tsc --noEmit            # types
npx eslint .                # lint
npx prettier --check .
npm test
npm audit --audit-level=high
npx depcheck                # unused / undeclared dependencies
npx knip                    # dead exports and files
```

Check `package.json` `engines`, and whether the lockfile (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`)
matches the package manager the CI actually uses.

**Native defect classes**

- **`==` vs `===`**, and the truthiness traps: `0`, `""`, `NaN`, `[]`, `"0"`.
- **`??` vs `||`** — `||` swallows legitimate `0` and `""`. A very frequent real bug.
- **Optional chaining hiding a bug** — `a?.b?.c` returning `undefined` where the absence was the defect.
- **Floating-point money** — `0.1 + 0.2`; use integer cents or a decimal library.
- **`parseInt` without a radix**; `Number("")` is `0`; `[10,1,2].sort()` is lexicographic.
- **Unhandled promise rejection** — a promise not awaited and not `.catch()`ed; `forEach` with an `async`
  callback (the loop does not wait); missing `await` inside `try` so the `catch` never fires.
- **`Promise.all` failing fast** where `allSettled` was meant, losing the successful results.
- **`this` binding** in a callback; arrow vs function.
- **Mutation of props / state / a frozen-by-convention object.**
- **`JSON.parse` without try/catch** on external input.
- **Prototype pollution** — merging untrusted objects with `__proto__`.
- **`fetch`/`axios` with no timeout or abort signal.**
- **TypeScript specifically** — `any` and `as` casts hiding real type errors; a non-null assertion `!` that is
  not guaranteed; `strict: false` in `tsconfig.json` (check it — half of TS's value is off by default);
  types that lie about runtime, especially at API boundaries where nothing validates the shape (use `zod`
  or equivalent at the boundary); enum vs union exhaustiveness with no `never` check in the default branch.
- **React** — missing `useEffect` cleanup (subscriptions, timers, listeners); wrong or missing dependency
  array (stale closure); state updated after unmount; `key` set to the array index in a reorderable list;
  `dangerouslySetInnerHTML` with untrusted content; expensive work in render; a context value recreated every
  render forcing a full subtree re-render.
- **Node** — a synchronous filesystem call in a request path; unbounded body parsing; `child_process.exec`
  with interpolation; secrets in `process.env` logged at startup.

---

## Java / Kotlin

**Toolchain**

```bash
./mvnw -B verify            # or ./gradlew build
./mvnw dependency:tree      # duplicate/conflicting versions
./mvnw org.owasp:dependency-check-maven:check
spotbugs / errorprone / pmd / checkstyle
ktlint / detekt             # Kotlin
jacoco                      # coverage
```

**Native defect classes**

- `NullPointerException` surfaces: an unannotated API, `Optional.get()` without `isPresent`, a Kotlin
  platform type from Java crossing into non-null.
- `equals` without `hashCode`; a mutable object used as a map key; `compareTo` inconsistent with `equals`.
- Resources not closed — use try-with-resources; a `Stream` from `Files.lines` not closed.
- Checked exceptions caught and ignored; `catch (Exception e) {}`.
- `SimpleDateFormat` is not thread-safe (use `java.time`).
- Integer overflow in `int` arithmetic; `double` for money instead of `BigDecimal`.
- Concurrency: non-atomic compound operations on a `ConcurrentHashMap`; `synchronized` on a mutable field;
  a shared `SimpleDateFormat`/`Random`; a thread pool with an unbounded queue.
- Spring: `@Transactional` on a private or self-invoked method (no proxy, so no transaction); field injection
  hiding a cycle; an `open-in-view` N+1; a `@RestController` returning an entity and lazily loading inside
  serialisation.
- Jackson: polymorphic deserialisation enabled on untrusted input (RCE class).
- Logging exceptions without the stack trace (`log.error(e.getMessage())`).

---

## Go

**Toolchain**

```bash
go build ./... && go vet ./...
staticcheck ./...
golangci-lint run
go test ./... -race -count=3   # -race is not optional in an audit
govulncheck ./...
```

**Native defect classes**

- **Ignored errors** — `_ = f()`, or a call whose error return is dropped. Search for it exhaustively.
- **`err != nil` handled by logging and continuing** with a zero value.
- **Loop variable capture in a goroutine** (pre-Go 1.22 semantics; check the `go` directive in `go.mod`).
- **Goroutine leaks** — a goroutine blocked forever on a channel nobody closes; no `context` propagation.
- **`defer` inside a loop** — resources accumulate until the function returns.
- **Nil map write** (panics); nil slice vs empty slice conflated in JSON output.
- **Slice aliasing after `append`** — the underlying array is shared until it grows.
- **A nil pointer inside a non-nil interface** — `err != nil` is true when the concrete value is nil.
- **`time.After` in a loop** — leaks timers.
- **HTTP client with no timeout**; response body not closed.
- **`sync.WaitGroup` `Add` inside the goroutine** rather than before it.

---

## Rust

**Toolchain**

```bash
cargo build --all-targets && cargo clippy --all-targets -- -D warnings
cargo test && cargo test --release      # debug/release differ on overflow
cargo audit && cargo deny check
cargo +nightly miri test                # if unsafe is present
```

**Native defect classes**

- `unwrap()` / `expect()` on a path that can genuinely fail — each one is a potential panic in production.
- Integer overflow: panics in debug, wraps in release. Use `checked_*`/`saturating_*` where it matters.
- `unsafe` blocks with no safety comment and no justification.
- Blocking calls inside an async runtime; holding a `std::sync::Mutex` guard across an `.await`.
- `Rc`/`Arc` cycles leaking; `RefCell` borrow panics at runtime.
- Error handling collapsing distinct failures into one `String` error, losing the ability to react.

---

## C / C++

**Toolchain**

```bash
-Wall -Wextra -Werror -Wconversion -Wshadow -fno-omit-frame-pointer
-fsanitize=address,undefined      # and run the suite under it
valgrind --leak-check=full
clang-tidy / cppcheck / include-what-you-use
```

**Native defect classes:** buffer overflow (every `strcpy`, `sprintf`, `gets`, unchecked `memcpy`), off-by-one
in array bounds, use-after-free, double free, uninitialised read, signed overflow (undefined behaviour),
implicit narrowing conversion, `malloc` return unchecked, mismatched allocator/deallocator, format-string
vulnerability, integer overflow in a size calculation before an allocation, `errno` checked after an
intervening call, missing `virtual` destructor, iterator invalidation after container mutation, static
initialisation order fiasco, data race on a non-atomic shared variable.

---

## C# / .NET

```bash
dotnet build -warnaserror && dotnet test
dotnet list package --vulnerable --include-transitive
dotnet format --verify-no-changes
```

Defects: `async void` outside an event handler (exceptions are unobservable); `.Result` / `.Wait()` deadlocking
on a synchronisation context; missing `ConfigureAwait(false)` in a library; `IDisposable` not disposed (no
`using`); `DbContext` shared across threads; EF Core lazy loading causing N+1 and serialisation cycles;
nullable reference types disabled; `string` concatenation building SQL; `DateTime.Now` instead of `UtcNow`.

---

## PHP / Ruby

**PHP:** `composer audit`, PHPStan/Psalm at max level, PHP_CodeSniffer. Defects: loose comparison `==`
(`"0e123" == "0e456"` is true — a real authentication bypass), `extract()` on request data, SQL built by
concatenation instead of prepared statements, `$_REQUEST` conflating GET/POST/COOKIE, unserialize on user
input, file upload with no MIME/extension validation, `include` with a user-controlled path.

**Ruby:** `bundle audit`, RuboCop, Brakeman (Rails). Defects: mass assignment without strong parameters,
`send`/`eval` with user input, SQL via string interpolation in `where`, N+1 without `includes`, callbacks
with hidden side effects, monkey patches changing core behaviour, `rescue` with no class (catches
`StandardError` and hides bugs).

---

## Shell

```bash
shellcheck script.sh
```

Every script gets `set -euo pipefail`. Defects: unquoted `$var` (word splitting and globbing — the single
most common shell bug), `rm -rf "$DIR/"` where `DIR` may be empty, no check that a `cd` succeeded, parsing
`ls` output, missing `--` before user-supplied filenames, a pipeline's failure hidden without `pipefail`,
`eval` on interpolated input, temp files created predictably rather than with `mktemp`.

---

## SQL

Defects: string-built queries; a missing index on a filtered, joined or sorted column; `SELECT *` in
application code (breaks silently when a column is added); implicit type conversion defeating an index;
`NULL` semantics in `NOT IN` (returns no rows if the subquery yields a NULL); `COUNT(column)` vs `COUNT(*)`;
`DELETE`/`UPDATE` with no `WHERE` in a script; a transaction left open; an isolation level that permits the
anomaly the code assumes away; a migration that rewrites a large table under a lock during business hours.

---

## Notebooks (.ipynb)

Treated as software when results depend on them — which, in research repositories, they always do.

Defects: **out-of-order execution** (the saved output does not correspond to top-to-bottom execution — check
the execution counts are monotonic); hidden state from deleted cells; hard-coded absolute paths; no random
seed set; credentials in a cell; large outputs and data committed; no requirements pinned; analysis logic
that exists only in the notebook and cannot be tested. The durable fix: move logic into an importable module,
have the notebook call it, and add `nbstripout` plus an execution check to CI.
