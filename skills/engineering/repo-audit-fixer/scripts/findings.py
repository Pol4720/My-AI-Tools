#!/usr/bin/env python3
"""Create, validate and summarise the audit findings ledger.

`findings.json` is the source of truth for the audit. `build_report.py` renders the
LaTeX from it, which is what stops the narrative drifting from the counts.

    python3 findings.py --init Reports/audit-2026-09-03-1540 --repo my-service
    python3 findings.py --validate Reports/audit-2026-09-03-1540/findings.json
    python3 findings.py --summary  Reports/audit-2026-09-03-1540/findings.json

`--validate` enforces the honest-ledger rule: it refuses a ledger containing a finding
with no state, a `fixed` finding with no verification, an `accepted` finding with no
reason, or a `critical` finding at `reported` confidence. Those refusals are the point.

Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SEVERITIES = ("critical", "major", "minor", "advisory")
STATES = ("fixed", "mitigated", "accepted", "open")
CONFIDENCES = ("verified", "inferred", "reported")
CATEGORIES = (
    "CORR", "SEC-INJ", "SEC-AUTH", "SEC-CRYPT", "SEC-SECRET", "SEC-XSS", "SEC-SSRF",
    "SEC-DESER", "SEC-CONF", "SEC-DOS", "RESIL", "DATA", "CONC", "CONTRACT", "INCOMPL",
    "TEST", "BUILD", "OBS", "PERF", "MAINT", "DOC", "UX", "LICENSE", "PRIV",
)
GATE_STAGES = ("install", "build", "lint", "typecheck", "test", "coverage", "audit", "secrets")

REQUIRED_FINDING_FIELDS = (
    "id", "title", "category", "severity", "confidence", "state",
    "location", "symptom", "root_cause", "impact",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def skeleton(repo: str, scope: str, language: str) -> dict:
    return {
        "schema": "repo-audit-fixer/findings/1",
        "audit": {
            "repository": repo,
            "remote": "",
            "branch": "",
            "commit_before": "",
            "commit_after": "",
            "scope": scope,
            "language": language,
            "started_at": now_iso(),
            "finished_at": "",
            "auditor": "",
            "environment": {"os": "", "runtimes": {}, "tools": {}},
        },
        "contract_ledger": [
            # {"id": "C-001", "promise": "...", "source": "README.md:42",
            #  "state": "honoured|repaired|withdrawn", "evidence": "..."}
        ],
        "gate": {
            stage: {"before": "not_run", "after": "not_run", "detail": ""}
            for stage in GATE_STAGES
        },
        "metrics": {
            "tests_before": None, "tests_after": None,
            "coverage_before": None, "coverage_after": None,
            "lint_errors_before": None, "lint_errors_after": None,
            "type_errors_before": None, "type_errors_after": None,
            "vulnerabilities_before": None, "vulnerabilities_after": None,
        },
        "findings": [],
        "not_examined": [
            # Honest scope limits. What you did not look at, and why.
        ],
    }


def example_finding() -> dict:
    return {
        "id": "F-001",
        "title": "",
        "category": "CORR",
        "severity": "major",
        "confidence": "verified",
        "state": "open",
        "location": [],
        "symptom": "",
        "root_cause": "",
        "impact": "",
        "evidence": "",
        "fix": "",
        "verification": "",
        "recommendation": "",
        "reason": "",
        "references": [],
    }


def validate(data: dict) -> list[str]:
    """Return a list of problems. Empty means the ledger is honest and well-formed."""
    problems: list[str] = []

    def bad(msg: str) -> None:
        problems.append(msg)

    if data.get("schema") != "repo-audit-fixer/findings/1":
        bad("schema: expected 'repo-audit-fixer/findings/1'")

    audit = data.get("audit")
    if not isinstance(audit, dict):
        bad("audit: missing or not an object")
    else:
        for field in ("repository", "scope", "started_at"):
            if not str(audit.get(field, "")).strip():
                bad(f"audit.{field}: empty")

    findings = data.get("findings")
    if not isinstance(findings, list):
        bad("findings: missing or not a list")
        return problems

    seen_ids: set[str] = set()
    for index, finding in enumerate(findings):
        where = f"findings[{index}]"
        if not isinstance(finding, dict):
            bad(f"{where}: not an object")
            continue
        fid = str(finding.get("id", "")).strip()
        where = f"{fid or where}"

        for field in REQUIRED_FINDING_FIELDS:
            value = finding.get(field)
            if value is None or (isinstance(value, str) and not value.strip()) or \
                    (isinstance(value, list) and not value):
                bad(f"{where}: required field '{field}' is empty")

        if fid:
            if fid in seen_ids:
                bad(f"{where}: duplicate id")
            seen_ids.add(fid)

        severity = finding.get("severity")
        state = finding.get("state")
        confidence = finding.get("confidence")
        category = finding.get("category")

        if severity not in SEVERITIES:
            bad(f"{where}: severity '{severity}' not one of {SEVERITIES}")
        if state not in STATES:
            bad(f"{where}: state '{state}' not one of {STATES} — "
                "every finding must end in exactly one state")
        if confidence not in CONFIDENCES:
            bad(f"{where}: confidence '{confidence}' not one of {CONFIDENCES}")
        if category not in CATEGORIES:
            bad(f"{where}: category '{category}' not in the taxonomy")

        # --- the honest-ledger rules ---------------------------------------------------
        if state == "fixed":
            if not str(finding.get("fix", "")).strip():
                bad(f"{where}: state 'fixed' requires 'fix' describing what changed")
            if not str(finding.get("verification", "")).strip():
                bad(f"{where}: state 'fixed' requires 'verification' — "
                    "how you proved it, including the test that fails on the pre-fix code")
        if state == "accepted" and not str(finding.get("reason", "")).strip():
            bad(f"{where}: state 'accepted' requires 'reason' explaining why it was not fixed")
        if state == "open" and not str(finding.get("reason", "")).strip():
            bad(f"{where}: state 'open' requires 'reason' naming what is blocking it")
        if state in ("accepted", "open") and not str(finding.get("recommendation", "")).strip():
            bad(f"{where}: state '{state}' requires 'recommendation' — what should be done")
        if state == "mitigated" and not str(finding.get("fix", "")).strip():
            bad(f"{where}: state 'mitigated' requires 'fix' describing the mitigation "
                "and what would defeat it")
        if severity == "critical" and confidence == "reported":
            bad(f"{where}: a critical finding at 'reported' confidence is not yet a finding — "
                "reproduce it to raise confidence, or lower the severity")
        if str(finding.get("root_cause", "")).strip() == str(finding.get("symptom", "")).strip() \
                and str(finding.get("symptom", "")).strip():
            bad(f"{where}: root_cause restates the symptom — "
                "the cause is the mechanism, and it is what tells the author what else is affected")

    ledger = data.get("contract_ledger", [])
    if isinstance(ledger, list):
        for index, entry in enumerate(ledger):
            if not isinstance(entry, dict):
                bad(f"contract_ledger[{index}]: not an object")
                continue
            if entry.get("state") not in ("honoured", "repaired", "withdrawn"):
                bad(f"contract_ledger[{index}] ({entry.get('id', '?')}): state must be "
                    "'honoured', 'repaired' or 'withdrawn' — none may be left unexamined")

    return problems


def summarise(data: dict) -> str:
    findings = data.get("findings", [])
    out: list[str] = []
    add = out.append

    audit = data.get("audit", {})
    add(f"Audit ledger — {audit.get('repository', '?')} ({audit.get('scope', 'scope unstated')})")
    add(f"{len(findings)} findings")

    add("\nBy severity / state")
    add(f"  {'':<10} " + " ".join(f"{s:>10}" for s in STATES) + f"{'total':>10}")
    for severity in SEVERITIES:
        row = [f for f in findings if f.get("severity") == severity]
        counts = [sum(1 for f in row if f.get("state") == state) for state in STATES]
        if not row:
            continue
        add(f"  {severity:<10} " + " ".join(f"{c:>10}" for c in counts) + f"{len(row):>10}")

    categories: dict[str, int] = {}
    for finding in findings:
        categories[finding.get("category", "?")] = categories.get(finding.get("category", "?"), 0) + 1
    if categories:
        add("\nBy category")
        for category, count in sorted(categories.items(), key=lambda kv: -kv[1]):
            add(f"  {category:<12} {count}")

    gate = data.get("gate", {})
    if gate:
        add("\nQuality gate")
        for stage in GATE_STAGES:
            entry = gate.get(stage, {})
            add(f"  {stage:<12} {str(entry.get('before', '?')):>12} -> {entry.get('after', '?')}")

    outstanding = [f for f in findings if f.get("state") in ("open", "accepted")]
    if outstanding:
        add(f"\nOutstanding ({len(outstanding)})")
        for finding in outstanding:
            add(f"  [{finding.get('severity', '?'):<8}] {finding.get('id', '?')} "
                f"{finding.get('title', '')[:70]}")
            reason = finding.get("reason", "")
            if reason:
                add(f"             {reason[:90]}")

    not_examined = data.get("not_examined", [])
    if not_examined:
        add("\nNot examined (stated scope limits)")
        for item in not_examined:
            add(f"  - {item}")

    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init", metavar="AUDIT_DIR",
                       help="create a findings.json skeleton in this audit directory")
    group.add_argument("--validate", metavar="FINDINGS_JSON",
                       help="validate a ledger; non-zero exit if it is not honest or well-formed")
    group.add_argument("--summary", metavar="FINDINGS_JSON", help="print a summary table")
    parser.add_argument("--repo", default="", help="repository name (with --init)")
    parser.add_argument("--scope", default="Full repository", help="audit scope (with --init)")
    parser.add_argument("--lang", default="en", choices=("en", "es"),
                        help="report language (with --init)")
    parser.add_argument("--with-example", action="store_true",
                        help="include a blank example finding (with --init)")
    args = parser.parse_args()

    if args.init:
        audit_dir = Path(args.init)
        audit_dir.mkdir(parents=True, exist_ok=True)
        (audit_dir / "evidence").mkdir(exist_ok=True)
        target = audit_dir / "findings.json"
        if target.exists():
            print(f"refusing to overwrite {target} — previous audits are never destroyed",
                  file=sys.stderr)
            return 2
        data = skeleton(args.repo or audit_dir.parent.parent.name, args.scope, args.lang)
        if args.with_example:
            data["findings"].append(example_finding())
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"created {target}")
        print(f"created {audit_dir / 'evidence'}/")
        return 0

    path = Path(args.validate or args.summary)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: {path} is not valid JSON — {exc}", file=sys.stderr)
        return 2

    if args.summary:
        print(summarise(data))
        return 0

    problems = validate(data)
    if problems:
        print(f"{len(problems)} problem(s) in {path}:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("\nThe ledger is not ready to render. Fix these before Phase 9.", file=sys.stderr)
        return 1
    print(f"{path}: valid · {len(data.get('findings', []))} findings, "
          f"{len(data.get('contract_ledger', []))} contract entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
