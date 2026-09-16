#!/usr/bin/env python3
"""Validate every skill in this repository before it is published or installed.

Checks the things that actually break a skill in practice:

  - SKILL.md exists, has YAML front matter, and the front matter parses
  - `name` matches the directory, is lowercase-hyphenated, and is at most 64 characters
  - `description` exists, is a single block, and is long enough to trigger reliably
  - every file the SKILL.md references under references/, scripts/ or assets/ exists
  - every bundled Python script parses and exposes --help
  - nothing that looks like a credential is committed

Run it from the repository root:

    python3 scripts/validate_skills.py
    python3 scripts/validate_skills.py --skill skills/engineering/repo-audit-fixer

Exit code 0 means every skill is publishable. Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME = 64
MIN_DESCRIPTION = 60
# claude.ai's own skill-upload validator rejects a description over 1024 characters
# (confirmed against the official skill-creator packager). A repository limit looser than
# the platform's is worse than none: it lets a skill validate green here and still get
# rejected on upload, silently, with no way to tell which of the two disagreed.
MAX_DESCRIPTION = 1024
MAX_SKILL_MD_LINES = 500

SECRET_PATTERNS = [
    (re.compile(r"(?i)\b(api[_-]?key|secret|passwd|password|token)\s*[:=]\s*['\"][A-Za-z0-9/_+-]{16,}"),
     "possible hard-coded credential"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "GitHub token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}"), "API secret key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
]

REFERENCE_RE = re.compile(r"`((?:references|scripts|assets|config)/[A-Za-z0-9_./-]+)`")


def parse_front_matter(text: str) -> tuple[dict, list[str]]:
    """Parse the leading `---` block. A deliberately small YAML subset: scalars,
    `key: >` folded blocks, and `key: |` literal blocks — which is all a SKILL.md needs."""
    problems: list[str] = []
    if not text.startswith("---"):
        return {}, ["SKILL.md does not begin with a `---` front-matter block"]
    end = text.find("\n---", 3)
    if end == -1:
        return {}, ["front-matter block is not closed with `---`"]

    block = text[3:end].strip("\n")
    data: dict[str, str] = {}
    key: str | None = None
    folded: list[str] = []
    mode = ""

    def flush() -> None:
        if key is not None:
            joiner = " " if mode == ">" else "\n"
            data[key] = joiner.join(part.strip() for part in folded).strip()

    for line in block.splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match and not line.startswith((" ", "\t")):
            flush()
            key, value = match.group(1), match.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                mode, folded = value[0], []
            else:
                mode, folded = "", [value]
        elif key is not None:
            folded.append(line)
        else:
            problems.append(f"front matter: cannot parse line {line!r}")
    flush()
    return data, problems


def check_skill(skill_dir: Path, repo_root: Path) -> tuple[list[str], list[str]]:
    """Return (problems, warnings). Problems fail the build; warnings do not."""
    rel = skill_dir.relative_to(repo_root)
    problems: list[str] = []
    warnings: list[str] = []

    def bad(message: str) -> None:
        problems.append(f"{rel}: {message}")

    def warn(message: str) -> None:
        warnings.append(f"{rel}: {message}")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{rel}: no SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    data, front_matter_problems = parse_front_matter(text)
    for problem in front_matter_problems:
        bad(problem)

    # --- name -------------------------------------------------------------------------
    name = data.get("name", "")
    if not name:
        bad("front matter has no `name`")
    else:
        if not NAME_RE.match(name):
            bad(f"name {name!r} must be lowercase letters, digits and single hyphens")
        if len(name) > MAX_NAME:
            bad(f"name is {len(name)} characters; the limit is {MAX_NAME}")
        if name != skill_dir.name:
            bad(f"name {name!r} does not match the directory name {skill_dir.name!r}")

    # --- description ------------------------------------------------------------------
    description = data.get("description", "")
    if not description:
        bad("front matter has no `description` — the skill will never trigger")
    else:
        if len(description) < MIN_DESCRIPTION:
            bad(f"description is only {len(description)} characters; a short description "
                "triggers unreliably — say what it does AND when to use it")
        if len(description) > MAX_DESCRIPTION:
            bad(f"description is {len(description)} characters; the limit is {MAX_DESCRIPTION}")

    # --- body size --------------------------------------------------------------------
    body_lines = len(text.splitlines())
    if body_lines > MAX_SKILL_MD_LINES:
        bad(f"SKILL.md is {body_lines} lines; move detail into references/ so the skill "
            f"loads lean (soft limit {MAX_SKILL_MD_LINES})")

    # --- referenced files exist --------------------------------------------------------
    for reference in sorted(set(REFERENCE_RE.findall(text))):
        if not (skill_dir / reference).exists():
            bad(f"SKILL.md references `{reference}`, which does not exist")

    # --- bundled scripts run ------------------------------------------------------------
    for script in sorted(skill_dir.glob("scripts/*.py")):
        try:
            ast.parse(script.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            bad(f"scripts/{script.name} does not parse: {exc}")
            continue
        result = subprocess.run([sys.executable, str(script), "--help"],
                                capture_output=True, text=True, timeout=60, check=False)
        if result.returncode != 0:
            output = result.stderr or result.stdout
            missing = re.search(r"No module named '([^']+)'", output)
            if missing:
                # A declared third-party dependency is a documentation question, not a
                # broken skill — but it is only acceptable if the skill says so.
                docs = " ".join(
                    path.read_text(encoding="utf-8", errors="replace")
                    for path in skill_dir.glob("*.md")
                )
                module = missing.group(1).split(".")[0]
                if module in docs:
                    warn(f"scripts/{script.name} needs `{module}`, which is documented "
                         "but not installed here — not run")
                else:
                    bad(f"scripts/{script.name} needs `{module}`, which no document in "
                        "the skill declares — add it to the install instructions")
            else:
                tail = output.strip().splitlines()[-3:]
                bad(f"scripts/{script.name} --help failed: {' '.join(tail)}")

    # --- no secrets ----------------------------------------------------------------------
    for path in skill_dir.rglob("*"):
        if not path.is_file() or path.suffix in (".png", ".jpg", ".pdf", ".zip"):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(content):
                bad(f"{path.relative_to(skill_dir)}: {label}")

    return problems, warnings


def find_skills(root: Path) -> list[Path]:
    return sorted(p.parent for p in (root / "skills").rglob("SKILL.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skill", help="validate a single skill directory")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skills = [Path(args.skill).resolve()] if args.skill else find_skills(root)

    if not skills:
        print("no skills found under skills/", file=sys.stderr)
        return 1

    all_problems: list[str] = []
    all_warnings: list[str] = []
    for skill in skills:
        problems, warnings = check_skill(skill, root)
        status = "FAIL" if problems else ("warn" if warnings else "ok")
        print(f"[{status:>4}] {skill.relative_to(root)}")
        all_problems.extend(problems)
        all_warnings.extend(warnings)

    if all_warnings:
        print(f"\n{len(all_warnings)} warning(s):")
        for warning in all_warnings:
            print(f"  - {warning}")

    if all_problems:
        print(f"\n{len(all_problems)} problem(s):", file=sys.stderr)
        for problem in all_problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"\n{len(skills)} skill(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
