# Tooling catalog — Phases 0, 2 and 8

What to run, per ecosystem, and which standard applies. Tools are an accelerator, never the audit itself:
they find the mechanical defects cheaply so that your attention goes to the ones only a reader can find.

**Rules for using them.**

- **Every tool output is a lead, not a finding.** Verify before it enters the ledger. Static analysers have
  false-positive rates that would embarrass any other measuring instrument.
- **Prefer what the repository already configures.** If it uses `ruff`, do not introduce `flake8`. Adding a
  new analyser produces a wall of pre-existing findings that buries the real ones.
- **Never install a tool into the user's project** as a side effect. Run it with `npx`/`uvx`/`pipx`, or note
  that it was unavailable.
- **If a tool is unavailable in the environment, say so in the report** rather than silently skipping the
  check. A skipped check reported as a pass is a lie.

---

## By ecosystem

| Ecosystem | Lint | Types | Test | Coverage | Security | Dependencies |
|---|---|---|---|---|---|---|
| Python | `ruff`, `pylint` | `mypy`, `pyright` | `pytest` | `coverage.py` | `bandit`, `semgrep` | `pip-audit`, `safety`, `deptry` |
| JS/TS | `eslint`, `oxlint` | `tsc --noEmit` | `vitest`, `jest` | `c8`, `istanbul` | `semgrep`, `eslint-plugin-security` | `npm audit`, `osv-scanner`, `depcheck`, `knip` |
| Java/Kotlin | `checkstyle`, `pmd`, `detekt` | compiler + `errorprone` | JUnit | JaCoCo | `spotbugs`+`find-sec-bugs` | OWASP `dependency-check` |
| Go | `golangci-lint`, `staticcheck` | compiler | `go test -race` | `go test -cover` | `gosec` | `govulncheck`, `nancy` |
| Rust | `clippy -D warnings` | compiler | `cargo test` | `cargo llvm-cov` | `cargo geiger` | `cargo audit`, `cargo deny` |
| C/C++ | `clang-tidy`, `cppcheck` | compiler `-Wall -Wextra -Werror` | ctest, gtest | `gcov`/`lcov` | ASan/UBSan/TSan, `flawfinder` | `conan`/`vcpkg` audit |
| C#/.NET | analyzers, `dotnet format` | Roslyn + nullable | `dotnet test` | coverlet | `security-scan` | `dotnet list package --vulnerable` |
| PHP | PHP_CodeSniffer | PHPStan, Psalm | PHPUnit | Xdebug | `psalm --taint-analysis` | `composer audit` |
| Ruby | RuboCop | Sorbet, RBS | RSpec, minitest | SimpleCov | Brakeman | `bundle audit` |
| Shell | `shellcheck` | — | `bats` | — | `shellcheck` | — |
| SQL | `sqlfluff` | — | `pgTAP` | — | — | — |
| Terraform | `tflint`, `terraform validate` | — | `terratest` | — | `checkov`, `tfsec`, `trivy config` | `terraform providers lock` |
| Docker | `hadolint` | — | — | — | `trivy image`, `grype`, `dockle` | `trivy` SBOM |
| Kubernetes | `kubeconform`, `kube-linter` | — | — | — | `kubesec`, `trivy config` | — |

**Cross-language, worth reaching for on any repository**

| Tool | Use |
|---|---|
| `semgrep --config=auto` | Multi-language pattern-based SAST. High value, low setup. |
| `osv-scanner -r .` | Vulnerabilities across every lockfile in a polyglot repository, in one pass. |
| `trivy fs .` | Vulnerabilities, secrets, misconfiguration and licences in one sweep. |
| `gitleaks detect` / `trufflehog` | Secrets in the working tree **and in git history**. Always run both scopes. |
| `syft` | Generate an SBOM — useful evidence for the report in regulated contexts. |
| `scc` / `tokei` | Language breakdown and complexity, for Phase 0 recon. |
| `lizard` | Cyclomatic complexity across many languages; finds the functions to read first. |
| `jscpd` | Copy-paste detection across languages — feeds the "defect family" hunt directly. |
| `git log --format= --name-only \| sort \| uniq -c \| sort -rn` | Churn hotspots. High-churn plus high-complexity is where the bugs are. |
| `licensee` / `pip-licenses` / `license-checker` | `LICENSE` findings. |

---

## Standards to audit against

Cite the specific clause in the report; a finding tied to a named standard carries weight a bare opinion does not.

| Domain | Standard | Use it for |
|---|---|---|
| Web security | **OWASP Top 10** (2021) and **OWASP ASVS 4.x** | ASVS is a checklist; walk the level that matches the app's risk |
| API security | **OWASP API Security Top 10** | Object-level authorisation, mass assignment, resource consumption |
| Defect classes | **CWE Top 25** | The `category` codes in `defect-taxonomy.md` map to CWE |
| Containers/CI | **CIS Benchmarks**, **SLSA** | Image hardening, build provenance |
| Dependencies | **OpenSSF Scorecard** | Maintenance health of what you depend on |
| Accessibility | **WCAG 2.2 AA** | Every user-facing interface |
| Health data | **HIPAA Security Rule**, **GDPR Art. 32**, local health-data law | Any repository touching clinical or personal data |
| Clinical research | **GCP (ICH E6)**, **21 CFR Part 11** where applicable | Audit trail, electronic records, data integrity (**ALCOA+**) |
| ML systems | **model cards**, **datasheets for datasets**, TRIPOD-AI / CONSORT-AI for clinical prediction | Documentation completeness for a model that informs decisions |
| Licensing | **SPDX** identifiers | Compatibility between the project licence and its dependencies |

**Note for Pol4720's typical repositories.** Vaccine-safety, surveillance and clinical-prediction code is
usually subject to ALCOA+ data-integrity expectations and to personal-data law. In those repositories treat
`PRIV` findings (identifiers in logs, fixtures, exports or error payloads) and audit-trail gaps as `Critical`,
and check that any de-identification step is applied on **every** export path, not just the main one.

---

## Web research in Phase 2

Where to look, and what makes a source usable in the report:

| Question | Source |
|---|---|
| Is this dependency version vulnerable? | GitHub Advisory Database, OSV.dev, NVD, the ecosystem's own advisory feed |
| Is this API deprecated? | The library's own current documentation and changelog — not a tutorial, not Stack Overflow |
| Is this still the recommended pattern? | The framework's official docs for the **installed major version** |
| What is the current stable version? | The package registry (PyPI, npm, crates.io, Maven Central) |
| Is this a known footgun? | The project's issue tracker — search closed issues for the symptom |
| What does the standard actually require? | The standard's own text, cited by clause |

Every finding sourced from the web carries its URL and the date you fetched it. Advisories change; a report
that cannot be re-checked cannot be trusted a year from now.

---

## Interpreting a coverage number

Coverage is a *floor*, not a target, and it is routinely misread. Two rules:

1. **Line coverage overstates.** A line executed is not a line verified — a test with no assertion covers
   perfectly. Read the assertions, not the percentage.
2. **The interesting number is the delta on the lines you changed.** Global coverage moving from 71% to 72%
   tells you nothing; every line of the fix being covered tells you the fix is tested.

Where coverage genuinely earns its keep in an audit: finding **entire files and error branches at 0%**, which
is Phase 5's "wired but dead" and "unhandled branches" evidence.
