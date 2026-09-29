#!/usr/bin/env python3
"""Check Inkscape inputs and outputs without opening Inkscape.

    python3 ink-verify.py FILE... [--png-size WxH]

Prints one JSON line per file and exits 1 if any file is unreadable or fails
an expectation. Standard library only.

  .svg  well-formed XML, root size and viewBox, element counts (paths, text,
        images, gradients, Inkscape layers), and total path coordinate pairs
        (a node-count proxy for comparing before/after path-simplify)
  .png  pixel width and height from the IHDR chunk; --png-size WxH asserts
        them (applies to every PNG given)
  .pdf  header, page count, and font objects (0 = all text is outlines)
  .eps  header and %%BoundingBox
"""

import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

SVG = "{http://www.w3.org/2000/svg}"
INK = "{http://www.inkscape.org/namespaces/inkscape}"
NUMBER = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")


def svg_info(path):
    root = ET.parse(path).getroot()
    if root.tag != SVG + "svg":
        raise ValueError(f"root element is {root.tag}, not svg")
    counts = {}
    for name in ("path", "text", "image", "rect", "circle", "ellipse", "polygon",
                 "linearGradient", "radialGradient", "use"):
        counts[name] = len(root.findall(f".//{SVG}{name}"))
    layers = [g.get(INK + "label") or g.get("id")
              for g in root.iter(SVG + "g") if g.get(INK + "groupmode") == "layer"]
    pairs = sum(len(NUMBER.findall(p.get("d", ""))) // 2
                for p in root.iter(SVG + "path"))
    return {"width": root.get("width"), "height": root.get("height"),
            "viewBox": root.get("viewBox"), "counts": counts,
            "layers": layers, "path_coord_pairs": pairs}


def png_info(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise ValueError("not a PNG")
    width, height = struct.unpack(">II", head[16:24])
    return {"width": width, "height": height}


def pdf_info(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if not data.startswith(b"%PDF-"):
        raise ValueError("missing %PDF- header")
    # Cairo (Inkscape's PDF backend) packs page objects into compressed object
    # streams, so inflate every Flate stream before counting.
    text = data
    for raw in re.findall(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            text += zlib.decompress(raw)
        except zlib.error:
            pass
    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", text))
    fonts = len(re.findall(rb"/Type\s*/Font\b", text))
    return {"version": data[5:8].decode("ascii", "replace"), "pages": pages, "fonts": fonts}


def eps_info(path):
    with open(path, "rb") as fh:
        data = fh.read(4096)
    if not data.startswith(b"%!PS"):
        raise ValueError("missing %!PS header")
    box = re.search(rb"%%BoundingBox:\s*([-\d. ]+)", data)
    return {"bounding_box": box.group(1).decode().strip() if box else None}


def main(argv):
    expect_png = None
    files = []
    args = iter(argv)
    for arg in args:
        if arg == "--png-size":
            w, _, h = next(args, "").partition("x")
            expect_png = (int(w), int(h))
        else:
            files.append(arg)
    if not files:
        print(__doc__.strip(), file=sys.stderr)
        return 2

    ok = True
    for path in files:
        ext = path.rsplit(".", 1)[-1].lower()
        report = {"file": path}
        try:
            info = {"svg": svg_info, "png": png_info, "pdf": pdf_info,
                    "eps": eps_info, "ps": eps_info}[ext](path)
            report.update(info)
            if ext == "png" and expect_png and (info["width"], info["height"]) != expect_png:
                report["error"] = "expected %dx%d" % expect_png
        except KeyError:
            report["error"] = f"unsupported extension .{ext}"
        except (OSError, ValueError, ET.ParseError) as exc:
            report["error"] = str(exc)
        ok = ok and "error" not in report
        print(json.dumps(report))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
