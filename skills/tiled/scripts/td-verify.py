#!/usr/bin/env python3
"""Validate Tiled maps and tilesets without Tiled. Standard library only.

    python3 td-verify.py map.tmx [more.tmj tiles.tsx ...]
    python3 td-verify.py map.tmx --ascii [--layer walls]     also draw tile layers as text
    python3 td-verify.py map.tmx --json                      machine-readable summary
    python3 td-verify.py map.tmx --expect-size 40x30 --expect-layers floor,walls,objects

Checks: the file parses; layer data decodes to width*height cells (or chunks on
infinite maps); every GID falls inside a tileset's range (flip bits masked off);
external .tsx and image files exist; image size matches the tileset grid; object
ids are unique and below nextobjectid; layer ids are unique and below nextlayerid;
typed property values parse (int, float, bool, color) and object references point
at an existing object id.

The summary lists, per tile layer, the count of non-empty cells and the tiles used,
and per object layer, the objects by class. --ascii renders each tile layer with one
character per cell: '.' empty, then 0-9a-zA-Z by local tile id (tileset order), '?'
beyond that.

Exit 0 when clean, 1 on any error. Warnings do not fail.
"""

import argparse
import base64
import gzip
import json
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

FLIP_MASK = 0x0FFFFFFF  # top 4 bits: horizontal, vertical, diagonal, hex-120 flip flags
CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Report:
    def __init__(self, path):
        self.path = str(path)
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


# ---------------------------------------------------------------- tilesets

def tileset_from_xml(el, base, rep, where):
    """Return {name, tilecount, columns, tilewidth, tileheight, image} from <tileset>."""
    ts = {
        "name": el.get("name", ""),
        "tilewidth": int(el.get("tilewidth", 0)),
        "tileheight": int(el.get("tileheight", 0)),
        "tilecount": int(el.get("tilecount", 0)),
        "columns": int(el.get("columns", 0)),
        "spacing": int(el.get("spacing", 0)),
        "margin": int(el.get("margin", 0)),
        "image": None,
    }
    img = el.find("image")
    if img is not None:
        ts["image"] = img.get("source")
        check_image(base / img.get("source", ""), ts, rep, where,
                    int(img.get("width", 0) or 0), int(img.get("height", 0) or 0))
    else:
        tiles = el.findall("tile")
        for t in tiles:
            ti = t.find("image")
            if ti is not None and not (base / ti.get("source", "")).is_file():
                rep.error(f"{where}: tile {t.get('id')} image not found: {ti.get('source')}")
        if not tiles and ts["tilecount"]:
            rep.warn(f"{where}: no <image> and no per-tile images")
    return ts


def tileset_from_json(d, base, rep, where):
    ts = {k: d.get(k, 0) for k in ("tilewidth", "tileheight", "tilecount", "columns", "spacing", "margin")}
    ts["name"] = d.get("name", "")
    ts["image"] = d.get("image")
    if ts["image"]:
        check_image(base / ts["image"], ts, rep, where, d.get("imagewidth", 0), d.get("imageheight", 0))
    return ts


def check_image(path, ts, rep, where, declared_w, declared_h):
    if not path.is_file():
        rep.error(f"{where}: tileset image not found: {path}")
        return
    size = png_size(path)
    if size is None:
        return  # not a PNG; trust the declared size
    w, h = size
    if declared_w and (w, h) != (declared_w, declared_h):
        rep.warn(f"{where}: image is {w}x{h} but the tileset declares {declared_w}x{declared_h}")
    tw, th = ts["tilewidth"], ts["tileheight"]
    if tw and th:
        sp, mg = ts["spacing"], ts["margin"]
        cols = (w - 2 * mg + sp) // (tw + sp)
        rows = (h - 2 * mg + sp) // (th + sp)
        if ts["columns"] and cols != ts["columns"]:
            rep.warn(f"{where}: image fits {cols} columns, tileset says {ts['columns']}")
        if ts["tilecount"] and cols * rows < ts["tilecount"]:
            rep.error(f"{where}: image holds {cols * rows} tiles, tileset says {ts['tilecount']}")


def load_tsx(path, rep):
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as e:
        rep.error(f"{path}: {e}")
        return None
    if root.tag != "tileset":
        rep.error(f"{path}: root element is <{root.tag}>, expected <tileset>")
        return None
    return tileset_from_xml(root, path.parent, rep, path.name)


