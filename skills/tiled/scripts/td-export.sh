#!/usr/bin/env bash
# Export a Tiled map or tileset with Tiled's CLI and check the result.
#
#   bash td-export.sh IN OUT [--format F] [options]
#   bash td-export.sh --formats             list formats (built-in plus installed extensions)
#
# IN is a map (.tmx/.tmj/…) or a tileset (.tsx/.tsj). The format comes from OUT's
# extension (.tmj/.json json, .lua lua, .tscn tscn, .csv csv, .js js, .tmx tmx,
# .tsx tsx, .tsj json, .gmx gmx, .yy yy) unless --format names one, which is how
# extension formats are picked.
#
# Options passed through to Tiled:
#   --embed-tilesets --detach-templates --resolve-types (= --resolve-types-and-properties)
#   --minimize --export-version V --project FILE
#
# --standalone (json, lua, tmx maps): embed tilesets and detach templates, then
#   copy every image the export references into OUT's folder (images/ next to
#   it) and rewrite the paths, so the folder can be shipped on its own. JSON tile
#   data is also written as plain arrays, since Phaser skips compressed layers.
#
# For .tscn (Godot 4) the script first checks the two things Tiled's Godot
# exporter needs or silently drops: a project.godot above OUT with every tileset
# image inside that project, and a resPath property on every object to export.
# Exit 0 ok, 1 failure, 2 Tiled missing.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)

usage() { sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; }

if [[ "${1:-}" == "--formats" ]]; then
  exec bash "$HERE/tiled.sh" --formats
fi

pos=() fmt="" flags=() pre=() standalone=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --format) fmt=${2:?--format needs a name}; shift 2 ;;
    --embed-tilesets|--detach-templates|--minimize) flags+=("$1"); shift ;;
    --standalone) standalone=1; shift ;;
    --resolve-types|--resolve-types-and-properties) flags+=(--resolve-types-and-properties); shift ;;
    --export-version) flags+=(--export-version "${2:?}"); shift 2 ;;
    --project) pre+=(--project "${2:?}"); shift 2 ;;
    -*) echo "td-export.sh: unknown option $1" >&2; exit 1 ;;
    *) pos+=("$1"); shift ;;
  esac
done
[[ ${#pos[@]} -eq 2 ]] || { usage >&2; exit 1; }
in=${pos[0]} out=${pos[1]}
[[ -f "$in" ]] || { echo "td-export.sh: input not found: $in" >&2; exit 1; }

kind=map mode=--export-map
case "$in" in
  *.tsx|*.tsj) kind=tileset mode=--export-tileset ;;
esac

if [[ -z "$fmt" ]]; then
  case "$out" in
    *.tmj|*.json) fmt=json ;;
    *.tsj) fmt=json ;;
    *.lua) fmt=lua ;;
    *.tscn) fmt=tscn ;;
    *.csv) fmt=csv ;;
    *.js) fmt=js ;;
    *.tmx) fmt=tmx ;;
    *.tsx) fmt=tsx ;;
    *.gmx) fmt=gmx ;;
    *.yy) fmt=yy ;;
    *) echo "td-export.sh: cannot tell the format from '$out' — pass --format (see --formats)" >&2; exit 1 ;;
  esac
fi

available=$(bash "$HERE/tiled.sh" --formats)
if ! grep -qx "$fmt" <<<"$available"; then
  echo "td-export.sh: Tiled has no export format '$fmt'. Available: $(tr '\n' ' ' <<<"$available")" >&2
  echo "  Extension formats load only from ~/Library/Preferences/Tiled/extensions, not from a project's extensionsPath." >&2
  exit 1
fi

if [[ $standalone -eq 1 ]]; then
  [[ "$kind" == map && "$fmt" =~ ^(json|lua|tmx)$ ]] || { echo "td-export.sh: --standalone supports json, lua and tmx map exports" >&2; exit 1; }
  flags+=(--embed-tilesets --detach-templates)
fi

mkdir -p "$(dirname "$out")"

if [[ "$fmt" == tscn && "$kind" == map ]]; then
  # Fails here, not halfway through Tiled, and catches what Tiled drops silently.
  python3 - "$in" "$out" <<'PY' || exit 1
import json, sys, xml.etree.ElementTree as ET
from pathlib import Path
src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
root = next((p for p in [out.parent, *out.parent.parents] if (p / "project.godot").is_file()), None)
if root is None:
    print(f"td-export.sh: no project.godot above {out} — the .tscn has to be written inside the Godot project")
    sys.exit(1)

def images(ts_el, base):
    for img in ts_el.iter("image"):
        yield (base / img.get("source", "")).resolve()

bad, objs, no_res = [], 0, []
if src.suffix == ".tmx":
    m = ET.parse(src).getroot()
    for ts in m.findall("tileset"):
        if ts.get("source"):
            tsx = (src.parent / ts.get("source")).resolve()
            if tsx.suffix == ".tsx" and tsx.is_file():
                bad += [i for i in images(ET.parse(tsx).getroot(), tsx.parent) if root not in i.parents]
        else:
            bad += [i for i in images(ts, src.parent) if root not in i.parents]
    for og in m.iter("objectgroup"):
        for o in og.findall("object"):
            objs += 1
            props = {p.get("name") for p in o.iter("property")}
            if "resPath" not in props and not o.get("template"):
                no_res.append(o.get("name") or o.get("id"))
if bad:
    print(f"td-export.sh: tileset image(s) outside the Godot project {root}:")
    for i in bad:
        print(f"  {i}")
    print("  Copy the image (and its .tsx) into the project and re-point the map, then export again.")
    sys.exit(1)
