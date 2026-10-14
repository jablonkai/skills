#!/usr/bin/env python3
"""Read an Apple Motion template (.moti/.motn/.moef/.motr) back as JSON.

  motn-read.py FILE [--table]

Reports the canvas, every text layer in FCP field order (text, PostScript font, size,
colour), shapes with their fill colour, rig widgets (checkboxes, popups, sliders) with
their values, every published parameter (what Final Cut Pro shows in the inspector),
which channels a rig widget drives, media references, and fonts missing on this Mac.
Read-only. Exit 1 on a file that isn't Motion ozml.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ozml  # noqa: E402


def read(path):
    doc = ozml.Doc(path)
    rig = ozml.rigged(doc)
    texts = []
    for i, n in enumerate(ozml.text_layers(doc), 1):
        st = ozml.styles_of(n)
        s0 = st[0] if st else None
        size = ozml.param_at(s0, ozml.STYLE_SIZE) if s0 is not None else None
        color = ozml.param_at(s0, ozml.STYLE_COLOR) if s0 is not None else None
        font = ozml.param_at(s0, ozml.STYLE_FONT) if s0 is not None else None
        texts.append({
            "field": i, "name": n.get("name"), "id": n.get("id"),
            "style_id": s0.get("id") if s0 is not None else None,
            "text": ozml.get_text(n),
            "font": font.findtext("font") if font is not None else None,
            "size": float(size.get("value")) if size is not None and size.get("value") else None,
            "color": ozml.hex_of(ozml.get_rgb(color)),
            "styles": len(st),
        })
    shapes = []
    for n in ozml.shape_layers(doc):
        fill = ozml.param_at(n, ozml.SHAPE_FILL)
        op = ozml.param_at(n, ozml.OPACITY)
        shapes.append({"name": n.get("name"), "id": n.get("id"),
                       "fill": ozml.hex_of(ozml.get_rgb(fill)) if fill is not None else None,
                       "opacity": float(op.get("value", op.get("default", "1"))) if op is not None else 1.0})
    wids = []
    for w in ozml.widgets(doc):
        v = ozml.param_at(w, ozml.WIDGET_VALUE)
        if v is None:
            continue
        snaps = ozml.param_at(w, ("2", "101"))
        wids.append({"name": w.get("name"), "id": w.get("id"), "value": v.get("value"),
                     "snapshots": len(snaps.findall("parameter")) if snaps is not None else 0})
    pub = []
    for t in ozml.targets(doc):
        obj, _, p = ozml.resolve_target(doc, t)
        kind, val = ozml.describe_param(p)
        pub.append({"name": t.get("name"), "object": t.get("object"),
                    "owner": ozml.owner_name(doc, obj), "channel": t.get("channel"),
                    "param": p.get("name") if p is not None else None, "kind": kind, "value": val,
                    **({"broken": "object not found"} if obj is None else {})})
    rigs = sorted({(ozml.owner_name(doc, doc.objects.get(o)) or o, ch, w)
                   for (o, ch), (w, _) in rig.items()})
    fonts = sorted({t["font"] for t in texts if t["font"]})
    ok = ozml.font_check(fonts)
    return {
        "file": os.path.abspath(path), "kind": ozml.kind_of(path),
        "ozml_version": doc.root.get("version"), "canvas": ozml.scene_info(doc),
        "text_layers": texts, "shapes": shapes, "widgets": wids, "published": pub,
        "rigged": [{"object": o, "channel": c, "widget": w} for o, c, w in rigs],
        "media": ozml.media_refs(doc),
        "fonts": ok,
        "missing_fonts": [f for f in fonts if ok.get(f) == "missing"],
    }


def table(r):
    c = r["canvas"]
    print(f"{r['file']}\n{r['kind']}  {c['width']}x{c['height']}  {c['fps']} fps  {c['seconds']} s")
    print("\nText fields (FCP order):")
    for t in r["text_layers"]:
        print(f"  {t['field']}. {t['name']!r}: {t['text']!r}  {t['font']} {t['size']}  {t['color']}")
    if r["shapes"]:
        print("\nShapes:")
        for s in r["shapes"]:
            print(f"  {s['name']!r} fill {s['fill']}" + (f"  opacity {s['opacity']:g}" if s['opacity'] < 1 else ""))
    if r["widgets"]:
        print("\nWidgets:")
        for w in r["widgets"]:
            print(f"  {w['name']!r} = {w['value']} ({w['snapshots']} snapshots)")
    print("\nPublished:")
    for p in r["published"]:
        print(f"  {p['name']!r} -> {p['owner']} {p['channel']} [{p['kind']}] {p['value'] if p['value'] is not None else ''}")
    if r["missing_fonts"]:
        print("\nMISSING FONTS:", ", ".join(r["missing_fonts"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--table", action="store_true", help="human-readable summary instead of JSON")
    a = ap.parse_args()
    try:
        r = read(a.file)
    except (ozml.OzmlError, OSError) as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 1
    if a.table:
        table(r)
    else:
        print(json.dumps({"ok": True, **r}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
