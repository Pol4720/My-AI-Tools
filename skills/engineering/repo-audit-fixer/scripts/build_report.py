#!/usr/bin/env python3
"""Render findings.json into the LaTeX audit report and compile it.

The ledger is the source of truth; the document is generated from it. That is what keeps
the narrative from drifting away from the counts.

    python3 build_report.py --audit-dir Reports/audit-2026-09-03-1540 --lang es
    python3 build_report.py --audit-dir <dir> --no-compile     # emit .tex only
    python3 build_report.py --new-audit-dir <repo-root>        # print the folder to create

Narrative prose (verdict, method, system portrait, recommendations) is written by the
auditor into `narrative.md` inside the audit directory, as `## key` sections. Anything
absent gets a placeholder that is obvious in the PDF, because a silent gap in an audit
report is exactly the failure this skill exists to prevent.

Standard library only. Requires pdflatex/latexmk only for the --compile step.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2, "advisory": 3}
STATES = ("fixed", "mitigated", "accepted", "open")

LABELS = {
    "en": {
        "babel": "english",
        "title": "Software Audit Report",
        "verdict": "Executive verdict",
        "counts": "Findings by severity and state",
        "scope": "Scope and method",
        "system": "The system as found",
        "findings": "Findings",
        "contract": "Completeness ledger",
        "gate": "Verification and quality gate",
        "open": "Open issues and risks",
        "recommendations": "Recommendations",
        "severity": "Severity", "state": "State", "total": "Total",
        "stage": "Stage", "before": "Before", "after": "After", "detail": "Detail",
        "promise": "Promise", "source": "Source", "evidence": "Evidence",
        "location": "Location", "symptom": "Symptom", "root_cause": "Root cause",
        "impact": "Impact", "correction": "Correction", "verification": "Verification",
        "recommendation": "Recommendation", "reason": "Reason", "references": "References",
        "repository": "Repository", "branch": "Branch", "commit_before": "Commit audited",
        "commit_after": "Commit delivered", "auditor": "Auditor", "scope_row": "Scope",
        "none": "None.", "no_findings": "No findings were recorded in this category.",
        "not_examined": "Not examined",
        "missing": r"\textit{[not written --- the auditor must complete this section]}",
        "metric": "Metric",
    },
    "es": {
        "babel": "spanish",
        "title": "Informe de Auditoría de Software",
        "verdict": "Veredicto ejecutivo",
        "counts": "Hallazgos por severidad y estado",
        "scope": "Alcance y método",
        "system": "El sistema tal como se encontró",
        "findings": "Hallazgos",
        "contract": "Registro de completitud",
        "gate": "Verificación y puerta de calidad",
        "open": "Asuntos abiertos y riesgos",
        "recommendations": "Recomendaciones",
        "severity": "Severidad", "state": "Estado", "total": "Total",
        "stage": "Etapa", "before": "Antes", "after": "Después", "detail": "Detalle",
        "promise": "Promesa", "source": "Fuente", "evidence": "Evidencia",
        "location": "Ubicación", "symptom": "Síntoma", "root_cause": "Causa raíz",
        "impact": "Impacto", "correction": "Corrección", "verification": "Verificación",
        "recommendation": "Recomendación", "reason": "Motivo", "references": "Referencias",
        "repository": "Repositorio", "branch": "Rama", "commit_before": "Commit auditado",
        "commit_after": "Commit entregado", "auditor": "Auditor", "scope_row": "Alcance",
        "none": "Ninguno.", "no_findings": "No se registraron hallazgos en esta categoría.",
        "not_examined": "No examinado",
        "missing": r"\textit{[sin redactar --- el auditor debe completar esta sección]}",
        "metric": "Métrica",
    },
}

SEVERITY_NAMES = {
    "en": {"critical": "Critical", "major": "Major", "minor": "Minor", "advisory": "Advisory"},
    "es": {"critical": "Crítico", "major": "Mayor", "minor": "Menor", "advisory": "Informativo"},
}
STATE_NAMES = {
    "en": {"fixed": "Fixed", "mitigated": "Mitigated", "accepted": "Accepted", "open": "Open"},
    "es": {"fixed": "Corregido", "mitigated": "Mitigado", "accepted": "Aceptado", "open": "Abierto"},
}

TEX_ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def tex(value) -> str:
    """Escape a value for LaTeX text mode.

    Consecutive hyphens are separated so that `--verbose` does not become an en dash;
    CLI flags appear verbatim in audit findings and must survive typesetting intact.
    """
    if value is None:
        return ""
    out = [TEX_ESCAPES.get(char, char) for char in str(value)]
    return re.sub(r"-(?=-)", "-{}", "".join(out))


def wrap(value) -> str:
    """Escape for a narrow table cell, inserting break opportunities in path-like tokens.

    Without these, a token such as tests/test_cli.py::test_format_json cannot be broken
    and overflows its column — an overfull box in a document whose subject is defects.
    """
    escaped = tex(value)
    return re.sub(r"(\\_|[/.:;,\-])", r"\1\\allowbreak{}", escaped)


def code(value) -> str:
    """Escape a value and render it as inline code."""
    if not value:
        return ""
    return r"\texttt{\small " + tex(value) + "}"


def parse_narrative(path: Path) -> dict[str, str]:
    """Read narrative.md, splitting on `## key` headings into a dict of raw markdown."""
    if not path.exists():
        return {}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^##\s+([a-z_]+)\s*$", line.strip())
        if heading:
            current = heading.group(1)
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {key: "\n".join(lines).strip() for key, lines in sections.items()}


def markdown_to_tex(text: str) -> str:
    """A deliberately small markdown subset: paragraphs, bullets, bold, italic, code."""
    if not text.strip():
        return ""
    out: list[str] = []
    in_list = False
    for raw in text.splitlines():
        line = raw.rstrip()
        bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        if bullet:
            if not in_list:
                out.append(r"\begin{itemize}")
                in_list = True
            out.append(r"  \item " + inline_to_tex(bullet.group(1)))
            continue
        if in_list:
            out.append(r"\end{itemize}")
            in_list = False
        if not line.strip():
            out.append("")
        else:
            out.append(inline_to_tex(line))
    if in_list:
        out.append(r"\end{itemize}")
    return "\n".join(out).strip()


def inline_to_tex(line: str) -> str:
    """Escape, then re-apply the inline markdown we support."""
    placeholders: list[str] = []

    def stash(match: re.Match, wrapper: str) -> str:
        placeholders.append(wrapper % tex(match.group(1)))
        return f"\x00{len(placeholders) - 1}\x00"

    line = re.sub(r"`([^`]+)`", lambda m: stash(m, r"\texttt{\small %s}"), line)
    line = re.sub(r"\*\*([^*]+)\*\*", lambda m: stash(m, r"\textbf{%s}"), line)
    line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", lambda m: stash(m, r"\textit{%s}"), line)
    line = tex(line)
    return re.sub(r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], line)


def counts_table(findings: list[dict], lang: str) -> str:
    labels, sev_names, state_names = LABELS[lang], SEVERITY_NAMES[lang], STATE_NAMES[lang]
    rows = [
        r"\textbf{" + labels["severity"] + "} & "
        + " & ".join(r"\textbf{" + state_names[s] + "}" for s in STATES)
        + r" & \textbf{" + labels["total"] + r"} \\",
        r"\midrule",
    ]
    for severity in sorted(SEVERITY_ORDER, key=lambda s: SEVERITY_ORDER[s]):
        subset = [f for f in findings if f.get("severity") == severity]
        cells = [str(sum(1 for f in subset if f.get("state") == state)) for state in STATES]
        rows.append(f"{sev_names[severity]} & " + " & ".join(cells)
                    + f" & {len(subset)} " + r"\\")
    rows.append(r"\midrule")
    totals = [str(sum(1 for f in findings if f.get("state") == state)) for state in STATES]
    rows.append(r"\textbf{" + labels["total"] + "} & "
                + " & ".join(r"\textbf{" + t + "}" for t in totals)
                + r" & \textbf{" + str(len(findings)) + r"} \\")
    return "\n".join(rows)


def frontmatter_table(audit: dict, lang: str) -> str:
    labels = LABELS[lang]
    rows = [
        (labels["repository"], audit.get("repository", "")),
        (labels["branch"], audit.get("branch", "")),
        (labels["commit_before"], audit.get("commit_before", "")),
        (labels["commit_after"], audit.get("commit_after", "")),
        (labels["scope_row"], audit.get("scope", "")),
        (labels["auditor"], audit.get("auditor", "")),
    ]
    return "\n".join(
        rf"\textbf{{{tex(name)}}} & {wrap(value)} \\"
        for name, value in rows if str(value).strip()
    )


def findings_body(findings: list[dict], lang: str) -> str:
    labels = LABELS[lang]
    if not findings:
        return labels["no_findings"]

    ordered = sorted(
        findings,
        key=lambda f: (SEVERITY_ORDER.get(f.get("severity", "advisory"), 9),
                       f.get("category", ""), f.get("id", "")),
    )
    blocks: list[str] = []
    for finding in ordered:
        state = finding.get("state", "open")
        head = (rf"\finding{{{tex(finding.get('id', '?'))}}}"
                rf"{{{tex(finding.get('title', ''))}}}"
                rf"{{{tex(finding.get('severity', 'advisory'))}}}"
                rf"{{{tex(state)}}}")

        locations = finding.get("location") or []
        if isinstance(locations, str):
            locations = [locations]
        rows: list[tuple[str, str]] = [
            (labels["location"], ", ".join(rf"\texttt{{\small {wrap(loc)}}}"
                                            for loc in locations)),
            (labels["symptom"], tex(finding.get("symptom", ""))),
            (labels["root_cause"], tex(finding.get("root_cause", ""))),
            (labels["impact"], tex(finding.get("impact", ""))),
            (labels["evidence"], code(finding.get("evidence", ""))
             if "/" in str(finding.get("evidence", "")) else tex(finding.get("evidence", ""))),
        ]
        if state in ("fixed", "mitigated"):
            rows.append((labels["correction"], tex(finding.get("fix", ""))))
            rows.append((labels["verification"], tex(finding.get("verification", ""))))
        else:
            rows.append((labels["recommendation"], tex(finding.get("recommendation", ""))))
            rows.append((labels["reason"], tex(finding.get("reason", ""))))

        references = finding.get("references") or []
        if references:
            rows.append((labels["references"],
                         ", ".join(rf"\url{{{ref}}}" if str(ref).startswith("http") else tex(ref)
                                   for ref in references)))

        body = [r"\begin{description}"]
        for name, value in rows:
            if str(value).strip():
                body.append(rf"  \item[{tex(name)}] {value}")
        body.append(r"\end{description}")
        category = tex(finding.get("category", ""))
        confidence = tex(finding.get("confidence", ""))
        body.append(rf"\noindent{{\footnotesize\textcolor{{muted}}{{{category} "
                    rf"$\cdot$ {confidence}}}}}")
        blocks.append(head + "\n" + "\n".join(body))
    return "\n\n\\medskip\n\n".join(blocks)


def contract_body(ledger: list[dict], lang: str) -> str:
    labels = LABELS[lang]
    if not ledger:
        return labels["none"]
    rows = [
        r"\small",
        r"\begin{longtable}{@{}L{1.3cm}L{5.9cm}L{2.0cm}L{5.1cm}@{}}",
        r"\toprule",
        (r"\textbf{ID} & \textbf{" + labels["promise"] + r"} & \textbf{"
         + labels["state"] + r"} & \textbf{" + labels["evidence"] + r"} \\"),
        r"\midrule\endhead",
    ]
    for entry in ledger:
        rows.append(" & ".join([
            wrap(entry.get("id", "")),
            wrap(entry.get("promise", "")),
            tex(entry.get("state", "")),
            wrap(entry.get("evidence", "") or entry.get("source", "")),
        ]) + r" \\")
    rows += [r"\bottomrule", r"\end{longtable}"]
    return "\n".join(rows)


def gate_body(gate: dict, metrics: dict, lang: str) -> str:
    labels = LABELS[lang]
    out = [
        r"\begin{center}\small",
        r"\begin{tabular}{@{}lllL{6.4cm}@{}}",
        r"\toprule",
        (r"\textbf{" + labels["stage"] + r"} & \textbf{" + labels["before"]
         + r"} & \textbf{" + labels["after"] + r"} & \textbf{" + labels["detail"] + r"} \\"),
        r"\midrule",
    ]
    for stage, entry in (gate or {}).items():
        out.append(" & ".join([
            tex(stage), tex(entry.get("before", "")), tex(entry.get("after", "")),
            wrap(entry.get("detail", "")),
        ]) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{center}"]

    pairs = [(k[:-7], metrics.get(k), metrics.get(k[:-7] + "_after"))
             for k in metrics or {} if k.endswith("_before")]
    pairs = [(name, before, after) for name, before, after in pairs
             if before is not None or after is not None]
    if pairs:
        out += [
            r"\medskip", r"\begin{center}\small",
            r"\begin{tabular}{@{}lrr@{}}", r"\toprule",
            (r"\textbf{" + labels["metric"] + r"} & \textbf{" + labels["before"]
             + r"} & \textbf{" + labels["after"] + r"} \\"),
            r"\midrule",
        ]
        for name, before, after in pairs:
            out.append(f"{tex(name.replace('_', ' '))} & {tex(before)} & {tex(after)} " + r"\\")
        out += [r"\bottomrule", r"\end{tabular}", r"\end{center}"]
    return "\n".join(out)


def open_body(findings: list[dict], not_examined: list, lang: str) -> str:
    labels = LABELS[lang]
    outstanding = [f for f in findings if f.get("state") in ("open", "accepted")]
    parts: list[str] = []
    if outstanding:
        parts.append(r"\small")
        parts.append(r"\begin{longtable}{@{}L{1.3cm}L{2.0cm}L{5.6cm}L{5.4cm}@{}}")
        parts.append(r"\toprule")
        parts.append(r"\textbf{ID} & \textbf{" + labels["severity"] + r"} & \textbf{"
                     + labels["recommendation"] + r"} & \textbf{" + labels["reason"] + r"} \\")
        parts.append(r"\midrule\endhead")
        for finding in sorted(outstanding,
                              key=lambda f: SEVERITY_ORDER.get(f.get("severity", "advisory"), 9)):
            parts.append(" & ".join([
                wrap(finding.get("id", "")),
                SEVERITY_NAMES[lang].get(finding.get("severity", "advisory"), ""),
                wrap(finding.get("recommendation", "")),
                wrap(finding.get("reason", "")),
            ]) + r" \\")
        parts += [r"\bottomrule", r"\end{longtable}"]
    else:
        parts.append(labels["none"])

    if not_examined:
        parts.append(r"\subsection*{" + labels["not_examined"] + "}")
        parts.append(r"\begin{itemize}")
        for item in not_examined:
            parts.append(r"  \item " + tex(item))
        parts.append(r"\end{itemize}")
    return "\n".join(parts)


def build(audit_dir: Path, lang: str, template_path: Path) -> Path:
    data = json.loads((audit_dir / "findings.json").read_text(encoding="utf-8"))
    labels = LABELS[lang]
    audit = data.get("audit", {})
    findings = data.get("findings", [])
    narrative = parse_narrative(audit_dir / "narrative.md")

    def prose(key: str) -> str:
        rendered = markdown_to_tex(narrative.get(key, ""))
        return rendered if rendered else labels["missing"]

    repository = audit.get("repository", "repository")
    started = audit.get("started_at", "") or datetime.now(timezone.utc).date().isoformat()

    substitutions = {
        "%%BABEL%%": labels["babel"],
        "%%TITLE%%": tex(labels["title"]),
        "%%SUBTITLE%%": tex(repository),
        "%%AUTHOR%%": tex(audit.get("auditor", "")),
        "%%DATE%%": tex(started[:10]),
        "%%HEADER%%": tex(f"{labels['title']} — {repository}"),
        "%%PDFTITLE%%": tex(f"{labels['title']} - {repository}"),
        "%%PDFAUTHOR%%": tex(audit.get("auditor", "")),
        "%%FRONTMATTER_TABLE%%": frontmatter_table(audit, lang),
        "%%H_VERDICT%%": tex(labels["verdict"]),
        "%%VERDICT_BODY%%": prose("verdict"),
        "%%H_COUNTS%%": tex(labels["counts"]),
        "%%COUNTS_TABLE%%": counts_table(findings, lang),
        "%%H_SCOPE%%": tex(labels["scope"]),
        "%%SCOPE_BODY%%": prose("scope"),
        "%%H_SYSTEM%%": tex(labels["system"]),
        "%%SYSTEM_BODY%%": prose("system"),
        "%%H_FINDINGS%%": tex(labels["findings"]),
        "%%FINDINGS_BODY%%": findings_body(findings, lang),
        "%%H_CONTRACT%%": tex(labels["contract"]),
        "%%CONTRACT_BODY%%": contract_body(data.get("contract_ledger", []), lang),
        "%%H_GATE%%": tex(labels["gate"]),
        "%%GATE_BODY%%": (prose("gate") + "\n\n" if "gate" in narrative else "")
                         + gate_body(data.get("gate", {}), data.get("metrics", {}), lang),
        "%%H_OPEN%%": tex(labels["open"]),
        "%%OPEN_BODY%%": open_body(findings, data.get("not_examined", []), lang),
        "%%H_RECOMMENDATIONS%%": tex(labels["recommendations"]),
        "%%RECOMMENDATIONS_BODY%%": prose("recommendations"),
    }

    document = template_path.read_text(encoding="utf-8")
    for token, value in substitutions.items():
        document = document.replace(token, value)

    leftover = re.findall(r"%%[A-Z_]+%%", document)
    if leftover:
        print(f"warning: unsubstituted tokens remain: {sorted(set(leftover))}", file=sys.stderr)

    target = audit_dir / "audit.tex"
    target.write_text(document, encoding="utf-8")
    return target


def compile_pdf(tex_path: Path) -> bool:
    audit_dir = tex_path.parent
    # Commands run with cwd=audit_dir, so the output directory is the current one.
    if shutil.which("latexmk"):
        runs = [["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                 "-outdir=.", tex_path.name]]
    elif shutil.which("pdflatex"):
        base = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                "-output-directory=.", tex_path.name]
        runs = [base, base, base]  # three passes: toc + references
    else:
        print("no LaTeX toolchain (latexmk/pdflatex) available — shipping audit.tex only.\n"
              "Say so in the audit README; do not claim a PDF that does not exist.",
              file=sys.stderr)
        return False

    for run in runs:
        result = subprocess.run(run, cwd=audit_dir, capture_output=True, text=True,
                                timeout=600, check=False)
        if result.returncode != 0:
            tail = (result.stdout + result.stderr).splitlines()[-40:]
            print("LaTeX compilation failed:\n  " + "\n  ".join(tail), file=sys.stderr)
            return False

    log = audit_dir / (tex_path.stem + ".log")
    if log.exists():
        text = log.read_text(encoding="utf-8", errors="replace")
        warnings = [ln for ln in text.splitlines()
                    if "Warning" in ln or "Overfull" in ln or "Underfull" in ln]
        if warnings:
            print(f"{len(warnings)} LaTeX warning(s) — the target is zero. First few:",
                  file=sys.stderr)
            for line in warnings[:10]:
                print("  " + line.strip(), file=sys.stderr)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--audit-dir", help="the Reports/audit-<timestamp> directory")
    parser.add_argument("--lang", default="en", choices=("en", "es"), help="report language")
    parser.add_argument("--template", help="override the template path")
    parser.add_argument("--no-compile", action="store_true", help="emit .tex without compiling")
    parser.add_argument("--new-audit-dir", metavar="REPO_ROOT",
                        help="print the audit directory path to create for this repository")
    args = parser.parse_args()

    if args.new_audit_dir:
        root = Path(args.new_audit_dir)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
        reports = next((root / name for name in ("Reports", "reports", "REPORTS")
                        if (root / name).is_dir()), root / "Reports")
        print(reports / f"audit-{stamp}")
        return 0

    if not args.audit_dir:
        parser.error("--audit-dir is required unless --new-audit-dir is given")

    audit_dir = Path(args.audit_dir)
    if not (audit_dir / "findings.json").exists():
        print(f"error: {audit_dir / 'findings.json'} not found — "
              "run findings.py --init first", file=sys.stderr)
        return 2

    template = Path(args.template) if args.template else \
        Path(__file__).resolve().parent.parent / "assets" / "audit-report-template.tex"
    if not template.exists():
        print(f"error: template not found at {template}", file=sys.stderr)
        return 2

    tex_path = build(audit_dir, args.lang, template)
    print(f"wrote {tex_path}")

    if args.no_compile:
        return 0
    ok = compile_pdf(tex_path)
    if ok:
        print(f"wrote {audit_dir / 'audit.pdf'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
