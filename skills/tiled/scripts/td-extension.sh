#!/usr/bin/env bash
# Try, install, list and remove Tiled JavaScript extensions (custom formats).
#
#   bash td-extension.sh try FILE.js MAP OUT [--format NAME]   run the format once, no install
#   bash td-extension.sh install FILE.js [--force]             copy into Tiled's extensions folder
#   bash td-extension.sh list                                  installed extension files and formats
#   bash td-extension.sh remove FILE.js                        delete an installed extension
#
# Tiled loads extensions only from ~/Library/Preferences/Tiled/extensions (on
# macOS) — the GUI and the CLI alike. A project's extensionsPath is ignored by
# headless --export-map. Installing changes the user's Tiled setup, so do it only
# when the user asked for the format to be available in Tiled. `try` registers the
# format in a throwaway --evaluate session and writes MAP through it, which is the
# way to test an extension before installing it.
# Exit 0 ok, 1 failure, 2 Tiled missing.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
EXT="${TILED_EXTENSIONS_DIR:-$HOME/Library/Preferences/Tiled/extensions}"

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; }
absolute() { (cd "$(dirname "$1")" && printf '%s/%s' "$(pwd)" "$(basename "$1")"); }

# Short names passed to tiled.registerMapFormat / registerTilesetFormat in FILE.
format_names() {
  grep -oE 'register(Map|Tileset)Format\(\s*["'"'"'][^"'"'"']+' "$1" | sed -E 's/.*["'"'"']//'
}

cmd=${1:-}
[[ -n "$cmd" ]] || { usage >&2; exit 1; }
shift
case "$cmd" in
  -h|--help) usage ;;
  try)
    file=${1:?try FILE.js MAP OUT}; map=${2:?try FILE.js MAP OUT}; out=${3:?try FILE.js MAP OUT}
    shift 3
    fmt=""
    [[ "${1:-}" == --format ]] && fmt=${2:?}
    [[ -n "$fmt" ]] || fmt=$(format_names "$file" | head -n1)
    [[ -n "$fmt" ]] || { echo "td-extension.sh: no registerMapFormat(\"name\", …) in $file" >&2; exit 1; }
    mkdir -p "$(dirname "$out")"
    runner=$(mktemp "${TMPDIR:-/tmp}/td-ext.XXXXXX")
    mv "$runner" "$runner.js"
    runner="$runner.js"
    trap 'rm -f "$runner"' EXIT
    {
      cat "$file"
      cat <<'JS'

;(function () {
  const [fmtName, mapPath, outPath] = tiled.scriptArguments;
  const fmt = tiled.mapFormat(fmtName);
  if (!fmt) throw new Error("format '" + fmtName + "' was not registered by the extension");
  const reader = /\.(tmj|json)$/.test(mapPath) ? "json" : "tmx";
  const map = tiled.mapFormat(reader).read(mapPath);
  const err = fmt.write(map, outPath);
  if (err) throw new Error("write failed: " + err);
  tiled.log("wrote " + outPath + " with format " + fmtName);
})();
JS
    } >"$runner"
    bash "$HERE/tiled.sh" eval "$runner" "$fmt" "$(absolute "$map")" "$(absolute "$out")"
    [[ -s "$out" ]] || { echo "td-extension.sh: $out is missing or empty" >&2; exit 1; }
    ;;
  install)
    file=${1:?install FILE.js}
    force=${2:-}
    [[ -f "$file" ]] || { echo "td-extension.sh: no such file: $file" >&2; exit 1; }
    names=$(format_names "$file")
    mkdir -p "$EXT"
    dest="$EXT/$(basename "$file")"
    if [[ -f "$dest" ]] && ! cmp -s "$file" "$dest" && [[ "$force" != --force ]]; then
      echo "td-extension.sh: $dest exists with different content — pass --force to replace it" >&2
      exit 1
    fi
    for n in $names; do
      clash=$(grep -lE "register(Map|Tileset)Format\(\s*[\"']${n}[\"']" "$EXT"/*.js "$EXT"/*.mjs 2>/dev/null | grep -vx "$dest" || true)
      [[ -z "$clash" ]] || { echo "td-extension.sh: format '$n' is already registered by $clash" >&2; exit 1; }
    done
    cp "$file" "$dest"
    echo "installed $dest"
    available=$(bash "$HERE/tiled.sh" --formats)
    for n in $names; do
      if grep -qx "$n" <<<"$available"; then
        echo "Tiled now lists format '$n'"
      else
        echo "td-extension.sh: Tiled does not list '$n' after install — the script probably fails to load" >&2
        echo "  Run: bash td-extension.sh try $file MAP OUT   to see the error" >&2
        exit 1
      fi
    done
    echo "A running Tiled GUI picks it up automatically (or after a restart)."
    ;;
  list)
    echo "$EXT"
    shopt -s nullglob
    for f in "$EXT"/*.js "$EXT"/*.mjs; do
      echo "  $(basename "$f"): $(format_names "$f" | tr '\n' ' ')"
    done
    ;;
  remove)
    name=$(basename "${1:?remove FILE.js}")
    [[ -f "$EXT/$name" ]] || { echo "td-extension.sh: $EXT/$name is not installed" >&2; exit 1; }
    rm "$EXT/$name"
    echo "removed $EXT/$name"
    ;;
  *) usage >&2; exit 1 ;;
esac
