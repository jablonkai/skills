"""Build an icon font from a folder of SVGs (runs inside FontForge: `ff.py iconfont ...`).

    ff.py iconfont ICONS_DIR --family "My Icons" [--map map.json|map.csv] \
        -o out/myicons.sfd -o out/myicons.otf -o out/myicons.woff2 [--css out/myicons.css]

Map file: JSON object {"name": "E001" | "U+E001" | 57345, ...} or CSV rows
`name,codepoint`; `name` is the SVG file stem. SVGs without an entry get the next
free code point from --start (default U+E000, Private Use Area). A map entry with no
SVG is an error. Glyph names are the stems sanitised to [A-Za-z0-9_.].

Every glyph is cleaned (overlaps removed, direction corrected, extrema added, points
rounded) and given the same advance (--width, default the em). --fit viewbox keeps
the SVG's own placement (its viewBox maps onto the ascent..descent box); --fit center
scales each icon's outline into the em box with --padding and centres it.

Prints a JSON report to stdout; exit 1 if any icon came out empty.
"""
import argparse
import csv
import json
import os
import re
import sys
import tempfile

import fontforge


def parse_cp(value):
    if isinstance(value, int):
        return value
    text = str(value).strip().upper()
    text = text[2:] if text.startswith(("U+", "0X")) else text
    text = text[1:] if text.startswith("\\") else text
    return int(text, 16)


def load_map(path):
    if not path:
        return {}
    with open(path, encoding="utf-8") as fh:
        if path.lower().endswith(".json"):
            raw = json.load(fh)
            if isinstance(raw, list):  # [{"name":..,"codepoint":..}]
                raw = {r["name"]: r.get("codepoint", r.get("unicode")) for r in raw}
        else:
            raw = {row[0].strip(): row[1].strip()
                   for row in csv.reader(fh) if len(row) >= 2 and not row[0].startswith("#")
                   and row[0].strip().lower() != "name"}
    return {name: parse_cp(cp) for name, cp in raw.items()}


def glyph_name(stem, cp):
    name = re.sub(r"[^A-Za-z0-9_.]", "_", stem)
    name = name if name and not name[0].isdigit() and name[0] != "." else "i_" + name
    # createChar() trusts an Adobe Glyph List name over the code point it is given:
    # a glyph called "plus" lands on U+002B, not on the PUA slot. Suffix those names.
    if fontforge.unicodeFromName(name) not in (-1, cp):
        name += ".icon"
    return name


ROTATE_CENTER = re.compile(
    r"rotate\(\s*([-+.\deE]+)[\s,]+([-+.\deE]+)[\s,]+([-+.\deE]+)\s*\)")
SVG_TAG = re.compile(r"<svg\b[^>]*>", re.S)
VIEWBOX = re.compile(r"""viewBox\s*=\s*["']\s*([-+.\deE]+)[\s,]+([-+.\deE]+)[\s,]+([-+.\deE]+)[\s,]+([-+.\deE]+)\s*["']""")


