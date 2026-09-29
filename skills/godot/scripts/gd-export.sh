#!/usr/bin/env bash
# Export a Godot 4 project with a preset from export_presets.cfg, then check that the
# build artifacts exist. Checks the preset name and the export templates first,
# because Godot's own errors for both are easy to miss in the log.
#
#   bash gd-export.sh PROJECT_DIR PRESET OUT_PATH [--debug] [--pack] [--timeout SEC]
#
#   OUT_PATH  Web: build/web/index.html   macOS: build/mac/Game.zip | .app | .dmg
#             Windows: build/win/Game.exe  Linux: build/linux/Game.x86_64
#             A relative OUT_PATH is relative to PROJECT_DIR, as with Godot itself.
#   --debug   debug build (--export-debug) instead of release
#   --pack    data only (--export-pack), OUT_PATH ending in .pck or .zip
#
# Exit codes: 0 artifacts present, 1 export failed, 2 usage/preset/template problem,
#             124 timeout.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() { awk 'NR > 1 && !/^#/ { exit } NR > 1 { sub(/^# ?/, ""); print }' "${BASH_SOURCE[0]}"; exit 2; }

[[ $# -ge 3 ]] || usage
project=$1 preset=$2 out=$3
shift 3
mode=--export-release timeout=600
while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug) mode=--export-debug; shift ;;
    --pack) mode=--export-pack; shift ;;
    --timeout) timeout=$2; shift 2 ;;
    -h | --help) usage ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

cfg="$project/export_presets.cfg"
if [[ ! -f "$cfg" ]]; then
  echo "no export_presets.cfg in $project — author one (see references/formats.md)" >&2
  exit 2
fi
names=$(sed -n 's/^name="\(.*\)"$/\1/p' "$cfg")
if ! grep -qxF "$preset" <<<"$names"; then
  echo "preset \"$preset\" not found; presets are:" >&2
  while IFS= read -r name; do echo "  $name"; done <<<"$names" >&2
  exit 2
fi
# The platform line follows the name line inside the same [preset.N] section.
platform=$(awk -v want="name=\"$preset\"" '
  /^\[preset\.[0-9]+\]$/ { hit = 0 }
  $0 == want { hit = 1 }
  hit && /^platform=/ { gsub(/^platform="|"$/, ""); print; exit }' "$cfg")

if [[ "$mode" != --export-pack ]]; then
  check=$(bash "$here/godot.sh" --check)
  if grep -q 'export templates: MISSING' <<<"$check"; then
    grep -A4 'export templates' <<<"$check" >&2
    exit 2
  fi
fi

project=$(cd "$project" && pwd)
case "$out" in
  /*) abs_out=$out ;;
  *) abs_out="$project/$out" ;;
esac
out_dir=$(dirname "$abs_out")
mkdir -p "$out_dir"
# Output inside the project would be imported and packed into the next export.
if [[ "$out_dir" == "$project"/* ]]; then
  rel=${out_dir#"$project"/}
  top="$project/${rel%%/*}"
  [[ -f "$top/.gdignore" ]] || { touch "$top/.gdignore"; echo "added $top/.gdignore"; }
fi

log=$(mktemp -t gd-export)
rc=0
(perl -e 'alarm shift; exec @ARGV' "$timeout" bash "$here/godot.sh" --headless \
  --path "$project" -l en "$mode" "$preset" "$abs_out" >"$log" 2>&1 || exit $?) 2>/dev/null || rc=$?
perl -pi -e 's/\e\[[0-9;]*m//g' "$log"
if [[ $rc -eq 142 ]]; then
  echo "export timed out after ${timeout}s; log: $log" >&2
  exit 124
fi

# Required artifacts per platform, next to OUT_PATH.
base="${abs_out%.*}"
missing=()
require() { [[ -s "$1" || -d "$1" ]] || missing+=("$1"); }
require "$abs_out"
if [[ "$mode" != --export-pack ]]; then
  case "$platform" in
    Web) require "$base.wasm"; require "$base.pck"; require "$base.js" ;;
    Windows\ Desktop | Linux) [[ "$abs_out" == *.zip ]] || require "$base.pck" ;;
  esac
fi

errors=$(grep -E '^(ERROR|USER ERROR|SCRIPT ERROR)' "$log" || true)
if [[ $rc -ne 0 || ${#missing[@]} -gt 0 ]]; then
  echo "export \"$preset\" ($platform) FAILED (godot status $rc); log: $log" >&2
  [[ -n "$errors" ]] && grep -A2 -E '^(ERROR|USER ERROR|SCRIPT ERROR)' "$log" | head -n 30 >&2
  for m in ${missing[@]+"${missing[@]}"}; do echo "missing: $m" >&2; done
  exit 1
fi
echo "exported \"$preset\" ($platform, ${mode#--export-}) -> $abs_out"
if [[ -d "$abs_out" ]]; then
  du -sh "$abs_out"
else
  find "$out_dir" -maxdepth 1 -type f ! -name .gdignore -exec du -h {} + | sort -k2
fi
if [[ -n "$errors" ]]; then
  echo "--- the export succeeded but logged errors (often a malformed preset) ---"
  grep -A2 -E '^(ERROR|USER ERROR|SCRIPT ERROR)' "$log" | head -n 20
fi
rm -f "$log"
