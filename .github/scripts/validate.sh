#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd "$(dirname "$0")" && pwd)
# shellcheck source-path=SCRIPTDIR
# shellcheck source=catalog-lib.sh
source "$script_dir/catalog-lib.sh"
cd "$repo_root"

echo "Validating skill catalog..."

# `summary` and `category` are required because the Available Skills sections of
# README.md and AGENTS.md are rendered from them — a skill missing either cannot
# be listed at all.
readonly REQUIRED_FRONTMATTER_FIELDS=(name description summary category)

check_skill_frontmatter() {
  local file
  local field

  while IFS= read -r file; do
    [[ -f "$file" ]] || continue

    if [[ $(head -n 1 "$file") != "---" ]]; then
      echo "Missing YAML frontmatter start: $file"
      exit 1
    fi

    if ! frontmatter_closed "$file"; then
      echo "Unterminated YAML frontmatter block: $file"
      exit 1
    fi

    for field in "${REQUIRED_FRONTMATTER_FIELDS[@]}"; do
      if ! frontmatter_has_key "$file" "$field"; then
        echo "Missing $field field: $file"
        exit 1
      fi
    done
  done < <(skill_dirs | sed 's|^|skills/|; s|$|/SKILL.md|')
}

# The documented field set (see AGENTS.md). Rejecting anything else keeps
# tool-generated blocks — e.g. the `metadata:` block written by `gh skill install`,
# which pins a repo URL and tree SHA — from drifting into the catalog.
readonly ALLOWED_FRONTMATTER_FIELDS=(
  name description summary category risk tags allowed-tools argument-hint license
)
readonly ALLOWED_RISK_VALUES=(low medium high)

check_skill_frontmatter_fields() {
  local dir_name
  local file
  local key
  local risk

  while IFS= read -r dir_name; do
    file="skills/$dir_name/SKILL.md"

    while IFS= read -r key; do
      if ! contains "$key" "${ALLOWED_FRONTMATTER_FIELDS[@]}"; then
        echo "Unknown frontmatter field '$key' in $file (allowed: ${ALLOWED_FRONTMATTER_FIELDS[*]})"
        exit 1
      fi
    done < <(frontmatter_keys "$file")

    if frontmatter_has_key "$file" risk; then
      risk=$(frontmatter_value "$file" risk)

      if ! contains "$risk" "${ALLOWED_RISK_VALUES[@]}"; then
        echo "Invalid risk value '$risk' in $file (allowed: ${ALLOWED_RISK_VALUES[*]})"
        exit 1
      fi
    fi
  done < <(skill_dirs)
}

# Caps from the Agent Skills spec: `description` is the only thing an agent sees
# when deciding whether to load a skill, and a description past the cap is
# truncated — silently costing the skill the tail of its trigger phrases.
readonly MAX_DESCRIPTION_LENGTH=1024
readonly MAX_NAME_LENGTH=64

check_skill_frontmatter_lengths() {
  local dir_name
  local file
  local value

  while IFS= read -r dir_name; do
    file="skills/$dir_name/SKILL.md"

    value=$(frontmatter_value "$file" name)
    if (( ${#value} > MAX_NAME_LENGTH )); then
      echo "Frontmatter name is ${#value} characters in $file (max $MAX_NAME_LENGTH)"
      exit 1
    fi

    value=$(frontmatter_value "$file" description)
    if (( ${#value} > MAX_DESCRIPTION_LENGTH )); then
      echo "Frontmatter description is ${#value} characters in $file (max $MAX_DESCRIPTION_LENGTH)"
      exit 1
    fi
  done < <(skill_dirs)
}

# Progressive disclosure (see AGENTS.md): a long SKILL.md with nothing in
# references/ means detail that should load on demand is instead loaded on every
# invocation. Only a warning — the budget is a smell, not a rule, and some skills
# legitimately have no detail worth splitting out.
readonly SKILL_LINE_BUDGET=250

check_skill_size_budget() {
  local dir_name
  local file
  local lines

  while IFS= read -r dir_name; do
    file="skills/$dir_name/SKILL.md"
    [[ -d "skills/$dir_name/references" ]] && continue

    # BSD wc pads its count with leading spaces; strip them so the message reads
    # cleanly and the comparison below gets a bare integer.
    lines=$(wc -l < "$file" | tr -d '[:space:]')
    if (( lines > SKILL_LINE_BUDGET )); then
      echo "Warning: $file is $lines lines (budget $SKILL_LINE_BUDGET) with no references/ — consider moving detail there"
    fi
  done < <(skill_dirs)
}

check_skill_structure() {
  local dir

  while IFS= read -r dir; do
    [[ -f "skills/$dir/SKILL.md" ]] || {
      echo "Missing SKILL.md in: skills/$dir"
      exit 1
    }
  done < <(skill_dirs)
}

check_kebab_case_skill_dirs() {
  local dir_name

  while IFS= read -r dir_name; do
    [[ "$dir_name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]] || {
      echo "Skill directory must use kebab-case: skills/$dir_name"
      exit 1
    }
  done < <(skill_dirs)
}

# The frontmatter `name:` must match the directory name, otherwise the skill
# resolves under a different name than it is filed under.
check_skill_name_matches_dir() {
  local dir_name
  local declared

  while IFS= read -r dir_name; do
    declared=$(frontmatter_value "skills/$dir_name/SKILL.md" name)

    if [[ "$declared" != "$dir_name" ]]; then
      echo "Frontmatter name '$declared' does not match directory: skills/$dir_name"
      exit 1
    fi
  done < <(skill_dirs)
}

# The Available Skills sections are generated, so the only honest check is to
# re-render them and compare. This subsumes the old presence-only check: a
# missing skill, a stale one, and a description that drifted from the
# frontmatter all show up as a diff.
check_catalog_generated() {
  "$script_dir/generate-catalog.sh" --check
}

# The published set of Markdown files: tracked files plus untracked ones that are
# not gitignored — exactly what a commit would publish. Scoping link checking this
# way keeps it in step with every check above, so a local run and CI agree.
# Outside a git checkout nothing is ignored and every *.md is checked.
markdown_files() {
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files --cached --others --exclude-standard -z -- '*.md' | tr '\0' '\n'
  else
    find . -type f -name '*.md' \
      -not -path './.git/*' -not -path './.serena/*' -not -path './node_modules/*' |
      sed 's|^\./||'
  fi | grep -v '^$' | sort -u
}

check_markdown_links() {
  local file
  local file_dir
  local target
  local resolved_target

  while IFS= read -r file; do
    file_dir=$(dirname "$file")

    while IFS= read -r target; do
      [[ -n "$target" ]] || continue

      if [[ "$target" == http://* || "$target" == https://* || "$target" == mailto:* || "$target" == \#* ]]; then
        continue
      fi

      target=${target%%#*}
      [[ -n "$target" ]] || continue

      if [[ "$target" == /* ]]; then
        resolved_target="$target"
      else
        resolved_target="$file_dir/$target"
      fi

      if [[ ! -e "$resolved_target" ]]; then
        echo "Broken relative Markdown link in $file: $target"
        exit 1
      fi
    done < <(grep -oE '\[[^]]+\]\(([^)]+)\)' "$file" | sed -E 's/.*\(([^)]+)\)/\1/' | sort -u)
  done < <(markdown_files)
}

check_skill_frontmatter
check_skill_frontmatter_fields
check_skill_frontmatter_lengths
check_skill_size_budget
check_skill_structure
check_kebab_case_skill_dirs
check_skill_name_matches_dir
check_catalog_generated
check_markdown_links

echo "Validation passed."
