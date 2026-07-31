#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$repo_root"

echo "Validating skill catalog..."

# Skills excluded from version control (see .gitignore) are kept local and are not
# part of the published catalog, so every check below operates on this list only
# — link checking included, via markdown_files() further down.
# Outside a git checkout nothing is ignored and all skill directories are checked.
skill_dirs() {
  local dir

  for dir in skills/*/; do
    dir=${dir%/}
    [[ -d "$dir" ]] || continue
    git check-ignore -q "$dir" 2>/dev/null && continue
    basename "$dir"
  done | sort
}

check_skill_frontmatter() {
  local file

  while IFS= read -r file; do
    [[ -f "$file" ]] || continue

    if [[ $(head -n 1 "$file") != "---" ]]; then
      echo "Missing YAML frontmatter start: $file"
      exit 1
    fi

    if ! grep -Eq '^name:' "$file"; then
      echo "Missing name field: $file"
      exit 1
    fi

    if ! grep -Eq '^description:' "$file"; then
      echo "Missing description field: $file"
      exit 1
    fi
  done < <(skill_dirs | sed 's|^|skills/|; s|$|/SKILL.md|')
}

# Top-level frontmatter keys of a SKILL.md: the unindented `key:` lines between the
# opening `---` and the closing one. Nested keys (list items, mapping values) are
# indented and therefore skipped.
frontmatter_keys() {
  awk 'NR == 1 && $0 == "---" { inside = 1; next }
       inside && $0 == "---" { exit }
       inside && /^[A-Za-z][A-Za-z0-9_-]*:/ { sub(/:.*/, ""); print }' "$1"
}

frontmatter_value() {
  grep -m1 -E "^$2:" "$1" | sed -E "s/^$2:[[:space:]]*//; s/^[\"']//; s/[\"']$//"
}

# The documented field set (see AGENTS.md). Rejecting anything else keeps
# tool-generated blocks — e.g. the `metadata:` block written by `gh skill install`,
# which pins a repo URL and tree SHA — from drifting into the catalog.
readonly ALLOWED_FRONTMATTER_FIELDS=(
  name description category risk tags allowed-tools argument-hint license
)
readonly ALLOWED_RISK_VALUES=(low medium high)

contains() {
  local needle=$1
  shift
  local candidate

  for candidate in "$@"; do
    [[ "$candidate" == "$needle" ]] && return 0
  done

  return 1
}

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

    if grep -Eq '^risk:' "$file"; then
      risk=$(frontmatter_value "$file" risk)

      if ! contains "$risk" "${ALLOWED_RISK_VALUES[@]}"; then
        echo "Invalid risk value '$risk' in $file (allowed: ${ALLOWED_RISK_VALUES[*]})"
        exit 1
      fi
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
    declared=$(grep -m1 -E '^name:' "skills/$dir_name/SKILL.md" | sed -E 's/^name:[[:space:]]*//; s/^["'"'"']//; s/["'"'"']$//')

    if [[ "$declared" != "$dir_name" ]]; then
      echo "Frontmatter name '$declared' does not match directory: skills/$dir_name"
      exit 1
    fi
  done < <(skill_dirs)
}

# The body of the `## Available Skills` section, up to the next `## ` heading.
# Matching the whole document instead would let a skill dropped from the list
# still pass on the strength of one passing mention elsewhere in the prose.
available_skills_section() {
  awk '/^## Available Skills[[:space:]]*$/ { inside = 1; next }
       /^## / { inside = 0 }
       inside' "$1"
}

# Keep the catalog in the docs honest: every skill directory must be listed in
# the Available Skills section of both README.md and AGENTS.md, and neither may
# list a skill that no longer exists.
check_docs_in_sync() {
  local doc
  local dir_name
  local listed
  local section

  for doc in README.md AGENTS.md; do
    section=$(available_skills_section "$doc")

    if [[ -z "$section" ]]; then
      echo "No '## Available Skills' section found in $doc"
      exit 1
    fi

    while IFS= read -r dir_name; do
      if ! grep -q -- "^- \`$dir_name\`:" <<<"$section"; then
        echo "Skill not listed in the Available Skills section of $doc: $dir_name"
        exit 1
      fi
    done < <(skill_dirs)

    while IFS= read -r listed; do
      if [[ ! -d "skills/$listed" ]]; then
        echo "$doc lists a skill that does not exist: $listed"
        exit 1
      fi
    done < <(grep -oE '^- \`[a-z0-9-]+\`' <<<"$section" | sed -E 's/^- `([a-z0-9-]+)`/\1/' | sort -u)
  done
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
check_skill_structure
check_kebab_case_skill_dirs
check_skill_name_matches_dir
check_docs_in_sync
check_markdown_links

echo "Validation passed."
