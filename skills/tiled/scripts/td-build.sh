#!/usr/bin/env bash
# Build a Tiled map (.tmx / .tmj) from a JSON spec through Tiled's JS API.
#
#   bash td-build.sh SPEC.json [--project FILE.tiled-project] [--no-verify]
#
# The spec format is in references/spec.md. --project loads a Tiled project so
# that custom enum/class property types from it can be used in the spec. After
# writing, the map is checked with td-verify.py unless --no-verify is given.
# Exit 0 ok, 1 spec or verification error, 2 Tiled missing.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)

usage() { sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; }
spec="" project="" verify=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --project) project=${2:?--project needs a file}; shift 2 ;;
    --no-verify) verify=0; shift ;;
    -*) echo "td-build.sh: unknown option $1" >&2; exit 1 ;;
    *) spec=$1; shift ;;
  esac
done
[[ -n "$spec" ]] || { usage >&2; exit 1; }
[[ -f "$spec" ]] || { echo "td-build.sh: spec not found: $spec" >&2; exit 1; }
spec_abs="$(cd "$(dirname "$spec")" && pwd)/$(basename "$spec")"

args=()
[[ -n "$project" ]] && args+=(--project "$project")
out=$(bash "$HERE/tiled.sh" ${args[@]+"${args[@]}"} eval "$HERE/td-build.js" "$spec_abs") || { echo "$out"; exit 1; }
echo "$out" | grep -v '^TD_RESULT ' || true
result=$(echo "$out" | sed -n 's/^TD_RESULT //p')
[[ -n "$result" ]] || { echo "td-build.sh: no result from td-build.js" >&2; exit 1; }
python3 -c 'import json,sys; r=json.loads(sys.argv[1]); print("wrote", r["output"]); [print("  %-6s %-20s %s" % (l["type"], l["name"], l.get("tiles", l.get("objects", "")))) for l in r["layers"]]' "$result"
if [[ $verify -eq 1 ]]; then
  output=$(python3 -c 'import json,sys; print(json.loads(sys.argv[1])["output"])' "$result")
  python3 "$HERE/td-verify.py" "$output" >/dev/null || { python3 "$HERE/td-verify.py" "$output"; exit 1; }
  echo "verified: td-verify.py clean"
fi
