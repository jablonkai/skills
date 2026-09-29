#!/usr/bin/env bash
# Add a complete export preset to export_presets.cfg (created if missing), in the
# form Godot 4.7 accepts without "Couldn't find the given section" errors.
#
#   bash gd-preset.sh PROJECT_DIR web|macos|windows|linux [options]
#
#   --name NAME        preset name (default: Web, macOS, Windows Desktop, Linux)
#   --out PATH         export_path (default: build/web/index.html, build/mac/<App>.zip,
#                      build/windows/<App>.exe, build/linux/<App>.x86_64)
#   --bundle-id ID     macOS bundle identifier (default: com.example.<app>)
#   --exclude GLOBS    exclude_filter (default: "tests/*")
#
# macos also sets rendering/textures/vram_compression/import_etc2_astc=true, without
# which Godot refuses the arm64/universal export. Refuses a duplicate preset name.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

usage() { awk 'NR > 1 && !/^#/ { exit } NR > 1 { sub(/^# ?/, ""); print }' "${BASH_SOURCE[0]}"; exit 2; }

[[ $# -ge 2 ]] || usage
project=$1 kind=$2
shift 2
name="" out="" bundle="" exclude="tests/*"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) name=$2; shift 2 ;;
    --out) out=$2; shift 2 ;;
    --bundle-id) bundle=$2; shift 2 ;;
    --exclude) exclude=$2; shift 2 ;;
    -h | --help) usage ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
if [[ ! -f "$project/project.godot" ]]; then
  echo "no project.godot in $project" >&2
  exit 2
fi
if [[ "$out" == /* ]]; then
  echo "--out must be relative to the project (export_path is project-relative)" >&2
  exit 2
fi

# A file-name-safe app name from config/name: "Coin Hunt" -> CoinHunt
app=$(sed -n 's/^config\/name="\(.*\)"$/\1/p' "$project/project.godot" | tr -cd '[:alnum:]')
[[ -n "$app" ]] || app=Game
lower=$(tr '[:upper:]' '[:lower:]' <<<"$app")

options=""
case "$kind" in
  web)
    platform=Web; name=${name:-Web}; out=${out:-build/web/index.html}
    options='variant/thread_support=false'
    ;;
  macos)
    platform=macOS; name=${name:-macOS}; out=${out:-build/mac/$app.zip}
    options="application/bundle_identifier=\"${bundle:-com.example.$lower}\""
    ;;
  windows)
    platform="Windows Desktop"; name=${name:-Windows Desktop}; out=${out:-build/windows/$app.exe}
    ;;
  linux)
    platform=Linux; name=${name:-Linux}; out=${out:-build/linux/$app.x86_64}
    ;;
  *) echo "kind must be web, macos, windows or linux" >&2; exit 2 ;;
esac

cfg="$project/export_presets.cfg"
index=0
if [[ -f "$cfg" ]]; then
  if grep -qxF "name=\"$name\"" "$cfg"; then
    echo "preset \"$name\" already exists in $cfg" >&2
    exit 2
  fi
  last=$(sed -n 's/^\[preset\.\([0-9]*\)\]$/\1/p' "$cfg" | sort -n | tail -n1)
  [[ -n "$last" ]] && index=$((last + 1))
fi

separator=""
[[ -s "$cfg" ]] && separator=$'\n'
{
  printf '%s' "$separator"
  cat <<EOF
[preset.$index]

name="$name"
platform="$platform"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter="$exclude"
export_path="$out"

[preset.$index.options]

EOF
  # An empty options section counts as missing, so always write at least one key.
  echo "${options:-binary_format/embed_pck=false}"
} >>"$cfg"

if [[ "$kind" == macos ]] && ! grep -q '^textures/vram_compression/import_etc2_astc=true' "$project/project.godot"; then
  (perl -e 'alarm 60; exec @ARGV' bash "$here/godot.sh" --headless --path "$project" -l en \
    --script "$here/gd-settings.gd" -- --set rendering/textures/vram_compression/import_etc2_astc=true \
    >/dev/null 2>&1 || exit $?) 2>/dev/null
  echo "set rendering/textures/vram_compression/import_etc2_astc=true (required for macOS)"
fi
mkdir -p "$project/$(dirname "$out")"
top="$project/${out%%/*}"
[[ "$out" == */* && ! -f "$top/.gdignore" ]] && touch "$top/.gdignore"
echo "added preset.$index \"$name\" ($platform) -> $out"
echo "export: bash $here/gd-export.sh $project \"$name\" $out"
