#!/usr/bin/env bash
# Locate Tiled and run it headless. Every other script in this skill goes through
# here, so the binary lookup, the timeout and the --evaluate error check live in
# one place.
#
#   bash tiled.sh --check                 binary, version, export formats, extensions folder
#   bash tiled.sh --bin                   print the binary path only
#   bash tiled.sh --formats               map and tileset export formats (one per line)
#   bash tiled.sh eval SCRIPT.js [ARGS…]  run a script with the JS API, then exit
#   bash tiled.sh --project P.tiled-project eval …   same, with a project loaded
#                                         (its custom property types, not its extensions)
#   bash tiled.sh [tiled args…]           run Tiled with the given arguments
#
# `eval` exists because `Tiled --evaluate` exits 0 even when the script throws or
# has a syntax error. It runs the script inside a try/catch and appends a
# completion marker, then exits 1 when the marker is missing or an exception was
# caught. Inside the script, tiled.scriptArguments holds ARGS. `throw` to fail.
#
# Override the lookup with TILED_BIN=/path/to/Tiled and the timeout (seconds,
# default 120) with TILED_TIMEOUT. Exit codes: 0 ok, 1 failure, 2 Tiled missing,
# 124 timeout.
set -euo pipefail

TIMEOUT=${TILED_TIMEOUT:-120}

find_tiled() {
  local candidate app
  for candidate in "${TILED_BIN:-}" "$(command -v tiled 2>/dev/null || true)"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  # The Homebrew cask and the DMG both install Tiled.app.
  for app in /Applications/Tiled.app "$HOME/Applications/Tiled.app"; do
    if [[ -x "$app/Contents/MacOS/Tiled" ]]; then
      printf '%s' "$app/Contents/MacOS/Tiled"
      return 0
    fi
  done
  return 1
}

if ! BIN=$(find_tiled); then
  echo "Tiled not found — install it (brew install --cask tiled) or set TILED_BIN" >&2
  exit 2
fi

# macOS has no `timeout`; perl's alarm kills Tiled with SIGALRM (exit 142).
run() {
  local rc=0
  perl -e 'alarm shift; exec @ARGV or die "exec: $!\n"' "$TIMEOUT" "$BIN" "$@" || rc=$?
  if [[ $rc -eq 142 ]]; then
    echo "tiled.sh: timed out after ${TIMEOUT}s: $*" >&2
    return 124
  fi
  return "$rc"
}

# Tiled prints its own messages in the UI language (from the system locale), so
# never parse them; the export-format list is the one thing worth reading, and it
# is indented with one space whatever the language.
formats() {
  run --export-formats 2>&1 | grep -E '^ [A-Za-z0-9_.-]+$' | sed 's/^ //'
}

pre=()
while [[ "${1:-}" == --project ]]; do
  pre+=(--project "${2:?--project needs a file}")
  shift 2
done

case "${1:-}" in
  --bin)
    echo "$BIN"
    ;;
  --check)
    echo "$BIN"
    run --version 2>/dev/null | head -n1
    echo "export formats: $(formats | tr '\n' ' ')"
    ext="$HOME/Library/Preferences/Tiled/extensions"
    if [[ -d "$ext" ]]; then
      n=$(find "$ext" -maxdepth 1 \( -name '*.js' -o -name '*.mjs' \) | wc -l | tr -d ' ')
      echo "extensions folder: $ext ($n script(s))"
    else
      echo "extensions folder: $ext (not created yet)"
    fi
    ;;
  --formats)
    formats
    ;;
  eval)
    shift
    script=${1:?usage: tiled.sh eval SCRIPT.js [ARGS…]}
    shift
    [[ -f "$script" ]] || { echo "tiled.sh: no such script: $script" >&2; exit 1; }
    tmp=${TMPDIR:-/tmp}
    wrapper=$(mktemp "${tmp%/}/tiled-eval.XXXXXX")
    mv "$wrapper" "$wrapper.js"
    wrapper="$wrapper.js"
    trap 'rm -f "$wrapper"' EXIT
    # The `try {` shares the script's first line, so line numbers in errors match.
    # ES module `import` statements cannot run inside it; use plain scripts.
    {
      printf 'try {'
      cat "$script"
      printf '\n} catch (e) { tiled.log("TD_EXCEPTION " + e + (e && e.stack ? "\\n" + e.stack : "")); throw e; }\n'
      printf 'tiled.log("TD_EVAL_DONE");\n'
    } >"$wrapper"
    rc=0
    out=$(run ${pre[@]+"${pre[@]}"} --evaluate "$wrapper" "$@" 2>&1) || rc=$?
    # Drop Tiled's localized "Evaluating <file>" banner and its exit-time chatter,
    # and show errors under the script's own name instead of the wrapper's.
    awk -v w="$wrapper" -v b="$(basename "$wrapper")" -v s="$script" '
      function swap(line, from, to,   i) {
        while ((i = index(line, from)) > 0)
          line = substr(line, 1, i - 1) to substr(line, i + length(from))
        return line
      }
      NR == 1 && index($0, b) && !index($0, "@file") { next }
      /^TD_EVAL_DONE$/ || /TilesetManager: There are still/ { next }
      { print swap(swap($0, "file://" w, s), b, s) }' <<<"$out"
    [[ $rc -eq 124 ]] && exit 124
    if grep -q '^TD_EXCEPTION' <<<"$out" || ! grep -q '^TD_EVAL_DONE$' <<<"$out"; then
      echo "tiled.sh: script failed: $script" >&2
      exit 1
    fi
    ;;
  *)
    run ${pre[@]+"${pre[@]}"} "$@"
    ;;
esac
