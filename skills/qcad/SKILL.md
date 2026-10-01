---
name: qcad
description: 'Draft, edit and convert 2D CAD drawings (DXF, and DWG with QCAD Pro) by running QCAD headless with its ECMAScript API — floor plans, site plans, part outlines, panel and laser-cut layouts with layers, lines, arcs, polylines, text, blocks, linear/aligned dimensions and hatches; add title blocks to existing drawings; batch-convert folders of DXF/DWG to PDF or PNG; read and modify existing DXF files, verified with ezdxf. Use whenever the user wants a 2D technical drawing, a DXF file, a dimensioned plan, a drawing exported to PDF, a title block added, or says "QCAD", "DXF", "2D CAD", "floor plan drawing", "convert DXF to PDF", "dimension this drawing" — even without mentioning QCAD. Hungarian: "készíts 2D rajzot", "alaprajz DXF-ben", "DXF-ből PDF", "tegyél rá szövegmezőt/fejlécet", "méretezd be a rajzot". Not for 3D/parametric parts or STEP/STL (use freecad), CSG solids (brl-cad), PCB layouts (kicad), vector illustration or SVG art (inkscape), or flowcharts and diagrams (drawio).'
summary: "draft 2D CAD drawings headless with QCAD — ECMAScript scripts for layers, entities, blocks, dimensions and hatches, title blocks on existing DXF, batch DXF/DWG to PDF/PNG, ezdxf-verified output"
category: cad
risk: low
tags:
    - qcad
    - cad
    - dxf
    - 2d-drafting
    - scripting
---

# QCAD headless drafting

QCAD is a 2D CAD app whose whole engine is scriptable in ECMAScript
(`RDocument`, entities, operations, importers/exporters). This skill runs it
**headless** — `qcad -no-gui -autostart script.js` — through a wrapper that
preloads a helper library, so a task is: write one JS file, run it, verify
the output files. No GUI, no bridge, nothing to keep running.

```
scripts/qcad-run.sh     run a JS file headless, lib.js preloaded, non-zero exit on script errors
scripts/lib.js          helpers: newDrawing/openDrawing/saveDrawing, layers, entities,
                        dimensions, hatches, blocks, extents, exportPdf/exportImage
scripts/batch-export.js folder of DXF/DWG -> PDF/PNG in one launch
scripts/title-block.js  add a TITLEBLOCK block + insert to existing DXFs (writes *-tb.dxf)
scripts/dxf-inspect.py  ezdxf JSON summary — the independent check of what was written
```

`SK=<this skill's directory>`; run everything from the user's working
directory — relative paths in arguments resolve against it.

## Setup check (once)

```bash
ls -d /Applications/QCAD*.app || brew install --cask qcad      # or set QCAD_BIN
python3 -c 'import ezdxf' 2>/dev/null || { python3 -m venv .venv-dxf && .venv-dxf/bin/pip -q install ezdxf; }
```

Use whichever interpreter has ezdxf (`.venv-dxf/bin/python` if you made one)
for `dxf-inspect.py`.

**Every launch costs a few seconds, plus 15 s when the bundled Pro add-on
runs in trial mode** ("Your script will start in 15 seconds…" — the default macOS
download includes the trial). So put the whole job — all files of a batch,
drawing *and* exporting — into one script and one launch; never loop over
files in the shell calling QCAD each time.

## Drawing from a spec

```js
// plan.js — run: $SK/scripts/qcad-run.sh plan.js out/
var out = ARGS[0];                         // ARGS = extra args; CWD = caller's dir
mkdirs(out);
var c = newDrawing();                      // units: mm (default)
addLayer(c, "WALLS", "white", "CONTINUOUS", RLineweight.Weight050);
addRect(c, v(0, 0), v(10000, 8000));       // closed polyline, opposite corners
addLine(c, v(6000, 0), v(6000, 3550));
addLayer(c, "DIMENSIONS", "cyan");
setDimScale(c, 100);                       // 1:100 plan: text/arrows 250 mm in the model
addDimLinear(c, v(0, 0), v(10000, 0), v(0, -800), 0);       // horizontal
addDimLinear(c, v(10000, 0), v(10000, 8000), v(10800, 0), 90); // vertical
print("EXT " + JSON.stringify(extents(c)));
saveDrawing(c, out + "/plan.dxf");
exportPdf(c, out + "/plan.pdf", { paper: "A3" });            // auto-fit, auto orientation
exportImage(c, out + "/plan.png", { width: 1600 });          // for your own visual check
```

