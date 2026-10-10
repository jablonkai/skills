# Recipes

Each recipe is a FontForge Python script; run it with `ff.py run recipe.py ARGS…`.
The bundled helpers (`ff.py iconfont|subset|validate|inspect`) already cover the
icon-font, subset and validate cases end to end — reach for these recipes when the
task needs something the helpers don't do.

## Contents
- [Metrics, kerning and names on an existing font](#metrics-kerning-and-names-on-an-existing-font)
- [Glyphs from SVG letters](#glyphs-from-svg-letters)
- [Batch convert a folder](#batch-convert-a-folder)
- [UFO round trip](#ufo-round-trip)
- [Composite (accented) glyphs](#composite-accented-glyphs)
- [Feature file in, feature file out](#feature-file-in-feature-file-out)

## Metrics, kerning and names on an existing font

```python
import fontforge, sys
src, out = sys.argv[1], sys.argv[2]
f = fontforge.open(src)

# --- names: set the properties AND the explicit name-table entries -----------------
family, style, version = "Kestrel Serif", "Regular", "1.200"
ps = family.replace(" ", "") + "-" + style
f.familyname, f.fullname, f.fontname = family, f"{family} {style}", ps
f.version = version                 # the version *string*
f.sfntRevision = float(version)     # head.fontRevision — not touched by f.version
for strid, value in (("Family", family), ("SubFamily", style),
                     ("Fullname", f"{family} {style}"), ("PostScriptName", ps),
                     ("Version", f"Version {version}"),
                     ("UniqueID", f"{version};{ps}"),
                     ("Preferred Family", family), ("Preferred Styles", style)):
    f.appendSFNTName("English (US)", strid, value)

# --- side bearings ------------------------------------------------------------------
for name, (lsb, rsb) in {"H": (90, 90), "O": (60, 60)}.items():
    g = f[name]
    g.left_side_bearing = lsb      # moves the outline
    g.right_side_bearing = rsb     # changes the advance width

# --- kerning pairs: override subtable FIRST in the existing kern lookup ------------
def kern_lookup(font):
    for lk in font.gpos_lookups:
        kind, _, feats = font.getLookupInfo(lk)
        if kind == "gpos_pair" and any(ft[0] == "kern" for ft in feats):
            return lk
    font.addLookup("kern", "gpos_pair", None,
                   (("kern", (("latn", ("dflt",)), ("DFLT", ("dflt",)))),))
    return "kern"

lk = kern_lookup(f)
f.addLookupSubtable(lk, "pair-overrides")         # no `after` → first → wins
for pair, value in {"AV": -120, "To": -100, "Ty": -80, "LT": -140}.items():
    left, right = f[ord(pair[0])], f[ord(pair[1])]
    left.addPosSub("pair-overrides", right.glyphname, 0, 0, value, 0, 0, 0, 0, 0)

f.generate(out, flags=("opentype",))
```

Verify: `ff.py inspect OUT --pairs AV,To,Ty,LT --glyph H --names`. The `pairs`
values must equal the requested numbers; if they come out as old + new, the pairs went
into a second lookup instead of the existing one.

Renaming an OFL font: if its licence declares a Reserved Font Name (Lato, Source, Noto…
— see the copyright string or OFL.txt), a modified version must not use that name.

## Glyphs from SVG letters

```python
import fontforge, os, sys
f = fontforge.open(sys.argv[1]) if sys.argv[1].endswith((".sfd", ".ufo", ".otf", ".ttf")) else fontforge.font()
svg_dir = sys.argv[2]                          # A.svg, B.svg, … or uni0041.svg
for fn in sorted(os.listdir(svg_dir)):
    stem, ext = os.path.splitext(fn)
    if ext.lower() != ".svg":
        continue
    cp = ord(stem) if len(stem) == 1 else fontforge.unicodeFromName(stem)
    g = f.createChar(cp, fontforge.nameFromUnicode(cp)) if cp >= 0 else f.createChar(-1, stem)
    g.clear()
    g.importOutlines(os.path.join(svg_dir, fn), correctdir=True)
    g.removeOverlap(); g.addExtrema(); g.round()
    g.left_side_bearing = 60; g.right_side_bearing = 60   # import leaves width 0
f.save(sys.argv[3])
```
Draw letters on a viewBox whose height equals the font's em (baseline at
`ascent` from the top) and they land at the right size; otherwise scale afterwards with
`g.transform(psMat.scale(k))`.

## Batch convert a folder

```python
import fontforge, glob, os, sys
src_dir, out_dir, ext = sys.argv[1], sys.argv[2], sys.argv[3]   # ext: woff2, otf, ttf, ufo
os.makedirs(out_dir, exist_ok=True)
for path in sorted(glob.glob(os.path.join(src_dir, "*"))):
    if not path.lower().endswith((".sfd", ".otf", ".ttf", ".woff", ".woff2", ".ufo")):
        continue
    f = fontforge.open(path)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(path))[0] + "." + ext)
    f.generate(out, flags=("opentype",))
    print(out, os.path.getsize(out))
    f.close()
```

## UFO round trip

```python
f = fontforge.open("Font.sfd"); f.generate("Font.ufo")    # UFO 3 directory
f = fontforge.open("Font.ufo"); f.save("Font.sfd")
```
Kerning and groups travel in `kerning.plist`/`groups.plist`; OpenType features other
than kerning go to `features.fea`. Hinting and FontForge-only data do not survive.

## Composite (accented) glyphs

```python
g = f.createChar(0xE1, "aacute")
g.clear(); g.addReference("a"); g.appendAccent("acute")   # positions via anchors if present
g.width = f["a"].width
# or the built-in composer: f.selection.select("aacute"); f.build()
```

## Feature file in, feature file out

```python
f.generateFeatureFile("dump.fea")       # every GSUB/GPOS lookup as AFDKO feature syntax
f.mergeFeature("extra.fea")             # add lookups from a .fea file
```
Use a `.fea` file when the user hands over kerning or ligatures as text, or wants them
reviewed in a diff.
