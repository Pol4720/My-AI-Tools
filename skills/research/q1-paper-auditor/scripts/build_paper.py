#!/usr/bin/env python3
"""Compile a LaTeX document and report every diagnostic with its source file.

The point of this script is that `pdflatex` tells you a box is overfull "at lines
200--201" without saying which file those lines are in, and in a paper that
`\\input`s generated tables that is exactly the information you need. It tracks
the file stack that LaTeX prints as balanced parentheses and attributes each
diagnostic to the file that was open when it was emitted.

Usage
-----
    python build_paper.py paper/en/article.tex
    python build_paper.py paper/en paper/es          # directories: finds the main file
    python build_paper.py paper/**/article.tex --json report.json
    python build_paper.py article.tex --keep-going   # do not stop at the first error

Exit status is 0 only when every document is completely clean: no errors, no
warnings, no bad boxes, no undefined references or citations.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Locating the document
# ---------------------------------------------------------------------------


def find_documents(target: Path) -> list[Path]:
    """Every compilable document at `target`.

    A directory may legitimately hold more than one document -- a manuscript
    beside its cover letter, or a folder of reports. Building only the first
    would silently leave the others unchecked, so return them all and let the
    caller see the full picture.
    """
    if target.is_file():
        return [target]
    if not target.is_dir():
        return []

    documents = [
        p for p in sorted(target.glob("*.tex"))
        if re.search(r"^\s*\\documentclass", p.read_text(encoding="utf-8", errors="replace"), re.M)
    ]
    # Put the conventional main file first so its result is read first.
    for preferred in ("manuscript", "paper", "main", "article"):
        for p in list(documents):
            if p.stem.lower() == preferred:
                documents.remove(p)
                documents.insert(0, p)
    return documents


# ---------------------------------------------------------------------------
# Toolchain
# ---------------------------------------------------------------------------


def have(tool: str) -> bool:
    return shutil.which(tool) is not None


def detect_bib_tool(tex: Path) -> str | None:
    """biber for biblatex, bibtex for natbib/plain, None when no bibliography."""
    text = tex.read_text(encoding="utf-8", errors="replace")
    if re.search(r"\\usepackage(\[[^\]]*\])?\{biblatex\}", text):
        return "biber" if have("biber") else None
    if re.search(r"\\bibliography\{|\\bibliographystyle\{|\\addbibresource\{", text):
        return "bibtex" if have("bibtex") else None
    return None


def run(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, timeout=timeout,
            text=True, errors="replace",
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    except FileNotFoundError:
        return 127, f"{cmd[0]} not found"


# ---------------------------------------------------------------------------
# Log parsing
# ---------------------------------------------------------------------------


@dataclass
class Diagnostic:
    kind: str          # error | warning | overfull | underfull | undefined_ref | undefined_cite
    message: str
    source_file: str = ""
    lines: str = ""
    severity: str = "warning"


@dataclass
class BuildResult:
    document: str = ""
    ok: bool = False
    engine: str = ""
    bib_tool: str = ""
    passes: int = 0
    pages: int | None = None
    diagnostics: list[Diagnostic] = field(default_factory=list)
    failure: str = ""

    def count(self, kind: str) -> int:
        return sum(1 for d in self.diagnostics if d.kind == kind)

    def summary(self) -> dict:
        return {
            "errors": self.count("error"),
            "warnings": self.count("warning"),
            "overfull": self.count("overfull"),
            "underfull": self.count("underfull"),
            "undefined_refs": self.count("undefined_ref"),
            "undefined_cites": self.count("undefined_cite"),
        }


_FILE_TOKEN = re.compile(r"\((?:\"([^\"]+)\"|([^\s()]+))|\)")
_INTERESTING_SUFFIX = (".tex", ".bbl", ".cls", ".sty")


def _track_files(line: str, stack: list[str]) -> None:
    """Update the open-file stack from LaTeX's parenthesised file trace.

    LaTeX prints "(path" when it opens a file and ")" when it closes one. The
    trace is wrapped across lines and interleaved with other output, so this is
    approximate -- but it is reliable enough to name the file responsible for a
    diagnostic, which is all we need.
    """
    for match in _FILE_TOKEN.finditer(line):
        token = match.group(0)
        if token == ")":
            if stack:
                stack.pop()
        else:
            name = match.group(1) or match.group(2) or ""
            if name.endswith(_INTERESTING_SUFFIX):
                stack.append(name)
            else:
                # Push a placeholder so the matching ")" pops the right depth.
                stack.append("")


def parse_log(log_text: str) -> tuple[list[Diagnostic], int | None]:
    diags: list[Diagnostic] = []
    pages: int | None = None
    stack: list[str] = []

    lines = log_text.splitlines()
    for i, line in enumerate(lines):

        def current_file() -> str:
            for name in reversed(stack):
                if name:
                    return name
            return ""

        # Errors: "! message" or "file.tex:12: message" with -file-line-error.
        if line.startswith("!"):
            text = line[1:].strip()
            if text and "Undefined control sequence" not in text:
                detail = ""
                for nxt in lines[i + 1 : i + 4]:
                    if nxt.startswith("l."):
                        detail = f" ({nxt.strip()})"
                        break
                diags.append(Diagnostic("error", text + detail, current_file(), severity="error"))
            elif text:
                diags.append(Diagnostic("error", text, current_file(), severity="error"))

        elif re.match(r"^[^\s:]+\.\w+:\d+:", line):
            diags.append(Diagnostic("error", line.strip(), current_file(), severity="error"))

        # Bad boxes.
        elif "Overfull \\hbox" in line or "Overfull \\vbox" in line:
            span = re.search(r"at lines (\d+--\d+)|at line (\d+)", line)
            amount = re.search(r"\(([\d.]+)pt too wide\)", line)
            diags.append(Diagnostic(
                "overfull",
                f"{amount.group(1)}pt too wide" if amount else line.strip(),
                current_file(),
                (span.group(1) or span.group(2)) if span else "",
            ))
        elif "Underfull \\hbox" in line or "Underfull \\vbox" in line:
            span = re.search(r"at lines (\d+--\d+)|at line (\d+)", line)
            badness = re.search(r"badness (\d+)", line)
            diags.append(Diagnostic(
                "underfull",
                f"badness {badness.group(1)}" if badness else line.strip(),
                current_file(),
                (span.group(1) or span.group(2)) if span else "",
            ))

        # Undefined references and citations are warnings worth separating out.
        elif "LaTeX Warning:" in line:
            message = line.split("LaTeX Warning:", 1)[1].strip()
            # Warnings wrap; pull in the continuation.
            for nxt in lines[i + 1 : i + 3]:
                if nxt.strip() and not nxt.startswith(("(", ")", "!", "[")) and "Warning" not in nxt:
                    message += " " + nxt.strip()
                else:
                    break
            if "Citation" in message and "undefined" in message:
                kind = "undefined_cite"
            elif "Reference" in message and "undefined" in message:
                kind = "undefined_ref"
            else:
                kind = "warning"
            diags.append(Diagnostic(kind, message, current_file()))

        elif "Package" in line and "Warning:" in line:
            message = line.split("Warning:", 1)[1].strip()
            diags.append(Diagnostic("warning", message, current_file()))

        if "Output written on" in line:
            m = re.search(r"\((\d+) pages?", line)
            if m:
                pages = int(m.group(1))

        _track_files(line, stack)

    # The same box is often reported on every pass; collapse exact duplicates.
    seen, unique = set(), []
    for d in diags:
        key = (d.kind, d.message, d.source_file, d.lines)
        if key not in seen:
            seen.add(key)
            unique.append(d)
    return unique, pages


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------


def build(tex: Path, timeout: int = 300, max_passes: int = 5) -> BuildResult:
    result = BuildResult(document=str(tex))
    cwd, stem = tex.parent, tex.stem

    # Delete the previous logs before building. If a run fails early, or the
    # build tool decides nothing needs redoing, the old log survives and gets
    # parsed as though it described the current sources -- which reports errors
    # that were fixed several edits ago and sends you hunting for a defect that
    # no longer exists. An absent log is an honest signal; a stale one is not.
    # The build database goes too: with the log removed but the database intact,
    # latexmk concludes everything is up to date, does nothing, and leaves no log
    # at all to parse.
    for suffix in (".log", ".blg", ".fdb_latexmk"):
        stale = cwd / f"{stem}{suffix}"
        if stale.exists():
            try:
                stale.unlink()
            except OSError:
                pass

    if have("latexmk"):
        result.engine = "latexmk"
        # -f keeps latexmk going through errors so the log records everything
        # rather than stopping at the first problem, which is what we want when
        # the aim is a complete list of defects rather than a successful build.
        code, output = run(
            ["latexmk", "-pdf", "-f", "-interaction=nonstopmode",
             "-file-line-error", f"{stem}.tex"],
            cwd, timeout,
        )
        result.passes = 1
    elif have("pdflatex"):
        result.engine = "pdflatex"
        bib_tool = detect_bib_tool(tex)
        result.bib_tool = bib_tool or ""

        def latex_pass() -> tuple[int, str]:
            return run(
                ["pdflatex", "-interaction=nonstopmode", "-file-line-error", f"{stem}.tex"],
                cwd, timeout,
            )

        code, output = latex_pass()
        result.passes = 1
        if bib_tool:
            run([bib_tool, stem], cwd, timeout)
            code, output = latex_pass()
            result.passes += 1
        # Extra passes until cross-references settle.
        for _ in range(max_passes - result.passes):
            code, output = latex_pass()
            result.passes += 1
            log = cwd / f"{stem}.log"
            if log.exists():
                text = log.read_text(encoding="utf-8", errors="replace")
                if "Rerun to get" not in text and "Label(s) may have changed" not in text:
                    break
    else:
        result.failure = "no LaTeX engine found (looked for latexmk and pdflatex)"
        return result

    log_path = cwd / f"{stem}.log"
    if not log_path.exists():
        result.failure = f"no log produced; compiler said: {output[-500:]}"
        return result

    result.diagnostics, result.pages = parse_log(
        log_path.read_text(encoding="utf-8", errors="replace")
    )
    result.diagnostics.extend(parse_bib_log(cwd / f"{stem}.blg"))
    result.ok = not result.diagnostics
    return result


def parse_bib_log(blg: Path) -> list[Diagnostic]:
    """Read the BibTeX/Biber log.

    These errors do not appear in the LaTeX log at all. A malformed .bib entry
    produces a confident, clean-looking pdflatex run while the entry silently
    fails to render -- so a build checked only against the .log can report
    "zero warnings" on a paper whose bibliography is broken.
    """
    if not blg.exists():
        return []
    diagnostics: list[Diagnostic] = []
    name = blg.name
    for line in blg.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if lowered.startswith(("i was expecting", "i couldn't", "sorry---")) or \
           re.match(r"^(error|repeated entry|illegal)", lowered):
            diagnostics.append(Diagnostic("error", stripped, name, severity="error"))
        elif lowered.startswith("warning--"):
            diagnostics.append(Diagnostic("warning", stripped[len("warning--"):].strip(), name))
        elif "there were" in lowered and "error message" in lowered:
            diagnostics.append(Diagnostic("error", stripped, name, severity="error"))
    return diagnostics


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def report(result: BuildResult, verbose: bool) -> None:
    name = Path(result.document).parent.name + "/" + Path(result.document).name
    if result.failure:
        print(f"  {name:<44} BUILD FAILED: {result.failure}")
        return

    s = result.summary()
    status = "CLEAN" if result.ok else "ISSUES"
    pages = f"{result.pages}p" if result.pages else "?"
    print(
        f"  {name:<44} {status:<7} "
        f"err={s['errors']} warn={s['warnings']} over={s['overfull']} "
        f"under={s['underfull']} undef_ref={s['undefined_refs']} "
        f"undef_cite={s['undefined_cites']} {pages}"
    )

    if result.ok:
        return

    order = ["error", "undefined_ref", "undefined_cite", "warning", "overfull", "underfull"]
    for kind in order:
        items = [d for d in result.diagnostics if d.kind == kind]
        if not items:
            continue
        shown = items if verbose else items[:8]
        print(f"      {kind} ({len(items)}):")
        for d in shown:
            where = f"{d.source_file}" if d.source_file else "?"
            at = f":{d.lines}" if d.lines else ""
            print(f"        {where}{at}  {d.message[:120]}")
        if len(items) > len(shown):
            print(f"        ... {len(items) - len(shown)} more (use --verbose)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="+", help=".tex files or directories containing one")
    ap.add_argument("--json", metavar="PATH", help="also write a machine-readable report")
    ap.add_argument("--verbose", action="store_true", help="show every diagnostic")
    ap.add_argument("--timeout", type=int, default=300, help="per-pass timeout in seconds")
    ap.add_argument("--keep-going", action="store_true", help="always exit 0")
    args = ap.parse_args()

    documents: list[Path] = []
    for raw in args.targets:
        found = find_documents(Path(raw))
        if not found:
            print(f"  {raw:<44} SKIPPED: no file with \\documentclass found")
            continue
        documents.extend(found)

    if not documents:
        print("nothing to build")
        return 0 if args.keep_going else 1

    print(f"building {len(documents)} document(s)")
    results = [build(tex, timeout=args.timeout) for tex in documents]
    for result in results:
        report(result, args.verbose)

    if args.json:
        payload = [
            {**asdict(r), "summary": r.summary(),
             "diagnostics": [asdict(d) for d in r.diagnostics]}
            for r in results
        ]
        Path(args.json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")

    clean = sum(1 for r in results if r.ok)
    print(f"\n{clean}/{len(results)} clean")
    if args.keep_going:
        return 0
    return 0 if clean == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