`addLayer` also makes the layer current; each `add*` draws on the current
layer. All helpers return the entity, throw on failure, and take angles in
degrees. Full list with signatures, the raw API underneath, and how to edit
or delete existing entities: [references/api-reference.md](references/api-reference.md).
Worked recipes (walls with thickness and door openings, hatched sections,
blocks with many inserts, modifying an existing DXF):
[references/recipes.md](references/recipes.md).

Pick the dimension scale from the plot scale (1:50 → 50, 1:1 part → 1);
without it, dimension text is 2.5 units — invisible on a plan drawn in mm.

## Batch conversion

```bash
$SK/scripts/qcad-run.sh $SK/scripts/batch-export.js in_dir out_dir pdf [png] [paper=A3] [color] [flat]
```

Recursive, mirrors sub-folders (or `flat`), spaces in names are fine, inputs
are only read. Prints `OK`/`FAIL` per file and `SUMMARY ok=N fail=M`; the
exit status is non-zero if anything failed. PDFs are auto-fitted, black on
white unless `color` (white/ACI-7 lines would vanish on paper otherwise).
DWG inputs need the Pro DWG plugin. SVG output: see the export matrix in
[references/gotchas.md](references/gotchas.md).

## Title blocks on existing drawings

```bash
$SK/scripts/qcad-run.sh $SK/scripts/title-block.js \
  'title=Ground floor plan' scale=1:100 'author=T. Jablonkai' date=2026-10-01 \
  [company=…] [rev=B] a.dxf:number=A-101 b.dxf:number=A-102 \
  [out=DIR] [suffix=-tb] [factor=N] [pdf]  a.dxf b.dxf
```

Shared fields apply to every file; `FILE:key=value` sets one file's value
(drawing numbers, sheet `1/3`…). Adds block `TITLEBLOCK` (frame + labelled
cells) and one insert on layer `TITLE`, right-aligned below the drawing's
lower-right corner, scaled to the drawing (`factor=` overrides). Writes
`<name>-tb.dxf` next to the input, or `out=DIR suffix=` to keep the names in
another folder; never over the input; skips files that already have a
`TITLEBLOCK`.
For a different layout, copy the script and edit its `cells` table.

## Verify — every time

A script that ran is not a drawing that is right. After each run:

1. `qcad-run.sh` exit status 0 and no `FAIL` lines.
2. Re-read the DXF independently:
   `python dxf-inspect.py out/plan.dxf [--texts] [--layer WALLS]` → layers,
   entity counts by type and layer, blocks and their inserts, extents. Check
   them against the spec (e.g. extents 10000 × 8000 + dimension offsets).
3. Look at it: export a PNG (or render the PDF with
   `sips -s format png file.pdf --out page.png`) and Read the image. Overlaps,
   missing dimension text and mis-scaled title blocks only show up here.

Note: QCAD writes text as `MTEXT` and saves DXF 2013 (`AC1027`) by default —
count `TEXT`+`MTEXT` together; `"DXF R12"` drops text entirely. Dimensions
are saved without geometry blocks, so ezdxf-based renderers show none —
check dimensions in the QCAD-exported PNG/PDF, not an ezdxf render.

## Gotchas (the ones that bite first)

- Script errors go to QCAD's log, not an exception in your shell — the
  wrapper turns `ERROR`/`Exception` lines into a non-zero exit; read the
  printed message, it names the file and line.
- Use `print()` for output; the wrapper strips QCAD's debug chatter.
- Work in a fresh drawing or on a copy: `saveDrawing` overwrites its target.
- Prefer `exportPdf`/`exportImage`/`batch-export.js` over the Pro CLI tools
  (`dwg2pdf`, `dwg2svg`, `dwg2bmp`): in trial mode those stamp a red
  "QCAD.org Trial Version" watermark on every page (the skill's export path
  does not), and `dwg2pdf` draws white lines white unless given `-n`.
- More — the CE/Pro/trial matrix, units, DXF versions, fonts, ezdxf as the
  no-QCAD fallback: [references/gotchas.md](references/gotchas.md).

## Hand-off

Report the files written, the checks run (dxf-inspect numbers, the PNG you
looked at), and anything approximated. A DXF opens in QCAD, LibreCAD,
AutoCAD, FreeCAD and most laser/CNC tools; mention units (mm unless set).
