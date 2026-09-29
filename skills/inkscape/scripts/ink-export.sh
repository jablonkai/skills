#!/usr/bin/env bash
# Export one SVG to one or more files in a single Inkscape run.
#
#   bash ink-export.sh INPUT.svg OUTPUT... [options]
#
# The output extension picks the format: .png .pdf .eps .ps .svg (plain SVG)
# .emf .wmf. A PNG named with an @Nx suffix (logo@2x.png) is rendered at N times
# the base DPI, so `logo.png logo@2x.png logo.pdf` gives the usual 1x/2x/vector set.
#
# Options (apply to every output):
#   --dpi N            base PNG resolution (default 96 = 1 px per user unit)
#   --id ID[,ID...]    export only these objects (others hidden)
#   --area page|drawing  export the page (default) or the drawing's bounding box
#   --margin N         extra margin around the export area, in user units
#   --background COLOR PNG background colour, e.g. white or '#ffffff'
#   --text-to-path     convert text to outlines in PDF/EPS/SVG output
#
# Inkscape exits 0 even when an action fails, so this script checks stderr and
# that every output was written, and exits 1 otherwise.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() {
  echo "usage: ink-export.sh INPUT.svg OUTPUT... [--dpi N] [--id IDS] [--area page|drawing] [--margin N] [--background COLOR] [--text-to-path]" >&2
  exit 2
}

[[ $# -ge 2 ]] || usage
input=$1
shift
[[ -f "$input" ]] || { echo "input not found: $input" >&2; exit 2; }

dpi=96
flags=()
outputs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dpi) dpi=${2:?}; shift 2 ;;
    --id) flags+=("--export-id=${2:?}" --export-id-only); shift 2 ;;
    --area)
      case "${2:-}" in
        page) flags+=(--export-area-page) ;;
        drawing) flags+=(--export-area-drawing) ;;
        *) usage ;;
      esac
      shift 2 ;;
    --margin) flags+=("--export-margin=${2:?}"); shift 2 ;;
    --background) flags+=("--export-background=${2:?}" --export-background-opacity=1); shift 2 ;;
    --text-to-path) flags+=(--export-text-to-path); shift ;;
    -*) usage ;;
    *) outputs+=("$1"); shift ;;
  esac
done
[[ ${#outputs[@]} -gt 0 ]] || usage

actions=""
for out in "${outputs[@]}"; do
  case "$out" in
    *";"*|*","*) echo "output path must not contain ';' or ',': $out" >&2; exit 2 ;;
  esac
  ext=$(printf '%s' "${out##*.}" | tr '[:upper:]' '[:lower:]')
  case "$ext" in
    png)
      scale=1
      if [[ "$out" =~ @([0-9]+)x\.[pP][nN][gG]$ ]]; then
        scale=${BASH_REMATCH[1]}
      fi
      actions+="export-dpi:$(( dpi * scale ));"
      ;;
    svg) actions+="export-plain-svg;" ;;
    pdf|eps|ps|emf|wmf) ;;
    *) echo "unsupported output extension: .$ext" >&2; exit 2 ;;
  esac
  mkdir -p "$(dirname "$out")"
  rm -f "$out"
  actions+="export-filename:$out;export-do;"
done

log=$(mktemp)
trap 'rm -f "$log"' EXIT
status=0
# ${flags[@]+...} keeps an empty array safe under set -u on macOS's bash 3.2.
bash "$here/inkscape.sh" "$input" ${flags[@]+"${flags[@]}"} --actions="$actions" >"$log" 2>&1 || status=$?

# Real failures show up only as messages; hide the routine ones.
grep -v -e '^Exporting only object' -e '^$' -e 'Gtk-WARNING' -e 'dbind-WARNING' "$log" >&2 || true
if grep -qiE 'did not find|not found|error|failed|select .*at least|expected argument' "$log"; then
  status=1
fi

for out in "${outputs[@]}"; do
  if [[ -s "$out" ]]; then
    echo "$out"
  else
    echo "export failed: $out was not written" >&2
    status=1
  fi
done
exit "$status"
