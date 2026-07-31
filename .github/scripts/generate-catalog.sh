#!/usr/bin/env bash

# Renders the "Available Skills" section of README.md and AGENTS.md from the
# `summary:` and `category:` frontmatter of each skill, so a skill is described
# in exactly one place. Run it after adding or editing a skill; validate.sh
# invokes it with --check, which fails when the committed docs differ from what
# the frontmatter renders — the same check-in-CI pattern as a formatter.
#
#   .github/scripts/generate-catalog.sh            # rewrite the docs in place
#   .github/scripts/generate-catalog.sh --check    # fail on drift, write nothing

set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source-path=SCRIPTDIR
# shellcheck source=catalog-lib.sh
source "$script_dir/catalog-lib.sh"
cd "$repo_root"

readonly BEGIN_MARKER='<!-- BEGIN GENERATED SKILLS -->'
readonly END_MARKER='<!-- END GENERATED SKILLS -->'

# README groups the catalog by theme; each theme collects one or more of the
# per-skill `category:` values. This is the only place the grouping lives, and a
# category missing from it is an error rather than a silent "other" bucket — an
# unlisted skill would otherwise vanish from README while still passing CI.
readonly CATALOG_SECTIONS=(
  "App automation|design-automation,3d,motion-design,cad"
  "GitHub workflows|git,development-workflow,project-management"
  "Development & analysis|code-quality,debugging,testing,documentation,document-conversion"
  "Ultrarunning domain|data-lookup,branding"
)

skill_field() {
  local dir_name=$1
  local field=$2
  local value

  value=$(frontmatter_value "skills/$dir_name/SKILL.md" "$field")

  if [[ -z "$value" ]]; then
    echo "Missing or empty '$field' field: skills/$dir_name/SKILL.md" >&2
    exit 1
  fi

  printf '%s' "$value"
}

section_for_category() {
  local category=$1
  local entry
  local title
  local categories

  for entry in "${CATALOG_SECTIONS[@]}"; do
    title=${entry%%|*}
    categories=${entry#*|}

    # Deliberate word splitting: the comma-separated list becomes separate arguments.
    # shellcheck disable=SC2086
    if contains "$category" ${categories//,/ }; then
      printf '%s' "$title"
      return 0
    fi
  done

  return 1
}

render_entry() {
  # The backticks are literal Markdown, not a command substitution.
  # shellcheck disable=SC2016
  printf -- '- `%s`: %s\n' "$1" "$(skill_field "$1" summary)"
}

# AGENTS.md: one flat, alphabetical list.
render_flat_catalog() {
  local dir_name

  while IFS= read -r dir_name; do
    render_entry "$dir_name"
  done < <(skill_dirs)
}

# README.md: the same entries, grouped under the themes declared above. Sections
# render in CATALOG_SECTIONS order, skills alphabetically within each.
render_grouped_catalog() {
  local entry
  local title
  local dir_name
  local category
  local matched
  local first_section=1

  for entry in "${CATALOG_SECTIONS[@]}"; do
    title=${entry%%|*}
    matched=0

    while IFS= read -r dir_name; do
      category=$(skill_field "$dir_name" category)
      [[ "$(section_for_category "$category" || true)" == "$title" ]] || continue

      if (( matched == 0 )); then
        (( first_section == 0 )) && printf '\n'
        printf '### %s\n' "$title"
        matched=1
        first_section=0
      fi

      render_entry "$dir_name"
    done < <(skill_dirs)
  done
}

# Every skill must land in a section, otherwise it would be silently dropped
# from README while AGENTS.md still lists it.
check_categories_covered() {
  local dir_name
  local category

  while IFS= read -r dir_name; do
    category=$(skill_field "$dir_name" category)

    if ! section_for_category "$category" >/dev/null; then
      echo "Category '$category' (skills/$dir_name) is not mapped to a README section" >&2
      echo "Add it to CATALOG_SECTIONS in .github/scripts/generate-catalog.sh" >&2
      exit 1
    fi
  done < <(skill_dirs)
}

# Exact whole-line matching, matching the awk below — so prose that merely quotes a
# marker inline (the docs explain the mechanism) is not mistaken for a second marker.
check_markers() {
  local file=$1
  local marker

  for marker in "$BEGIN_MARKER" "$END_MARKER"; do
    if [[ $(grep -cFx -- "$marker" "$file") != 1 ]]; then
      echo "Expected exactly one line reading '$marker' in $file" >&2
      exit 1
    fi
  done
}

# The file as it should look: everything outside the markers untouched, the
# rendered catalog between them.
render_doc() {
  local file=$1
  local body=$2

  check_markers "$file"

  BODY="$body" awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
    $0 == begin { print; printf "%s", ENVIRON["BODY"]; skipping = 1; next }
    $0 == end { skipping = 0 }
    !skipping { print }
  ' "$file"
}

main() {
  local mode=${1-}
  local drift=0
  local doc
  local body
  local rendered

  case "$mode" in
    "" | --check) ;;
    *)
      echo "Usage: $0 [--check]" >&2
      exit 2
      ;;
  esac

  check_categories_covered

  for doc in README.md AGENTS.md; do
    if [[ "$doc" == README.md ]]; then
      body=$(render_grouped_catalog)
    else
      body=$(render_flat_catalog)
    fi

    rendered=$(render_doc "$doc" "$body"$'\n')

    if [[ "$mode" == --check ]]; then
      if [[ "$rendered" != "$(cat "$doc")" ]]; then
        echo "$doc is out of sync with the SKILL.md frontmatter:"
        diff -u "$doc" <(printf '%s\n' "$rendered") | tail -n +3 || true
        drift=1
      fi
    else
      printf '%s\n' "$rendered" >"$doc"
    fi
  done

  if (( drift )); then
    echo
    echo "Run .github/scripts/generate-catalog.sh and commit the result."
    exit 1
  fi
}

main "$@"
