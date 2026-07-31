#!/usr/bin/env bash

# Shared helpers for the catalog scripts. Sourced by validate.sh and
# generate-catalog.sh so the two agree on which skills exist and how their
# frontmatter is read — a disagreement there would let the generator emit a
# catalog the validator considers correct, or vice versa.

# Consumed by the sourcing script, which cd's here before calling anything below —
# skill_dirs() and the frontmatter helpers all use repo-relative paths.
# shellcheck disable=SC2034
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

# Skills excluded from version control (see .gitignore) are kept local and are not
# part of the published catalog, so every check and every rendered entry operates
# on this list only — link checking included, via markdown_files() in validate.sh.
# Outside a git checkout nothing is ignored and all skill directories are used.
skill_dirs() {
  local dir

  for dir in skills/*/; do
    dir=${dir%/}
    [[ -d "$dir" ]] || continue
    git check-ignore -q "$dir" 2>/dev/null && continue
    basename "$dir"
  done | sort
}

# Top-level frontmatter keys of a SKILL.md: the unindented `key:` lines between the
# opening `---` and the closing one. Nested keys (list items, mapping values) are
# indented and therefore skipped.
frontmatter_keys() {
  awk 'NR == 1 && $0 == "---" { inside = 1; next }
       inside && $0 == "---" { exit }
       inside && /^[A-Za-z][A-Za-z0-9_-]*:/ { sub(/:.*/, ""); print }' "$1"
}

# The value of a single-line frontmatter field, with one layer of surrounding
# quotes removed. Fields rendered into the catalog (summary, category) are
# single-line by convention so this stays a plain read rather than a YAML parse.
frontmatter_value() {
  grep -m1 -E "^$2:" "$1" | sed -E "s/^$2:[[:space:]]*//; s/^[\"']//; s/[\"']$//"
}

contains() {
  local needle=$1
  shift
  local candidate

  for candidate in "$@"; do
    [[ "$candidate" == "$needle" ]] && return 0
  done

  return 1
}
