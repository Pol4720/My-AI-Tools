#!/usr/bin/env python3
"""Inventory a repository before auditing it.

Reports languages and line counts, package manifests, build systems, test frameworks,
CI definitions, entry points, container and IaC files, database migrations, lockfile
health, and churn/complexity hotspots.

Standard library only. Run it first, read it before forming any opinion.

    python3 repo_recon.py <path> [--json] [--top 25]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

# --------------------------------------------------------------------------------------
# Classification tables
# --------------------------------------------------------------------------------------

LANGUAGES = {
    ".py": "Python", ".pyi": "Python", ".ipynb": "Jupyter Notebook",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala", ".groovy": "Groovy",
    ".go": "Go", ".rs": "Rust",
    ".c": "C", ".h": "C/C++ header", ".cc": "C++", ".cpp": "C++", ".cxx": "C++", ".hpp": "C++",
    ".cs": "C#", ".fs": "F#", ".vb": "Visual Basic",
    ".rb": "Ruby", ".php": "PHP", ".pl": "Perl", ".lua": "Lua",
    ".swift": "Swift", ".m": "Objective-C", ".mm": "Objective-C++", ".dart": "Dart",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".ps1": "PowerShell",
    ".sql": "SQL", ".r": "R", ".jl": "Julia", ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang",
    ".html": "HTML", ".htm": "HTML", ".css": "CSS", ".scss": "SCSS", ".sass": "SCSS", ".less": "Less",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro",
    ".tf": "Terraform", ".tfvars": "Terraform", ".hcl": "HCL",
    ".yml": "YAML", ".yaml": "YAML", ".json": "JSON", ".toml": "TOML", ".xml": "XML",
    ".md": "Markdown", ".rst": "reStructuredText", ".tex": "LaTeX",
    ".proto": "Protocol Buffers", ".graphql": "GraphQL", ".gql": "GraphQL",
}

# Source languages, as opposed to config/docs/markup. Used for the "code" totals.
CODE_LANGUAGES = {
    "Python", "Jupyter Notebook", "JavaScript", "TypeScript", "Java", "Kotlin", "Scala",
    "Groovy", "Go", "Rust", "C", "C++", "C/C++ header", "C#", "F#", "Visual Basic", "Ruby",
    "PHP", "Perl", "Lua", "Swift", "Objective-C", "Objective-C++", "Dart", "Shell",
    "PowerShell", "SQL", "R", "Julia", "Elixir", "Erlang", "Vue", "Svelte", "Astro",
}

MANIFESTS = {
    "pyproject.toml": ("Python", "PEP 621 / poetry / uv"),
    "setup.py": ("Python", "setuptools (legacy)"),
    "setup.cfg": ("Python", "setuptools"),
    "requirements.txt": ("Python", "pip"),
    "Pipfile": ("Python", "pipenv"),
    "environment.yml": ("Python", "conda"),
    "package.json": ("JavaScript/TypeScript", "npm/yarn/pnpm/bun"),
    "deno.json": ("TypeScript", "deno"),
    "pom.xml": ("Java", "Maven"),
    "build.gradle": ("Java/Kotlin", "Gradle"),
    "build.gradle.kts": ("Kotlin", "Gradle"),
    "go.mod": ("Go", "go modules"),
    "Cargo.toml": ("Rust", "cargo"),
    "composer.json": ("PHP", "composer"),
    "Gemfile": ("Ruby", "bundler"),
    "pubspec.yaml": ("Dart/Flutter", "pub"),
    "CMakeLists.txt": ("C/C++", "CMake"),
    "Makefile": ("any", "make"),
    "justfile": ("any", "just"),
    "Taskfile.yml": ("any", "task"),
    "mix.exs": ("Elixir", "mix"),
    "DESCRIPTION": ("R", "R package"),
}

LOCKFILES = {
    "poetry.lock": "pyproject.toml",
    "uv.lock": "pyproject.toml",
    "Pipfile.lock": "Pipfile",
    "package-lock.json": "package.json",
    "yarn.lock": "package.json",
    "pnpm-lock.yaml": "package.json",
    "bun.lockb": "package.json",
    "Cargo.lock": "Cargo.toml",
    "go.sum": "go.mod",
    "composer.lock": "composer.json",
    "Gemfile.lock": "Gemfile",
    "pubspec.lock": "pubspec.yaml",
}

TEST_MARKERS = {
    "pytest": [r"^\s*import pytest", r"^\s*\[tool\.pytest", r"pytest\.ini", r"conftest\.py"],
    "unittest": [r"^\s*import unittest", r"unittest\.TestCase"],
    "jest": [r'"jest"', r"jest\.config"],
    "vitest": [r'"vitest"', r"vitest\.config"],
    "mocha": [r'"mocha"'],
    "playwright": [r"@playwright/test", r"playwright\.config"],
    "cypress": [r"cypress\.config", r'"cypress"'],
    "junit": [r"org\.junit", r"<artifactId>junit"],
    "go test": [r"^func Test[A-Z]"],
    "cargo test": [r"#\[test\]", r"#\[cfg\(test\)\]"],
    "rspec": [r"^\s*require ['\"]rspec"],
    "phpunit": [r"PHPUnit\\Framework"],
    "xunit/nunit": [r"using Xunit", r"using NUnit"],
}

CI_FILES = [
    (".github/workflows", "GitHub Actions"),
    (".gitlab-ci.yml", "GitLab CI"),
    ("Jenkinsfile", "Jenkins"),
    (".circleci/config.yml", "CircleCI"),
    ("azure-pipelines.yml", "Azure Pipelines"),
    (".travis.yml", "Travis CI"),
    ("bitbucket-pipelines.yml", "Bitbucket Pipelines"),
    (".drone.yml", "Drone"),
]

CONTAINER_PATTERNS = ["Dockerfile", "Dockerfile.*", "*.dockerfile", "docker-compose*.yml",
                      "docker-compose*.yaml", "compose.yml", "compose.yaml"]

IAC_PATTERNS = ["*.tf", "*.tfvars", "*.bicep", "serverless.yml", "template.yaml",
                "Chart.yaml", "kustomization.yaml", "ansible.cfg", "playbook*.yml"]

MIGRATION_DIR_NAMES = {"migrations", "migration", "alembic", "versions", "db/migrate",
                       "changelog", "liquibase", "flyway"}

ENTRYPOINT_PATTERNS = [
    (r'if __name__ == ["\']__main__["\']', "Python __main__"),
    (r"^\s*func main\s*\(", "Go main"),
    (r"^\s*fn main\s*\(", "Rust main"),
    (r"public static void main", "Java main"),
    (r'"bin"\s*:', "npm bin"),
    (r"^\s*ENTRYPOINT|^\s*CMD ", "container entrypoint"),
    (r"\[project\.scripts\]|console_scripts", "installed console script"),
]

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "out", "target",
    "__pycache__", ".venv", "venv", "env", ".env", ".tox", ".nox", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".gradle", ".idea", ".vscode", "coverage",
    "htmlcov", ".next", ".nuxt", ".svelte-kit", ".terraform", "Pods", "DerivedData",
    "site-packages", ".cache", "bower_components", ".parcel-cache", ".turbo",
}

BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp", ".pdf", ".zip",
    ".gz", ".tar", ".bz2", ".xz", ".7z", ".jar", ".war", ".class", ".so", ".dylib",
    ".dll", ".exe", ".bin", ".o", ".a", ".pyc", ".pyd", ".wasm", ".woff", ".woff2",
    ".ttf", ".eot", ".mp3", ".mp4", ".mov", ".avi", ".parquet", ".db", ".sqlite",
    ".sqlite3", ".pkl", ".pickle", ".h5", ".npz", ".npy", ".onnx", ".pt", ".pth",
}

MAX_SCAN_BYTES = 2_000_000  # skip pathological files when counting/searching


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def walk(root: Path):
    """Yield every non-skipped file under root."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".egg-info")]
        for name in filenames:
            yield Path(dirpath) / name


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_SCAN_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return ""


