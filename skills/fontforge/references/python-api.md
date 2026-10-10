# FontForge Python API — the parts this skill uses

Checked against FontForge 20251009 and the official reference
(<https://fontforge.org/docs/scripting/python/fontforge.html>). Scripts run with
`ff.py run script.py ARGS…`; `sys.argv` is `['script.py', ARGS…]`, so `argparse` works.

## Contents
- [Fonts](#fonts) · [Glyphs and outlines](#glyphs-and-outlines) · [Metrics](#metrics)
- [Names](#names) · [Lookups and kerning](#lookups-and-kerning) · [Selection](#selection)
- [Generate](#generate) · [Validation bitmask](#validation-bitmask)

## Fonts

| Call | Notes |
|---|---|
| `fontforge.open(path)` | SFD, UFO (dir), OTF, TTF, TTC (`path(Name)`), WOFF, WOFF2, PFB, SVG fonts |
| `fontforge.font()` | new empty font (em 1000, ascent 800, descent 200) |
| `font.save(path.sfd)` | native, lossless source — the format to keep and diff |
| `font.generate(path, flags=…)` | binary output; the extension picks the format |
| `font.em`, `font.ascent`, `font.descent` | setting `em` scales outlines; ascent+descent should equal em |
| `font.glyphs()` | iterator in GID order; `len(list(font.glyphs()))` is the glyph count |
| `cp in font`, `name in font` | membership by code point or glyph name |
| `font[cp]`, `font["A"]` | glyph access; `KeyError` if absent |
| `font.removeGlyph(name)` | drop a glyph (prefer to `clear()`, which keeps an empty slot) |
| `font.encoding = "UnicodeBmp"` | re-encode compactly after removing glyphs |
| `font.layers["Fore"].is_quadratic` | True for TrueType-flavoured sources |
| `font.mergeFonts(other)` | copy glyphs from another font that this one lacks |
| `font.close()` | free a font in long batch loops |

## Glyphs and outlines

| Call | Notes |
|---|---|
| `font.createChar(cp, name)` | creates or returns the glyph; **an AGL name wins over `cp`** (see gotchas) |
| `fontforge.unicodeFromName(name)` | AGL code point for a name, `-1` if none |
| `glyph.importOutlines(path, correctdir=True)` | SVG/EPS/PDF outline import; scales the SVG viewBox height to ascent+descent, top at the ascent; strokes are expanded to outlines; **width is left at 0** |
| `glyph.glyphPen()` / `glyphPen(replace=False)` | draw with `moveTo/lineTo/curveTo/qCurveTo/closePath/endPath` |
| `glyph.foreground` | a `layer` copy; iterate contours → points (`p.x`, `p.y`, `p.on_curve`); assign back after edits |
| `contour.closed` | False for an open path |
| `glyph.references` | tuple of `(name, (xx,xy,yx,yy,dx,dy), selected)` |
| `glyph.addReference(name, matrix)` / `glyph.unlinkRef()` | build or flatten composites |
| `glyph.transform((xx,xy,yx,yy,dx,dy))` | `psMat.translate/scale/rotate` build these matrices |
| `glyph.removeOverlap()` | merge overlapping contours (needs closed contours) |
| `glyph.correctDirection()` | outer clockwise / counters anti-clockwise (PostScript convention) |
| `glyph.addExtrema()` | insert points at horizontal/vertical extremes |
| `glyph.round()` | snap to integers — do it after `addExtrema`, which adds fractional points |
| `glyph.simplify(error_bound)` | remove redundant points (changes the design slightly) |
| `glyph.boundingBox()` | `(xmin, ymin, xmax, ymax)` |
| `glyph.export("a.png", pixelsize)` / `("a.svg")` | single-glyph image |

## Metrics

| Property | Notes |
|---|---|
| `glyph.width` | advance width |
| `glyph.left_side_bearing`, `glyph.right_side_bearing` | setting LSB shifts the outline; setting RSB changes the width |
| `font.os2_typoascent/typodescent/typolinegap`, `font.hhea_ascent/descent/linegap`, `font.os2_winascent/windescent` | vertical metrics |
| `font.*_add` (e.g. `hhea_ascent_add`) | True = value is an offset from the font's ascent/descent; set False for absolute values |

## Names

- Properties: `font.familyname` (nameID 1), `font.fullname` (4), `font.fontname` (6, PostScript, no spaces), `font.version` (string), `font.sfntRevision` (float → `head.fontRevision`), `font.copyright`, `font.weight`.
- `glyph.altuni` — extra code points a glyph is encoded at (tuple of `(cp, variation_selector, 0)`), e.g. space also at U+00A0; set to `None` to clear.
- `font.sfnt_names` — tuple of `(language, strid, string)`; strids include `Copyright`, `Family`, `SubFamily`, `UniqueID`, `Fullname`, `Version`, `PostScriptName`, `Trademark`, `Manufacturer`, `Designer`, `Descriptor`, `Vendor URL`, `Designer URL`, `License`, `License URL`, `Preferred Family`, `Preferred Styles`, `Compatible Full`, `Sample Text`, `WWS Family`, `WWS Subfamily`.
- `font.appendSFNTName("English (US)", "Version", "Version 1.200")` — adds or replaces one entry.
- An explicit `sfnt_names` entry overrides the property when the font is generated (fonts opened from OTF/TTF carry them). Set both, or rewrite the tuple; see gotchas.

## Lookups and kerning

```python
# a new kern lookup (pair positioning) registered for latn + DFLT
font.addLookup("kern", "gpos_pair", None,
               (("kern", (("latn", ("dflt",)), ("DFLT", ("dflt",)))),))
font.addLookupSubtable("kern", "kern-pairs")          # no `after` → first in the lookup
font["A"].addPosSub("kern-pairs", "V", 0, 0, -80, 0, 0, 0, 0, 0)   # xadv1 = -80
# class kerning: offsets has len(first) * len(second) entries; second class 0 is
# "everything else" and must be given explicitly as None
font.addKerningClass("kern", "kern-classes", (("A", "Agrave"),), (None, ("V", "W")), (0, -60))
```

- `font.gpos_lookups` / `font.gsub_lookups` — lookup names, in order.
- `font.getLookupInfo(lookup)` → `(type, flags, ((feature, ((script, (langs…)),…)),…))`.
- `font.getLookupSubtables(lookup)`, `font.isKerningClass(sub)`, `font.getKerningClass(sub)` → `(first_classes, second_classes, offsets)` with `offsets[i*len(second)+j]`; second class 0 is "all others".
- `glyph.getPosSub(sub)` → tuples `(sub, "Pair", other, xoff1, yoff1, xadv1, …)`; `"*"` for all subtables.
- `glyph.removePosSub(sub)`; `font.removeLookup(lookup)`; `font.removeLookupSubtable(sub)`.
- `font.mergeFeature("file.fea")` / `font.generateFeatureFile("out.fea")` — round-trip OpenType features as text.

Lookup semantics: within one lookup the **first subtable that has the pair wins**; separate
lookups **all apply and add up**. To change an existing pair, put an override subtable at
the start of the existing kern lookup; a second kern lookup would add to the old value.

## Selection

```python
font.selection.none()
font.selection.select(("more", "unicode"), 0x41)            # add one code point
font.selection.select(("more", "unicode", "ranges"), 0x30, 0x39)
font.selection.select(("more",), "aacute")                   # by glyph name
font.selection.invert()
[g.glyphname for g in font.selection.byGlyphs]
```
Font-wide operations then apply to the selection: `font.removeOverlap()`, `font.round()`,
`font.correctDirection()`, `font.addExtrema()`, `font.unlinkReferences()`, `font.clear()`.

## Generate

`font.generate(path, flags=(…))` — format from the extension: `.otf` (CFF), `.ttf`,
`.woff`, `.woff2`, `.ufo`, `.pfb`, `.svg`. Useful flags:

| Flag | Effect |
|---|---|
| `opentype` | write OpenType tables (GSUB/GPOS/GDEF) — keep it on |
| `round` | round coordinates on output |
| `omit-instructions` | drop TrueType hinting instructions (smaller web fonts) |
| `no-hints` | drop PostScript hints |
| `no-FFTM-table` | omit FontForge's timestamp table (reproducible bytes) |
| `PfEd-comments`, `PfEd-colors`, `PfEd-lookups` | FontForge private data — leave off for delivery |

WOFF2 support is compiled into the macOS app; `ff.py check` proves it with a real generate.

## Validation bitmask

`glyph.validate(force=True)` returns the mask below; `font.validate()` ORs every glyph.
`0x1` only means "has been validated" — mask it off.

| Bit | Meaning | Auto-fix |
|---|---|---|
| 0x2 | open contour | close (`contour.closed = True`) or redraw |
| 0x4 | self-intersecting / overlapping | `removeOverlap()` |
| 0x8 | wrong direction | `correctDirection()` |
| 0x10 | flipped reference | `unlinkRef()` then `correctDirection()` |
| 0x20 | missing extrema | `addExtrema()` then `round()` |
| 0x40 | lookup refers to a missing glyph | remove the lookup entry |
| 0x80 / 0x100 | PostScript point / hint limits | `simplify()` / drop hints |
| 0x200 | invalid PostScript glyph name | rename |
| 0x400–0x8000 | TrueType maxp limits | simplify, unlink deep references |
| 0x10000 | references nested too deeply | `unlinkRef()` |
| 0x40000 | points too far apart (> 32767) | rescale |
| 0x80000 | non-integer coordinates (TrueType only) | `round()` |
| 0x100000 | missing anchor | add the anchor point |
| 0x200000 / 0x400000 | duplicate glyph name / code point | rename / re-encode |
| 0x800000 | overlapping hints | re-hint |
