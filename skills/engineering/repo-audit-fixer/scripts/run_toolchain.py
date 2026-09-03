#!/usr/bin/env python3
"""Detect and run a repository's quality gate, then report the result uniformly.

Stages: install, build, lint, typecheck, test, coverage, audit, secrets.

Use it twice: once at Phase 0 for the baseline, once at Phase 8 for the final state.
The two JSON outputs are the before/after table in the audit report.

    python3 run_toolchain.py <path> --stage all --json
    python3 run_toolchain.py <path> --stage test --timeout 900
    python3 run_toolchain.py <path> --dry-run          # show the plan, run nothing

A stage that reports "unavailable" is not a passing stage. Say so in the report.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

STAGES = ("install", "build", "lint", "typecheck", "test", "coverage", "audit", "secrets")


def has(binary: str) -> bool:
    return shutil.which(binary) is not None


def exists(root: Path, *names: str) -> bool:
    return any((root / n).exists() for n in names)


def read(root: Path, name: str) -> str:
    try:
        return (root / name).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def npm_scripts(root: Path) -> dict:
    try:
        return json.loads(read(root, "package.json") or "{}").get("scripts", {}) or {}
    except json.JSONDecodeError:
        return {}


def make_targets(root: Path) -> set[str]:
    targets = set()
    for line in read(root, "Makefile").splitlines():
        if line and not line.startswith("\t") and ":" in line and not line.startswith("."):
            name = line.split(":", 1)[0].strip()
            if name and " " not in name:
                targets.add(name)
    return targets


def plan(root: Path) -> dict[str, list[dict]]:
    """Build the command plan. Repository conventions win over invented commands."""
    commands: dict[str, list[dict]] = {stage: [] for stage in STAGES}

    def add(stage: str, cmd: list[str], why: str, preferred: bool = False) -> None:
        commands[stage].append({"cmd": cmd, "why": why, "preferred": preferred})

    targets = make_targets(root)
    scripts = npm_scripts(root)

    # --- the repository's own task runner comes first ---------------------------------
    for stage, names in (
        ("install", ("install", "deps", "bootstrap", "setup")),
        ("build", ("build", "compile", "all")),
        ("lint", ("lint", "check", "style")),
        ("typecheck", ("typecheck", "types", "mypy")),
        ("test", ("test", "tests", "check")),
        ("coverage", ("coverage", "cov")),
    ):
        if has("make") and (root / "Makefile").exists():
            for name in names:
                if name in targets:
                    add(stage, ["make", name], "repository Makefile target", preferred=True)
                    break
        if scripts:
            runner = "npm"
            if (root / "pnpm-lock.yaml").exists() and has("pnpm"):
                runner = "pnpm"
            elif (root / "yarn.lock").exists() and has("yarn"):
                runner = "yarn"
            for name in names:
                if name in scripts:
                    add(stage, [runner, "run", name], f"package.json script `{name}`", preferred=True)
                    break

    # --- Python -------------------------------------------------------------------------
    if exists(root, "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"):
        if (root / "uv.lock").exists() and has("uv"):
            add("install", ["uv", "sync", "--frozen"], "uv lockfile")
        elif (root / "poetry.lock").exists() and has("poetry"):
            add("install", ["poetry", "install", "--no-interaction"], "poetry lockfile")
        elif (root / "requirements.txt").exists():
            add("install", [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                "requirements.txt")
        if has("ruff"):
            add("lint", ["ruff", "check", "."], "ruff")
        elif has("flake8"):
            add("lint", ["flake8", "."], "flake8")
        if has("mypy") and exists(root, "mypy.ini", ".mypy.ini", "pyproject.toml", "setup.cfg"):
            add("typecheck", ["mypy", "."], "mypy")
        if has("pytest"):
            add("test", ["pytest", "-q", "--maxfail=0"], "pytest")
            add("coverage", ["pytest", "-q", "--cov", "--cov-report=term-missing"], "pytest-cov")
        elif has("python3"):
            add("test", [sys.executable, "-m", "unittest", "discover", "-v"], "unittest discovery")
        if has("pip-audit"):
            add("audit", ["pip-audit", "--progress-spinner=off"], "pip-audit")
        elif has("safety"):
            add("audit", ["safety", "check", "--short-report"], "safety")
        if has("bandit"):
            add("audit", ["bandit", "-r", ".", "-q", "-ll"], "bandit security lint")

    # --- JavaScript / TypeScript ---------------------------------------------------------
    if (root / "package.json").exists():
        if (root / "pnpm-lock.yaml").exists() and has("pnpm"):
            add("install", ["pnpm", "install", "--frozen-lockfile"], "pnpm lockfile")
        elif (root / "yarn.lock").exists() and has("yarn"):
            add("install", ["yarn", "install", "--frozen-lockfile"], "yarn lockfile")
        elif (root / "package-lock.json").exists() and has("npm"):
            add("install", ["npm", "ci"], "npm ci (respects the lockfile)")
        elif has("npm"):
            add("install", ["npm", "install"], "npm install (NO LOCKFILE — this is a finding)")
        if (root / "tsconfig.json").exists() and has("npx"):
            add("typecheck", ["npx", "--no-install", "tsc", "--noEmit"], "tsc")
        if has("npx"):
            add("lint", ["npx", "--no-install", "eslint", "."], "eslint")
        if has("npm"):
            add("audit", ["npm", "audit", "--audit-level=high"], "npm audit")

    # --- other ecosystems -----------------------------------------------------------------
    if (root / "go.mod").exists() and has("go"):
        add("build", ["go", "build", "./..."], "go build")
        add("lint", ["go", "vet", "./..."], "go vet")
        add("test", ["go", "test", "./...", "-race", "-count=1"], "go test with race detector")
        add("coverage", ["go", "test", "./...", "-cover"], "go cover")
        if has("govulncheck"):
            add("audit", ["govulncheck", "./..."], "govulncheck")

    if (root / "Cargo.toml").exists() and has("cargo"):
        add("build", ["cargo", "build", "--all-targets"], "cargo build")
        add("lint", ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"], "clippy")
        add("test", ["cargo", "test"], "cargo test")
        if has("cargo-audit"):
            add("audit", ["cargo", "audit"], "cargo audit")

    if (root / "pom.xml").exists():
        mvn = "./mvnw" if (root / "mvnw").exists() else ("mvn" if has("mvn") else None)
        if mvn:
            add("build", [mvn, "-B", "-q", "compile"], "maven compile")
            add("test", [mvn, "-B", "test"], "maven test")
    if exists(root, "build.gradle", "build.gradle.kts"):
        gradle = "./gradlew" if (root / "gradlew").exists() else ("gradle" if has("gradle") else None)
        if gradle:
            add("build", [gradle, "build", "-x", "test"], "gradle build")
            add("test", [gradle, "test"], "gradle test")

    if any(root.glob("*.csproj")) or any(root.glob("*.sln")):
        if has("dotnet"):
            add("build", ["dotnet", "build", "--nologo"], "dotnet build")
            add("test", ["dotnet", "test", "--nologo"], "dotnet test")
            add("audit", ["dotnet", "list", "package", "--vulnerable", "--include-transitive"],
                "dotnet vulnerable packages")

    if (root / "Gemfile").exists() and has("bundle"):
        add("install", ["bundle", "install"], "bundler")
        add("test", ["bundle", "exec", "rspec"], "rspec")
        if has("bundle-audit"):
            add("audit", ["bundle-audit", "check"], "bundler-audit")

    if (root / "composer.json").exists() and has("composer"):
        add("install", ["composer", "install", "--no-interaction"], "composer")
        add("audit", ["composer", "audit"], "composer audit")

    # --- cross-cutting ---------------------------------------------------------------------
    for binary, cmd, why in (
        ("osv-scanner", ["osv-scanner", "-r", "."], "OSV across every lockfile"),
        ("trivy", ["trivy", "fs", "--scanners", "vuln", "--quiet", "."], "trivy filesystem scan"),
    ):
        if has(binary):
            add("audit", cmd, why)

    for binary, cmd, why in (
        ("gitleaks", ["gitleaks", "detect", "--no-banner", "--redact"], "gitleaks (working tree + history)"),
        ("trufflehog", ["trufflehog", "filesystem", ".", "--no-update"], "trufflehog"),
    ):
        if has(binary):
            add("secrets", cmd, why)

    if any(root.glob("**/Dockerfile")) and has("hadolint"):
        add("lint", ["hadolint"] + [str(p) for p in list(root.glob("**/Dockerfile"))[:10]],
            "hadolint")

    if has("shellcheck"):
        shells = [str(p) for p in list(root.glob("**/*.sh"))[:50]
                  if "node_modules" not in str(p) and ".git" not in str(p)]
        if shells:
            add("lint", ["shellcheck"] + shells, "shellcheck")

    return commands


def choose(entries: list[dict]) -> list[dict]:
    """Preferred (repository-native) commands win; otherwise run everything detected."""
    preferred = [e for e in entries if e["preferred"]]
    return preferred if preferred else entries


def run(root: Path, stage: str, entry: dict, timeout: int) -> dict:
    started = time.monotonic()
    env = {**os.environ, "CI": "1", "NO_COLOR": "1", "FORCE_COLOR": "0",
           "PYTHONUNBUFFERED": "1"}
    try:
        proc = subprocess.run(
            entry["cmd"], cwd=root, capture_output=True, text=True,
            timeout=timeout, env=env, check=False,
        )
        stdout, stderr, code, status = proc.stdout, proc.stderr, proc.returncode, "ok"
    except subprocess.TimeoutExpired:
        stdout, stderr, code, status = "", f"timed out after {timeout}s", None, "timeout"
    except FileNotFoundError:
        stdout, stderr, code, status = "", f"command not found: {entry['cmd'][0]}", None, "unavailable"
    except OSError as exc:
        stdout, stderr, code, status = "", str(exc), None, "error"

    combined = (stdout + "\n" + stderr).strip()
    return {
        "stage": stage,
        "command": " ".join(entry["cmd"]),
        "why": entry["why"],
        "status": status if status != "ok" else ("passed" if code == 0 else "failed"),
        "exit_code": code,
        "duration_s": round(time.monotonic() - started, 1),
        "output_lines": len(combined.splitlines()),
        "output_tail": "\n".join(combined.splitlines()[-60:]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--stage", default="all", choices=("all", *STAGES),
                        help="stage to run (default: all)")
    parser.add_argument("--timeout", type=int, default=900, help="per-command timeout in seconds")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and exit")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    commands = plan(root)
    stages = STAGES if args.stage == "all" else (args.stage,)

    if args.dry_run:
        for stage in stages:
            chosen = choose(commands[stage])
            print(f"\n{stage}")
            if not chosen:
                print("  (nothing detected — record this as a gap in the report)")
            for entry in chosen:
                print(f"  $ {' '.join(entry['cmd'])}   # {entry['why']}")
        return 0

    results, missing = [], []
    for stage in stages:
        chosen = choose(commands[stage])
        if not chosen:
            missing.append(stage)
            continue
        for entry in chosen:
            result = run(root, stage, entry, args.timeout)
            results.append(result)
            if not args.json:
                icon = {"passed": "PASS", "failed": "FAIL", "timeout": "TIME",
                        "unavailable": "N/A ", "error": "ERR "}[result["status"]]
                print(f"[{icon}] {stage:<10} {result['command'][:78]}  ({result['duration_s']}s)")
                if result["status"] in ("failed", "timeout", "error"):
                    for line in result["output_tail"].splitlines()[-20:]:
                        print(f"         | {line}")

    summary = {
        "root": str(root.resolve()),
        "stages_run": sorted({r["stage"] for r in results}),
        "stages_with_no_tooling": missing,
        "passed": sum(1 for r in results if r["status"] == "passed"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "unavailable": sum(1 for r in results if r["status"] in ("unavailable", "timeout", "error")),
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"\n{summary['passed']} passed · {summary['failed']} failed · "
              f"{summary['unavailable']} could not run")
        if missing:
            print("No tooling detected for: " + ", ".join(missing))
            print("A stage with no tooling is a BUILD finding, not a pass.")

    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
