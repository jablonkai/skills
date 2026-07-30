#!/usr/bin/env bash

set -euo pipefail

repo_root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$repo_root"

echo "Validating skill catalog..."

# Skills excluded from version control (see .gitignore) are kept local and are not
# part of the published catalog, so every check below operates on this list only.
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

# Keep the catalog in the docs honest: every skill directory must be listed in
# both README.md and AGENTS.md, and neither may list a skill that no longer exists.
check_docs_in_sync() {
  local doc
  local dir_name
  local listed

  for doc in README.md AGENTS.md; do
    while IFS= read -r dir_name; do
      if ! grep -q "\`$dir_name\`" "$doc"; then
        echo "Skill not listed in $doc: $dir_name"
        exit 1
      fi
    done < <(skill_dirs)

    while IFS= read -r listed; do
      if [[ ! -d "skills/$listed" ]]; then
        echo "$doc lists a skill that does not exist: $listed"
        exit 1
      fi
    done < <(grep -oE '^- \`[a-z0-9-]+\`' "$doc" | sed -E 's/^- `([a-z0-9-]+)`/\1/' | sort -u)
  done
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
  done < <(find . -type f -name '*.md' -not -path './.git/*' -not -path './.serena/*' -not -path './node_modules/*' | sort)
}

check_skill_frontmatter
check_skill_structure
check_kebab_case_skill_dirs
check_skill_name_matches_dir
check_docs_in_sync
check_markdown_links

echo "Validation passed."
