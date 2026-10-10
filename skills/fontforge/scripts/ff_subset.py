"""Subset a font to a character set (runs inside FontForge: `ff.py subset ...`).

    ff.py subset IN.ttf -o OUT.woff2 [-o OUT.ttf] --text "Hello, Világ!"
    ff.py subset IN.otf -o OUT.woff2 --text-file page.txt --unicodes U+0020-007E,U+2013

Keeps .notdef, space (unless --no-space) and exactly the requested characters that
the font has. Accented glyphs built from references to dropped glyphs (á = a + acute)
are unlinked into plain outlines first, so the cmap holds only what was asked for
and nothing renders blank. Kerning, ligatures and other lookups touching dropped
glyphs shrink with them. Names, metrics and the licence text are kept as they are.

Prints a JSON report (kept, missing, sizes) to stdout; exit 1 if a requested
character is not in the font (the output is still written).
"""
import argparse
import json
import os
import sys

import fontforge


def parse_ranges(spec):
    cps = set()
    for part in filter(None, (p.strip() for p in spec.split(","))):
        lo, _, hi = part.upper().replace("U+", "").partition("-")
        lo_i = int(lo, 16)
        cps.update(range(lo_i, (int(hi, 16) if hi else lo_i) + 1))
    return cps


def prune_kerning_classes(font):
    """Drop removed glyphs and the classes left empty from class-kerning subtables.

    Without this the generated GPOS keeps every class of the full font; shapers cope,
    but FontForge mis-reads its own output ("Nonsensical class assigned to a glyph")
    and reports the kerning as gone, and the table carries dead weight.
    """
    present = {g.glyphname for g in font.glyphs()}
    for lookup in font.gpos_lookups:
        if font.getLookupInfo(lookup)[0] != "gpos_pair":
            continue
        for sub in font.getLookupSubtables(lookup):
            if not font.isKerningClass(sub):
                continue
            first, second, offsets = font.getKerningClass(sub)
            n2 = len(second)
            first_f = [tuple(g for g in (c or ()) if g in present) for c in first]
            second_f = [tuple(g for g in (c or ()) if g in present) for c in second]
            rows = [i for i, c in enumerate(first_f) if c]
            cols = [0] + [j for j, c in enumerate(second_f) if j and c]  # class 0 = all others
            if not rows or len(cols) == 1:
                font.removeLookupSubtable(sub)
                continue
            new_first = tuple(first_f[i] for i in rows)
            new_second = (None,) + tuple(second_f[j] for j in cols[1:])
            new_offsets = tuple(offsets[i * n2 + j] for i in rows for j in cols)
            font.alterKerningClass(sub, new_first, new_second, new_offsets)


def generate_quietly(font, out, flags):
    """generate() with FontForge's C-level stderr captured; returns the number of
    'unused glyph' lookup warnings and passes any other message through."""
    import tempfile
    sys.stderr.flush()
    saved = os.dup(2)
    with tempfile.TemporaryFile(mode="w+b") as tmp:
        os.dup2(tmp.fileno(), 2)
        try:
            font.generate(out, flags=flags)
        finally:
            os.dup2(saved, 2)
            os.close(saved)
        tmp.seek(0)
        lines = tmp.read().decode("utf-8", "replace").splitlines()
    noise = [ln for ln in lines if "contains unused glyph" in ln]
    for line in lines:
        if line not in noise:
            print(line, file=sys.stderr)
    return len(noise)


def main():
    ap = argparse.ArgumentParser(prog="ff.py subset")
    ap.add_argument("font")
    ap.add_argument("-o", "--output", action="append", required=True)
    ap.add_argument("--text", action="append", default=[])
    ap.add_argument("--text-file", action="append", default=[])
    ap.add_argument("--unicodes", action="append", default=[],
                    help="comma list of U+XXXX or U+XXXX-YYYY ranges")
    ap.add_argument("--no-space", action="store_true")
    ap.add_argument("--no-hints", action="store_true",
                    help="drop TrueType instructions / PostScript hints (smaller web fonts)")
    opt = ap.parse_args()

    wanted = set()
    for text in opt.text:
        wanted.update(ord(c) for c in text)
    for path in opt.text_file:
        with open(path, encoding="utf-8") as fh:
            wanted.update(ord(c) for c in fh.read())
    for spec in opt.unicodes:
        wanted |= parse_ranges(spec)
    wanted -= {0x0A, 0x0D, 0x09}  # line breaks and tabs in text files
    if not opt.no_space:
        wanted.add(0x20)
    if not wanted:
        sys.exit("nothing to keep: pass --text, --text-file or --unicodes")

    font = fontforge.open(opt.font)
    before = len(list(font.glyphs()))
    keep, missing = {".notdef"}, []
    for cp in sorted(wanted):
        if cp in font:
            keep.add(font[cp].glyphname)
        else:
            missing.append(f"U+{cp:04X} {chr(cp)!r}")

    # Unlink references to glyphs that will be dropped, so composites survive.
    unlinked = []
    for name in sorted(keep):
        if name in font and any(ref[0] not in keep for ref in font[name].references):
            font[name].unlinkRef()
            unlinked.append(name)

    # A kept glyph can carry extra code points (Lato's space also encodes U+00A0);
    # drop the ones that were not asked for so the cmap holds exactly the request.
    for name in keep:
        if name in font and font[name].altuni:
            alts = tuple(a for a in font[name].altuni if a[0] in wanted)
            font[name].altuni = alts or None

    drop = [g.glyphname for g in font.glyphs() if g.glyphname not in keep]
    for name in drop:
        font.removeGlyph(name)
    prune_kerning_classes(font)
    # Re-encode compactly so no stale slots from the original encoding are written out.
    font.encoding = "UnicodeBmp" if all(cp <= 0xFFFF for cp in wanted) else "UnicodeFull"

    flags = ("opentype", "omit-instructions") if opt.no_hints else ("opentype",)
    report = {"input": opt.font, "input_bytes": os.path.getsize(opt.font),
              "glyphs_before": before, "glyphs_after": len(list(font.glyphs())),
              "kept": sorted(f"U+{font[n].unicode:04X} {n}" for n in keep
                             if n in font and font[n].unicode >= 0),
              "missing": missing, "unlinked_composites": unlinked, "outputs": {}}
    dropped_subtables = 0
    for out in opt.output:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        if out.lower().endswith(".sfd"):
            font.save(out)
        else:
            dropped_subtables = generate_quietly(font, out, flags)
        report["outputs"][out] = os.path.getsize(out)
    # FontForge drops every substitution/positioning subtable that still names a removed
    # glyph (small caps, superiors, old-style figures...) and warns once per glyph.
    # Kerning between kept glyphs survives. Report the count instead of the flood.
    report["lookup_subtable_warnings"] = dropped_subtables
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(1 if missing else 0)


main()
