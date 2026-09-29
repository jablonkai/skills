---
name: inkscape
description: 'Automate Inkscape (open-source vector editor) headless via its CLI — author SVG illustrations directly (shapes, text, gradients, layers, pages), transform them with Inkscape actions (text to path, boolean path ops, simplify, bitmap trace), and export PNG at any DPI or @2x, PDF, EPS and plain SVG, one file or a folder. Use whenever the user wants a vector logo, badge, icon or illustration built from a description, SVGs converted or batch-converted to PNG/PDF/EPS, a raster image traced (vectorized) to SVG, text outlined for print, objects or layers exported by ID, or mentions Inkscape, .svg files, "vectorize this", "SVG to PNG at 300 DPI". Also covers Hungarian: "csinálj egy logót SVG-ben", "vektorizáld ezt a képet", "exportáld PNG-be 300 DPI-vel", "alakítsd görbévé a szöveget". Not for diagrams, flowcharts or architecture drawings (use drawio), raster photo editing or painting (use gimp or krita), Affinity documents (use affinity), charts of numeric data (use a plotting library), or CAD parts (use freecad).'
summary: "drive Inkscape headless from the CLI — author SVG illustrations directly, run actions such as text to path, boolean path ops, simplify and bitmap trace, then export PNG at any DPI or @2x, PDF, EPS and plain SVG, one file or whole folders"
category: design-automation
risk: low
tags:
    - inkscape
    - svg
    - vector
    - export
    - trace
---

# Inkscape Control

Inkscape 1.x is driven **headless through its command line**: write or patch the SVG
as text, run Inkscape *actions* on it (`--actions="select-by-id:a,b;path-union;…"`),
and export. Nothing opens on the user's screen and nothing is left running. Verified
against **Inkscape 1.4.4** on macOS
(`/Applications/Inkscape.app/Contents/MacOS/inkscape`).

There is no live bridge: Inkscape on macOS exposes no scripting server (its D-Bus
interface is Linux-only), so a session the user has open cannot be controlled. Work on
files. If the user has the file open in Inkscape, tell them to reload it (File ▸
Revert) after you change it, and never write over a file they have unsaved changes in.

- [scripts/inkscape.sh](scripts/inkscape.sh) — finds the binary and checks it is 1.x
  (`--check`). `--actions-grep RE` searches `--action-list`. Any other arguments pass
  through to Inkscape.
- [scripts/ink-export.sh](scripts/ink-export.sh) — one SVG → several outputs in one
  run. The extension picks the format, and `name@2x.png` doubles the DPI. Options:
  `--dpi`, `--id`, `--area page|drawing`, `--margin`, `--background`,
  `--text-to-path`.
- [scripts/ink-batch.sh](scripts/ink-batch.sh) — a folder or list of SVGs → PNG, PDF,
  EPS, PS or SVG, all in one Inkscape process (`--shell`).
- [scripts/ink-trace.sh](scripts/ink-trace.sh) — a bitmap → a traced SVG of filled
  paths, with the source image removed and `--simplify` optional.
- [scripts/ink-verify.py](scripts/ink-verify.py) — no Inkscape needed. Checks that
  SVG is well-formed and counts its elements, layers and path nodes; reads PNG pixel
  size (`--png-size WxH` asserts it), PDF page and font count (0 fonts = text is
  outlined) and EPS bounding box.
- [references/actions.md](references/actions.md) — the actions, with the argument
  formats verified on 1.4, and CLI export flags.
- [references/recipes.md](references/recipes.md) — complete worked examples: a badge
  from a spec, icon sets, batch export, tracing, booleans, exporting layers.
- [references/gotchas.md](references/gotchas.md) — selection state, silent failures,
  units and DPI, fonts, version differences. **Read it before the first action chain.**

## Workflow

1. **Check the install**: `bash scripts/inkscape.sh --check`. Exit 2 means it is
   missing or pre-1.0. Suggest `brew install --cask inkscape`; 0.92 syntax
   (`-e`, `--verb`) does not work here.
2. **Author or patch the SVG as text.** For new artwork this is faster and more
   precise than actions. Follow the SVG rules below, then check it is well-formed:
   `python3 scripts/ink-verify.py art.svg`.
3. **Transform with actions** only for what plain SVG cannot express: text to
   outlines, boolean path operations, simplify, trace, stroke to path. **Never guess
   an action name**, because they changed between 1.0, 1.2 and 1.4:
   `bash scripts/inkscape.sh --actions-grep 'path-(union|difference)'`. Chain
   actions, save with `export-plain-svg;export-filename:out.svg;export-do` or with
   `export-overwrite;export-do` (see [actions.md](references/actions.md)).
4. **Export**: `bash scripts/ink-export.sh art.svg art.png art@2x.png art.pdf`.
   For folders: `bash scripts/ink-batch.sh --out png/ --dpi 300 svgs/`.
