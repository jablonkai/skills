# Affinity SDK map — curated digest of `sdk-docs/`

Distilled from the vendored SDK source (Affinity 3.2.3). Use this file to find the right
module and API shape *before* grepping `sdk-docs/`; grep only for exact signatures/params.
All modules load as `require('/name')` (vendored file `name.js` mirrors the module).

## The three ways to change a document

1. **`doc.<verb>(...)` convenience methods** — `Document` wraps nearly every command:
   `setBlendMode`, `setOpacity`, `setText`, `formatText`, `applyTransform`, `setShape`,
   `setLineWeight`, `setBrushFillDescriptor`, `deleteSelection`, `flatten`, … Most take
   `(args…, selection, [options], preview)`; pass `null` selection to use the current one.
   **Prefer these** — one call, one undo step.
2. **`DocumentCommand.create*(...)` + `doc.executeCommand(cmd, preview)`** — same verbs as
   statics (~300 in `commands.js`), needed when batching via
   `CompoundCommandBuilder.create()` → `addCommand(cmd)` → `createCommand()`.
3. **Node insertion** — single node: `doc.addNode(nodeDefinition, targetNode = null,
   childList = NodeChildType.Main, preview)`. Multiple/positioned:
   `AddChildNodesCommandBuilder` (see api-reference.md drawing recipe).

Everything is undoable: `doc.undo()/redo()`, `doc.history` (DocumentHistory),
snapshots (`doc.snapshots`, `DocumentCommand.createAddDocumentSnapshot`).

## document.js — Document (the hub)

- Lifecycle: `Document.current/.all/.load(path)`, `.createFromPreset(preset, landscape)`,
  `.create(options)` (`NewDocumentOptions.createDefault()`), `save()`, `saveAs(path)`,
  `close()`; `isDirty`, `title`, `path`.
- Structure: `rootNode`, `currentSpread`, `spreads`, `artboards`, `layers`, `pageCount`,
  `hasArtboards`; sizes `sizePixels/widthPixels/heightPixels`, `dpi`, `units`, `format`.
- Selection: `doc.selection` (Selection), `selectAll()`, `DocumentCommand.createSetSelection`.
- Export: `doc.export(path, FileExportOptions, FileExportArea, size)` —
  `FileExportOptions.createWithPresetName(name)` (names: `FileExportOptions.allPresetNames`);
  `FileExportArea.createForWholeDocument()/CurrentSpread()/Selection(sel)/Pages("1-3")`.
  Remember: script fs writes are Desktop-only.
- Spread/artboard mgmt: `addRectangularArtboard(rect, copyProps, copyGuides)`,
  `setSpreadSizeWithAnchor`, `setDocumentProperties`; switch spread with
  `DocumentCommand.createSetCurrentSpread(spreadNode)` (clears selection!).
- Guides: `addGuide(horizontal, pixels96)`, `moveGuide`, `removeGuide`.
- AI / photo ops (whole-doc verbs): `generateImage(prompt)`, `generativeEditImage(prompt)`,
  `removeBackground()`, `selectSubject()`, `detectDepth()`, `colourise()`,
  `imageTrace(edgeThreshold, curveFittingTolerance)` (bitmap → vector), macros
  (`importMacro/exportMacro/startRecordingMacro/…`).
- Raster selection: `rasterSelectAll/Deselect/InvertSelection`, `setRasterSelectionFromPolygon/
  FromObject`, `growShrink/feather/smooth/outlineRasterSelection`; also `flatten()`,
  `mergeVisible()`.
- Layer-effect setters: ~150 `set<Fx>LayerEffect*` methods (Bevel/Emboss, Outline, Inner/Outer
  Shadow & Glow, ColourOverlay, GradientOverlay, PhongBevel, GaussianBlur) — all take
  `(selection, …, enableIfDisabled, preview)`; `removeAllLayerEffects(selection)`.

## nodes.js — node model (the 180 KB one)

Hierarchy: `Node` → `LogicalNode` (fills/strokes) → `ContainerNode` (layers), `GroupNode`,
`DocumentNode`; `Node` → `PhysicalNode` → `SpreadNode`, `TextNode` (Art/Frame/Path/Table…),
`VectorNode` (`ShapeNode`, `PolyCurveNode`, `ImageNode`), `RasterNode` (pixel layers,
adjustments, live filters), `EmbeddedDocumentNode`.

