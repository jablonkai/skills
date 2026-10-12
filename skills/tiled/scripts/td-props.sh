#!/usr/bin/env bash
# Bulk-set or remove custom properties on the objects of a Tiled map.
#
#   bash td-props.sh MAP.tmx RULES.json [--out NEW.tmx] [--dry-run] [--project FILE]
#
# The rules format is at the top of td-props.js and in references/spec.md. The map
# is rewritten in place unless --out is given; --dry-run only lists the changes.
# --project loads a Tiled project for custom enum/class property types. The result
# is checked with td-verify.py. Exit 0 ok, 1 rule or verification error, 2 Tiled missing.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)

usage() { sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; }
absolute() { (cd "$(dirname "$1")" && printf '%s/%s' "$(pwd)" "$(basename "$1")"); }
pos=() out="" dry=0 project=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --out) out=${2:?--out needs a file}; shift 2 ;;
    --dry-run) dry=1; shift ;;
    --project) project=${2:?--project needs a file}; shift 2 ;;
    -*) echo "td-props.sh: unknown option $1" >&2; exit 1 ;;
    *) pos+=("$1"); shift ;;
  esac
done
[[ ${#pos[@]} -eq 2 ]] || { usage >&2; exit 1; }
map=${pos[0]} rules=${pos[1]}
[[ -f "$map" ]] || { echo "td-props.sh: map not found: $map" >&2; exit 1; }
[[ -f "$rules" ]] || { echo "td-props.sh: rules not found: $rules" >&2; exit 1; }
map=$(absolute "$map")
rules=$(absolute "$rules")
if [[ -n "$out" ]]; then
  mkdir -p "$(dirname "$out")"
  out=$(absolute "$out")
fi

args=()
[[ -n "$project" ]] && args+=(--project "$project")
res=$(bash "$HERE/tiled.sh" ${args[@]+"${args[@]}"} eval "$HERE/td-props.js" "map=$map" "rules=$rules" "out=${out:-$map}" "dry=$dry") || { echo "$res"; exit 1; }
echo "$res" | grep -v '^TD_RESULT ' || true
json=$(echo "$res" | sed -n 's/^TD_RESULT //p')
python3 - "$json" <<'PY'
import json, sys
r = json.loads(sys.argv[1])
for rule in r["rules"]:
    print(f"rule {rule['rule']}: {rule['matched']} object(s) {json.dumps(rule['where'])}")
for c in r["changes"]:
    print(f"  {c['target']}: {c['property']} {json.dumps(c['old'])} -> {json.dumps(c['new'])}")
print(f"{len(r['changes'])} change(s) " + (f"written to {r['output']}" if r["output"] else "(dry run, nothing written)"))
PY
if [[ $dry -eq 0 ]]; then
  target=${out:-$map}
  python3 "$HERE/td-verify.py" "$target" >/dev/null || { python3 "$HERE/td-verify.py" "$target"; exit 1; }
  echo "verified: td-verify.py clean"
fi
