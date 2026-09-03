# Recommended skills

Eight Anthropic built-in skills are enabled on the account, four skills are owned and live
in this repository, and the Claude Code harness ships another sixteen that need no
enabling at all. The gaps are small — and most of what is missing is better written than
installed, because a skill that encodes *your* standards beats a generic one.

---

## Built-in skills already enabled

`skill-creator` · `canvas-design` · `docx` · `xlsx` · `pptx` · `pdf` · `import-memory` · `morning`

Nothing here is redundant. `pdf` and `xlsx` in particular are load-bearing: the paper
auditors use `pdf` to read reference PDFs, and `xlsx` handles the data files that arrive
from collaborators.

## Available in Claude Code without enabling anything

These ship with the harness. Worth knowing they exist, because they are easy to forget:

| Skill | Use it for |
|---|---|
| `code-review` | A review of the current diff or a PR, at a chosen effort level |
| `security-review` | A security pass over pending changes on a branch |
| `simplify` | Reuse, simplification and efficiency cleanups — quality only, not bug hunting |
| `run` | Launching a project to see a change working, rather than trusting the tests |
| `init` | Generating a `CLAUDE.md` for a repository |
| `dataviz` | **Load before writing any chart code.** It is the difference between a chart and a good chart |
| `loop` | Running something on a recurring interval |
| `update-config` | Hooks, permissions and settings in `settings.json` |
| `fewer-permission-prompts` | Building an allowlist from your own transcripts |
| `claude-api` | Reference for the Claude API — model IDs, pricing, caching, tool use |

`repo-audit-fixer` leans on `run`, `code-review`, `security-review`, `dataviz` and `pdf`
by name. They are not optional extras to it; they are part of how it works.

---

## Worth adding, from plugins

Standalone additions in the Anthropic catalogue are thin for this profile — the useful
engineering and data skills arrive **bundled in plugins**, which is where to get them. See
[`plugins.md`](plugins.md); the short version:

- `engineering` → `code-review`, `debug`, `testing-strategy`, `tech-debt`, `architecture`
- `data` → `statistical-analysis`, `validate-data`, `explore-data`, `sql-queries`
- `bio-research` → `nextflow-development`, `scientific-problem-selection`

---

## Worth writing — the higher-value path

Every skill in this repository exists because a generic tool did not encode the standard
being applied. That is the pattern to keep following. Four candidates, in the order they
would pay off:

### 1. `dicei-data-guardian`
A skill for the vaccine-safety and surveillance repositories that encodes, in one place:
the de-identification rules, the ALCOA+ data-integrity expectations, the audit-trail
requirements, and the specific checks that must pass before any export leaves the
institution. `repo-audit-fixer` treats `PRIV` findings as Critical for these projects, but
it cannot know *your* institutional rules — a dedicated skill can.

**Highest value of the four.** It is the domain where a mistake is most expensive and
where generic tooling helps least.

### 2. `ml-experiment-auditor`
The ML analogue of `q1-paper-auditor`, aimed at the model rather than the manuscript: data
leakage across the split, group leakage, a threshold chosen on the test set, a metric that
does not suit the target's imbalance, an absent seed, a non-reproducible environment.
Relevant to `mortality-ami-predictor`, `Hybrid-Modeling` and `ML_tool`.

Today `repo-audit-fixer`'s data/ML section in `stack-playbooks.md` covers the ground; a
dedicated skill would go deeper and could actually re-run the training to check.

### 3. `project-bootstrapper`
Scaffolds a new repository already carrying everything the audit skill checks for: the
quality gate, the CI workflow, the lockfile, the `LICENSE`, the `Reports/` directory, the
`CLAUDE.md`. Prevention rather than repair — this is the shape of `repo-audit-fixer` run
backwards, and it stops the same findings recurring in every new project.

### 4. `spanish-technical-writer`
The academic and institutional output here is bilingual. A skill holding the Spanish
technical register, the terminology decisions, and the parity rules between language
versions would stop the same choices being re-made every time.

Use the enabled **`skill-creator`** skill to build any of these — it also runs evals, which
is how you find out whether a skill actually triggers when it should.

---

## Deliberately not recommended

**Do not enable skills you will not use.** Every enabled skill occupies attention in every
session; a long list of near-misses makes the right one harder to reach. The account's
current set is well chosen — the recommendation is to keep it small and write what is
missing.
