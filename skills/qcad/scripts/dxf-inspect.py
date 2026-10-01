#!/usr/bin/env python3
"""Summarise DXF files as JSON with ezdxf, independently of QCAD.

    python3 dxf-inspect.py FILE.dxf [FILE.dxf ...] [--texts] [--layer NAME]

Per file: DXF version, units, layers, model-space entity counts by type and
by layer, user blocks (name -> entity counts, inserts in model space), and
model-space extents. --texts adds every TEXT/MTEXT string (model space and
blocks); --layer limits the entity lists to one layer. Exit status 1 if any
file cannot be read.

Needs ezdxf (pip install ezdxf); run it with the interpreter that has it.
"""
import argparse
import collections
import json
import sys

try:
    import ezdxf
    from ezdxf import bbox
except ImportError:
    sys.exit("ezdxf missing: python3 -m pip install ezdxf (a venv is fine)")


def text_of(e):
    if e.dxftype() == "MTEXT":
        return e.plain_text()
    if e.dxftype() in ("TEXT", "ATTRIB", "ATTDEF"):
        return e.dxf.text
    return None


def inspect(path, want_texts, layer):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    ents = [e for e in msp if layer is None or e.dxf.layer == layer]
    blocks = {}
    for b in doc.blocks:
        if b.name.startswith("*"):
            continue
        blocks[b.name] = {
            "entities": dict(collections.Counter(e.dxftype() for e in b)),
            "inserts": [
                {"layer": i.dxf.layer, "at": [round(i.dxf.insert.x, 3), round(i.dxf.insert.y, 3)],
                 "xscale": i.dxf.xscale}
                for i in msp.query("INSERT") if i.dxf.name == b.name
            ],
        }
    box = bbox.extents(msp, fast=True)
    out = {
        "file": path,
        "dxfversion": doc.dxfversion,
        "insunits": doc.header.get("$INSUNITS"),
        "layers": sorted(l.dxf.name for l in doc.layers),
        "entity_count": len(ents),
        "by_type": dict(collections.Counter(e.dxftype() for e in ents)),
        "by_layer": dict(collections.Counter(e.dxf.layer for e in ents)),
        "blocks": blocks,
        "extents": None if not box.has_data else {
            "min": [round(box.extmin.x, 3), round(box.extmin.y, 3)],
            "max": [round(box.extmax.x, 3), round(box.extmax.y, 3)],
            "size": [round(box.size.x, 3), round(box.size.y, 3)],
        },
    }
    if want_texts:
        texts = [{"layer": e.dxf.layer, "text": text_of(e)} for e in ents if text_of(e) is not None]
        for name, b in ((b.name, b) for b in doc.blocks if not b.name.startswith("*")):
            texts += [{"block": name, "text": text_of(e)} for e in b if text_of(e) is not None]
        out["texts"] = texts
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--texts", action="store_true")
    ap.add_argument("--layer")
    a = ap.parse_args()
    results, failed = [], False
    for f in a.files:
        try:
            results.append(inspect(f, a.texts, a.layer))
        except (IOError, ezdxf.DXFError) as e:
            results.append({"file": f, "error": str(e)})
            failed = True
    json.dump(results if len(results) > 1 else results[0], sys.stdout, indent=1)
    print()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
