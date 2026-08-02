#!/usr/bin/env bash

# Syntax and shell-correctness checks for the code this repository ships.
#
# None of the bridges can be executed in CI — they need a live Blender, FreeCAD,
# Cavalry, GIMP, Krita, Rebelle or Affinity on the other end — so a static check
# is the only safety net between a broken script and everyone running
# `npx skills add jablonkai/skills`. shellcheck, python3 and node are all
# preinstalled on GitHub's ubuntu runners, so this adds no CI dependencies.

set -euo pipefail

script_dir=$(cd "$(dirname "$0")" && pwd)
# shellcheck source-path=SCRIPTDIR
# shellcheck source=catalog-lib.sh
source "$script_dir/catalog-lib.sh"
cd "$repo_root"

# Byte-code and other tool droppings go here rather than into the skill
# directories, so a local run leaves the working tree untouched.
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT

echo "Linting shipped scripts..."

# Every file with one of the given extensions under the repo's own scripts
# directory and under the scripts/ of each published skill. Nested package
# directories (figma_rn/, krita_bridge/) are included, which a flat
# skills/*/scripts/*.py glob would silently skip. Skills excluded from version
# control are local and never reach a consumer, so skill_dirs() leaves them out
# here as it does in validate.sh.
lint_files() {
  local name_expr=()
  local ext
  local skill

  for ext in "$@"; do
    [[ ${#name_expr[@]} -eq 0 ]] || name_expr+=(-o)
    name_expr+=(-name "*.$ext")
  done

  {
    find .github/scripts -type f \( "${name_expr[@]}" \)

    while IFS= read -r skill; do
      [[ -d "skills/$skill/scripts" ]] || continue
      find "skills/$skill/scripts" -type f \( "${name_expr[@]}" \)
    done < <(skill_dirs)
  } | sort
}

# Collects lint_files() output into the caller's `files` array. A plain read loop
# rather than mapfile, which macOS's bash 3.2 does not have.
collect() {
  local file

  files=()

  while IFS= read -r file; do
    files+=("$file")
  done < <(lint_files "$@")
}

require() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Cannot lint: $1 is not installed — $2"
    exit 1
  fi
}

check_shell() {
  local files

  collect sh
  [[ ${#files[@]} -gt 0 ]] || return 0

  require shellcheck "install it with 'brew install shellcheck'"
  shellcheck "${files[@]}"
  echo "  shellcheck: ${#files[@]} files"
}

check_python() {
  local files

  collect py
  [[ ${#files[@]} -gt 0 ]] || return 0

  require python3 "install Python 3"
  PYTHONPYCACHEPREFIX="$scratch/pycache" python3 -m py_compile "${files[@]}"
  echo "  python3 -m py_compile: ${#files[@]} files"
}

check_javascript() {
  local files
  local file

  collect js mjs
  [[ ${#files[@]} -gt 0 ]] || return 0

  require node "install Node.js"

  for file in "${files[@]}"; do
    node --check "$file"
  done

  echo "  node --check: ${#files[@]} files"
}

check_shell
check_python
check_javascript

echo "Lint passed."