print(f"godot project: {root}")
if no_res:
    print(f"WARNING: {len(no_res)} of {objs} object(s) have no resPath and will NOT be exported: "
          + ", ".join(no_res[:8]) + (" …" if len(no_res) > 8 else ""))
    print("  Give each one a string property resPath = res://path/to/scene.tscn (td-props.sh), or ignore if intended.")
PY
fi

before=0
[[ -f "$out" ]] && before=$(stat -f %m "$out")
rc=0
msg=$(bash "$HERE/tiled.sh" ${pre[@]+"${pre[@]}"} "$mode" "$fmt" "$in" "$out" ${flags[@]+"${flags[@]}"} 2>&1) || rc=$?
if [[ $rc -ne 0 ]]; then
  echo "$msg" | grep -v -i 'locale' >&2 || true
  echo "td-export.sh: Tiled export failed (exit $rc)" >&2
  exit 1
fi
if [[ "$fmt" == csv && ! -s "$out" ]]; then
  # With several tile layers the csv exporter writes <base>_<layer>.csv instead.
  shopt -s nullglob
  parts=("${out%.csv}"_*.csv)
  if [[ ${#parts[@]} -gt 0 ]]; then
    echo "exported map $in -> ${#parts[@]} csv file(s), one per tile layer: ${parts[*]}"
    exit 0
  fi
fi
if [[ ! -s "$out" ]]; then
  echo "td-export.sh: Tiled reported success but $out is missing or empty" >&2
  exit 1
fi
if [[ $before -ne 0 && $(stat -f %m "$out") -lt $before ]]; then
  echo "td-export.sh: $out was not rewritten" >&2
  exit 1
fi
if [[ $standalone -eq 1 ]]; then
  python3 - "$out" "$fmt" <<'PY' || exit 1
import json, re, shutil, sys
import xml.etree.ElementTree as ET
from pathlib import Path
out, fmt = Path(sys.argv[1]).resolve(), sys.argv[2]
base = out.parent
dest = base / "images"
copied = {}

def localize(ref):
    if not ref:
        return ref
    src = (base / ref).resolve()
    if src.is_relative_to(base) and src.is_file():
        return ref                                # already inside the folder
    if not src.is_file():
        print(f"td-export.sh: referenced image not found: {ref}", file=sys.stderr)
        sys.exit(1)
    if src not in copied:
        dest.mkdir(exist_ok=True)
        name, n = src.name, 1
        while (dest / name).exists() and (dest / name).resolve() not in copied.values():
            name = f"{src.stem}_{n}{src.suffix}"; n += 1
        shutil.copy2(src, dest / name)
        copied[src] = (dest / name).resolve()
    return "images/" + copied[src].name

def plain(layer):
    # Phaser (and most hand-written loaders) skip compressed or base64 layer data.
    import base64, gzip, struct, zlib
    for holder in [layer] + layer.get("chunks", []):
        data = holder.get("data")
        if not isinstance(data, str):
            continue
        raw = base64.b64decode(data)
        comp = layer.get("compression")
        if comp == "zlib":
            raw = zlib.decompress(raw)
        elif comp == "gzip":
            raw = gzip.decompress(raw)
        elif comp:
            print(f"td-export.sh: cannot decompress {comp} layer data; save the map with zlib or CSV", file=sys.stderr)
            sys.exit(1)
        holder["data"] = list(struct.unpack(f"<{len(raw) // 4}I", raw))
    layer.pop("encoding", None)
    layer.pop("compression", None)
    for child in layer.get("layers", []):
        plain(child)

if fmt == "json":
    d = json.loads(out.read_text())
    for L in d.get("layers", []):
        plain(L)
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "image" and isinstance(v, str):
                    node[k] = localize(v)
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(d)
    out.write_text(json.dumps(d, indent=1))
elif fmt == "lua":
    text = out.read_text()
    text = re.sub(r'(\bimage = ")([^"]+)(")', lambda m: m.group(1) + localize(m.group(2)) + m.group(3), text)
    out.write_text(text)
else:
    tree = ET.parse(out)
    for img in tree.getroot().iter("image"):
        img.set("source", localize(img.get("source")))
    tree.write(out, encoding="UTF-8", xml_declaration=True)
print(f"standalone: {len(copied)} image(s) copied into {dest}" if copied else "standalone: all images already inside the folder")
PY
fi
# Exports write tileset and image paths relative to the OUTPUT file. Flag the
# ones that climb out of the output's folder: they break when the folder is shipped.
if [[ "$kind" == map && "$fmt" =~ ^(json|lua|js|tmx)$ ]] && grep -qE '(source|filename|image)[" =:]+[^,]*\.\.\\?/\.\.\\?/' "$out" 2>/dev/null; then
  echo "WARNING: $out references tilesets or images outside its folder (../../…)." >&2
  echo "  If it will be deployed: --embed-tilesets, and copy the tileset images next to it" >&2
  echo "  (or export from a map whose tilesets already sit there)." >&2
fi
case "$fmt" in
  json)
    if [[ "$kind" == map ]]; then
      python3 "$HERE/td-verify.py" "$out" >/dev/null || { python3 "$HERE/td-verify.py" "$out"; exit 1; }
    else
      python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$out"
    fi ;;
  tmx|tsx)
    python3 "$HERE/td-verify.py" "$out" >/dev/null || { python3 "$HERE/td-verify.py" "$out"; exit 1; } ;;
esac
echo "exported $kind $in -> $out ($fmt, $(wc -c <"$out" | tr -d ' ') bytes)"