- Type guards on every class: `node.isShapeNode`, `.isTextNodeDefinition`, etc.
- Traversal: `node.children` / `.descendents` (lazy `Collection` — `filter/map/take/toArray`),
  `nextSibling`, `spread`, `document`; reorder with `moveToFirstChild/moveToParent/…`;
  `delete()`, `duplicate(transform?)`.
- Geometry: `spreadBaseBox`, `localVisibleBox`, `getExactSpreadVisibleBox()`,
  `transform` / `transformInterface`, `baseToSpreadTransform`.
- State: `isVisible`, `globalOpacity`, `blendMode`, `isLocked`/`lock()`, `description`,
  `tagColour`, `exportConfig`, `quickFX` (layer effects), `selfSelection` (1-node Selection).
- `LogicalNode`/`VectorNode` styling getters: `brushFillDescriptor`, `penFill`, `lineStyle`,
  `lineWeightPts`, `dashPattern`, `strokeAlignment`, `transparencyFill` — set via `doc.set*`.
- Adjustments (`*AdjustmentRasterNode`): BlackAndWhite, BrightnessContrast, ColourBalance,
  Curves, Exposure, HSLShift, Invert, Levels, Recolour, SelectiveColour, ShadowsHighlights,
  SplitToning, Threshold, Vibrance, WhiteBalance, ToneCompression/Stretch, Normals, Posterise.
  Live filters (`*FilterRasterNode`): Gaussian/Box/Median/Motion/Radial/Lens/Field/Max/Min
  blur, DepthOfField, Clarity, UnsharpMask, HighPass, Denoise, AddNoise, Bloom, Pixelate,
  Halftone, Ripple, Twirl, Spherical, PinchPunch, Vignette, Defringe, Voronoi, DustAndScratch…
  Pattern: `XxxRasterNodeDefinition.createDefault()` or `.create(params)` → add as child of
  the target node; tune later via `def/node.parameters` + `doc.executeCommand(
  DocumentCommand.createSetXxxParameters(selection, params))`.

## Creating specific node kinds

- **Shape**: `ShapeNodeDefinition.create(shape, rect, brushFill, lineFill, lineStyle,
  transparencyFill)` — recipe in api-reference.md.
- **Text**: build content first, then a definition from it:
  ```js
  const { StoryBuilder } = require('/storybuilder');
  const { ArtTextNodeDefinition, FrameTextNodeDefinition } = require('/nodes');
  const sb = StoryBuilder.create();
  sb.setToArtisticTextDefaultStyle(doc.dpi);        // or setToFrameTextDefaultStyle
  sb.addText('Hello'); sb.addParagraphBreak();
  sb.applyGlyphDelta(StoryDelta.createComposite([...]));   // pre-style the text
  doc.addNode(ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 300}, sb));
  // FrameTextNodeDefinition.createFromStoryBuilder(frameRect, sb) for text frames
  ```
- **Image**: `ImageNodeDefinition.create(format)` + `.setBitmap(Bitmap.loadFromFile(path))`;
  pixel layer: `RasterNodeDefinition` + `.setBitmap(bm)` (see `tests/rasterNodeTests.js`).
- **Freeform path**: `PolyCurveNodeDefinition.create(curve, brushFill, lineStyle, lineFill,
  transparencyFill)` with a `PolyCurve` from geometry.
- **Layer/group**: `ContainerNodeDefinition.create(name)`; table: `TableTextNodeDefinition`
  (working example: `examples/tableFromJson.js`).

## Text stack (story*.js, glyphatts, paragraphatts, fonts)

- Read: `textNode.text` / `.getText(start, maxLen, format)`, `.story`, `.storyRange`,
  `.textFrameInterface` (overflow/flow info).
- Write: `doc.setText(text, selection)` replaces; `doc.formatText(delta, selection)` styles
  the *text selection* (or whole node selection).
- `StoryDelta` statics = every text attribute: `createFamilyName/Weight/Italic/Width`,
  `createFont`, `createAlignX(ParagraphAlignXType.Centre)`, `createBrushFill(fd)` (text
  colour), `createGlyphDouble(GlyphAttDoubleType.Height, pts)` (font size), underline/caps/
  super-sub/leading/indent/hyphenation…, combined with `createComposite([...])`.
