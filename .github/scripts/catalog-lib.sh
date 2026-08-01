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

# The body of the YAML frontmatter: the lines between the opening `---` on line 1
# and the closing one. Nothing is printed when the block is missing or never
# closed, so no reader below can be fooled by a body line that happens to look
# like a frontmatter field. Every frontmatter read goes through here.
frontmatter_block() {
  awk 'NR == 1 && $0 == "---" { inside = 1; next }
       inside && $0 == "---" { closed = 1; exit }
       inside { block = block $0 "\n" }
       END { if (closed) printf "%s", block }' "$1"
}

# Whether the frontmatter block opens on line 1 and is closed. Separate from
# frontmatter_block() so callers can report an unterminated block rather than
# silently treating it as empty.
frontmatter_closed() {
  awk 'NR == 1 && $0 == "---" { inside = 1; next }
       inside && $0 == "---" { closed = 1; exit }
       END { exit(closed ? 0 : 1) }' "$1"
}

# Top-level frontmatter keys of a SKILL.md: the unindented `key:` lines inside the
# block. Nested keys (list items, mapping values) are indented and therefore
# skipped.
frontmatter_keys() {
  frontmatter_block "$1" | awk '/^[A-Za-z][A-Za-z0-9_-]*:/ { sub(/:.*/, ""); print }'
}

# Whether a top-level key is declared in the frontmatter block.
frontmatter_has_key() {
  local key

  while IFS= read -r key; do
    [[ "$key" == "$2" ]] && return 0
  done < <(frontmatter_keys "$1")

  return 1
}

# The value of a single-line frontmatter field, with one layer of surrounding
# quotes removed; empty when the field is absent. Fields rendered into the catalog
# (summary, category) are single-line by convention so this stays a plain read
# rather than a YAML parse.
frontmatter_value() {
  frontmatter_block "$1" | awk -v key="$2" '
    !found && index($0, key ":") == 1 {
      found = 1
      value = substr($0, length(key) + 2)
      sub(/^[[:space:]]+/, "", value)
      sub(/^["'"'"']/, "", value)
      sub(/["'"'"']$/, "", value)
      print value
    }'
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
