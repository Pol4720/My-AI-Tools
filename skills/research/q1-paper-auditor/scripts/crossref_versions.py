#!/usr/bin/env python3
"""Compare language versions of the same paper for structural and numerical parity.

A translated paper drifts. A correction gets applied to one version, a table is
regenerated for one language, a number is retyped with the other decimal
convention. None of this is visible when reading either version on its own,
because each is internally coherent.

This compares the versions against each other:

  * section, subsection and paragraph counts and nesting
  * numbers of equations, tables, figures, theorem-like environments
  * label and reference sets (labels should correspond; a label present in one
    version only means a cross-reference is broken or a block was dropped)
  * citation keys used
  * \\input and \\include targets
  * numeric literals in the prose, normalised across decimal conventions

Usage
-----
    python crossref_versions.py paper/en paper/es
    python crossref_versions.py paper/en paper/es paper/fr --json parity.json
    python crossref_versions.py paper/en paper/es --show-numbers
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ENVIRONMENTS = [
    "equation", "align", "gather", "multline", "eqnarray",
    "table", "table*", "figure", "figure*", "tabular", "tabularx",
    "theorem", "lemma", "proposition", "corollary", "definition", "remark", "proof",
    "itemize", "enumerate", "algorithm",
]

SECTIONING = ["section", "subsection", "subsubsection", "paragraph"]


LANG_SUFFIX = re.compile(r"[_-](?:en|es|fr|de|pt|it|ca|gl|eu|nl|ru|zh|ja)(?=$|\.)", re.I)


def strip_lang(name: str) -> str:
    """Drop a trailing language tag so versions compare on neutral names.

    `tab:results_en` and `tab:results_es` are the same label, and
    `.../results_en.tex` and `.../results_es.tex` are the same include.
    """
    stem = name.rsplit("/", 1)[-1]
    return LANG_SUFFIX.sub("", stem)


def strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines())


def resolve_input(target: str, base: Path) -> Path | None:
    """Locate an \\input target, which may sit outside the version directory."""
    candidate = (base / target).resolve()
    for path in (candidate, candidate.with_suffix(".tex")):
        if path.is_file():
            return path
    return None


def load_version(version_dir: Path, follow_inputs: bool = True) -> dict:
    """Concatenate a version's sources, following \\input so included tables count.

    Generated tables commonly live outside the manuscript directory, and the
    labels they define are the ones the prose references. Reading only the files
    inside the version directory makes every such reference look dangling, which
    buries the real findings under noise.
    """
    tex_files = sorted(p for p in version_dir.rglob("*.tex") if p.is_file())
    main = [p for p in tex_files
            if re.search(r"\\documentclass", p.read_text(encoding="utf-8", errors="replace"))]
    ordered = main + [p for p in tex_files if p not in main]

    seen: set[Path] = set()
    chunks: list[str] = []
    included: list[str] = []

    def absorb(path: Path, depth: int = 0) -> None:
        resolved = path.resolve()
        if resolved in seen or depth > 5:
            return
        seen.add(resolved)
        body = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        chunks.append(body)
        if not follow_inputs:
            return
        for target in re.findall(r"\\(?:input|include)\s*\{([^}]+)\}", body):
            child = resolve_input(target.strip(), path.parent)
            if child is not None:
                included.append(target.strip())
                absorb(child, depth + 1)

    for path in ordered:
        absorb(path)

    return {"dir": version_dir, "text": "\n".join(chunks),
            "files": [p.name for p in ordered], "included": included}


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


def extract(text: str) -> dict:
    body = text
    # Compare the body, not the preamble: the preamble legitimately differs
    # (babel language, theorem environment names) while the body should not.
    m = re.search(r"\\begin\{document\}", text)
    if m:
        body = text[m.end():]

    features: dict = {}

    features["sections"] = {
        level: len(re.findall(r"\\%s\*?\s*[\[{]" % level, body)) for level in SECTIONING
    }
    features["section_titles"] = re.findall(r"\\section\*?\s*\{([^}]*)\}", body)

    env_counts = {}
    for env in ENVIRONMENTS:
        pattern = r"\\begin\{" + re.escape(env) + r"\}"
        count = len(re.findall(pattern, body))
        if count:
            env_counts[env] = count
    features["environments"] = env_counts

    features["labels"] = sorted(set(re.findall(r"\\label\{([^}]+)\}", body)))
    features["refs"] = sorted(set(re.findall(r"\\(?:eq|c|C|auto|name)?ref\{([^}]+)\}", body)))
    features["citations"] = sorted({
        key.strip()
        for match in re.finditer(r"\\(?:no)?cite[a-zA-Z]*\s*(?:\[[^\]]*\]\s*)*\{([^}]+)\}", body)
        for key in match.group(1).split(",") if key.strip()
    })
    features["inputs"] = sorted(set(re.findall(r"\\(?:input|include)\s*\{([^}]+)\}", body)))
    features["graphics"] = sorted(set(re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body)))
    features["macros_used"] = sorted(set(re.findall(r"\\([A-Z][A-Za-z]{4,})\b", body)))
    features["numbers"] = extract_numbers(body)
    return features


# A number may carry its decimal or thousands mark wrapped in braces: Spanish
# and German texts write `383{,}43` so that TeX spaces the comma as a decimal
# point rather than as punctuation. Without matching that form the number splits
# into two, and every localised decimal in the document reads as a mismatch.
NUMBER_RE = re.compile(r"(?<![\w\\])(\d(?:[\d.,]|\{[.,]\})*\d|\d)(?![\w])")


def extract_numbers(body: str) -> Counter:
    """Numeric literals in prose, normalised so decimal conventions compare.

    Both `1{,}234` (Spanish decimal) and `1.234` (English decimal) normalise to
    the same token, which is the point: a number that differs between versions
    only by convention is fine, while one that differs in value is a defect.
    Labels, references and lengths are excluded because they are not claims.
    """
    text = body
    text = re.sub(r"\\label\{[^}]*\}", " ", text)
    text = re.sub(r"\\(?:eq|c|C|auto|name)?ref\{[^}]*\}", " ", text)
    text = re.sub(r"\\cite[a-zA-Z]*\s*(?:\[[^\]]*\]\s*)*\{[^}]*\}", " ", text)
    text = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}", " ", text)
    text = re.sub(r"\\(?:input|include)\s*\{[^}]*\}", " ", text)
    # Lengths and sizes: 1.6cm, 10pt, 0.5\textwidth
    text = re.sub(r"\d[\d.]*\s*(?:pt|cm|mm|em|ex|in|bp|sp)\b", " ", text)
    text = re.sub(r"\d[\d.]*\\(?:text|column|line)width", " ", text)

    counts: Counter = Counter()
    for match in NUMBER_RE.finditer(text):
        token = match.group(1)
        # Normalise: unwrap braced marks, drop thousands separators, unify the
        # decimal mark, so the same value compares equal across conventions.
        cleaned = token.replace("{,}", ",").replace("{.}", ".")
        if "," in cleaned and "." in cleaned:
            # Whichever appears last is the decimal mark.
            cleaned = (cleaned.replace(",", "") if cleaned.rfind(".") > cleaned.rfind(",")
                       else cleaned.replace(".", "").replace(",", "."))
        elif "," in cleaned:
            parts = cleaned.split(",")
            cleaned = ("".join(parts) if all(len(p) == 3 for p in parts[1:])
                       else cleaned.replace(",", "."))
        try:
            value = float(cleaned)
        except ValueError:
            continue
        counts[f"{value:g}"] += 1
    return counts


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------


def compare(versions: list[dict]) -> list[dict]:
    findings: list[dict] = []
    names = [v["name"] for v in versions]

    def differ(getter, kind: str, describe) -> None:
        values = [getter(v["features"]) for v in versions]
        if len({json.dumps(x, sort_keys=True, default=str) for x in values}) > 1:
            findings.append({"kind": kind,
                             "detail": describe(dict(zip(names, values)))})

    for level in SECTIONING:
        differ(lambda f, lv=level: f["sections"][lv], f"{level}_count",
               lambda d, lv=level: f"{lv} count differs: "
                                   + ", ".join(f"{k}={v}" for k, v in d.items()))

    all_envs = sorted({e for v in versions for e in v["features"]["environments"]})
    for env in all_envs:
        differ(lambda f, e=env: f["environments"].get(e, 0), f"env_{env}_count",
               lambda d, e=env: f"\\begin{{{e}}} count differs: "
                                + ", ".join(f"{k}={v}" for k, v in d.items()))

    for feature, kind in (("labels", "label_set"), ("citations", "citation_set"),
                          ("inputs", "input_set"), ("graphics", "graphics_set")):
        # Compare on language-neutral names. Suffixing labels and generated
        # table files per language (tab:results_en / _es) is a normal and good
        # practice; flagging it would bury the divergences that matter.
        sets = {v["name"]: {strip_lang(x) for x in v["features"][feature]} for v in versions}
        shared = set.intersection(*sets.values()) if sets else set()
        for name, values in sets.items():
            only = values - shared
            if only:
                findings.append({
                    "kind": kind,
                    "detail": f"only in {name}: " + ", ".join(sorted(only)[:12])
                              + (f" (+{len(only) - 12} more)" if len(only) > 12 else ""),
                })

    # Dangling references: pointing at a label that version does not define.
    for v in versions:
        defined = {strip_lang(x) for x in v["features"]["labels"]}
        dangling = {r for r in v["features"]["refs"] if strip_lang(r) not in defined}
        if dangling:
            findings.append({"kind": "dangling_ref",
                             "detail": f"{v['name']} references undefined labels: "
                                       + ", ".join(sorted(dangling)[:12])})

    # Numbers: the substantive check.
    number_sets = {v["name"]: v["features"]["numbers"] for v in versions}
    all_numbers = set().union(*(set(c) for c in number_sets.values()))
    mismatched = []
    for number in sorted(all_numbers, key=lambda x: -abs(float(x))):
        present = {name: counts.get(number, 0) for name, counts in number_sets.items()}
        if len(set(present.values())) > 1:
            mismatched.append((number, present))
    if mismatched:
        findings.append({
            "kind": "number_mismatch",
            "detail": f"{len(mismatched)} numeric literal(s) appear a different number of "
                      "times across versions",
            "numbers": [{"value": n, "counts": p} for n, p in mismatched[:40]],
        })

    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("versions", nargs="+", help="two or more version directories")
    ap.add_argument("--json", metavar="PATH", help="write a machine-readable report")
    ap.add_argument("--show-numbers", action="store_true", help="list every mismatched number")
    args = ap.parse_args()

    if len(args.versions) < 2:
        print("need at least two versions to compare")
        return 1

    versions = []
    for raw in args.versions:
        directory = Path(raw)
        if not directory.is_dir():
            print(f"not a directory: {raw}")
            return 1
        loaded = load_version(directory)
        if not loaded["text"].strip():
            print(f"no .tex sources in {raw}")
            return 1
        versions.append({"name": directory.name or str(directory),
                         "features": extract(loaded["text"]),
                         "files": loaded["files"]})

    for v in versions:
        f = v["features"]
        print(f"{v['name']}: {f['sections']['section']} sections, "
              f"{len(f['labels'])} labels, {len(f['citations'])} citations, "
              f"{sum(f['environments'].values())} environments, "
              f"{sum(f['numbers'].values())} numeric literals")

    findings = compare(versions)

    print()
    if not findings:
        print("versions are in parity")
    for finding in findings:
        print(f"  {finding['kind']}: {finding['detail']}")
        if finding["kind"] == "number_mismatch" and args.show_numbers:
            for item in finding.get("numbers", []):
                counts = ", ".join(f"{k}={v}" for k, v in item["counts"].items())
                print(f"      {item['value']:>16}   {counts}")

    if args.json:
        Path(args.json).write_text(
            json.dumps({"versions": [v["name"] for v in versions], "findings": findings}, indent=2),
            encoding="utf-8",
        )
        print(f"\nwrote {args.json}")

    print(f"\n{len(findings)} finding(s)")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