def normalise_svg(path, tmpdir):
    """Work around two FontForge SVG-import bugs in a temp copy of the file.

    - rotate(a cx cy) is applied about the wrong point: rewrite it as
      translate(cx cy) rotate(a) translate(-cx -cy).
    - a viewBox with a non-zero origin is placed as if it started at 0,0: shift the
      content by the origin and zero it.
    Returns the path to import (the original when nothing needed changing).
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    new = ROTATE_CENTER.sub(
        lambda m: f"translate({m[2]} {m[3]}) rotate({m[1]}) translate({-float(m[2])} {-float(m[3])})",
        text)
    tag = SVG_TAG.search(new)
    vb = VIEWBOX.search(tag.group(0)) if tag else None
    if vb and (float(vb[1]) or float(vb[2])):
        minx, miny, w, h = (float(v) for v in vb.groups())
        svg_open = tag.group(0).replace(vb.group(0), f'viewBox="0 0 {w} {h}"')
        close = new.rfind("</svg>")
        new = (new[:tag.start()] + svg_open + f'<g transform="translate({-minx} {-miny})">'
               + new[tag.end():close] + "</g>" + new[close:])
    if new == text:
        return path
    out = os.path.join(tmpdir, os.path.basename(path))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(new)
    return out


def fit_center(glyph, em, ascent, descent, padding, width):
    xmin, ymin, xmax, ymax = glyph.boundingBox()
    w, h = xmax - xmin, ymax - ymin
    if w <= 0 or h <= 0:
        return
    box = em - 2 * padding
    scale = min(box / w, box / h)
    glyph.transform((1, 0, 0, 1, -xmin - w / 2, -ymin - h / 2))
    glyph.transform((scale, 0, 0, scale, 0, 0))
    glyph.transform((1, 0, 0, 1, width / 2, (ascent - descent) / 2))


def main():
    ap = argparse.ArgumentParser(prog="ff.py iconfont")
    ap.add_argument("icons_dir")
    ap.add_argument("--family", required=True)
    ap.add_argument("--style", default="Regular")
    ap.add_argument("--version", default="1.000")
    ap.add_argument("--copyright", default="")
    ap.add_argument("--map")
    ap.add_argument("--start", default="E000", help="first auto code point (hex)")
    ap.add_argument("--em", type=int, default=1000)
    ap.add_argument("--descent", type=int, help="default em/8 (ascent = em - descent)")
    ap.add_argument("--width", type=int, help="advance width, default the em")
    ap.add_argument("--fit", choices=("viewbox", "center"), default="viewbox")
    ap.add_argument("--padding", type=int, default=0, help="--fit center margin, font units")
    ap.add_argument("-o", "--output", action="append", required=True,
                    help="output file; extension picks the format (.sfd .ufo .otf .ttf .woff .woff2)")
    ap.add_argument("--css", help="also write @font-face + one class per icon")
    ap.add_argument("--css-prefix", default="icon-")
    opt = ap.parse_args()

    svgs = {os.path.splitext(f)[0]: os.path.join(opt.icons_dir, f)
            for f in sorted(os.listdir(opt.icons_dir)) if f.lower().endswith(".svg")}
    if not svgs:
        sys.exit(f"no .svg files in {opt.icons_dir}")
    mapping = load_map(opt.map)
    missing = sorted(set(mapping) - set(svgs))
    if missing:
        sys.exit(f"map entries without an SVG: {', '.join(missing)}")
    dupes = {cp for cp in mapping.values() if list(mapping.values()).count(cp) > 1}
    if dupes:
        sys.exit("duplicate code points in map: " + ", ".join(f"U+{c:04X}" for c in sorted(dupes)))
    used, nxt = set(mapping.values()), parse_cp(opt.start)
    for stem in svgs:
        if stem not in mapping:
            while nxt in used:
                nxt += 1
            mapping[stem] = nxt
            used.add(nxt)

    em = opt.em
    descent = opt.descent if opt.descent is not None else em // 8
    ascent = em - descent
    width = opt.width or em
    font = fontforge.font()
    font.em = em
    font.ascent, font.descent = ascent, descent
    family = opt.family.strip()
    ps_family = re.sub(r"[^A-Za-z0-9]", "", family) or "IconFont"
    ps_style = re.sub(r"[^A-Za-z0-9]", "", opt.style) or "Regular"
    font.familyname = family
    font.fontname = f"{ps_family}-{ps_style}"
    font.fullname = family if opt.style == "Regular" else f"{family} {opt.style}"
    font.version = opt.version
    font.copyright = opt.copyright
    font.appendSFNTName("English (US)", "SubFamily", opt.style)
    for attr, val in (("os2_typoascent", ascent), ("os2_typodescent", -descent),
                      ("os2_typolinegap", 0), ("hhea_ascent", ascent),
                      ("hhea_descent", -descent), ("hhea_linegap", 0),
                      ("os2_winascent", ascent), ("os2_windescent", descent)):
        setattr(font, attr, val)
    for attr in ("os2_typoascent_add", "os2_typodescent_add", "hhea_ascent_add",
                 "hhea_descent_add", "os2_winascent_add", "os2_windescent_add"):
        setattr(font, attr, False)

    report = {"family": family, "fontname": font.fontname, "em": em,
              "glyphs": [], "warnings": [], "outputs": []}
    tmpdir = tempfile.mkdtemp(prefix="ff_iconfont-")
    for stem, path in svgs.items():
        cp = mapping[stem]
        name = glyph_name(stem, cp)
        g = font.createChar(cp, name)
        g.importOutlines(normalise_svg(path, tmpdir), correctdir=True)
        if len(g.foreground) == 0:
            report["warnings"].append(f"{stem}: no outlines imported (empty SVG, text or image only?)")
        else:
            g.removeOverlap()
            if opt.fit == "center":
                fit_center(g, em, ascent, descent, opt.padding, width)
            g.correctDirection()
            g.addExtrema()
            g.round()
        g.width = width
        bbox = [round(v) for v in g.boundingBox()]
        if len(g.foreground) and (bbox[2] - bbox[0] < em * 0.02 or bbox[3] - bbox[1] < em * 0.02):
            report["warnings"].append(f"{stem}: outline is very thin {bbox} — hairline stroke?")
        if len(g.foreground) and (bbox[0] < 0 or bbox[2] > width or bbox[3] > ascent or bbox[1] < -descent):
            report["warnings"].append(f"{stem}: outline {bbox} spills outside the em box; try --fit center")
        report["glyphs"].append({"name": name, "file": os.path.basename(path),
                                 "unicode": f"U+{cp:04X}", "contours": len(g.foreground),
                                 "bbox": bbox, "validation": hex(g.validate(True))})

    for out in opt.output:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        if out.lower().endswith(".sfd"):
            font.save(out)
        else:
            font.generate(out, flags=("opentype", "round"))
        report["outputs"].append(out)

    if opt.css:
        webfont = next((o for o in opt.output if o.lower().endswith(".woff2")),
                       next((o for o in opt.output if not o.lower().endswith((".sfd", ".ufo"))), ""))
        rel = os.path.relpath(webfont, os.path.dirname(os.path.abspath(opt.css))) if webfont else ""
        fmt = {"woff2": "woff2", "woff": "woff", "otf": "opentype", "ttf": "truetype"}.get(
            rel.rsplit(".", 1)[-1].lower(), "woff2")
        lines = ["@font-face {", f'  font-family: "{family}";',
                 f'  src: url("{rel}") format("{fmt}");',
                 "  font-weight: normal;", "  font-style: normal;", "  font-display: block;", "}",
                 f'[class^="{opt.css_prefix}"], [class*=" {opt.css_prefix}"] {{',
                 f'  font-family: "{family}";', "  font-style: normal;", "  font-weight: normal;",
                 "  line-height: 1;", "  speak: never;", "}"]
        for gl in report["glyphs"]:
            css_name = re.sub(r"[^A-Za-z0-9_-]", "-", os.path.splitext(gl["file"])[0])
            lines.append(f'.{opt.css_prefix}{css_name}::before {{ content: "\\{gl["unicode"][2:].lower()}"; }}')
        with open(opt.css, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        report["outputs"].append(opt.css)

    print(json.dumps(report, indent=2))
    empty = [gl for gl in report["glyphs"] if gl["contours"] == 0]
    sys.exit(1 if empty else 0)


main()