def load_tsj(path, rep):
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        rep.error(f"{path}: {e}")
        return None
    return tileset_from_json(d, path.parent, rep, path.name)


# ---------------------------------------------------------------- layer data

def decode_data(text, encoding, compression, count, rep, where):
    text = (text or "").strip()
    if encoding == "csv":
        vals = [int(v) for v in text.replace("\n", "").split(",") if v.strip()]
    elif encoding == "base64":
        raw = base64.b64decode(text)
        if compression == "zlib":
            raw = zlib.decompress(raw)
        elif compression == "gzip":
            raw = gzip.decompress(raw)
        elif compression == "zstd":
            rep.warn(f"{where}: zstd-compressed data cannot be checked without Tiled")
            return None
        elif compression:
            rep.error(f"{where}: unknown compression {compression}")
            return None
        if len(raw) % 4:
            rep.error(f"{where}: base64 data length {len(raw)} is not a multiple of 4")
            return None
        vals = list(struct.unpack(f"<{len(raw) // 4}I", raw))
    else:
        rep.error(f"{where}: unsupported encoding {encoding!r}")
        return None
    if count is not None and len(vals) != count:
        rep.error(f"{where}: {len(vals)} cells, expected {count}")
    return vals


# ---------------------------------------------------------------- properties

def check_props(props, where, rep, object_ids, refs):
    for name, ptype, value in props:
        w = f"{where} property {name!r}"
        try:
            if ptype == "int":
                int(value)
            elif ptype == "float":
                float(value)
            elif ptype == "bool":
                if str(value).lower() not in ("true", "false"):
                    raise ValueError(value)
            elif ptype == "color":
                v = str(value)
                if v and not (v.startswith("#") and len(v) in (7, 9)):
                    raise ValueError(v)
            elif ptype == "object":
                refs.append((w, int(value or 0)))
        except ValueError:
            rep.error(f"{w}: {value!r} is not a valid {ptype}")


def xml_props(el):
    out = []
    p = el.find("properties")
    if p is None:
        return out
    for prop in p.findall("property"):
        value = prop.get("value")
        if value is None:
            value = prop.text or ""
        out.append((prop.get("name"), prop.get("type", "string"), value))
    return out


def json_props(d):
    return [(p.get("name"), p.get("type", "string"), p.get("value")) for p in d.get("properties", []) or []]


# ---------------------------------------------------------------- maps

def new_summary(path):
    return {"file": str(path), "kind": "map", "layers": [], "tilesets": [], "errors": [], "warnings": []}


def gid_owner(gid, tilesets):
    """Return (tileset index, local id) for a masked gid, or None."""
    for i in range(len(tilesets) - 1, -1, -1):
        first, ts = tilesets[i]
        if gid >= first:
            if ts and ts["tilecount"] and gid - first >= ts["tilecount"]:
                return None
            return i, gid - first
    return None


def tile_layer_summary(name, lid, width, height, cells, tilesets, rep, where, grids):
    used = {}
    nonempty = 0
    keys = []  # per cell: None (empty), "!" (bad gid) or (tileset index, local id)
    for y in range(height):
        for x in range(width):
            raw = cells[y * width + x] if cells and y * width + x < len(cells) else 0
            gid = raw & FLIP_MASK
            if gid == 0:
                keys.append(None)
                continue
            nonempty += 1
            owner = gid_owner(gid, tilesets)
            if owner is None:
                rep.error(f"{where}: gid {gid} at ({x},{y}) is outside every tileset")
                keys.append("!")
                continue
            ti, local = owner
            key = f"{tilesets[ti][1]['name'] if tilesets[ti][1] else ti}:{local}"
            used[key] = used.get(key, 0) + 1
            keys.append(owner)
    # One tileset and small ids: the character is the local tile id. Otherwise
    # characters are handed out in order of appearance and listed in a legend.
    owners = {k for k in keys if isinstance(k, tuple)}
    direct = len({k[0] for k in owners}) <= 1 and all(k[1] < len(CHARS) for k in owners)
    chars, legend = {}, []
    for k in keys:
        if isinstance(k, tuple) and k not in chars:
            if direct:
                chars[k] = CHARS[k[1]]
            else:
                chars[k] = CHARS[len(chars)] if len(chars) < len(CHARS) else "?"
                ts = tilesets[k[0]][1]
                legend.append(f"{chars[k]}={ts['name'] if ts else k[0]}:{k[1]}")
    cell = [("." if k is None else "!" if k == "!" else chars[k]) for k in keys]
    grids[name] = ([("legend: " + " ".join(legend))] if legend else []) + \
        ["".join(cell[y * width:(y + 1) * width]) for y in range(height)]
    return {"name": name, "id": lid, "type": "tile", "width": width, "height": height,
            "nonEmpty": nonempty, "tiles": dict(sorted(used.items()))}


