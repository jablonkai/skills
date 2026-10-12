#!/usr/bin/env bash
# Prove that a Tiled .tscn export loads in Godot 4: import the project headless,
# instantiate the scene, and compare it with the source map.
#
#   bash td-godot-check.sh GODOT_PROJECT_DIR res://levels/level1.tscn [--map level1.tmx]
#
# Reports import errors that mention the scene or its resources, then per tile
# layer the number of used cells, and every child that is a scene instance with
# its position. With --map, the cell count of each tile layer must equal the
# non-empty tiles of the same layer in the map, and the number of instances must
# equal the map's objects that carry a resPath property.
#
# Godot is found via GODOT_BIN, `godot` on PATH or /Applications/Godot.app.
# Exit 0 ok, 1 mismatch or error, 2 Godot missing.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)

usage() { sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; }
pos=() map=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --map) map=${2:?--map needs a file}; shift 2 ;;
    -*) echo "td-godot-check.sh: unknown option $1" >&2; exit 1 ;;
    *) pos+=("$1"); shift ;;
  esac
done
[[ ${#pos[@]} -eq 2 ]] || { usage >&2; exit 1; }
proj=$(cd "${pos[0]}" && pwd)
scene=${pos[1]}
[[ -f "$proj/project.godot" ]] || { echo "td-godot-check.sh: no project.godot in $proj" >&2; exit 1; }
if [[ "$scene" != res://* ]]; then
  abs="$(cd "$(dirname "$scene")" && pwd)/$(basename "$scene")"
  [[ "$abs" == "$proj"/* ]] || { echo "td-godot-check.sh: $scene is not inside $proj" >&2; exit 1; }
  scene="res://${abs#"$proj"/}"
fi
[[ -f "$proj/${scene#res://}" ]] || { echo "td-godot-check.sh: $scene not found in $proj" >&2; exit 1; }

GODOT=""
for c in "${GODOT_BIN:-}" "$(command -v godot 2>/dev/null || true)" /Applications/Godot.app/Contents/MacOS/Godot "$HOME/Applications/Godot.app/Contents/MacOS/Godot"; do
  if [[ -n "$c" && -x "$c" ]]; then GODOT=$c; break; fi
done
[[ -n "$GODOT" ]] || { echo "Godot not found — install it (brew install --cask godot) or set GODOT_BIN" >&2; exit 2; }

timed() { perl -e 'alarm shift; exec @ARGV or die "exec: $!\n"' 180 "$@"; }

# Exit-time leak reports are noise in headless runs; anything else is real.
noise='resources still in use at exit|RID allocations|were leaked|ObjectDB instances|leaked at exit|at: cleanup|at: _cleanup'
echo "godot: $("$GODOT" --version 2>/dev/null | tail -n1)"
imp=$(timed "$GODOT" --headless --path "$proj" --import 2>&1) || true
errs=$(grep -E '^(ERROR|SCRIPT ERROR)' <<<"$imp" | grep -vE "$noise" || true)
if [[ -n "$errs" ]]; then
  echo "import errors:"
  echo "$errs" | head -20 | sed 's/^/  /'
fi

probe=$(mktemp "${TMPDIR:-/tmp}/td-godot.XXXXXX")
mv "$probe" "$probe.gd"
probe="$probe.gd"
trap 'rm -f "$probe"' EXIT
cat >"$probe" <<'GD'
extends SceneTree
# Prints one TD_GODOT line of JSON describing the instantiated scene.

func _initialize() -> void:
	var path: String = OS.get_cmdline_user_args()[0]
	var packed = load(path)
	if packed == null:
		print("TD_GODOT " + JSON.stringify({"error": "cannot load " + path}))
		quit(1)
		return
	var root: Node = packed.instantiate()
	var out := {"root": root.name, "layers": [], "instances": [], "resources": []}
	_walk(root, root, out)
	for dep in ResourceLoader.get_dependencies(path):
		out["resources"].append(dep.get_slice("::", dep.get_slice_count("::") - 1))
	print("TD_GODOT " + JSON.stringify(out))
	root.free()
	quit(0)

func _walk(node: Node, root: Node, out: Dictionary) -> void:
	for c in node.get_children():
		if c is TileMapLayer:
			out["layers"].append({"name": String(c.name), "cells": c.get_used_cells().size(), "node": "TileMapLayer"})
		elif c is TileMap:
			for i in c.get_layers_count():
				out["layers"].append({"name": c.get_layer_name(i), "cells": c.get_used_cells(i).size(), "node": "TileMap"})
		if c.scene_file_path != "" and c != root:
			var pos = c.position if c is Node2D else Vector2.ZERO
			out["instances"].append({"name": String(c.name), "scene": c.scene_file_path, "x": pos.x, "y": pos.y})
		else:
			_walk(c, root, out)
GD
run=$(timed "$GODOT" --headless --path "$proj" --script "$probe" -- "$scene" 2>&1) || true
json=$(sed -n 's/^TD_GODOT //p' <<<"$run" | tail -n1)
run_errs=$(grep -E '^(ERROR|SCRIPT ERROR)' <<<"$run" | grep -vE "$noise" || true)
if [[ -z "$json" ]]; then
  echo "td-godot-check.sh: the scene did not instantiate:" >&2
  echo "$run" | grep -vE "$noise" | tail -15 >&2
  exit 1
fi

map_json="{}"
if [[ -n "$map" ]]; then
  map_json=$(python3 "$HERE/td-verify.py" --json "$map") || { python3 "$HERE/td-verify.py" "$map"; exit 1; }
  # resPath objects: td-verify does not keep properties, so count them here.
  respath=$(python3 - "$map" <<'PY'
import json, sys, xml.etree.ElementTree as ET
p = sys.argv[1]
n = 0
if p.endswith(".tmx"):
    for o in ET.parse(p).getroot().iter("object"):
        n += any(pr.get("name") == "resPath" for pr in o.iter("property"))
else:
    def walk(layers):
        global n
        for L in layers:
            walk(L.get("layers", []))
            for o in L.get("objects", []):
                n += any(pr.get("name") == "resPath" for pr in o.get("properties", []))
    walk(json.load(open(p)).get("layers", []))
print(n)
PY
)
  map_json=$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); d["respath"]=int(sys.argv[2]); print(json.dumps(d))' "$map_json" "$respath")
fi

python3 - "$json" "$map_json" "$errs" "$run_errs" <<'PY'
import json, sys
g, m = json.loads(sys.argv[1]), json.loads(sys.argv[2])
errs = [e for e in (sys.argv[3] + "\n" + sys.argv[4]).splitlines() if e.strip()]
ok = not errs
if "error" in g:
    print("FAIL", g["error"]); sys.exit(1)
print(f"scene root {g['root']!r}: {len(g['layers'])} tile layer(s), {len(g['instances'])} scene instance(s)")
for L in g["layers"]:
    print(f"  {L['node']:12} {L['name']!r}: {L['cells']} cells")
for i in g["instances"][:20]:
    print(f"  instance {i['name']!r} of {i['scene']} at ({i['x']:g}, {i['y']:g})")
if len(g["instances"]) > 20:
    print(f"  … {len(g['instances']) - 20} more")
outside = [r for r in g["resources"] if not r.startswith("res://")]
if outside:
    ok = False
    print("FAIL resources outside the project:", outside)
if m:
    tiles = {L["name"].split("/")[-1]: L["nonEmpty"] for L in m["layers"] if L["type"] == "tile"}
    seen = {L["name"]: L["cells"] for L in g["layers"]}
    for name, n in tiles.items():
        if name not in seen:
            if n:
                ok = False
                print(f"FAIL map layer {name!r} ({n} tiles) is missing in Godot (noExport, or a tile layer inside a group?)")
        elif seen[name] != n:
            ok = False
            print(f"FAIL layer {name!r}: map has {n} tiles, Godot has {seen[name]} cells")
        else:
            print(f"OK   layer {name!r}: {n} tiles == {seen[name]} cells")
    want = m.get("respath", 0)
    if want != len(g["instances"]):
        ok = False
        print(f"FAIL map has {want} object(s) with resPath, Godot scene has {len(g['instances'])} instance(s)")
    else:
        print(f"OK   {want} resPath object(s) == {len(g['instances'])} instance(s)")
if errs:
    print("FAIL Godot logged errors (see above)")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
