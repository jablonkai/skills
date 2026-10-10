"""Read a font back as JSON (runs inside FontForge: `ff.py inspect ...`).

    ff.py inspect FONT [--cmap] [--names] [--glyph A --glyph V] [--pairs "AV,To,T o"]

Always: names (family, full, PostScript, version, copyright), em/ascent/descent,
glyph count, encoded count, outline type, lookups by feature, kerning pair count,
and how many glyphs fail validation. --cmap lists every encoded glyph, --names the
full name table, --glyph the metrics of a glyph (repeatable), --pairs the kerning
value FontForge would apply to each pair (two characters, or "left right" glyph names).

Works on SFD, UFO, OTF, TTF, WOFF and WOFF2. Use it to verify a result before
reporting it done.
"""
import argparse
import json
import os

import fontforge


def glyph_of(font, token):
    if token in font:
        return font[token]
    if len(token) == 1 and ord(token) in font:
        return font[ord(token)]
    return None


def pair_subtables(font):
    for lookup in font.gpos_lookups:
        if font.getLookupInfo(lookup)[0] == "gpos_pair":
            for sub in font.getLookupSubtables(lookup):
                yield lookup, sub


def kern_value(font, left, right):
    """First pair adjustment that applies, per lookup order (as a shaper would)."""
    for lookup, sub in pair_subtables(font):
        if font.isKerningClass(sub):
            first, second, offsets = font.getKerningClass(sub)
            i = next((n for n, cls in enumerate(first) if cls and left in cls), None)
            j = next((n for n, cls in enumerate(second) if cls and right in cls), 0)
            if i is not None:
                value = offsets[i * len(second) + j]
                if value:
                    return value, sub
            continue
        for entry in font[left].getPosSub(sub):
            if entry[1] == "Pair" and entry[2] == right:
                return entry[5], sub  # xadv of the first glyph
    return 0, None


def count_pairs(font):
    total = 0
    for _, sub in pair_subtables(font):
        if font.isKerningClass(sub):
            first, second, offsets = font.getKerningClass(sub)
            total += sum(1 for v in offsets if v)
        else:
            total += sum(len([e for e in g.getPosSub(sub) if e[1] == "Pair"])
                         for g in font.glyphs())
    return total


def main():
    ap = argparse.ArgumentParser(prog="ff.py inspect")
    ap.add_argument("font")
    ap.add_argument("--cmap", action="store_true")
    ap.add_argument("--names", action="store_true")
    ap.add_argument("--glyph", action="append", default=[])
    ap.add_argument("--pairs", help='comma list: "AV,To" or glyph names "T o"')
    opt = ap.parse_args()

    font = fontforge.open(opt.font)
    glyphs = list(font.glyphs())
    encoded = sorted((g.unicode, g.glyphname) for g in glyphs if g.unicode >= 0)
    features = {}
    for table, lookups in (("GSUB", font.gsub_lookups), ("GPOS", font.gpos_lookups)):
        for lookup in lookups:
            for feat in font.getLookupInfo(lookup)[2]:
                features.setdefault(f"{table}:{feat[0]}", 0)
                features[f"{table}:{feat[0]}"] += 1
    invalid = sum(1 for g in glyphs if g.validate(True) & ~0x1)
    out = {
        "file": opt.font, "bytes": os.path.getsize(opt.font) if os.path.isfile(opt.font) else None,
        "familyname": font.familyname, "fullname": font.fullname, "fontname": font.fontname,
        "weight": font.weight, "version": font.version, "copyright": font.copyright,
        "em": font.em, "ascent": font.ascent, "descent": font.descent,
        "outline_type": "quadratic" if font.layers["Fore"].is_quadratic else "cubic",
        "glyph_count": len(glyphs), "encoded_count": len(encoded),
        "unicode_range": [f"U+{encoded[0][0]:04X}", f"U+{encoded[-1][0]:04X}"] if encoded else None,
        "features": features, "kerning_pairs": count_pairs(font),
        "glyphs_failing_validation": invalid,
    }
    if opt.cmap:
        out["cmap"] = {f"U+{cp:04X}": name for cp, name in encoded}
    if opt.names:
        out["names"] = [list(n) for n in font.sfnt_names]
    if opt.glyph:
        out["glyphs"] = {}
        for token in opt.glyph:
            g = glyph_of(font, token)
            out["glyphs"][token] = None if g is None else {
                "name": g.glyphname, "unicode": f"U+{g.unicode:04X}" if g.unicode >= 0 else None,
                "width": g.width, "lsb": round(g.left_side_bearing), "rsb": round(g.right_side_bearing),
                "bbox": [round(v) for v in g.boundingBox()], "contours": len(g.foreground),
                "references": [r[0] for r in g.references]}
    if opt.pairs:
        out["pairs"] = {}
        for pair in (p for p in opt.pairs.split(",") if p):
            left, right = pair.split() if " " in pair.strip() else (pair[0], pair[1:])
            gl, gr = glyph_of(font, left), glyph_of(font, right)
            if gl is None or gr is None:
                out["pairs"][pair] = None
                continue
            value, sub = kern_value(font, gl.glyphname, gr.glyphname)
            out["pairs"][pair] = {"value": value, "subtable": sub}
    print(json.dumps(out, indent=2, ensure_ascii=False))


main()