- `GlyphAtts.create()` / `ParagraphAtts.create()` — absolute attribute sets for StoryBuilder
  (`sb.setGlyphAtts`); deltas are usually easier.
- Fonts: `Font.create(family, weight, isItalic, width)`, `Font.all`, `FontFamily.all`,
  `FontWeight.Bold` etc.; document fonts: `doc.getFontNames()`.
- Glyph objects (fields, breaks, anchors, index marks): `glyphs.js`;
  `doc.insertGlyph(glyph, selection)`.

## Colour, fills, strokes (colours.js, fills.js, linestyle.js, hatch.js)

- `Colour.createRGBA8({r, g, b, alpha})` (0-255), also `createHSLAf/CMYKA8/LABA16/…`;
  convert via `colour.rgba8` etc. `SVG11.<name>` = all 147 named colours, `SVG11.random()`.
- `FillDescriptor.createSolid(solidFill, blendMode)` / `.create(fill, scaleWithObject,
  transform, blendMode, anchoredToSpread)`; fill types: `SolidFill.create(colour)`,
  `GradientFill.create(Gradient.create(stops), gradientFillType)`, `BitmapFill.create(bitmap,
  extendType, resamplerType, ignoreAlpha)`, `HatchFill`, `NoFill`.
- `LineStyle.create(opts)` / `.createDefaultWithWeight(w)`; `LineStyleDescriptor.create(
  lineStyle, options)` adds arrowheads (`ArrowHead.create(style, opts)`), pressure,
  stroke alignment. Apply via `doc.setLineStyleDescriptor` or the per-prop setters.
- Gradients on canvas: `doc.setBrushFillDescriptor(fd, selection)`; blend modes:
  `BlendMode` enum (exported from several modules).

## geometry.js

`Point`, `Rectangle(x, y, w, h)`, `Size`, `Vector`, `Transform` (mutable, chainable:
`setIdentity().translate…` — prototype helpers over struct), `TransformBuilder`.
Curves: `Curve.createLine/Rectangle/Ellipse/Diamond/Lozenge`, `CurveBuilder`
(`addBezier`, `addArc`, `bulgeTo`, `versineTo`), `PolyCurve.create()` + `addCurve`,
`PolyPolyCurve` (hit-testing: `containsPoint`), `Polygon` (for raster selection),
`Spline` (for curves adjustments), helpers `rectsIntersect`, `unionRects`, `pointInRect`.

## Raster & pixels (rasterobject.js, pixelaccessor.js, rasterbrush.js)

- `Bitmap.create(w, h, RasterFormat.RGBA8)` / `Bitmap.loadFromFile(path)`; `PixelBuffer`
  exposes `.buffer` for byte access.
- `PixelReaderWriterRGBA8` (+ 16-bit/CMYK/LAB/mono variants) — direct pixel IO on raster
  nodes/bitmaps; working example `examples/bitmapWriter.js`.
- `doc.rasterSelection` (`RasterSelection`), brushes: `RasterBrush`, `VectorBrush`.

## Selections (selections.js)

`doc.selection` → `Selection` (`length`, `at(i)`, `items`, `add(node)`); construct fresh via
`node.selfSelection` or add nodes to selection then call `doc.set*`. Sub-selections
(curve nodes/edges, fill mesh, table cells, text ranges): `CurveNodeSubSelection`,
`TableSubSelection`, `TextSelection`… — mostly consumed by curve-editing commands
(`createDeleteCurveNodes`, `createSetCurveNodeStyle`, knife/scissor cuts).

## UI, files, misc

- **dialog.js** — full declarative dialog API: `Dialog` + `DialogColumn/Group/TextBox/
  ComboBox/Switch/ColourPicker/FillEditor/UnitValueEditor/…` for user-facing scripts;
  quick prompts: `app.alert/confirm/prompt/chooseFile` (+ `*Async`).
- **fs.js** — `fs`/`File.readAll(path)`, `File.open`, `Directory`, `FileSystemPromises`
  (exists/copy/remove/createDirectories…). Sandbox: Desktop only (`app.userDesktopPath`).
