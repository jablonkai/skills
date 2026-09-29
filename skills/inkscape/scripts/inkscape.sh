#!/usr/bin/env bash
# Locate the Inkscape 1.x command-line binary and run it. Every other script in
# this skill goes through here, so the binary lookup and the version gate live in
# one place.
#
#   bash inkscape.sh --check          print binary path and version, exit 2 if unusable
#   bash inkscape.sh --actions-grep RE  grep --action-list (never guess action names)
#   bash inkscape.sh [inkscape args...] run Inkscape with the given arguments
#
# Override the lookup with INKSCAPE_BIN=/path/to/inkscape.
set -euo pipefail

find_inkscape() {
  local candidate
  for candidate in \
    "${INKSCAPE_BIN:-}" \
    /Applications/Inkscape.app/Contents/MacOS/inkscape \
    "$HOME/Applications/Inkscape.app/Contents/MacOS/inkscape" \
    "$(command -v inkscape 2>/dev/null || true)"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

if ! BIN=$(find_inkscape); then
  echo "Inkscape not found — install it (brew install --cask inkscape) or set INKSCAPE_BIN" >&2
  exit 2
fi

version=$("$BIN" --version 2>/dev/null | sed -n 's/^Inkscape \([0-9][0-9.]*\).*/\1/p' | head -n1)
if [[ "${version%%.*}" != "1" ]]; then
  echo "Inkscape 1.x required, found '${version:-unknown}' at $BIN" >&2
  exit 2
fi

case "${1:-}" in
  --check)
    echo "$BIN"
    echo "Inkscape $version"
    # Extensions (org.inkscape.* actions) run under the bundled Python; when macOS
    # kills it they silently do nothing, so report it up front.
    py="$(dirname "$BIN")/../Resources/bin/python3"
    if [[ -x "$py" ]]; then
      # A subshell keeps bash's own "Killed: 9" notice out of the output.
      rc=$( { "$py" -c 'import inkex' >/dev/null 2>&1; echo $?; } 2>/dev/null )
      if [[ $rc -eq 0 ]]; then
        echo "extensions: available"
      else
        echo "extensions: UNAVAILABLE (bundled Python fails, rc=$rc) — use actions or direct SVG edits"
      fi
    fi
    ;;
  --actions-grep)
    if [[ $# -lt 2 ]]; then
      echo "usage: inkscape.sh --actions-grep REGEX" >&2
      exit 2
    fi
    "$BIN" --action-list 2>/dev/null | grep -Ei -- "$2" || {
      echo "no action matches '$2' in Inkscape $version" >&2
      exit 1
    }
    ;;
  *)
    exec "$BIN" "$@"
    ;;
esac