def verify_tmx(path, rep, grids):
    s = new_summary(path)
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as e:
        rep.error(f"{e}")
        return s
    if root.tag != "map":
        if root.tag == "tileset":
            s["kind"] = "tileset"
            s["tilesets"].append(load_tsx(path, rep))
            return s
        rep.error(f"root element is <{root.tag}>, expected <map>")
        return s
    base = path.parent
    W, H = int(root.get("width", 0)), int(root.get("height", 0))
    infinite = root.get("infinite") == "1"
    s.update({"width": W, "height": H, "tilewidth": int(root.get("tilewidth", 0)),
              "tileheight": int(root.get("tileheight", 0)), "orientation": root.get("orientation"),
              "infinite": infinite})
    tilesets = []
    for el in root.findall("tileset"):
        first = int(el.get("firstgid", 0))
        if el.get("source"):
            src = base / el.get("source")
            ts = None
            if not src.is_file():
                rep.error(f"external tileset not found: {el.get('source')}")
            elif src.suffix in (".tsj", ".json"):
                ts = load_tsj(src, rep)
            else:
                ts = load_tsx(src, rep)
            s["tilesets"].append({"firstgid": first, "source": el.get("source"), **(ts or {})})
        else:
            ts = tileset_from_xml(el, base, rep, f"tileset {el.get('name')}")
            s["tilesets"].append({"firstgid": first, "embedded": True, **ts})
        tilesets.append((first, ts))
    tilesets.sort(key=lambda t: t[0])

    object_ids, refs, layer_ids = set(), [], set()
    next_obj = int(root.get("nextobjectid", 0) or 0)
    next_layer = int(root.get("nextlayerid", 0) or 0)
    check_props(xml_props(root), "map", rep, object_ids, refs)

    def walk(parent, prefix):
        for el in parent:
            if el.tag not in ("layer", "objectgroup", "imagelayer", "group"):
                continue
            name = prefix + el.get("name", "")
            lid = int(el.get("id", 0) or 0)
            where = f"layer {name!r}"
            if lid in layer_ids:
                rep.error(f"{where}: duplicate layer id {lid}")
            layer_ids.add(lid)
            if next_layer and lid >= next_layer:
                rep.error(f"{where}: id {lid} >= nextlayerid {next_layer}")
            check_props(xml_props(el), where, rep, object_ids, refs)
            if el.tag == "group":
                s["layers"].append({"name": name, "id": lid, "type": "group"})
                walk(el, name + "/")
            elif el.tag == "layer":
                lw, lh = int(el.get("width", W)), int(el.get("height", H))
                data = el.find("data")
                cells = []
                if data is None:
                    rep.error(f"{where}: no <data>")
                elif infinite:
                    for ch in data.findall("chunk"):
                        cw, chh = int(ch.get("width")), int(ch.get("height"))
                        v = decode_data(ch.text, data.get("encoding"), data.get("compression"),
                                        cw * chh, rep, where + " chunk")
                        cells.extend(v or [])
                    lw, lh = len(cells), 1
                elif data.get("encoding") is None:
                    cells = [int(t.get("gid", 0)) for t in data.findall("tile")]
                else:
                    cells = decode_data(data.text, data.get("encoding"), data.get("compression"),
                                        lw * lh, rep, where) or []
                s["layers"].append(tile_layer_summary(name, lid, lw, lh, cells, tilesets, rep, where,
                                                      grids if not infinite else {}))
            elif el.tag == "objectgroup":
                by_class = {}
                objs = []
                for o in el.findall("object"):
                    oid = int(o.get("id", 0) or 0)
                    ow = f"object {oid} ({o.get('name', '')})"
                    if oid in object_ids:
                        rep.error(f"{ow}: duplicate object id")
                    object_ids.add(oid)
                    if next_obj and oid >= next_obj:
                        rep.error(f"{ow}: id >= nextobjectid {next_obj}")
                    cls = o.get("type") or o.get("class") or ""
                    by_class[cls] = by_class.get(cls, 0) + 1
                    if o.get("gid"):
                        if gid_owner(int(o.get("gid")) & FLIP_MASK, tilesets) is None:
                            rep.error(f"{ow}: gid {o.get('gid')} outside every tileset")
                    if o.get("template") and not (base / o.get("template")).is_file():
                        rep.error(f"{ow}: template not found: {o.get('template')}")
                    check_props(xml_props(o), ow, rep, object_ids, refs)
                    objs.append({"id": oid, "name": o.get("name", ""), "class": cls,
                                 "x": float(o.get("x", 0)), "y": float(o.get("y", 0))})
                s["layers"].append({"name": name, "id": lid, "type": "object", "objects": len(objs),
                                    "byClass": dict(sorted(by_class.items())), "list": objs})
            else:
                img = el.find("image")
                if img is not None and not (base / img.get("source", "")).is_file():
                    rep.error(f"{where}: image not found: {img.get('source')}")
                s["layers"].append({"name": name, "id": lid, "type": "image"})

    walk(root, "")
    for w, target in refs:
        if target and target not in object_ids:
            rep.error(f"{w}: references object {target}, which does not exist")
    return s