5. **Verify**, then **look**:
   `python3 scripts/ink-verify.py art.png art@2x.png art.pdf --png-size 256x256`
   (the size assertion applies to every PNG in the call, so check each scale
   separately). Then open the PNG with the Read tool. Overflowing text, a wrong
   z-order and gradients missing from the render only show up visually.

Inkscape **exits 0 even when an action fails** (unknown ID, a boolean with nothing
selected, bad arguments). The scripts catch this. With raw `inkscape` calls, read
stderr and check that the output exists.

## SVG rules for files Inkscape will open

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="256" height="256" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="bg-grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1e88e5"/><stop offset="1" stop-color="#0d47a1"/>
    </linearGradient>
  </defs>
  <g id="layer-bg" inkscape:groupmode="layer" inkscape:label="Background">
    <circle id="disc" cx="128" cy="128" r="120" style="fill:url(#bg-grad)"/>
  </g>
  <g id="layer-text" inkscape:groupmode="layer" inkscape:label="Text">
    <text id="label" x="128" y="140" text-anchor="middle"
          style="font-family:Helvetica, Arial, sans-serif;font-size:40px;font-weight:bold;fill:#ffffff">ACME</text>
  </g>
</svg>
```

- **Size**: set `width`/`height` in px (or `in`/`mm` for print) and a matching
  `viewBox`. At 96 DPI, one user unit is one pixel when width = viewBox width. That is
  how `name@2x.png` gives exactly twice the pixels.
- **Style in `style=""`, not presentation attributes.** Path operations (union,
  difference, …) keep the bottom object's `id` and `style` but **drop** attributes like
  `fill="red"`, so the result renders black. `style="fill:#ff0000"` survives.
- **IDs**: give every object you will select, export or verify a readable `id`.
  Actions and `--export-id` address objects by ID only.
- **Layers** are `<g inkscape:groupmode="layer" inkscape:label="…">`. Export one with
  `--id layer-bg`. Plain-SVG export removes the `inkscape:` attributes, so keep the
  Inkscape SVG as the source and treat plain SVG as a deliverable.
- **Text**: list fallback fonts, and `text-anchor="middle"` to centre. A font missing
  at render time is silently substituted. For print or hand-off, outline the text:
  `--text-to-path` on export, or the `object-to-path` action on the `<text>`.
- **Pages** (1.2+): `<inkscape:page>` elements in `<sodipodi:namedview>` give a
  multi-page document. PDF export includes every page; PNG export writes page 1
  unless you pass `--export-page=N` to Inkscape.

## Common chains

```bash
I=scripts/inkscape.sh   # call as `bash "$I" …` — zsh does not word-split "bash $I"
# Boolean union: the result takes the bottom object's id and style; save as a new file
bash "$I" in.svg --actions="select-by-id:a,b;path-union;export-plain-svg;export-filename:out.svg;export-do"
# Outline all text, write back into the same file
bash "$I" in.svg --actions="select-by-element:text;object-to-path;export-overwrite;export-do"
# Where is an object? id,x,y,w,h in user units — use it to check layout
bash "$I" --query-all in.svg
```

Tracing uses Inkscape's multi-colour Potrace, and the right settings depend on the
source:

- **Logos, icons, flat art**:
  `bash scripts/ink-trace.sh logo.png logo.svg --flat --scans N`, where N = the
  number of colours including the background.
  - `--flat` turns off pre-smoothing and stacking and keeps corners sharp.
  - On a 3-colour logo it measured 1.3% pixel error with 345 nodes. The defaults
    gave 3.8% error and 1054 nodes, with halos and rounded letters.
  - It is already light. `--simplify` on top of it cost accuracy (2.6% error), so
    use it only when the user wants fewer nodes more than fidelity.
- **Photos, scans, noisy sources**: the defaults (smoothing on), 8+ scans,
  `--speckles 4` or more, and `--simplify`.

Always render the result and compare it with the source by eye, and with
`magick compare -metric RMSE` when ImageMagick is installed.

## Python extensions (`inkex`)

Inkscape ships `inkex` extensions (Extensions menu) under
`Inkscape.app/Contents/Resources/share/inkscape/extensions/`. They appear in
`--action-list` as `org.inkscape.*`. They need Inkscape's bundled Python, which some
installs cannot start. When it doesn't start, extensions do nothing and report no
error. `inkscape.sh --check` prints `extensions: available` or `UNAVAILABLE`. Prefer
actions and direct SVG edits either way, and after any extension, check that the
output actually changed.

## Safety

- Everything writes local files. Write new files by default. Overwrite a source only
  when the user asked (`export-overwrite`), because Inkscape rewrites the entire file
  and drops formatting and comments.
- Don't open or edit a file that is open with unsaved changes in the user's Inkscape
  window. A later save from the app would overwrite your work, or yours theirs.
- Traced output from photos or logos the user doesn't own is their licensing call.
  Mention it when the source is clearly third-party artwork.
