#!/usr/bin/env bash
# Batch-convert many SVGs in one Inkscape process (--shell mode), which is far
# faster than one launch per file.
#
#   bash ink-batch.sh --out DIR [--type png|pdf|eps|ps|svg] [--dpi N] [--id ID] INPUT...
#
# INPUT can be SVG files or directories (their *.svg files, not recursive).
# Each file is written to DIR/<name>.<type>. --dpi applies to PNG only
# (default 96); --id exports only that object from every file.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() {
  echo "usage: ink-batch.sh --out DIR [--type png|pdf|eps|ps|svg] [--dpi N] [--id ID] INPUT..." >&2
  exit 2
}

out_dir="" type=png dpi=96 id=""
inputs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --out) out_dir=${2:?}; shift 2 ;;
    --type) type=$(printf '%s' "${2:?}" | tr '[:upper:]' '[:lower:]'); shift 2 ;;
    --dpi) dpi=${2:?}; shift 2 ;;
    --id) id=${2:?}; shift 2 ;;
    -*) usage ;;
    *) inputs+=("$1"); shift ;;
  esac
done
[[ -n "$out_dir" && ${#inputs[@]} -gt 0 ]] || usage
case "$type" in png|pdf|eps|ps|svg) ;; *) echo "unsupported type: $type" >&2; exit 2 ;; esac

files=()
for item in "${inputs[@]}"; do
  if [[ -d "$item" ]]; then
    for f in "$item"/*.svg "$item"/*.SVG; do
      [[ -f "$f" ]] && files+=("$f")
    done
  elif [[ -f "$item" ]]; then
    files+=("$item")
  else
    echo "not found: $item" >&2
    exit 2
  fi
done
[[ ${#files[@]} -gt 0 ]] || { echo "no SVG files found" >&2; exit 2; }

mkdir -p "$out_dir"
script=$(mktemp)
log=$(mktemp)
trap 'rm -f "$script" "$log"' EXIT

prefix=""
[[ "$type" == png ]] && prefix+="export-dpi:$dpi;"
[[ "$type" == svg ]] && prefix+="export-plain-svg;"
[[ -n "$id" ]] && prefix+="export-id:$id;export-id-only:true;"

expected=()
for f in "${files[@]}"; do
  name=$(basename "$f")
  out="$out_dir/${name%.*}.$type"
  case "$f$out" in
    *";"*|*","*|*$'\n'*) echo "skipping path with ';', ',' or newline: $f" >&2; continue ;;
  esac
  rm -f "$out"
  printf 'file-open:%s;%sexport-filename:%s;export-do;file-close\n' "$f" "$prefix" "$out" >>"$script"
  expected+=("$out")
done
echo "quit" >>"$script"

bash "$here/inkscape.sh" --shell <"$script" >"$log" 2>&1 || true
grep -iE 'did not find|not found|error|failed' "$log" >&2 || true

missing=0
for out in ${expected[@]+"${expected[@]}"}; do
  if [[ -s "$out" ]]; then
    echo "$out"
  else
    echo "export failed: $out was not written" >&2
    missing=$(( missing + 1 ))
  fi
done
echo "${#expected[@]} file(s), $missing failed" >&2
[[ $missing -eq 0 && ${#expected[@]} -eq ${#files[@]} ]]
