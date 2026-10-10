# Gotchas

Each item was hit on FontForge 20251009 (macOS app) unless marked otherwise.

## Running FontForge

- **The binary is not on PATH** with the macOS app: it is
  `FontForge.app/Contents/Resources/opt/local/bin/fontforge`. `ff.py` finds it; set
  `$FONTFORGE` for an unusual install. The Homebrew `fontforge-app` cask is disabled
  (fails Gatekeeper); `brew install fontforge` (the formula) still works.
- **Banner noise on stderr** every run (copyright, version, `Core python package
  'pkg_resources' not found`, `Compressed N to M` from WOFF2). Harmless; `ff.py` filters it.
- An uncaught Python exception exits 1 with a traceback; `ff.py` also maps a printed
  traceback with exit 0 to exit 2. FontForge-level errors (bad SVG, unknown flag) often
  only print a message — check that the output files exist, not just the exit code.
- `fontimage`, `fontlint` and `sfddiff` ship as FontForge-script files with a shebang
  pointing at the CI build machine, so they fail with "bad interpreter". Run them through
  the binary: `fontforge -lang=ff -script …/fontimage …` (`ff.py specimen` does this).
- `FFPython` (in `Contents/MacOS`) imports `fontforge` too, but warns about platform
  libraries; prefer `ff.py run`.
- Opening an OTF/TTF prints `The following table(s) in the font have been ignored by
  FontForge` (DSIG, STAT, …). Those tables are dropped from anything you generate —
  say so if the user relies on them. FontForge does not write OpenType variable fonts;
  use a static instance as input.

## SVG import

- **Imported glyphs have width 0.** Set `glyph.width` (or the side bearings) after
  `importOutlines`, or every glyph overlaps the next.
- The SVG viewBox height is scaled onto ascent+descent with the top at the ascent.
  Draw on that grid and positions carry over exactly.
- **A non-zero viewBox origin is ignored** (`viewBox="-12 -12 24 24"` lands off the em
  box). `ff_iconfont.py` shifts the content; in your own scripts, normalise the SVG first.
- **`rotate(a cx cy)` is applied about the wrong point.** Rewrite it as
  `translate(cx cy) rotate(a) translate(-cx -cy)` (the helper does) or flatten transforms
  in Inkscape before import.
- Strokes are expanded to outlines on import (a 2-unit stroke becomes a filled band), so
  stroked icon sets work. Very thin results usually mean a hairline stroke in the source.
- Text, `<image>` and `<use>` elements are not outlines — convert text to paths first
  (Inkscape: Path → Object to Path).

## Glyph names and encoding

- **An Adobe Glyph List name overrides the code point** passed to `createChar`:
  `createChar(0xE004, "plus")` lands on U+002B. FontForge warns ("its name indicates it
  should be mapped to …"). Use names that `fontforge.unicodeFromName()` maps to `-1`
  (the helper appends `.icon`) or `uniXXXX`-style names.
- TrueType output adds `.null` and `nonmarkingreturn` (U+000D) glyphs; that is normal.

## Names and licences

- Fonts opened from OTF/TTF carry explicit `sfnt_names` entries, and **those win over the
  properties**: setting `font.version` leaves nameID 5 at the old version, and nameID 3
  (UniqueID) keeps the old PostScript name. Update both the properties and the entries
  with `appendSFNTName` (recipe in `recipes.md`).
- `font.version` is only the version string; `head.fontRevision` comes from
  `font.sfntRevision` (a float) and keeps the old number unless you set it too.
- OFL fonts may declare a **Reserved Font Name** (e.g. Lato, Source, Noto). A modified or
  subset version distributed under a new name must not use it; a pure subset for your own
  website is fine under OFL. Keep the copyright and licence entries.

## Outlines and validation

- `removeOverlap()` on a glyph with **open contours** mangles it — close or skip those
  first (the validate helper skips them unless `--close-open`).
- An open contour left in the SFD is **closed implicitly** when an OTF/TTF is generated
  (straight segment back to the start), often in the wrong direction. Tell the user the
  binary already differs from the source for that glyph.
- Glyphs with references: unlink before `removeOverlap`/`correctDirection` when the
  problem is in the composite (flipped references, overlap between components).
- `addExtrema()` inserts fractional points; `round()` afterwards.
- `glyph.validate()` flags non-integer coordinates only for TrueType (quadratic) fonts;
  CFF output is rounded on generate anyway, but the SFD keeps fractions.
  `ff_validate.py` checks coordinates directly.
- Direction convention: `correctDirection()` uses PostScript direction (outer clockwise);
  keep sources that way and let `generate()` handle TrueType output.

## Subsetting

- FontForge drops every GSUB/GPOS subtable that still names a removed glyph and warns
  once per glyph ("Lookup subtable contains unused glyph … making the whole subtable
  invalid"). Kerning between kept glyphs survives (checked with HarfBuzz); features whose
  output glyphs were removed (small caps, superiors, old-style figures) are gone.
  `ff_subset.py` counts these warnings instead of printing them.
- Class-kerning subtables keep every class of the full font after glyphs are removed.
  Shapers cope, but FontForge then mis-reads its own output (`Nonsensical class assigned
  to a glyph`) and reports the kerning as 0. `ff_subset.py` prunes the empty classes with
  `alterKerningClass` before generating, which also makes the file smaller; do the same
  in your own subsetting scripts.
- When the job is *only* web subsetting and layout features must survive intact,
  `pyftsubset` (fontTools) is the better tool; offer it if fontTools is available.

## Kerning

- Separate pair-positioning lookups **add up**; inside one lookup the first subtable with
  the pair wins. To set a pair to a value in a font that already kerns, add an override
  subtable at the start of the existing kern lookup. Verify with
  `ff.py inspect FONT --pairs AV,To`.
- `addKerningClass` wants `len(first) × len(second)` offsets, and second-class 0 ("all
  others") must be passed as `None`.

## Security posture

- Scripts run arbitrary Python inside FontForge with the user's permissions; read any
  script handed over before running it.
- Font and SFD/UFO files are untrusted input to a C parser; open fonts from unknown
  sources in a disposable directory.
- The helpers write only to the paths passed with `-o`/`--css` and never overwrite the
  input font. There is no server, socket or background process: each run is a single
  timeout-guarded process (`FF_TIMEOUT`, default 300 s).
