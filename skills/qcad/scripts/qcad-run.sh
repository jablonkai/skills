#!/usr/bin/env bash
# Run a QCAD ECMAScript file headless with the skill's lib.js preloaded.
#
#   qcad-run.sh [--timeout SECONDS] [--keep-log LOG] script.js [args...]
#
# Inside the script: ARGS = [args...], SKILL_DIR = this directory, and every
# helper from lib.js (newDrawing, openDrawing, addLine, exportPdf, ...).
# QCAD runs from its own Resources directory; CWD holds the caller's working
# directory and the lib.js file helpers resolve relative paths against it.
#
# Exit status: 0 on success; 1 when the script threw, printed "ERROR", or the
# run timed out; 2 on usage errors or when QCAD cannot be found.
# QCAD binary lookup: $QCAD_BIN, then /Applications/QCAD*.app, ~/Applications.
set -euo pipefail

timeout_s=600
keep_log=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --timeout) timeout_s="$2"; shift 2 ;;
    --keep-log) keep_log="$2"; shift 2 ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    --) shift; break ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) break ;;
  esac
done
[[ $# -ge 1 ]] || { echo "usage: qcad-run.sh [--timeout S] script.js [args...]" >&2; exit 2; }

skill_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

find_qcad() {
  if [[ -n "${QCAD_BIN:-}" && -x "$QCAD_BIN" ]]; then echo "$QCAD_BIN"; return; fi
  local app
  for app in /Applications/QCAD.app /Applications/QCAD-Pro.app /Applications/QCAD*.app "$HOME"/Applications/QCAD*.app; do
    if [[ -x "$app/Contents/Resources/qcad" ]]; then echo "$app/Contents/Resources/qcad"; return; fi
  done
  command -v qcad 2>/dev/null || true
}
qcad=$(find_qcad)
[[ -n "$qcad" ]] || { echo "QCAD not found — install it (brew install --cask qcad) or set QCAD_BIN" >&2; exit 2; }

abspath() {
  case "$1" in
    /*) printf '%s' "$1" ;;
    *) printf '%s/%s' "$PWD" "$1" ;;
  esac
}

script=$(abspath "$1"); shift
[[ -f "$script" ]] || { echo "no such script: $script" >&2; exit 2; }

work=$(mktemp -d "${TMPDIR:-/tmp}/qcad-run.XXXXXX")
trap 'rm -rf "$work"' EXIT
boot="$work/boot.js"
log="${keep_log:-$work/qcad.log}"

js_str() { local s=${1//\\/\\\\}; s=${s//\"/\\\"}; printf '"%s"' "$s"; }
{
  printf 'var SKILL_DIR = %s;\n' "$(js_str "$skill_dir")"
  printf 'var CWD = %s;\n' "$(js_str "$PWD")"
  printf 'var ARGS = args.slice(1);\n'
  printf 'include(SKILL_DIR + "/lib.js");\n'
  printf 'try { include(%s); } catch (e) { print("ERROR " + e + (e.stack ? "\\n" + e.stack : "")); }\n' "$(js_str "$script")"
} > "$boot"

# QCAD resolves "scripts/..." includes relative to its Resources directory.
cd "$(dirname "$qcad")"
set +e
perl -e 'alarm shift; exec @ARGV' "$timeout_s" \
  "$qcad" -no-gui -no-dock-icon -allow-multiple-instances -autostart "$boot" "$@" \
  > "$log" 2>&1
rc=$?
set -e

# Script output (print) without QCAD's debug chatter and the trial banner.
grep -v -E '^[0-9:]+: Debug:|^Warning:  Unimplemented code|trial version|qcad.org/shop|purchase the full|productively|Thank you for trying|^$' "$log" || true

if [[ $rc -eq 142 ]]; then
  echo "qcad-run: timed out after ${timeout_s}s" >&2; exit 1
fi
if grep -q -E '^ERROR |Exception:|include exception' "$log"; then
  echo "qcad-run: script failed (see output above)" >&2; exit 1
fi
exit 0
