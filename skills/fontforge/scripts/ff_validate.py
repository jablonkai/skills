"""Report and fix font validation problems (runs inside FontForge: `ff.py validate ...`).

    ff.py validate FONT                          # report only
    ff.py validate FONT --fix -o fixed.sfd [-o fixed.otf] [--close-open]

Report: every glyph with a problem, decoded from FontForge's validation bitmask, plus
non-integer coordinates (checked directly, since FontForge flags those only for
TrueType outlines). --fix repairs what is safe to repair automatically, in this
order per glyph: unlink flipped/overlapping references, remove overlaps, correct
contour direction, add extrema, round to integers — then re-validates and reports
before → after. Open contours are left alone (removing overlaps on them destroys
outlines) unless --close-open is given, which closes each with a straight segment.

The input is never overwritten; --fix needs at least one -o. JSON report on stdout;
exit 0 when nothing (fixable or not) remains, 1 otherwise.
"""
import argparse
import json
import os
import sys

import fontforge

# glyph.validate() bitmask, per the FontForge Python docs (0x1 = "has been validated").
BITS = {
    0x2: "open contour",
    0x4: "self-intersecting / overlapping contours",
    0x8: "contour drawn in wrong direction",
    0x10: "flipped reference",
    0x20: "missing extrema",
    0x40: "lookup refers to a glyph not in the font",
    0x80: "more points than PostScript allows (1500)",
    0x100: "more hints than PostScript allows (96)",
    0x200: "invalid PostScript glyph name",
    0x400: "more points than maxp allows",
    0x800: "more contours than maxp allows",
    0x1000: "composite: more points than maxp allows",
    0x2000: "composite: more contours than maxp allows",
    0x4000: "instructions longer than maxp allows",
    0x8000: "more references than maxp allows",
    0x10000: "references nested too deeply",
    0x40000: "points too far apart",
    0x80000: "non-integer coordinates",
    0x100000: "missing anchor",
    0x200000: "duplicate glyph name",
    0x400000: "duplicate Unicode code point",
    0x800000: "overlapping hints",
}
NONINT = "non-integer coordinates"
AUTO_FIXABLE = {BITS[b] for b in (0x4, 0x8, 0x10, 0x20, 0x80000)}


def has_open(glyph):
    return any(not c.closed for c in glyph.foreground)


def problems(glyph):
    mask = glyph.validate(True) & ~0x1
    found = [text for bit, text in BITS.items() if mask & bit]
    # Cubic outlines only: FontForge's own bit covers TrueType, and quadratic contours
    # yield implied on-curve midpoints (half units) that are never stored in the file.
    if NONINT not in found and not glyph.foreground.is_quadratic and any(
            p.x != round(p.x) or p.y != round(p.y) for c in glyph.foreground for p in c):
        found.append(NONINT)
    # A closed font can still have an open contour FontForge reports only as an overlap.
    if has_open(glyph) and BITS[0x2] not in found:
        found.append(BITS[0x2])
    return found


def fix(glyph, close_open):
    steps = []
    if has_open(glyph):
        if not close_open:
            return ["skipped: open contour — close it by hand or rerun with --close-open"]
        layer = glyph.foreground
        for contour in layer:
            if not contour.closed:
                contour.closed = True
        glyph.foreground = layer
        steps.append("closed open contours")
    if glyph.references:
        glyph.unlinkRef()
        steps.append("unlinked references")
    glyph.removeOverlap()
    glyph.correctDirection()
    glyph.addExtrema()
    glyph.round()
    steps += ["removed overlaps", "corrected direction", "added extrema", "rounded"]
    return steps


def main():
    ap = argparse.ArgumentParser(prog="ff.py validate")
    ap.add_argument("font")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--close-open", action="store_true")
    ap.add_argument("-o", "--output", action="append", default=[])
    opt = ap.parse_args()
    if opt.fix and not opt.output:
        sys.exit("--fix needs -o OUTPUT (the input is never overwritten)")
    if any(os.path.abspath(o) == os.path.abspath(opt.font) for o in opt.output):
        sys.exit("refusing to overwrite the input font; pick another -o path")

    font = fontforge.open(opt.font)
    report = {"font": opt.font, "fontname": font.fontname, "glyph_count": 0,
              "outline_type": "quadratic (TrueType)" if font.layers["Fore"].is_quadratic
              else "cubic (PostScript/CFF)", "summary": {}, "glyphs": []}
    for glyph in font.glyphs():
        report["glyph_count"] += 1
        found = problems(glyph)
        if not found:
            continue
        entry = {"glyph": glyph.glyphname,
                 "unicode": f"U+{glyph.unicode:04X}" if glyph.unicode >= 0 else None,
                 "problems": found}
        if opt.fix:
            entry["fix"] = fix(glyph, opt.close_open)
            entry["after"] = problems(glyph)
        report["glyphs"].append(entry)

    remaining = {}
    for entry in report["glyphs"]:
        for p in entry["problems"]:
            report["summary"][p] = report["summary"].get(p, 0) + 1
        for p in entry.get("after", entry["problems"]):
            remaining[p] = remaining.get(p, 0) + 1
    report["remaining"] = remaining
    report["needs_manual_fix"] = sorted(
        e["glyph"] for e in report["glyphs"]
        if set(e.get("after", e["problems"])) - (set() if opt.fix else AUTO_FIXABLE))

    for out in opt.output:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        if out.lower().endswith(".sfd"):
            font.save(out)
        else:
            font.generate(out, flags=("opentype",))
    report["outputs"] = opt.output
    print(json.dumps(report, indent=2))
    sys.exit(1 if remaining else 0)


main()