def verify_tmj(path, rep, grids):
    s = new_summary(path)
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as e:
        rep.error(str(e))
        return s
    if d.get("type") == "tileset":
        s["kind"] = "tileset"
        s["tilesets"].append(tileset_from_json(d, path.parent, rep, path.name))
        return s
    if d.get("type") != "map":
        rep.error(f"type is {d.get('type')!r}, expected 'map'")
        return s
    base = path.parent
    W, H = d.get("width", 0), d.get("height", 0)
    s.update({"width": W, "height": H, "tilewidth": d.get("tilewidth"), "tileheight": d.get("tileheight"),
              "orientation": d.get("orientation"), "infinite": d.get("infinite", False)})
    tilesets = []
    for t in d.get("tilesets", []):
        first = t.get("firstgid", 0)
        if "source" in t:
            src = base / t["source"]
            ts = None
            if not src.is_file():
                rep.error(f"external tileset not found: {t['source']}")
            elif src.suffix in (".tsx", ".xml"):
                ts = load_tsx(src, rep)
            else:
                ts = load_tsj(src, rep)
            s["tilesets"].append({"firstgid": first, "source": t["source"], **(ts or {})})
        else:
            ts = tileset_from_json(t, base, rep, f"tileset {t.get('name')}")
            s["tilesets"].append({"firstgid": first, "embedded": True, **ts})
        tilesets.append((first, ts))
    tilesets.sort(key=lambda t: t[0])
    object_ids, refs, layer_ids = set(), [], set()
    check_props(json_props(d), "map", rep, object_ids, refs)

    def walk(layers, prefix):
        for L in layers:
            name = prefix + L.get("name", "")
            where = f"layer {name!r}"
            if L.get("id") in layer_ids:
                rep.error(f"{where}: duplicate layer id {L.get('id')}")
            layer_ids.add(L.get("id"))
            check_props(json_props(L), where, rep, object_ids, refs)
            if L["type"] == "group":
                s["layers"].append({"name": name, "id": L.get("id"), "type": "group"})
                walk(L.get("layers", []), name + "/")
            elif L["type"] == "tilelayer":
                lw, lh = L.get("width", W), L.get("height", H)
                data = L.get("data")
                if "chunks" in L:
                    cells = []
                    for ch in L["chunks"]:
                        cd = ch["data"]
                        if isinstance(cd, str):
                            cd = decode_data(cd, "base64", L.get("compression"), ch["width"] * ch["height"],
                                             rep, where) or []
                        cells.extend(cd)
                    lw, lh = len(cells), 1
                elif isinstance(data, str):
                    cells = decode_data(data, "base64", L.get("compression"), lw * lh, rep, where) or []
                else:
                    cells = data or []
                    if len(cells) != lw * lh:
                        rep.error(f"{where}: {len(cells)} cells, expected {lw * lh}")
                s["layers"].append(tile_layer_summary(name, L.get("id"), lw, lh, cells, tilesets, rep, where,
                                                      grids if "chunks" not in L else {}))
            elif L["type"] == "objectgroup":
                by_class, objs = {}, []
                for o in L.get("objects", []):
                    ow = f"object {o.get('id')} ({o.get('name', '')})"
                    if o.get("id") in object_ids:
                        rep.error(f"{ow}: duplicate object id")
                    object_ids.add(o.get("id"))
                    cls = o.get("type") or o.get("class") or ""
                    by_class[cls] = by_class.get(cls, 0) + 1
                    check_props(json_props(o), ow, rep, object_ids, refs)
                    objs.append({"id": o.get("id"), "name": o.get("name", ""), "class": cls,
                                 "x": o.get("x", 0), "y": o.get("y", 0)})
                s["layers"].append({"name": name, "id": L.get("id"), "type": "object", "objects": len(objs),
                                    "byClass": dict(sorted(by_class.items())), "list": objs})
            else:
                s["layers"].append({"name": name, "id": L.get("id"), "type": "image"})

    walk(d.get("layers", []), "")
    for w, target in refs:
        if target and target not in object_ids:
            rep.error(f"{w}: references object {target}, which does not exist")
    return s