def count_lines(path: Path) -> int:
    try:
        if path.stat().st_size > MAX_SCAN_BYTES:
            return 0
        with path.open("rb") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def git(root: Path, *args: str) -> str:
    try:
        res = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=60, check=False,
        )
        return res.stdout if res.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


# --------------------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------------------

def analyse(root: Path, top: int) -> dict:
    files = list(walk(root))
    rel = lambda p: str(p.relative_to(root))  # noqa: E731

    lang_files: Counter[str] = Counter()
    lang_lines: Counter[str] = Counter()
    largest: list[tuple[int, str]] = []
    text_files: list[Path] = []

    for path in files:
        suffix = path.suffix.lower()
        if suffix in BINARY_SUFFIXES:
            continue
        lang = LANGUAGES.get(suffix)
        lines = count_lines(path)
        if lang:
            lang_files[lang] += 1
            lang_lines[lang] += lines
            if lang in CODE_LANGUAGES:
                largest.append((lines, rel(path)))
        if suffix not in BINARY_SUFFIXES:
            text_files.append(path)

    # --- manifests, lockfiles, task runners -------------------------------------------
    manifests, lockfiles = [], []
    present_names = {p.name for p in files}
    for path in files:
        if path.name in MANIFESTS:
            ecosystem, tool = MANIFESTS[path.name]
            manifests.append({"file": rel(path), "ecosystem": ecosystem, "tool": tool})
        if path.name in LOCKFILES:
            lockfiles.append({"file": rel(path), "locks": LOCKFILES[path.name]})

    unlocked = []
    for manifest in manifests:
        name = Path(manifest["file"]).name
        expected = [lock for lock, target in LOCKFILES.items() if target == name]
        if expected and not any(e in present_names for e in expected):
            unlocked.append({"manifest": manifest["file"], "expected_one_of": expected})

    # --- CI ----------------------------------------------------------------------------
    ci = []
    for candidate, system in CI_FILES:
        target = root / candidate
        if target.is_dir():
            workflows = sorted(rel(p) for p in target.iterdir() if p.suffix in (".yml", ".yaml"))
            if workflows:
                ci.append({"system": system, "files": workflows})
        elif target.exists():
            ci.append({"system": system, "files": [candidate]})

    # --- containers, IaC, migrations ---------------------------------------------------
    containers, iac = [], []
    for path in files:
        if any(path.match(pat) for pat in CONTAINER_PATTERNS):
            containers.append(rel(path))
        if any(path.match(pat) for pat in IAC_PATTERNS):
            iac.append(rel(path))

    migrations: dict[str, int] = defaultdict(int)
    for path in files:
        parts = {p.lower() for p in path.relative_to(root).parts[:-1]}
        hit = parts & MIGRATION_DIR_NAMES
        if hit:
            migrations[sorted(hit)[0]] += 1

    # --- tests, entry points -----------------------------------------------------------
    frameworks: set[str] = set()
    entrypoints: list[dict] = []
    test_files = 0
    for path in text_files:
        name = path.name.lower()
        relpath = rel(path)
        if ("test" in name or "spec" in name
                or any(part.lower() in ("test", "tests", "spec", "specs", "__tests__")
                       for part in path.relative_to(root).parts[:-1])):
            if path.suffix.lower() in LANGUAGES:
                test_files += 1
        if path.suffix.lower() not in LANGUAGES and path.name not in MANIFESTS:
            continue
        content = read_text(path)
        if not content:
            continue
        for framework, patterns in TEST_MARKERS.items():
            if framework in frameworks:
                continue
            if any(re.search(p, content, re.MULTILINE) for p in patterns):
                frameworks.add(framework)
        for pattern, label in ENTRYPOINT_PATTERNS:
            if re.search(pattern, content, re.MULTILINE):
                entrypoints.append({"file": relpath, "kind": label})
                break

    # --- documentation -----------------------------------------------------------------
    docs = sorted(
        rel(p) for p in files
        if p.suffix.lower() in (".md", ".rst", ".adoc")
        and (p.parent == root or "doc" in str(p.parent).lower())
    )

    # --- git history --------------------------------------------------------------------
    is_git = (root / ".git").exists()
    history: dict = {"is_git_repo": is_git}
    if is_git:
        history["current_branch"] = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
        history["head"] = git(root, "rev-parse", "HEAD").strip()[:12]
        status = git(root, "status", "--porcelain")
        history["dirty"] = bool(status.strip())
        history["uncommitted_files"] = len([ln for ln in status.splitlines() if ln.strip()])
        history["commits"] = len(git(root, "log", "--oneline", "-n", "10000").splitlines())
        churn = Counter(
            line for line in git(root, "log", "--format=", "--name-only", "-n", "500").splitlines()
            if line.strip()
        )
        history["churn_hotspots"] = [
            {"file": f, "changes": n} for f, n in churn.most_common(top)
            if not any(part in SKIP_DIRS for part in Path(f).parts)
        ][:top]

    largest.sort(reverse=True)
    total_code_lines = sum(n for lang, n in lang_lines.items() if lang in CODE_LANGUAGES)

    # --- things whose absence is itself a finding ---------------------------------------
    gaps = []
    if not frameworks and test_files == 0:
        gaps.append("No test framework detected and no test files found.")
    if not ci:
        gaps.append("No CI configuration found — nothing enforces a quality gate.")
    if unlocked:
        gaps.append(f"{len(unlocked)} manifest(s) with no lockfile — the build is not reproducible.")
    root_names = {p.name for p in files if p.parent == root}
    if not any(n.lower().startswith("readme") for n in root_names):
        gaps.append("No README at the repository root.")
    if not any(n.split(".")[0].upper() in ("LICENSE", "LICENCE", "COPYING") for n in root_names):
        gaps.append("No LICENSE file at the repository root.")
    if is_git and history.get("dirty"):
        gaps.append("Working tree is dirty — do not start editing until this is resolved.")
    if containers and not (root / ".dockerignore").exists():
        gaps.append("Dockerfile present but no .dockerignore — the build context may ship secrets.")

    return {
        "root": str(root.resolve()),
        "totals": {
            "files_scanned": len(files),
            "code_lines": total_code_lines,
            "test_files": test_files,
        },
        "languages": [
            {"language": lang, "files": lang_files[lang], "lines": lang_lines[lang]}
            for lang, _ in lang_lines.most_common()
        ],
        "manifests": manifests,
        "lockfiles": lockfiles,
        "manifests_without_lockfile": unlocked,
        "ci": ci,
        "containers": sorted(set(containers)),
        "infrastructure_as_code": sorted(set(iac)),
        "migrations": [{"directory": k, "files": v} for k, v in sorted(migrations.items())],
        "test_frameworks": sorted(frameworks),
        "entrypoints": entrypoints[:top],
        "documentation": docs[:top],
        "largest_source_files": [{"lines": n, "file": f} for n, f in largest[:top]],
        "git": history,
        "gaps": gaps,
    }