- **network.js** — `HttpRequest` exists but script networking is normally disabled.
- **timers.js** — `setTimeout/setInterval/setImmediate` (scripts can be async;
  console output only while script runs).
- **collection.js** — every `.children`/`.all` is a lazy `Collection`: `filter/map/some/
  reduce/take/toArray`; don't index like an array, use `.at(i)`.
- **buffer.js** — Node-like `Buffer` for pixel/file IO.
- **exportconfig.js** — per-node export setup (`ExportConfig`/`ExportFormat`/`ExportScale`),
  applied with `DocumentCommand.createSetExportConfig(selection, cfg)`; for one-off exports
  prefer `doc.export`.
- **Interfaces** (`*interface.js`) — thin per-aspect views a node exposes (`baseBoxInterface`,
  `blendModeInterface`, `curvesInterface`, `pictureFrameInterface`, `storyInterface`,
  `artboardInterface`, `marginsInterface`…). Reach them from the node; rarely constructed.

## Gotchas found in the sources

- `Document` command wrappers execute immediately; the `DocumentCommand.create*` statics
  only *build* — nothing happens until `doc.executeCommand`.
- `preview: true` renders a preview without committing; clear with `doc.clearPreviews()`.
- Coordinate space for node definitions is spread coordinates (origin top-left of spread),
  in document units at `doc.dpi`.
- Almost every API has an `xxxAsync(…, callback)` twin plus `doc.promises` /
  `DocumentPromises` — stick to sync in scripts, it's simpler and output ordering is stable.
- `examples/*.js` wrap code in `function main()` + `module.exports.main` — live execution
  needs top-level code instead; the logic inside is still accurate. `tests/*.js` are partly
  stale — treat as idea sources only.
- Enum classes expose `keys`/`values`/`entries` as **properties**; log
  `SomeEnum.keys` to discover valid values.
- Param bounds live in `param_ranges.min.json` / `struct_ranges.min.json` — check before
  guessing valid numeric ranges.

## File index (grep targets)

| Area | Files |
|---|---|
| App entry, documents | `application.js`, `document.js`, `documentproperties.js` |
| Node model, adjustments, filters | `nodes.js` |
| Commands, batching | `commands.js` |
| Shapes (30+ classes, QR payloads) | `shapes.js`, `shapeinterface.js` |
| Geometry, curves, transforms | `geometry.js`, `curvesinterface.js`, `drawingscale.js`, `units.js` |
| Colour, fills, strokes | `colours.js`, `fills.js`, `linestyle.js`, `linestyleinterface.js`, `hatch.js`, `brushfillinterface.js` |
| Text | `story.js`, `storybuilder.js`, `storydelta.js`, `storyinterface.js`, `glyphs.js`, `glyphatts.js`, `paragraphatts.js`, `fonts.js`, `textframeinterface.js` |
| Raster, pixels, brushes | `rasterobject.js`, `rasterinterface.js`, `pixelaccessor.js`, `rasterbrush.js`, `vectorbrush.js`, `rasterselection.js`, `buffer.js` |
| Layer effects | `layereffects.js`, `layereffectsinterface.js` |
| Selections | `selections.js`, `selectable.js` |
| Export | `exportconfig.js`, `exportableinterface.js` (+ `doc.export` in `document.js`) |
| Artboards, spreads, pages | `artboardinterface.js`, `artboardproperties.js`, `pageboxinterface.js`, `marginsinterface.js`, `physicalroot*.js` |
| UI dialogs | `dialog.js` |
| Files, network, timers | `fs.js`, `network.js`, `timers.js` |
| Node aspect interfaces | `baseboxinterface.js`, `blendmodeinterface.js`, `transforminterface.js`, `transparencyinterface.js`, `visibilityinterface.js`, `taginterface.js`, `descriptioninterface.js`, `editabilityinterface.js`, `imageresourceinterface.js`, `pictureframeinterface.js`, `compoundoperationinterface.js`, `exportableinterface.js` |
| Embedded documents | `nodes.js` (`EmbeddedDocumentNode`) |
| Valid ranges | `param_ranges.min.json`, `struct_ranges.min.json`, `struct_array_sizes.min.json` |
| Working examples | `examples/` (artboardGrid, tableFromJson, bitmapWriter, boldItalics, addGuides, flexibleLayout…) |
