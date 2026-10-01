# QCAD scripting reference (QCAD 3.33)

Everything here was exercised headless (`-no-gui`) on QCAD 3.33.1. Upstream
class reference: <https://www.qcad.org/doc/qcad/latest/developer/> (the C++
classes map 1:1 to the script names).

## Contents
- [Run model](#run-model)
- [lib.js helpers](#libjs-helpers)
- [Raw API: documents and operations](#raw-api-documents-and-operations)
- [Entity classes](#entity-classes)
- [Querying](#querying)
- [Modifying and deleting](#modifying-and-deleting)
- [Layers](#layers)
- [Blocks](#blocks)
- [Dimensions](#dimensions)
- [Hatches](#hatches)
- [Text](#text)
- [Import, export, printing](#import-export-printing)
- [Qt from script](#qt-from-script)

## Run model

`qcad-run.sh script.js args…` writes a bootstrap that defines `SKILL_DIR`,
`CWD` (caller's directory) and `ARGS`, includes `lib.js`, then your script, and
launches `QCAD.app/Contents/Resources/qcad -no-gui -no-dock-icon
-allow-multiple-instances -autostart boot.js args…`. QCAD's own `args` array
is `[boot.js, …your args]`. The working directory is QCAD's `Resources`, which
is why `include("scripts/…")` paths resolve — and why your own file paths go
through `resolve()`.

`--timeout S` (default 600) kills a hung run; `--keep-log FILE` keeps the raw
log. Exit 1 on `ERROR …`, `Exception:` or `include exception` in the log.

## lib.js helpers

| Helper | Notes |
|---|---|
| `v(x, y)` | `new RVector(x, y)` |
| `resolve(path)` | absolute path against `CWD`; `~` expands |
| `newDrawing([unit])` | `{doc, di, scene, view}`; unit `RS.Millimeter` (default), `RS.Meter`, `RS.Inch`, `RS.Foot`, `RS.Centimeter` |
| `openDrawing(path)` | imports DXF (DWG with Pro); throws on failure |
| `saveDrawing(c, path, [version])` | `"DXF 2013"` default; `"DXF 2000"`, `"DXF R12"`, `"DWG 2013"` (Pro) |
| `addLayer(c, name, [color], [linetype], [lineweight])` | creates/updates and makes current; color names or `#rrggbb`; linetypes `CONTINUOUS`, `DASHED`, `CENTER`, `HIDDEN`, `DOT`, … |
| `setLayer(c, name)` | make an existing layer current |
| `addLine(c, p1, p2)` | |
| `addCircle(c, center, r)` | |
| `addArc(c, center, r, startDeg, endDeg)` | counter-clockwise |
| `addPolyline(c, [p…], closed)` | LWPOLYLINE in DXF |
| `addRect(c, p1, p2)` | closed polyline |
| `addText(c, pos, text, {height, angleDeg, hAlign, vAlign, font})` | `hAlign` left/center/right, `vAlign` top/middle/base/bottom; saved as MTEXT |
| `setDimScale(c, factor)` | DIMSCALE applied to dimensions added afterwards |
| `addDimLinear(c, p1, p2, linePos, angleDeg)` | 0 = horizontal, 90 = vertical; dimension line through `linePos` |
| `addDimAligned(c, p1, p2, linePos)` | parallel to p1→p2 |
| `addHatch(c, [[p…], …], pattern, [scale], [angleDeg])` | `"SOLID"` or a pattern (`ANSI31`, `ANSI37`, `AR-CONC`, `BRICK`, …); each loop closes itself |
| `defineBlock(c, name, basePoint, function(c){…})` | `add*` calls inside go into the block |
| `insertBlock(c, name, pos, [scale], [angleDeg])` | INSERT on the current layer |
| `addEntity(c, entity)` | add any raw entity (below) |
| `entities(c, [layer])` | model-space entities, optionally one layer |
| `entityType(e)` | `"LINE"`, `"ARC"`, `"POLYLINE"`, `"TEXT"`, `"INSERT"`, `"DIMENSION"`, … (`e.constructor.name` is just `Object`) |
| `extents(c)` | `{minX, minY, maxX, maxY, w, h}` of visible model space |
| `exportPdf(c, path, {paper, landscape, monochrome})` | `paper` `A4`/`A3`/…/`Letter` or `420x297`; auto-fit + centre; orientation auto unless given; monochrome default |
| `exportImage(c, path, {width, height, margin, background})` | PNG/JPG by extension; zoom-to-fit |
| `listFiles(dir, ["dxf"], [recursive])` | sorted absolute paths |
| `mkdirs(dir)` | `mkdir -p` |

## Raw API: documents and operations

```js
var doc = new RDocument(new RMemoryStorage(), createSpatialIndex());
var di  = new RDocumentInterface(doc);
var op  = new RAddObjectsOperation();      // batch many objects in one op — faster
op.addObject(new RLineEntity(doc, new RLineData(v(0,0), v(10,0))));
di.applyOperation(op);                       // nothing exists until applied
```

All changes go through operations: `RAddObjectsOperation` (add),
`RModifyObjectsOperation` (changed objects, layers, blocks),
`RDeleteObjectsOperation` (`deleteObject(e)`), `RAddObjectOperation(obj)`
(single). `di.setCurrentLayer(name)` and `di.setCurrentBlock(name)` decide
where new entities land; `RBlock.modelSpaceName` is `*Model_Space`.
`RDocumentInterface` has no `destroy()` in script — just drop it.

Angles in the raw API are **radians** (`RMath.deg2rad`, `RMath.rad2deg`).

## Entity classes

| Entity | Data constructor |
|---|---|
| `RLineEntity` | `RLineData(p1, p2)` |
| `RCircleEntity` | `RCircleData(center, r)` |
| `RArcEntity` | `RArcData(center, r, startRad, endRad, reversed)` |
| `REllipseEntity` | `REllipseData(center, majorPoint, ratio, startParam, endParam, reversed)` |
| `RPolylineEntity` | `RPolylineData(polyline)`; `polyline = new RPolyline(); appendVertex(p[, bulge]); setClosed(b)` |
| `RSplineEntity` | `RSplineData()` + `appendFitPoint(p)` / `appendControlPoint(p)`, `setDegree(3)` |
| `RPointEntity` | `RPointData(p)` |
| `RTextEntity` | `RTextData(…)` — see [Text](#text) |
| `RBlockReferenceEntity` | `RBlockReferenceData(blockId, pos, scaleVec, angleRad)` |
| `RHatchEntity` | `RHatchData` — see [Hatches](#hatches) |
| `RDimRotatedEntity`, `RDimAlignedEntity`, `RDimAngularEntity`, `RDimRadialEntity`, `RDimDiametricEntity` | see [Dimensions](#dimensions) |

Type tests (global functions): `isLineEntity(e)`, `isArcEntity`,
`isCircleEntity`, `isPolylineEntity`, `isTextEntity`, `isTextBasedEntity`
(text + attributes), `isBlockReferenceEntity`, `isHatchEntity`,
`isDimensionEntity`.

## Querying

```js
var ids = doc.queryAllEntities(false, true);   // (undone=false, allBlocks=true)
var e = doc.queryEntity(id);                    // a copy you may edit and re-apply
e.getLayerName(); e.getBlockId(); e.getBoundingBox();
doc.getModelSpaceBlockId();
doc.getBoundingBox(true, true);                 // visible-only, exclude frozen
doc.getLayerNames(); doc.getBlockNames();       // include "0", "Defpoints", "*Model_Space", "*Paper_Space"
doc.queryLayer("WALLS"); doc.getLayerId("WALLS"); doc.getBlockId("MARK");  // RObject.INVALID_ID if absent
doc.getUnit();                                   // RS.Millimeter, RS.Meter, RS.None, …
```

Line: `getStartPoint()`, `getEndPoint()`, `getLength()`; circle/arc:
`getCenter()`, `getRadius()`, arc `getStartAngle()`/`getEndAngle()` (rad);
polyline: `countVertices()`, `getVertexAt(i)`, `isClosed()`; text:
`getPlainText()`, `getPosition()`; block ref: `getReferencedBlockName()`,
`getPosition()`, `getScaleFactors()`.

## Modifying and deleting

```js
var op = new RModifyObjectsOperation();
entities(c, "WALLS").forEach(function (e) {
    if (isCircleEntity(e)) { e.setRadius(e.getRadius() * 2); op.addObject(e, false); }
    if (isLineEntity(e))   { e.setLayerId(c.doc.getLayerId("HIDDEN")); e.setColor(new RColor("red")); op.addObject(e, false); }
});
c.di.applyOperation(op);

e.move(v(dx, dy)); e.rotate(RMath.deg2rad(a), center); e.scale(f, center); e.mirror(new RLine(p1, p2));
// then op.addObject(e, false) + applyOperation

var del = new RDeleteObjectsOperation();
entities(c, "TEMP").forEach(function (e) { del.deleteObject(e); });
c.di.applyOperation(del);
```

Pass `false` as the second argument of `addObject` on modify operations so
the entity keeps its own layer/colour instead of taking the current ones.
New colour `new RColor("red")`; by-layer `new RColor(RColor.ByLayer)`.

## Layers

`new RLayer(doc, name, frozen, locked, RColor, linetypeId, RLineweight)`;
modify existing via `doc.queryLayer(name)` → `setFrozen(true)`, `setOff(true)`,
`setLocked(true)`, `setColor(…)` → `RModifyObjectsOperation`. Lineweights:
`RLineweight.Weight000…Weight211` (hundredths of mm, e.g. `Weight035`),
`WeightByLayer`. Layer colour "white" is stored as ACI 7 (black on paper in
most viewers).

## Blocks

```js
var blk = new RBlock(doc, "MARK", v(0, 0));          // base point
di.applyOperation(new RAddObjectOperation(blk));
di.setCurrentBlock("MARK"); /* add entities */ di.setCurrentBlock(RBlock.modelSpaceName);
var ref = new RBlockReferenceEntity(doc, new RBlockReferenceData(doc.getBlockId("MARK"), pos, v(1, 1), 0));
```

Attributes (`RAttributeDefinitionEntity`/`RAttributeEntity`) exist but need
more setup; plain text inside the block is simpler when every drawing gets
its own block (as `title-block.js` does).

## Dimensions

```js
var d = new RDimRotatedData();                 // linear; RDimAlignedData for aligned (no rotation)
d.setRotation(RMath.deg2rad(90));              // FIRST — see below
d.setExtensionPoint1(p1); d.setExtensionPoint2(p2);
d.setDefinitionPoint(linePos);                 // a point on the dimension line
var e = new RDimRotatedEntity(doc, d);
e.setDimscale(100);                            // text/arrows/gaps x100
```

`setDefinitionPoint` projects the point using the rotation set *at that
moment*: set the rotation after it and a vertical dimension line lands on
the measured edge instead of at `linePos`. Dimension entities have no
`getMeasuredValue()` in script; check the measurement with `dxf-inspect.py`
/ ezdxf (`dim.get_measurement()`) or from the extension points.

Override the label with `d.setText("4.50 m")` (`"<>"` = measured value).
Setting `RS.DIMTXT`/`RS.DIMASZ` document variables headless does **not**
change the rendered size — use the per-entity `setDimscale` (what
`setDimScale()` in lib.js does).

## Hatches

```js
var h = new RHatchData();
h.setSolid(false); h.setPatternName("ANSI31"); h.setScale(50); h.setAngle(0);
h.newLoop(); h.addBoundary(new RLine(a, b)); h.addBoundary(new RLine(b, c)); …   // closed loop
h.newLoop(); …                                                                   // a hole
addEntity(c, new RHatchEntity(c.doc, h));
```

Boundaries can also be `RArc` segments. Pattern scale is in drawing units:
mm plans need 20–100, parts 0.5–2.

## Text

```js
new RTextData(pos, alignPos, height, width /*0*/, RS.VAlignBase, RS.HAlignLeft,
              RS.LeftToRight, RS.Exact, 1.0 /*line spacing*/, "text",
              "Standard" /*font*/, false /*bold*/, false /*italic*/, angleRad, false /*simple*/)
```

Multi-line: `"line 1\\Pline 2"` (MTEXT paragraph code). Fonts: QCAD's CAD
fonts (`Standard`, `Courier`, `Cursive`, …) or a system TTF name such as
`Arial`.

## Import, export, printing

- `di.importFile(path)` → `RDocumentInterface.IoErrorNoError` (0) on success.
- `di.exportFile(path, "DXF 2013")` → bool. Formats: `DXF 2013`, `DXF 2010`,
  `DXF 2007`, `DXF 2004`, `DXF 2000`, `DXF R12` (**drops all text** — QCAD
  writes text as MTEXT, which R12 lacks); `DWG 2013` etc. with Pro and a
  `.dwg` path.
- PDF: `include("scripts/File/Print/Print.js")`, set `PageSettings/PaperWidth`,
  `PageSettings/PaperHeight` (mm, with `UnitSettings/PaperUnit` = mm),
  `Print.autoFitDrawing(di, autoOrientation)`, then
  `new Print(undefined, doc, view).print(pdfPath)` with an
  `RGraphicsViewImage` view attached to an `RGraphicsSceneQt(di)`. Colour mode
  `view.setColorMode(RGraphicsView.BlackWhite | GrayScale | FullColor)`.
- Image: `include("scripts/File/BitmapExport/BitmapExportWorker.js")`,
  `exportBitmap(doc, scene, path, props, view)` returns `[ok, message]`;
  props `width`, `height`, `margin`, `backgroundColor`, `antialiasing`,
  `monochrome`, `zoomAll`.

## Qt from script

The Qt bindings are available: `QFile`, `QDir`, `QFileInfo`, `QTextStream`,
`QProcess`, `QTimer`, `QTcpServer`/`QTcpSocket`, `QImage`. For text files use
the library helpers — `readTextFile(path)` (string, `undefined` on failure)
and `writeTextFile(path, str)` (bool):

```js
var rows = readTextFile(resolve("rooms.csv")).split("\n").filter(String)
               .map(function (l) { return l.split(","); });
var spec = JSON.parse(readTextFile(resolve("spec.json")));
```

Flag arguments to Qt calls need the library wrappers too:
`makeQIODeviceOpenMode(QIODevice.ReadOnly, QIODevice.Text)`,
`makeQDirFilters(QDir.Files, …)`, `makeQDirSortFlags(QDir.Name)` — the
`new QDir.Filters(a | b)` / `new QIODevice.OpenMode(…)` forms throw
`TypeError: Type error`. 
