#!/usr/bin/env python3
"""Find what was never finished.

Detects abandoned-work markers, explicit unimplemented raises, stub bodies, swallowed
exceptions, discarded errors, non-exhaustive dispatch, commented-out code blocks and
other shapes of incompleteness across many languages.

Every hit is a LEAD, not a finding. Triage each one: is it reachable, is it behind a
documented promise, and how old is it? See references/incompleteness-hunting.md.

Standard library only.

    python3 incompleteness_scan.py <path> [--json] [--severity major] [--include-tests]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "out", "target",
    "__pycache__", ".venv", "venv", "env", ".tox", ".nox", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".gradle", ".idea", ".vscode", "coverage", "htmlcov", ".next", ".nuxt",
    ".svelte-kit", ".terraform", "Pods", "site-packages", ".cache", "bower_components",
    "migrations", ".turbo", "__snapshots__",
}

SOURCE_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue",
    ".svelte", ".java", ".kt", ".kts", ".scala", ".go", ".rs", ".c", ".h", ".cc", ".cpp",
    ".cxx", ".hpp", ".cs", ".rb", ".php", ".swift", ".m", ".mm", ".dart", ".sh", ".bash",
    ".sql", ".r", ".jl", ".ex", ".exs", ".lua", ".pl", ".tf", ".ps1",
}

MAX_BYTES = 2_000_000

# ---------------------------------------------------------------------------------------
# Rules
#
# severity is the *starting* severity for triage, not the final one. Reachability and
# whether the gap sits behind a documented promise decide the real severity.
# ---------------------------------------------------------------------------------------

Rule = tuple[str, str, str, str]  # (code, severity, description, regex)

RULES: list[Rule] = [
    # --- explicit abandonment ---------------------------------------------------------
    ("MARK-FIXME", "major", "FIXME/BUG/HACK/XXX marker — the author recorded a defect here",
     r"(?://|#|--|/\*|\*|<!--)\s*(FIXME|BUG|HACK|XXX|BROKEN|WORKAROUND)\b"),
    ("MARK-TODO", "minor", "TODO/WIP marker — unfinished work",
     r"(?://|#|--|/\*|\*|<!--)\s*(TODO|WIP|TBD|PENDING|POR HACER|PENDIENTE)\b"),
    ("MARK-TEMP", "major", "Temporary-by-intention code, which is usually permanent",
     r"(?://|#|--|/\*|\*)\s*(temporary|temporarily|for now|por ahora|provisional|quick fix|placeholder)\b"),

    # --- explicit unimplemented -------------------------------------------------------
    ("STUB-RAISE", "major", "Explicitly unimplemented — reaching this raises",
     r"\b(NotImplementedError|NotImplementedException|UnsupportedOperationException"
     r"|todo!\(\)|unimplemented!\(\)|raise NotImplemented\b"
     r"|panic!?\(\s*[\"'](?:not implemented|unimplemented|TODO)"
     r"|fatalError\(\s*[\"'](?:not implemented|unimplemented))"),

    # --- stub bodies ------------------------------------------------------------------
    ("STUB-PASS", "minor", "Function body is only `pass` — a stub or a silent no-op",
     r"^[ \t]*def\s+\w+\s*\([^)]*\)\s*(?:->\s*[^:]+)?:\s*(?:\n[ \t]*(?:\"\"\"(?:[^\"]|\"(?!\"\"))*\"\"\"|'''(?:[^']|'(?!''))*''')\s*)?\n[ \t]+pass\s*$"),
    ("STUB-ELLIPSIS", "minor", "Function body is only `...` — a stub outside a .pyi stub file",
     r"^[ \t]*def\s+\w+\s*\([^)]*\)\s*(?:->\s*[^:]+)?:\s*\n[ \t]+\.\.\.\s*$"),
    ("STUB-EMPTY-BLOCK", "minor", "Empty function or method body",
     r"\b(?:function|func|fn)\s+\w+\s*\([^)]*\)\s*(?:->\s*[\w<>\[\], ]+\s*)?\{\s*\}"),
    ("STUB-RETURN-NULL", "minor", "Body returns only null/None/empty — possibly never implemented",
     r"^[ \t]*(?:def|function|func|fn)\s+\w+[^\n{:]*[:{]\s*\n[ \t]+return\s+(?:null|None|nil|undefined|\[\]|\{\}|\"\"|'')\s*;?\s*$"),

    # --- swallowed failures -----------------------------------------------------------
    ("ERR-SWALLOW-PY", "major", "Exception caught and discarded — the failure is now invisible",
     r"^[ \t]*except[^\n:]*:\s*\n[ \t]+pass\s*$"),
    ("ERR-BARE-EXCEPT", "major", "Bare `except:` also catches KeyboardInterrupt and SystemExit",
     r"^[ \t]*except\s*:\s*$"),
    ("ERR-SWALLOW-JS", "major", "Empty catch block — the failure is now invisible",
     r"catch\s*(?:\([^)]*\))?\s*\{\s*\}"),
    ("ERR-SWALLOW-JAVA", "major", "Exception caught and ignored",
     r"catch\s*\([^)]*\)\s*\{\s*(?://[^\n]*\s*)?\}"),
    ("ERR-DISCARD-GO", "major", "Go error explicitly discarded",
     r"^[ \t]*_\s*(?::?=)\s*[\w.]+\([^\n]*\)\s*$|,\s*_\s*=\s*[\w.]+\.[A-Z]\w*\("),
    ("ERR-UNWRAP-RS", "minor", "Rust unwrap/expect — panics if the fallible path is taken",
     r"\.(?:unwrap|expect)\s*\("),
    ("ERR-EMPTY-RESCUE", "major", "Ruby rescue with an empty body",
     r"rescue[^\n]*\n\s*end\b"),

    # --- silent fallthrough ------------------------------------------------------------
    ("DISPATCH-NO-DEFAULT", "minor", "switch with no default — an unrecognised value falls through silently",
     r"switch\s*\([^)]*\)\s*\{(?:(?!default\s*:)[^{}]|\{[^{}]*\})*\}"),

    # --- disabled verification ---------------------------------------------------------
    ("TEST-SKIPPED", "major", "Test disabled — verify there is a reason and a ticket",
     r"(?:@(?:pytest\.mark\.)?(?:skip|skipif|xfail)\b|\.skip\s*\(|\bxit\s*\(|\bxdescribe\s*\("
     r"|@Ignore\b|@Disabled\b|t\.Skip\s*\(|#\[ignore\]|it\.todo\s*\()"),
    ("CHECK-SUPPRESSED", "major", "Static check suppressed — confirm it is a false positive, not a hidden defect",
     r"(?:#\s*type:\s*ignore|@ts-(?:ignore|expect-error|nocheck)|eslint-disable(?:-next-line)?"
     r"|#\s*noqa(?!\s*:\s*E501)|# *pylint: *disable|@SuppressWarnings|#\[allow\(|nolint)"),

    # --- insecure or unfinished configuration -------------------------------------------
    ("SEC-VERIFY-OFF", "critical", "Certificate or signature verification disabled",
     r"(?:verify\s*=\s*False|rejectUnauthorized\s*:\s*false|InsecureSkipVerify\s*:\s*true"
     r"|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0|CURLOPT_SSL_VERIFYPEER\s*,\s*(?:0|false))"),
    ("SEC-DEBUG-ON", "major", "Debug mode enabled in committed configuration",
     r"(?:DEBUG\s*[:=]\s*True|debug\s*:\s*true|FLASK_DEBUG\s*=\s*1|app\.debug\s*=\s*True)"),
    ("SEC-WILDCARD-CORS", "major", "Permissive CORS origin",
     r"(?:Access-Control-Allow-Origin[\"']?\s*[:,]\s*[\"']\*|allow_origins\s*=\s*\[\s*[\"']\*)"),

    # --- dead or parked code -------------------------------------------------------------
    ("DEAD-COMMENTED", "minor", "Commented-out code block — delete it; git remembers",
     r"(?:^[ \t]*(?://|#)[ \t]*(?:if|for|while|return|def |function |class |import |const |let |var )[^\n]*\n){3,}"),
    ("DEBUG-PRINT", "minor", "Debug output left in source",
     r"(?:^[ \t]*console\.(?:log|debug)\s*\(|^[ \t]*print\s*\(|\bdebugger;|\bbinding\.pry\b|breakpoint\(\))"),
]

COMPILED = [(code, sev, desc, re.compile(pattern, re.MULTILINE)) for code, sev, desc, pattern in RULES]

# Rules that only make sense for particular languages, to cut false positives.
LANG_SCOPED = {
    "STUB-PASS": {".py"},
    "STUB-ELLIPSIS": {".py"},
    "ERR-SWALLOW-PY": {".py"},
    "ERR-BARE-EXCEPT": {".py"},
    "ERR-DISCARD-GO": {".go"},
    "ERR-UNWRAP-RS": {".rs"},
    "ERR-EMPTY-RESCUE": {".rb"},
    "ERR-SWALLOW-JAVA": {".java", ".kt", ".cs", ".scala"},
    "ERR-SWALLOW-JS": {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte"},
    "DISPATCH-NO-DEFAULT": {".js", ".jsx", ".ts", ".tsx", ".java", ".cs", ".go", ".c", ".cc",
                            ".cpp", ".php", ".swift", ".kt"},
}

SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2}


def is_test_path(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    name = path.name.lower()
    return (
        any(p in ("test", "tests", "spec", "specs", "__tests__", "testing", "e2e") for p in parts)
        or name.startswith("test_") or name.startswith("spec_")
        or "_test." in name or ".test." in name or ".spec." in name
    )


def walk(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix.lower() in SOURCE_SUFFIXES:
                yield path


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def scan(root: Path, include_tests: bool, min_severity: str) -> dict:
    threshold = SEVERITY_ORDER[min_severity]
    hits: list[dict] = []
    files_scanned = 0

    for path in walk(root):
        if not include_tests and is_test_path(path):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files_scanned += 1
        suffix = path.suffix.lower()
        lines = text.splitlines()

        for code, severity, description, regex in COMPILED:
            if SEVERITY_ORDER[severity] > threshold:
                continue
            scope = LANG_SCOPED.get(code)
            if scope and suffix not in scope:
                continue
            if code == "STUB-ELLIPSIS" and suffix == ".pyi":
                continue  # `...` is correct in a stub file
            for match in regex.finditer(text):
                lineno = line_of(text, match.start())
                snippet = lines[lineno - 1].strip() if lineno <= len(lines) else ""
                hits.append({
                    "rule": code,
                    "severity": severity,
                    "description": description,
                    "file": str(path.relative_to(root)),
                    "line": lineno,
                    "snippet": snippet[:160],
                })

    hits.sort(key=lambda h: (SEVERITY_ORDER[h["severity"]], h["rule"], h["file"], h["line"]))
    by_rule = Counter(h["rule"] for h in hits)
    by_severity = Counter(h["severity"] for h in hits)
    by_file = Counter(h["file"] for h in hits)

    return {
        "root": str(root.resolve()),
        "files_scanned": files_scanned,
        "total_hits": len(hits),
        "by_severity": dict(by_severity),
        "by_rule": dict(by_rule.most_common()),
        "worst_files": [{"file": f, "hits": n} for f, n in by_file.most_common(20)],
        "hits": hits,
    }


def render(result: dict, limit: int) -> str:
    out: list[str] = []
    add = out.append
    add(f"Incompleteness scan — {result['root']}")
    add(f"{result['files_scanned']} source files scanned · {result['total_hits']} leads")
    sev = result["by_severity"]
    add("  " + " · ".join(f"{k}: {sev[k]}" for k in ("critical", "major", "minor") if k in sev))

    if not result["hits"]:
        add("\nNo leads. That is a result worth stating in the report, not a reason to stop —")
        add("the highest-yield incompleteness (documentation minus code) is invisible to a scanner.")
        return "\n".join(out)

    add("\nBy rule")
    add("-------")
    for rule, count in result["by_rule"].items():
        desc = next(d for c, _, d, _ in RULES if c == rule)
        add(f"  {count:>5}  {rule:<22} {desc}")

    if result["worst_files"]:
        add("\nConcentration (start here — leads cluster around unfinished modules)")
        add("-" * 68)
        for f in result["worst_files"][:12]:
            add(f"  {f['hits']:>5}  {f['file']}")

    add(f"\nLeads (showing up to {limit})")
    add("-" * 68)
    for hit in result["hits"][:limit]:
        add(f"  [{hit['severity']:<8}] {hit['rule']:<22} {hit['file']}:{hit['line']}")
        if hit["snippet"]:
            add(f"             {hit['snippet']}")
    if len(result["hits"]) > limit:
        add(f"  ... {len(result['hits']) - limit} more — use --json for the full list")

    add("\nNext: triage each lead. Reachable? Behind a documented promise? How old"
        " (git log -S)?")
    add("A stub nobody calls is Advisory. A stub behind an auth check is Critical.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("path", nargs="?", default=".", help="repository root (default: .)")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--severity", choices=("critical", "major", "minor"), default="minor",
                        help="minimum severity to report (default: minor, i.e. everything)")
    parser.add_argument("--include-tests", action="store_true",
                        help="also scan test files (skipped by default)")
    parser.add_argument("--limit", type=int, default=80, help="leads to print in text mode")
    args = parser.parse_args()

    root = Path(args.path)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    result = scan(root, args.include_tests, args.severity)
    print(json.dumps(result, indent=2) if args.json else render(result, args.limit))
    return 0


if __name__ == "__main__":
    sys.exit(main())
