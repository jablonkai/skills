---
name: fontforge
description: 'Build, edit, convert, debug and validate fonts headless with FontForge''s Python API — assemble an icon font from a folder of SVGs with a codepoint map (OTF/TTF/WOFF2 + CSS), import SVG letters as glyphs, set side bearings, kerning and name-table entries, subset a web font to the characters a page uses, convert between SFD, UFO, OTF, TTF and WOFF2, find why glyphs render as blank boxes or lose accents, and fix validation problems (overlaps, direction, extrema, open contours), verified by read-back and a rendered specimen. Use for "make an icon font from these SVGs", "subset this font to a woff2 for our site", "my font fails validation", "á shows as an empty box in my font", "add kerning for AV and To", "rename the family and bump the version", "turn my .sfd into OTF", or Hungarian "csinálj ikonfontot ezekből az SVG-kből". Not for drawing the SVG artwork (inkscape), installing system fonts, laying out documents (scribus, libreoffice), or raster text effects (gimp, krita, pixelmator-pro).'
summary: "build, edit and validate fonts headless with FontForge — icon fonts from SVG folders, glyph import, side bearings, kerning and name tables, subsetting, SFD/UFO/OTF/TTF/WOFF2 conversion, overlap, direction and extrema fixes"
category: design-automation
risk: low
tags:
    - fontforge
    - fonts
    - otf
    - ttf
    - woff2
    - ufo
    - icon-font
    - typography
metadata:
  version: "1.0.0"
---

# FontForge Control

FontForge is driven **headless through its embedded Python** (`fontforge -lang=py
-script`): each task is one short-lived process that opens a font, changes it, and
writes new files. Nothing opens on screen and nothing keeps running. Verified against
**FontForge 20251009** on macOS (the binary lives inside
`FontForge.app/Contents/Resources/opt/local/bin/`, not on PATH).

There is no live bridge: FontForge has no remote-control interface into a running GUI.
Work on files. If the user wants to look at the result, `open -a FontForge out.sfd`.

All helpers run through one entry point, `python3 scripts/ff.py`, which finds the
binary, filters FontForge's banner noise, applies a timeout and turns a Python
traceback into a non-zero exit:

- [scripts/ff.py](scripts/ff.py) — `check` (version, Python, real WOFF2 test),
  `run SCRIPT.py ARGS…` for your own FontForge scripts, `specimen FONT -o x.png --text …`
  to render a PNG, and the four helpers below.
- `ff.py iconfont DIR --family NAME [--map map.json|csv] -o x.sfd -o x.otf -o x.woff2
  [--css x.css]` — [ff_iconfont.py](scripts/ff_iconfont.py): SVG folder → icon font.
  Unmapped icons get PUA code points from U+E000. Every glyph is cleaned and given one
  advance; `--fit center --padding N` normalises icons drawn on inconsistent canvases.
- `ff.py subset FONT -o x.woff2 --text "…" | --text-file page.txt | --unicodes
  U+0020-007E` — [ff_subset.py](scripts/ff_subset.py): keeps exactly those characters
  (+ .notdef, space), unlinks accented composites so nothing renders blank, keeps names
  and kerning between kept glyphs.
- `ff.py validate FONT [--fix -o fixed.sfd -o fixed.otf] [--close-open]` —
  [ff_validate.py](scripts/ff_validate.py): per-glyph problems decoded from the
  validation bitmask, plus non-integer points; `--fix` repairs and re-validates.
- `ff.py inspect FONT [--cmap] [--names] [--glyph H] [--pairs AV,To]` —
  [ff_inspect.py](scripts/ff_inspect.py): JSON read-back of names, metrics, glyph and
  kerning counts, features, validation failures, and the kerning value of given pairs.
- [references/python-api.md](references/python-api.md) — the API calls, generate
  flags, lookups/kerning, selection, and the full validation bitmask table.