def verify(path, grids):
    rep = Report(path)
    if not path.is_file():
        rep.error("file not found")
        s = new_summary(path)
    elif path.suffix in (".tmj", ".json", ".tsj"):
        s = verify_tmj(path, rep, grids)
    elif path.suffix == ".tsx":
        s = new_summary(path)
        s["kind"] = "tileset"
        s["tilesets"].append(load_tsx(path, rep))
    else:
        s = verify_tmx(path, rep, grids)
    s["errors"], s["warnings"] = rep.errors, rep.warnings
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--json", action="store_true", help="print the full summary as JSON")
    ap.add_argument("--ascii", action="store_true", help="draw tile layers as text")
    ap.add_argument("--layer", help="with --ascii: only this layer")
    ap.add_argument("--expect-size", help="WxH the map must have, e.g. 40x30")
    ap.add_argument("--expect-layers", help="comma-separated layer names that must exist")
    a = ap.parse_args()

    failed = False
    out = []
    for f in a.files:
        grids = {}
        s = verify(f, grids)
        if a.expect_size and s.get("kind") == "map":
            w, h = (int(v) for v in a.expect_size.lower().split("x"))
            if (s.get("width"), s.get("height")) != (w, h):
                s["errors"].append(f"size is {s.get('width')}x{s.get('height')}, expected {w}x{h}")
        if a.expect_layers:
            names = {L["name"] for L in s["layers"]}
            for n in a.expect_layers.split(","):
                if n.strip() and n.strip() not in names:
                    s["errors"].append(f"layer {n.strip()!r} missing")
        failed |= bool(s["errors"])
        if a.json:
            out.append(s)
            continue
        status = "FAIL" if s["errors"] else "OK"
        if s.get("width") is None and s["kind"] == "map":
            print(f"{status} {f}")
        elif s["kind"] == "map":
            print(f"{status} {f}: {s.get('width')}x{s.get('height')} {s.get('orientation')}, "
                  f"{s.get('tilewidth')}x{s.get('tileheight')} px tiles, {len(s['tilesets'])} tileset(s)")
            for ts in s["tilesets"]:
                where = ts.get("source") or "embedded"
                print(f"  tileset {ts.get('name')!r} firstgid={ts.get('firstgid')} {where} "
                      f"tiles={ts.get('tilecount')} image={ts.get('image')}")
            for L in s["layers"]:
                if L["type"] == "tile":
                    print(f"  tile   {L['name']!r}: {L['nonEmpty']} tiles {L['tiles']}")
                elif L["type"] == "object":
                    print(f"  object {L['name']!r}: {L['objects']} objects {L['byClass']}")
                else:
                    print(f"  {L['type']:6} {L['name']!r}")
        else:
            for ts in s["tilesets"]:
                if ts:
                    print(f"{status} {f}: tileset {ts.get('name')!r} {ts.get('tilewidth')}x{ts.get('tileheight')} "
                          f"tiles={ts.get('tilecount')} columns={ts.get('columns')} image={ts.get('image')}")
            if not s["tilesets"] or not s["tilesets"][0]:
                print(f"{status} {f}")
        for w in s["warnings"]:
            print(f"  WARN  {w}")
        for e in s["errors"]:
            print(f"  ERROR {e}")
        if a.ascii:
            for name, grid in grids.items():
                if a.layer and name != a.layer:
                    continue
                print(f"\n  [{name}]")
                for row in grid:
                    print("  " + row)
    if a.json:
        print(json.dumps(out if len(out) > 1 else out[0], indent=1))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
