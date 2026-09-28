#!/usr/bin/env bash
# Look up the installed DaVinci Resolve scripting API — the version-matched source of truth.
#
# Usage:
#   resolve-api.sh AppendToTimeline        every stub line mentioning it, with its docstring
#   resolve-api.sh RenderSettings          a parameter dict (TypedDict) and all of its keys
#   resolve-api.sh --path                  print where the SDK lives (README.md, .pyi, Examples/)
#   resolve-api.sh --changelog             what changed per Resolve version
#
# Reads DaVinciResolveScript.pyi, which Resolve 21.1+ installs next to its scripting README.
set -euo pipefail

case "$(uname -s)" in
    Darwin) sdk="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting" ;;
    Linux) sdk="/opt/resolve/Developer/Scripting" ;;
    MINGW* | MSYS* | CYGWIN*) sdk="${PROGRAMDATA:-C:/ProgramData}/Blackmagic Design/DaVinci Resolve/Support/Developer/Scripting" ;;
    *) echo "ERROR: unsupported platform" >&2; exit 2 ;;
esac
sdk="${RESOLVE_SCRIPT_API:-$sdk}"
pyi="$sdk/DaVinciResolveScript.pyi"

[ $# -ge 1 ] || { echo "usage: resolve-api.sh <Name> | --path | --changelog" >&2; exit 2; }
case "$1" in
    --path) echo "$sdk"; exit 0 ;;
    --changelog) cat "$sdk/CHANGELOG.md"; exit 0 ;;
esac
[ -f "$pyi" ] || { echo "ERROR: $pyi not found (pre-21.1 install? read $sdk/README.txt instead)" >&2; exit 1; }

# A TypedDict name prints the whole class body; anything else prints matching defs + docstring.
awk -v name="$1" '
    $0 ~ "^class " name "\\(TypedDict" { show = 1; print; next }
    show && /^class / { show = 0 }
    show { print; next }
    $0 ~ ("def " name "\\(") || $0 ~ ("^" name "[ :=]") { print FILENAME ":" FNR ": " $0; getline; print "    " $0 }
' "$pyi"
