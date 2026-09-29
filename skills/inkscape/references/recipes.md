# Recipes

Paths are relative to the skill directory. `I=scripts/inkscape.sh`, called as
`bash "$I" …`. All recipes were run on Inkscape 1.4.4.

## Badge or logo from a written spec → 1x/2x PNG + PDF

1. Turn the spec into numbers first: canvas size, centre, radii, colours, font size.
   Put every value you will verify into an attribute with an `id`.
2. Write the SVG (see *SVG rules* in SKILL.md): one layer per role (background, art,
   text), gradients in `<defs>`, and styles in `style=""`.

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="256" height="256" viewBox="0 0 256 256">
  <defs>
    <radialGradient id="glow" cx="0.5" cy="0.35" r="0.7">
      <stop offset="0" stop-color="#ffd54f"/><stop offset="1" stop-color="#f57f17"/>
    </radialGradient>
  </defs>
  <g id="layer-base" inkscape:groupmode="layer" inkscape:label="Base">
    <circle id="ring" cx="128" cy="128" r="124" style="fill:#3e2723"/>
    <circle id="disc" cx="128" cy="128" r="108" style="fill:url(#glow)"/>
  </g>
  <g id="layer-mark" inkscape:groupmode="layer" inkscape:label="Mark">
    <path id="star" style="fill:#ffffff"
          d="M128 52 L146 104 L200 104 L156 136 L172 188 L128 156 L84 188 L100 136 L56 104 L110 104 Z"/>
    <text id="label" x="128" y="228" text-anchor="middle"
          style="font-family:Helvetica, Arial, sans-serif;font-size:22px;font-weight:bold;fill:#ffffff">GOLD</text>
  </g>
</svg>
```

3. Export and verify:

```bash
bash scripts/ink-export.sh badge.svg badge.png badge@2x.png badge.pdf --text-to-path
python3 scripts/ink-verify.py badge.svg badge.pdf
python3 scripts/ink-verify.py badge.png --png-size 256x256
python3 scripts/ink-verify.py badge@2x.png --png-size 512x512
```

4. Open `badge@2x.png` with the Read tool. Check that the text fits inside the ring,
   the gradient shows, and the z-order is right.

`--text-to-path` puts outlines in the PDF only; the source SVG keeps live, editable
text.

## Icon set at several sizes

The same SVG at 16, 32, 64, 128, 256 and 512 px. A 256-unit viewBox at 96 DPI is
256 px, so set pixel width directly:

```bash
for s in 16 32 64 128 256 512; do
  bash "$I" icon.svg --export-width="$s" -o "icons/icon-$s.png"
done
python3 scripts/ink-verify.py icons/*.png
```

At 16–32 px, thin strokes blur. If the user cares about small sizes, make a separate
simplified SVG for them.

## Batch-convert a folder at 300 DPI

```bash
bash scripts/ink-batch.sh --out out/png --dpi 300 art/          # every art/*.svg
bash scripts/ink-batch.sh --out out/pdf --type pdf art/a.svg art/b.svg
python3 scripts/ink-verify.py out/png/*.png
```

Expected width = document width in inches × 300. A `width="2in"` file gives 600 px;
a `width="192"` (px) file gives 192/96 × 300 = 600 px. The script runs one Inkscape
process for the whole list and exits 1 if any file failed to write.

## Export each layer or object separately

```bash
bash "$I" --query-all art.svg | cut -d, -f1              # list the ids
bash scripts/ink-export.sh art.svg parts/bg.png   --id layer-bg
bash scripts/ink-export.sh art.svg parts/mark.png --id layer-mark --dpi 192
```

`--id` crops to that object's bounding box and hides everything else. Add
`--area page` to keep the full page with only that object visible.

## Trace a raster image

```bash
# Flat logo with 3 ink colours on white: 4 scans including the background
bash scripts/ink-trace.sh logo.png logo.svg --flat --scans 4
bash scripts/ink-export.sh logo.svg logo-preview.png --background '#ffffff'
python3 scripts/ink-verify.py logo.svg logo-preview.png   # path_coord_pairs = node count
magick compare -metric RMSE logo-preview.png logo.png null:   # if ImageMagick exists
```

Measured on a 600×400 three-colour logo (Inkscape 1.4.4):

| Options | RMSE | Coordinate pairs |
|---------|------|------------------|
| `--scans 4` (defaults) | 3.8% | 1054 |
| `--scans 4 --simplify` | 4.5% | 501 |
| `--flat --scans 4` | **1.3%** | **345** |
| `--flat --scans 4 --simplify` | 2.6% | 270 |
| `--flat --scans 8` | 4.8% | 2836 (extra anti-aliasing layers) |

- **Too many scans** turn anti-aliased edges into thin outline layers. **Too few**
  merge two colours. Count the distinct colours, include the background, and check
  the result's fills (`grep -o 'fill:#[0-9a-f]*' logo.svg`).
- **Default (smoothed, stacked) mode** blurs before quantizing. That rounds letter
  corners and leaves a halo of one colour around another. Use it for photos and noisy
  scans, not for flat art.
- **Exact brand colours**: traced fills come out a step or two off (for example
  `#1a5d1f` for `#1b5e20`). If the user gives the colours, or ImageMagick can read
  them (`magick logo.png -format %c histogram:info:`), replace the fills in the SVG.
- **Photos**: `--scans 8`–`16 --speckles 4 --simplify`. Expect a posterized result,
  not a faithful photo.
- **Two-tone line art**: `--flat --scans 2`.
- `--keep-background` keeps the background colour as a full-size shape.

## Boolean shapes (cut-outs, merged outlines)

```bash
# Punch the star out of the disc: bottom minus top, the result keeps the disc's style
bash "$I" badge.svg --actions="select-by-id:disc,star;path-difference;export-plain-svg;export-filename:cut.svg;export-do"
# Merge overlapping shapes into one outline
bash "$I" parts.svg --actions="select-by-element:circle;path-union;export-plain-svg;export-filename:merged.svg;export-do"
```

The z-order decides "bottom" and "top", not the order of IDs in `select-by-id`.

## Hand-off SVG (no fonts, no editor metadata)

```bash
bash "$I" art.svg --actions="select-by-element:text;object-to-path;export-plain-svg;export-filename:art-final.svg;export-do"
python3 scripts/ink-verify.py art-final.svg     # counts.text should be 0
```

## Multi-page document (1.2+)

Add pages inside a `sodipodi:namedview`
(`xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"`):

```xml
<sodipodi:namedview>
  <inkscape:page id="p1" x="0"   y="0" width="100" height="100"/>
  <inkscape:page id="p2" x="120" y="0" width="100" height="100"/>
</sodipodi:namedview>
```

Place each page's artwork inside its rectangle. `ink-export.sh doc.svg doc.pdf` writes
every page (`ink-verify.py` reports `pages: 2`). For PNGs, run
`bash "$I" doc.svg --export-page=2 -o p2.png`.
