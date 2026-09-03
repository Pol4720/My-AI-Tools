#!/usr/bin/env bash
#
# Install this repository's skills into a local Claude Code installation.
#
#   ./scripts/install_skills.sh                  # symlink every skill (recommended)
#   ./scripts/install_skills.sh --copy           # copy instead of symlink
#   ./scripts/install_skills.sh --list           # show what would be installed
#   ./scripts/install_skills.sh repo-audit-fixer # install one skill by name
#   ./scripts/install_skills.sh --target ./.claude/skills   # project-scoped install
#
# Symlinks are the default: edit a skill in this repository and the change is live in
# Claude Code immediately, with git as the single source of truth. Use --copy for a
# machine where the repository will not stay checked out.
#
# Claude Code discovers skills in:
#   ~/.claude/skills/<name>/SKILL.md      personal, every project
#   <project>/.claude/skills/<name>/      project-scoped, shareable via the project repo
#
# Skills enabled through claude.ai are managed there, not by this script — see
# docs/03-manual-setup-checklist.md.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/skills"
TARGET_DIR="${HOME}/.claude/skills"
MODE="symlink"
WANTED=()

usage() { sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)    MODE="copy"; shift ;;
    --list)    MODE="list"; shift ;;
    --target)  TARGET_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    -*)        echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)         WANTED+=("$1"); shift ;;
  esac
done

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "error: no skills/ directory at ${SOURCE_DIR}" >&2
  exit 1
fi

# Collect skills/<domain>/<name>/SKILL.md
mapfile -t SKILL_PATHS < <(find "$SOURCE_DIR" -name SKILL.md -mindepth 2 -maxdepth 3 | sort)

if [[ ${#SKILL_PATHS[@]} -eq 0 ]]; then
  echo "error: no SKILL.md found under ${SOURCE_DIR}" >&2
  exit 1
fi

installed=0
skipped=0

for skill_md in "${SKILL_PATHS[@]}"; do
  skill_dir="$(dirname "$skill_md")"
  name="$(basename "$skill_dir")"
  domain="$(basename "$(dirname "$skill_dir")")"

  if [[ ${#WANTED[@]} -gt 0 ]] && [[ ! " ${WANTED[*]} " =~ [[:space:]]${name}[[:space:]] ]]; then
    continue
  fi

  if [[ "$MODE" == "list" ]]; then
    printf '  %-24s %-14s %s\n' "$name" "($domain)" "${skill_dir#"$REPO_ROOT"/}"
    continue
  fi

  mkdir -p "$TARGET_DIR"
  destination="${TARGET_DIR}/${name}"

  # Only ever replace something this script itself installed. A directory we did not
  # create may be a skill the user is editing in place, and it is not ours to delete.
  if [[ -L "$destination" ]]; then
    rm "$destination"
  elif [[ -e "$destination" ]]; then
    if [[ -f "${destination}/.installed-by-my-ai-tools" ]]; then
      rm -rf "$destination"
    else
      echo "  skip    ${name} — ${destination} exists and was not installed by this script"
      skipped=$((skipped + 1))
      continue
    fi
  fi

  if [[ "$MODE" == "symlink" ]]; then
    ln -s "$skill_dir" "$destination"
    echo "  link    ${name} -> ${skill_dir#"$REPO_ROOT"/}"
  else
    cp -R "$skill_dir" "$destination"
    date -u +"installed %Y-%m-%dT%H:%M:%SZ from My-AI-Tools" \
      > "${destination}/.installed-by-my-ai-tools"
    echo "  copy    ${name}"
  fi
  installed=$((installed + 1))
done

if [[ "$MODE" == "list" ]]; then
  exit 0
fi

echo
echo "${installed} skill(s) installed into ${TARGET_DIR}"
[[ $skipped -gt 0 ]] && echo "${skipped} skipped (see above)"
echo "Restart Claude Code, or start a new session, for it to pick them up."
