# QCAD gotchas

Observed on QCAD 3.33.1 (Qt 6, macOS), Pro add-on in trial mode.

## Editions, trial and what needs Pro

| Capability | Community (GPL) | Pro add-on |
|---|---|---|
| ECMAScript API, `-no-gui -autostart` | yes | yes |
| DXF read/write (R12 … 2013) | yes | yes |
| PDF via `exportPdf` (QCAD print engine) | yes | yes |
| PNG/JPG via `exportImage` | yes | yes |
| DWG read/write | no | yes (`libqcaddwg`) |
| SVG export | no (no `File/SvgExport`) | `dwg2svg` |
| CLI tools `dwg2pdf`, `dwg2svg`, `dwg2bmp`, `dwginfo`, `dwg2csv` … | no | `QCAD.app/Contents/Resources/` |

- The qcad.org macOS download (and the Homebrew cask) bundles the Pro add-on
  as a **trial**: every launch prints "You are using a trial version of QCAD
  Professional … Your script will start in 15 seconds" and waits. A run costs
  about 18 s even for a one-line script. That is why batch jobs belong in one
  script: `batch-export.js` converts a whole folder in a single launch.
- Community-only installs (no Pro plugins) start without the wait; DWG input
  then fails with an import error — convert to DXF elsewhere (ODA File
  Converter) or ask for DXF.
- SVG without Pro: export the PDF with `exportPdf`, then
  `pdftocairo -svg plan.pdf plan.svg` (poppler) — vector, dimensions
  included. The ezdxf SVG backend (`ezdxf.addons.drawing.svg.SVGBackend`)
  also works but drops QCAD's dimensions (see "Dimensions in other tools").
- The Pro CLI tools in **trial** mode stamp a red "QCAD.org Trial Version"
  watermark on every output page/image — not usable as deliverables. The
  skill's `exportPdf`/`exportImage` go through the Community print and
  bitmap code and carry no watermark, even with the trial installed.
- `dwg2pdf` (Pro) keeps entity colours: white/ACI-7 lines become white on
  white paper. Pass `-n` (monochrome) or `-color-correction`, and `-a`
  (auto-fit), `-f` (overwrite), `-o out.pdf` or `-outfile=out.pdf` (`-o=out.pdf` is ignored). Our `exportPdf` defaults to
  black-on-white.

## Running headless

- QCAD runs from `QCAD.app/Contents/Resources`; `include("scripts/…")`
  depends on it. Your paths go through `resolve()` (lib.js does it in every
  file helper), so relative paths mean the caller's directory.
- One QCAD instance per launch: `-allow-multiple-instances` lets runs overlap
  with a GUI QCAD the user has open — they do not touch its documents.
- Script errors do not crash QCAD — they print `Warning: include exception:
  "TypeError: …"` plus a `%entry:LINE` trace and QCAD exits normally.
  `qcad-run.sh` greps for that and exits 1; the line number refers to your
  script (the first trace line) or lib.js.
- Harmless noise: `QImage::scaled: Image is a null image`,
  `RGraphicsViewImage::paintOverlay: no workers`, `Unimplemented code`,
  `Drawing units ($INSUNITS) are not exported for DXF R12`.
- A wedged run (dialog waiting for input — happens when a GUI-only action is
  triggered) is killed by `--timeout` (default 600 s).
- Don't call GUI actions (`EAction`, `RMainWindowQt.getMainWindow()`, the
  "simple" API's `getDocument()`): there is no main window in `-no-gui`. Use
  the `ctx` from `newDrawing`/`openDrawing`.

## Script-language quirks

- QtScript is ES5: `var`, `function`; no `let`/`const`, arrow functions,
  template strings, `Array.prototype.includes`. `JSON`, `forEach`, `map`,
  `filter` are fine.
- Qt flag arguments need the library wrappers (`makeQDirFilters`,
  `makeQDirSortFlags`, `makeQIODeviceOpenMode`) — `new QDir.Filters(…)`
  throws `TypeError: Type error`.
- `RDocumentInterface.destroy()` is not exposed. Let documents go out of
  scope.
- `e.constructor.name` is `"Object"` for every entity — use `entityType(e)`.
- Raw API angles are radians; lib.js helpers take degrees.

## Geometry, units, styles

- New drawings are mm. DXF from other tools may carry `$INSUNITS` = metres
  (ezdxf's default for `ezdxf.new()`!) or none; `ctx.doc.getUnit()` tells you
  what QCAD read. A "120 m bracket" usually means wrong units, not a wrong
  drawing.
- Dimension size: 2.5 units default — use `setDimScale` (per-entity DIMSCALE).
  Setting `RS.DIMTXT`/`DIMASZ` document variables headless has no effect.
- `RDimRotatedData`: set the rotation **before** the definition point.
- Dimensions in other tools: QCAD writes DIMENSION entities **without** the
  anonymous `*D` geometry blocks. QCAD itself (and full CAD apps that
  recompute dimensions) draws them; block-only consumers (ezdxf's renderer,
  some laser/CNC importers) show nothing. When the recipient is such a tool,
  send the PDF alongside the DXF.
- `doc.getBoundingBox(true, true)` includes dimensions and text — extents of
  a dimensioned plan are larger than the walls. For "is the building
  10 × 8 m" check one layer (`dxf-inspect.py --layer WALLS`).
- Hatch pattern scale is in drawing units: a 1:100 plan in mm needs scale
  20–100 or the pattern is a solid grey blur; check the PNG.
- Text: QCAD saves its text as MTEXT. `DXF R12` has no MTEXT and the text is
  silently dropped — use 2000 or later unless the recipient insists on R12
  (then use ezdxf to write TEXT entities).
- Layer colour "white" is ACI 7 — displayed black on white paper by most
  viewers and by our monochrome PDF.
- `saveDrawing` overwrites without asking. Write to a new name (the scripts
  use `-tb`/an output folder) and never over the input.

## ezdxf as the fallback

When QCAD is missing or a change is pure data editing (rename layers, swap
text, count entities), ezdxf alone is often enough:

```python
import ezdxf
doc = ezdxf.readfile("in.dxf"); msp = doc.modelspace()
for t in msp.query("TEXT"):
    t.dxf.text = t.dxf.text.replace("REV A", "REV B")
for t in msp.query("MTEXT"):
    t.text = t.text.replace("REV A", "REV B")
doc.layers.get("WALLS").color = 7
doc.saveas("out.dxf")
```

ezdxf cannot plot a faithful PDF the way QCAD does (its drawing add-on is a
preview renderer: no line weights per plot style, approximated fonts), so
use QCAD for deliverable PDFs and ezdxf for checks and data edits.
