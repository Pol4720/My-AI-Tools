#!/usr/bin/env python3
"""Check bibliography integrity for a LaTeX paper, across language versions.

Finds the things a referee or copy-editor will find: citations with no entry,
entries nobody cites, duplicate keys, entries missing fields their type requires,
suspect years, unmarked preprints, and -- for multi-language papers -- entries
that differ between versions.

Usage
-----
    python audit_bibliography.py paper/en
    python audit_bibliography.py paper/en paper/es      # also compares versions
    python audit_bibliography.py paper/en --json bib.json

Exit status is 0 when nothing was found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Fields a reader needs in order to actually find the work. Deliberately not the
# full BibTeX requirement list -- the aim is "could someone locate this", which
# is the standard a copy-editor applies.
REQUIRED_FIELDS = {
    "article": ["author", "title", "journal", "year"],
    "inproceedings": ["author", "title", "booktitle", "year"],
    "conference": ["author", "title", "booktitle", "year"],
    "book": ["author", "title", "publisher", "year"],
    "inbook": ["author", "title", "publisher", "year"],
    "incollection": ["author", "title", "booktitle", "publisher", "year"],
    "phdthesis": ["author", "title", "school", "year"],
    "mastersthesis": ["author", "title", "school", "year"],
    "techreport": ["author", "title", "institution", "year"],
    "misc": ["title"],
    "unpublished": ["author", "title", "note"],
    "online": ["title", "url"],
}

PREPRINT_HINTS = ("arxiv", "biorxiv", "medrxiv", "ssrn", "preprint", "hal-", "osf.io")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_bib(text: str) -> dict[str, dict]:
    """Split a .bib file into {key: {type, fields, raw}} by brace matching.

    Regex alone cannot do this: entries nest braces arbitrarily deep inside
    field values. Matching braces is the only correct approach.
    """
    entries: dict[str, dict] = {}
    for match in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        entry_type, key = match.group(1).lower(), match.group(2)
        # Start brace counting at the brace that opens the entry, not at the
        # comma after the key: starting later makes the first field's closing
        # brace look like the end of the entry, which silently truncates every
        # record to its first field.
        open_brace = text.find("{", match.start())
        if open_brace == -1:
            continue
        depth, end = 0, None
        for i in range(open_brace, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if end is None:
            continue  # unbalanced braces; reported as unparseable below
        raw = text[match.start() : end]
        body = text[match.end() : end - 1]

        fields: dict[str, str] = {}
        for fmatch in re.finditer(r"(\w+)\s*=\s*", body):
            name = fmatch.group(1).lower()
            rest = body[fmatch.end() :].lstrip()
            if not rest:
                continue
            if rest[0] == "{":
                d, stop = 0, None
                for j, ch in enumerate(rest):
                    if ch == "{":
                        d += 1
                    elif ch == "}":
                        d -= 1
                        if d == 0:
                            stop = j
                            break
                value = rest[1:stop] if stop else rest[1:]
            elif rest[0] == '"':
                stop = rest.find('"', 1)
                value = rest[1:stop] if stop > 0 else rest[1:]
            else:
                value = re.split(r"[,\n]", rest)[0]
            fields[name] = " ".join(value.split())

        entries[key] = {"type": entry_type, "fields": fields, "raw": raw}
    return entries


CITE_PATTERN = re.compile(r"\\(?:no)?cite[a-zA-Z]*\s*(?:\[[^\]]*\]\s*)*\{([^}]+)\}")


def collect_citations(tex_files: list[Path]) -> dict[str, list[str]]:
    """Map each cited key to the files citing it, ignoring commented-out lines."""
    cited: dict[str, list[str]] = {}
    for path in tex_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            code = re.sub(r"(?<!\\)%.*$", "", line)
            for match in CITE_PATTERN.finditer(code):
                for key in match.group(1).split(","):
                    key = key.strip()
                    if key:
                        cited.setdefault(key, []).append(path.name)
    return cited


def gather(version_dir: Path) -> tuple[list[Path], list[Path]]:
    tex = sorted(p for p in version_dir.rglob("*.tex") if p.is_file())
    bib = sorted(p for p in version_dir.rglob("*.bib") if p.is_file())
    return tex, bib


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def audit_version(version_dir: Path) -> dict:
    tex_files, bib_files = gather(version_dir)
    findings: list[dict] = []

    if not bib_files:
        return {
            "version": str(version_dir),
            "findings": [{"kind": "no_bibliography", "detail": "no .bib file found"}],
            "entries": {}, "cited": {},
        }

    entries: dict[str, dict] = {}
    duplicates: list[str] = []
    for bib in bib_files:
        text = bib.read_text(encoding="utf-8", errors="replace")
        parsed = parse_bib(text)

        declared = len(re.findall(r"^\s*@\w+\s*\{", text, re.M))
        if declared > len(parsed):
            findings.append({
                "kind": "unparseable_entries",
                "detail": f"{bib.name}: {declared - len(parsed)} entries could not be parsed "
                          "(unbalanced braces?)",
            })
        for key, entry in parsed.items():
            if key in entries:
                duplicates.append(key)
            entries[key] = entry

    for key in sorted(set(duplicates)):
        findings.append({"kind": "duplicate_key", "key": key,
                         "detail": "defined more than once; BibTeX silently keeps one"})

    cited = collect_citations(tex_files)

    for key in sorted(set(cited) - set(entries)):
        findings.append({"kind": "cited_but_missing", "key": key,
                         "detail": f"cited in {', '.join(sorted(set(cited[key])))} but absent from the .bib"})

    for key in sorted(set(entries) - set(cited)):
        findings.append({"kind": "uncited_entry", "key": key,
                         "detail": "present in the .bib but never cited"})

    for key in sorted(set(cited) & set(entries)):
        entry = entries[key]
        required = REQUIRED_FIELDS.get(entry["type"], ["title"])
        missing = [f for f in required if not entry["fields"].get(f)]
        if missing:
            findings.append({"kind": "incomplete_entry", "key": key,
                             "detail": f"@{entry['type']} missing: {', '.join(missing)}"})

        year = entry["fields"].get("year", "")
        if year and not re.fullmatch(r"\d{4}", year.strip()):
            findings.append({"kind": "suspect_year", "key": key, "detail": f"year = '{year}'"})

        blob = " ".join(entry["fields"].get(f, "") for f in
                        ("journal", "booktitle", "note", "howpublished", "url", "eprint")).lower()
        if any(hint in blob for hint in PREPRINT_HINTS):
            marked = "preprint" in blob or entry["type"] in ("misc", "unpublished", "online")
            if not marked:
                findings.append({"kind": "unmarked_preprint", "key": key,
                                 "detail": "looks like a preprint but is typed as a peer-reviewed work"})

    return {"version": str(version_dir), "findings": findings,
            "entries": entries, "cited": cited}


def compare_versions(audits: list[dict]) -> list[dict]:
    """Entries that differ between language versions of the same paper."""
    findings: list[dict] = []
    if len(audits) < 2:
        return findings

    key_sets = {a["version"]: set(a["entries"]) for a in audits if a["entries"]}
    if len(key_sets) < 2:
        return findings

    shared = set.intersection(*key_sets.values())
    everything = set.union(*key_sets.values())

    for key in sorted(everything - shared):
        present = [Path(v).name for v, keys in key_sets.items() if key in keys]
        absent = [Path(v).name for v, keys in key_sets.items() if key not in keys]
        findings.append({"kind": "version_key_mismatch", "key": key,
                         "detail": f"present in {', '.join(present)}; absent from {', '.join(absent)}"})

    # Same key, different content: usually a correction applied to one version only.
    for key in sorted(shared):
        variants = {}
        for audit in audits:
            entry = audit["entries"].get(key)
            if not entry:
                continue
            signature = tuple(sorted(
                (f, v) for f, v in entry["fields"].items()
                if f in ("author", "title", "year", "journal", "booktitle", "volume", "pages")
            ))
            variants.setdefault(signature, []).append(Path(audit["version"]).name)
        if len(variants) > 1:
            findings.append({
                "kind": "version_entry_differs", "key": key,
                "detail": "same key, different metadata across versions: "
                          + " vs ".join("/".join(v) for v in variants.values()),
            })
    return findings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

SEVERITY = {
    "cited_but_missing": "error",
    "duplicate_key": "error",
    "unparseable_entries": "error",
    "no_bibliography": "error",
    "version_key_mismatch": "error",
    "version_entry_differs": "error",
    "incomplete_entry": "major",
    "suspect_year": "major",
    "unmarked_preprint": "minor",
    "uncited_entry": "minor",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("versions", nargs="+", help="directories, one per language version")
    ap.add_argument("--json", metavar="PATH", help="write a machine-readable report")
    ap.add_argument("--ignore-uncited", action="store_true",
                    help="do not report entries that are present but never cited")
    args = ap.parse_args()

    audits = [audit_version(Path(v)) for v in args.versions]
    cross = compare_versions(audits)

    total = 0
    for audit in audits:
        findings = audit["findings"]
        if args.ignore_uncited:
            findings = [f for f in findings if f["kind"] != "uncited_entry"]
        name = Path(audit["version"]).name or audit["version"]
        n_entries, n_cited = len(audit["entries"]), len(audit["cited"])
        print(f"\n{name}: {n_entries} entries, {n_cited} distinct citations")
        if not findings:
            print("  clean")
        for finding in sorted(findings, key=lambda f: SEVERITY.get(f["kind"], "minor")):
            total += 1
            key = f" [{finding['key']}]" if finding.get("key") else ""
            print(f"  {SEVERITY.get(finding['kind'], 'minor'):<5} {finding['kind']}{key}: {finding['detail']}")

    if cross:
        print(f"\ncross-version ({len(args.versions)} versions)")
        for finding in cross:
            total += 1
            key = f" [{finding['key']}]" if finding.get("key") else ""
            print(f"  error {finding['kind']}{key}: {finding['detail']}")
    elif len(args.versions) > 1:
        print("\ncross-version: bibliographies agree")

    if args.json:
        payload = {
            "versions": [{"version": a["version"], "findings": a["findings"],
                          "n_entries": len(a["entries"]), "n_cited": len(a["cited"])}
                         for a in audits],
            "cross_version": cross,
        }
        Path(args.json).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")

    print(f"\n{total} finding(s)")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