- [references/recipes.md](references/recipes.md) — metrics + kerning + names on an
  existing font, SVG letters → glyphs, batch conversion, UFO round trip, composites,
  feature files.
- [references/gotchas.md](references/gotchas.md) — the traps found on this version
  (SVG import bugs, glyph names overriding code points, stale name-table entries,
  additive kerning lookups) and the security posture. **Read it before writing your own
  script.**

## Workflow

1. **Check the install**: `python3 scripts/ff.py check`. Exit 127 means FontForge is
   missing — suggest the app from fontforge.org or `brew install fontforge` (the
   Homebrew *cask* is disabled).
2. **Pick the helper or write a script.** The four helpers cover icon fonts,
   subsetting, validation and read-back. For anything else — metrics, kerning, renaming,
   conversion, glyph surgery — write a small FontForge Python script (start from
   [recipes.md](references/recipes.md)) and run it with `ff.py run`.
3. **Keep a source.** Save SFD (or UFO) next to the binaries; generate OTF/TTF/WOFF2
   from it. A binary font is an output, not something to keep editing.
4. **Never overwrite the input font.** Write to a new path, and tell the user which
   file is which.
5. **Verify before you report done**:
   - `ff.py inspect OUT --cmap --names` — glyph count, code points, family/version.
   - `ff.py inspect OUT --pairs AV,To --glyph H` — kerning and metrics you changed.
   - `ff.py validate OUT` — exit 0 means no problems left.
   - `ff.py specimen OUT -o specimen.png --text "…"` and **look at the PNG**: blank boxes,
     shifted or giant icons, and missing accents show up there and nowhere else.

## Diagnosing blank or missing glyphs

When a character renders as an empty box or loses its accent, check in this order with
`ff.py inspect FONT --cmap --glyph á --glyph a --glyph acute`:
1. **Not encoded** — the character is missing from `cmap` (glyph exists under another
   code point, or an AGL name pulled it elsewhere).
2. **Broken composite** — `references` names a glyph that is not in the font (after a
   subset or a merge); unlink before removing bases, or add the base back.
3. **Empty outline** — `contours: 0` with a non-zero width; an import or a subset left
   the glyph empty.
4. **Outline problems** — `ff.py validate FONT`: open contours and wrong direction can
   render as holes or nothing at all in some rasterizers.
Then render `ff.py specimen` with the failing text to confirm the fix.

## Rules that save a round trip

- **Imported SVG glyphs have width 0** — set `glyph.width` (the iconfont helper does).
- **A glyph name from the Adobe Glyph List beats the code point** (`plus` lands on
  U+002B, not your PUA slot). Check names with `fontforge.unicodeFromName(name)`.
- **Changing names on an existing OTF/TTF**: set the properties *and* the
  `sfnt_names` entries (Version, UniqueID, Family, Fullname, PostScriptName), plus
  `font.sfntRevision` for `head.fontRevision`, or the old version and ID ship. Respect
  the OFL Reserved Font Name when renaming.
- **Changing kerning in a font that already kerns**: put an override subtable *first in
  the existing kern lookup*. A new lookup adds to the old values instead of replacing
  them.
- **Validation fixes run in order** removeOverlap → correctDirection → addExtrema →
  round, and never removeOverlap on an open contour (it mangles the glyph). Report open
  contours rather than silently closing them unless the user agrees.
- **Subsetting**: features whose glyphs were removed are dropped (FontForge warns per
  glyph; the helper counts the warnings). Kerning among the kept glyphs survives. If the
  user needs every layout feature intact on a web subset, mention `pyftsubset`.

## Reporting

Tell the user what was produced (paths, formats, sizes), what changed (glyph count,
code points, names, pairs), and what the verification showed — the inspect numbers,
remaining validation problems (or none), and the specimen. Say plainly what FontForge
dropped (ignored tables, invalidated lookups) and anything left for manual work, such
as open contours.
