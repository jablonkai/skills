#!/usr/bin/env bash
# Trace a raster image (PNG, JPEG, BMP, ...) to an SVG of filled paths with
# Inkscape's multi-colour Potrace, remove the source bitmap, and optionally
# simplify the result.
#
#   bash ink-trace.sh INPUT.png OUTPUT.svg [options]
#
# Options:
#   --flat              preset for logos, icons and flat artwork: --no-smooth
#                       --no-stack --smooth-corners 0 (sharp, exact edges, no halos)
#   --scans N           colours to separate (default 8; 2 gives a bold two-tone)
#   --speckles N        suppress blobs smaller than N px (default 2)
#   --smooth-corners F  0 = sharp corners .. 1.34 = round (default 1.0)
#   --optimize F        curve optimisation tolerance (default 0.2)
#   --keep-background   keep the lightest (background) colour layer
#   --no-stack          cut holes instead of stacking scans on top of each other
#   --no-smooth         skip Potrace's pre-smoothing of the bitmap
#   --simplify          run path-simplify after tracing (fewer nodes)
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() {
  echo "usage: ink-trace.sh INPUT OUTPUT.svg [--flat] [--scans N] [--speckles N] [--smooth-corners F] [--optimize F] [--keep-background] [--no-stack] [--no-smooth] [--simplify]" >&2
  exit 2
}

[[ $# -ge 2 ]] || usage
input=$1 output=$2
shift 2
[[ -f "$input" ]] || { echo "input not found: $input" >&2; exit 2; }
case "$output" in *.svg) ;; *) echo "output must end in .svg" >&2; exit 2 ;; esac
case "$output" in *";"*|*","*) echo "output path must not contain ';' or ','" >&2; exit 2 ;; esac

scans=8 speckles=2 corners=1.0 optimize=0.2 remove_bg=true stack=true smooth=true simplify=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --flat) smooth=false stack=false corners=0; shift ;;
    --scans) scans=${2:?}; shift 2 ;;
    --speckles) speckles=${2:?}; shift 2 ;;
    --smooth-corners) corners=${2:?}; shift 2 ;;
    --optimize) optimize=${2:?}; shift 2 ;;
    --keep-background) remove_bg=false; shift ;;
    --no-stack) stack=false; shift ;;
    --no-smooth) smooth=false; shift ;;
    --simplify) simplify="select-clear;select-by-element:path;path-simplify;"; shift ;;
    *) usage ;;
  esac
done

mkdir -p "$(dirname "$output")"
rm -f "$output"

# object-trace takes exactly 7 positional arguments on 1.4:
# scans, smooth, stack, remove_background, speckles, smooth_corners, optimize.
# Opening a bitmap directly wraps the <image> in a group, so select it by element.
actions="select-by-element:image;"
actions+="object-trace:$scans,$smooth,$stack,$remove_bg,$speckles,$corners,$optimize;"
actions+="select-clear;select-by-element:image;delete-selection;"
actions+="$simplify"
actions+="export-plain-svg;export-filename:$output;export-do"

log=$(mktemp)
trap 'rm -f "$log"' EXIT
bash "$here/inkscape.sh" "$input" --actions="$actions" >"$log" 2>&1 || true
grep -v -e '^Tracing' -e '^$' "$log" >&2 || true

if [[ ! -s "$output" ]] || grep -q '<image' "$output"; then
  echo "trace failed: $output missing or still contains the bitmap" >&2
  exit 1
fi
echo "$output"