# --------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------

def render(report: dict) -> str:
    out: list[str] = []
    add = out.append

    def section(title: str) -> None:
        add("")
        add(title)
        add("-" * len(title))

    add(f"Repository recon — {report['root']}")
    t = report["totals"]
    add(f"{t['files_scanned']} files scanned · {t['code_lines']:,} lines of code · "
        f"{t['test_files']} test files")

    if report["gaps"]:
        section("Immediate observations")
        for gap in report["gaps"]:
            add(f"  ! {gap}")

    section("Languages")
    for row in report["languages"][:15]:
        add(f"  {row['language']:<22} {row['files']:>5} files  {row['lines']:>9,} lines")

    if report["manifests"]:
        section("Package manifests")
        for m in report["manifests"]:
            add(f"  {m['file']:<40} {m['ecosystem']} ({m['tool']})")
    if report["manifests_without_lockfile"]:
        add("  Missing lockfiles:")
        for m in report["manifests_without_lockfile"]:
            add(f"    {m['manifest']} — expected one of {', '.join(m['expected_one_of'])}")

    if report["ci"]:
        section("Continuous integration")
        for c in report["ci"]:
            add(f"  {c['system']}: {', '.join(c['files'][:6])}")

    if report["test_frameworks"]:
        section("Test frameworks")
        add("  " + ", ".join(report["test_frameworks"]))

    if report["entrypoints"]:
        section("Entry points")
        for e in report["entrypoints"]:
            add(f"  {e['file']:<50} {e['kind']}")

    if report["containers"] or report["infrastructure_as_code"]:
        section("Deployment surface")
        for f in report["containers"]:
            add(f"  container  {f}")
        for f in report["infrastructure_as_code"][:20]:
            add(f"  iac        {f}")

    if report["migrations"]:
        section("Database migrations")
        for m in report["migrations"]:
            add(f"  {m['directory']}: {m['files']} files")

    if report["largest_source_files"]:
        section("Largest source files (read these first)")
        for f in report["largest_source_files"][:12]:
            add(f"  {f['lines']:>7,}  {f['file']}")

    g = report["git"]
    if g.get("is_git_repo"):
        section("Git")
        add(f"  branch {g.get('current_branch')} @ {g.get('head')} · "
            f"{g.get('commits')} commits · dirty: {g.get('dirty')}")
        if g.get("churn_hotspots"):
            add("  Churn hotspots (cross-reference with complexity — bugs live here):")
            for h in g["churn_hotspots"][:10]:
                add(f"    {h['changes']:>4}  {h['file']}")

    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    parser.add_argument("--top", type=int, default=25, help="entries per ranked list (default: 25)")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    report = analyse(root, args.top)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
