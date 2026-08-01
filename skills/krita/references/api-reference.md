# Krita (libkis) Python API reference

Every member listed here was checked by introspection against a running **Krita 5.3.3**
(Python 3.13, PyQt5 5.15.11); signatures are the PyQt ones, which differ from the C++ docs
in places (`paintLine` is the loud example). The upstream C++ reference is at
<https://api.kde.org/legacy/krita/html/annotated.html> — treat anything it lists that
isn't here as *not present in 5.3.3* until you have probed for it
(see [recipes.md](recipes.md#probing-what-you-dont-know-yet)), because several documented
members (`Krita.blendingModes`, `Document.gridConfig`, `Node.setPinnedToTimeline`,
`Shape.isSelectable`) only exist on master.

Everything runs in the live session through the bridge, so the objects here *are* the
documents and layers the user is looking at.

## Contents

- [Application: `Krita`](#application-krita)
- [Document](#document)
- [Node — layers and masks](#node--layers-and-masks)
- [Painting with the brush engine](#painting-with-the-brush-engine)
- [Pixels: `QImage` in and out](#pixels-qimage-in-and-out)
- [Vector layers and shapes](#vector-layers-and-shapes)
- [Filters](#filters)
- [Selections](#selections)
- [Animation](#animation)
- [Colour: `ManagedColor`, profiles, palettes](#colour-managedcolor-profiles-palettes)
- [Resources and brush presets](#resources-and-brush-presets)
- [Views, windows, actions](#views-windows-actions)
- [Export configuration (`InfoObject`)](#export-configuration-infoobject)

## Application: `Krita`

```python
from krita import Krita
app = Krita.instance()                 # the singleton application
```

| Call | Returns / effect |
|---|---|
| `app.version()` | `"5.3.3"` (plus git sha for dev builds) |
| `app.createDocument(w, h, name, colorModel, colorDepth, profile, resolution)` | new `Document` with one transparent layer; `profile=""` means the default |
| `app.openDocument(filename)` | loads a file into a new `Document` (no view attached) |
| `app.activeDocument()` / `app.setActiveDocument(doc)` | the document of the active view |
| `app.documents()` | every open `Document` |
| `app.activeWindow()`, `app.windows()`, `app.views()`, `app.openWindow()` | UI handles |
| `app.batchmode()` / `app.setBatchmode(bool)` | application-level "no dialogs" flag |
| `app.filters()` / `app.filter(name)` | filter ids / a configured `Filter` |
| `app.filterStrategies()` | scaling strategies (`"Bicubic"`, `"Lanczos3"`, …) |
| `app.colorModels()`, `app.colorDepths(model)`, `app.profiles(model, depth)` | colour-space vocabulary |
| `app.resources(type)` | `{name: Resource}` for `"pattern"`, `"gradient"`, `"brush"`, `"preset"`, `"palette"`, `"workspace"` |
| `app.action(name)`, `app.actions()` | `QAction`s of the active window — `action("...").trigger()` runs a menu command |
| `app.readSetting(group, name, default)` / `app.writeSetting(group, name, value)` | `kritarc` access |
| `app.recentDocuments()`, `app.icon(name)`, `app.notifier()` | misc |
| `app.addExtension(ext)`, `app.addDockWidgetFactory(f)` | plugin registration (startup only) |

Verified vocabulary on 5.3.3 — colour models `RGBA`, `XYZA`, `LABA`, `CMYKA`, `GRAYA`,
`YCbCrA`, `A`; depths `U8`, `U16`, `F16`, `F32`; scaling strategies `Bicubic`, `Bilinear`,
`BSpline`, `Bell`, `Hermite`, `Lanczos3`, `Mitchell`, `NearestNeighbor`.

There is **no** API that lists blending modes (`Krita.blendingModes()` is master-only) —
use the ids the Layers docker shows: `normal`, `multiply`, `screen`, `overlay`, `add`,
`subtract`, `darken`, `lighten`, `erase`, `dissolve`, `color`, `saturation`, `luminize`, …
`node.blendingMode()` after setting one by hand is the reliable way to learn an exotic id.

## Document

Creation, identity, size:

```python
doc.name(), doc.setName(s)          doc.fileName(), doc.setFileName(s)
doc.width(), doc.height()           doc.setWidth(int), doc.setHeight(int)
doc.resolution(), doc.setResolution(int)      # ppi;  xRes()/yRes() are per-axis
doc.bounds()                                   # QRect
doc.colorModel(), doc.colorDepth(), doc.colorProfile()
doc.setColorSpace(model, depth, profile)       # converts the whole image
doc.setColorProfile(profile)                   # assigns without converting
doc.backgroundColor(), doc.setBackgroundColor(QColor)
```

Layer tree:

```python
doc.rootNode()                      # the root GroupLayer
doc.topLevelNodes()                 # its children
doc.nodeByName(name), doc.nodeByUniqueID(uuid)
doc.activeNode(), doc.setActiveNode(node)
doc.createNode(name, nodeType)      # see the node-type table below
doc.createGroupLayer(name)
doc.createVectorLayer(name)
doc.createFileLayer(name, fileName, scalingMethod, scalingFilter="Bicubic")
doc.createFillLayer(name, generatorName, InfoObject, Selection)   # "pattern", "color", …
doc.createFilterLayer(name, Filter, Selection)
doc.createFilterMask(name, Filter, selection_source_node)         # or (name, Filter, Selection)
doc.createTransparencyMask(name), doc.createSelectionMask(name)
doc.createTransformMask(name), doc.createColorizeMask(name)
doc.createCloneLayer(name, source_node)
```

A created node is **not** in the tree until `parent.addChildNode(node, above)` — pass
`None` as `above` to put it on top of that parent's children.

`createDocument` already gives you one paint layer, and **its name is translated** — on a
Hungarian Krita it is `Háttér`, not `Background`. Reach it as
`doc.rootNode().childNodes()[0]`; `nodeByName("Background")` returns `None` on most
installations and is the classic way to waste a debugging round.

Whole-image operations:

```python
doc.crop(x, y, w, h)                doc.resizeImage(x, y, w, h)
doc.scaleImage(w, h, xres, yres, strategy)      # xres/yres are ints — int(doc.xRes())!
doc.rotateImage(radians)            doc.shearImage(angleX, angleY)
doc.flatten()                       doc.clone()
```

`xRes()`/`yRes()` return floats but `scaleImage` and `setResolution` take ints, and PyQt
raises `TypeError` rather than rounding for you — wrap them in `int(...)`.

Reading the composed image, and saving:

```python
doc.refreshProjection(); doc.waitForDone()      # ALWAYS before reading or exporting
doc.projection(x=0, y=0, w=0, h=0)              # QImage of the merged canvas
doc.thumbnail(w, h)                             # QImage, scaled
doc.pixelData(x, y, w, h)                       # raw merged bytes
doc.save()                                      # to fileName()
doc.saveAs(path)                                # .kra keeps layers; other extensions flatten
doc.exportImage(path, InfoObject())             # format from the extension
doc.close()
doc.setBatchmode(True)                          # suppress format dialogs — set it first
doc.modified(), doc.setModified(bool), doc.setAutosave(bool)
doc.lock(), doc.unlock(), doc.tryBarrierLock()  # for long multi-step edits
```

`doc.selection()`, `doc.setSelection(sel)` hold the global selection; `doc.guidesConfig()`
and `doc.setHorizontalGuides([...])` cover guides (`gridConfig()` is master-only).

## Node — layers and masks

`doc.createNode(name, type)` accepts: `paintlayer`, `grouplayer`, `filelayer`,
`filterlayer`, `filllayer`, `clonelayer`, `vectorlayer`, `transparencymask`,
`filtermask`, `transformmask`, `selectionmask`, `colorizemask`.

```python
node.name(), node.setName(s)              node.type()          # the id above
node.visible(), node.setVisible(bool)     node.locked(), node.setLocked(bool)
node.opacity(), node.setOpacity(0..255)   node.blendingMode(), node.setBlendingMode(id)
node.inheritAlpha(), node.setInheritAlpha(bool)
node.alphaLocked(), node.setAlphaLocked(bool)
node.colorLabel(), node.setColorLabel(index)
node.bounds()          # QRect of actual content — empty until pixels exist
node.position(), node.hasExtents(), node.index(), node.uniqueId()
node.parentNode(), node.childNodes(), node.addChildNode(child, above)
node.removeChildNode(child), node.remove(), node.duplicate(), node.clone()
node.findChildNodes(name, recursive, partialMatch, type, colorLabelIndex)
node.mergeDown()
node.move(x, y), node.cropNode(x, y, w, h), node.rotateNode(radians)
node.scaleNode(QPointF(origin), w, h, strategy), node.shearNode(angleX, angleY)
node.thumbnail(w, h)                       # QImage sized to the LAYER, not the image
node.save(filename, xRes, yRes, InfoObject(), exportRect)   # export one layer
node.layerStyleToAsl(), node.setLayerStyleFromAsl(asl)
```

`node.save()` writes the file but returns `None` through PyQt (the C++ `bool` is lost), so
check the file exists instead of the return value. `setPinnedToTimeline` is master-only.

Blend-mode ids are Krita's own (`"normal"`, `"multiply"`, `"add"`, `"screen"`,
`"overlay"`, `"erase"`, …), not CSS names.

## Painting with the brush engine

Krita *can* paint real strokes with the current brush preset — these go through the same
paint ops as a tablet stroke, so a watercolour or textured preset behaves like one:

```python
node.paintLine(QPoint(x1, y1), QPoint(x2, y2), 1.0, 0.2, "ForegroundColor")  # QPoint!
node.paintRectangle(QRectF(x, y, w, h), "ForegroundColor", "None")
node.paintEllipse(QRectF(x, y, w, h), "ForegroundColor", "None")
node.paintPolygon([QPointF(...), ...], "ForegroundColor", "None")
node.paintPath(QPainterPath(...), "ForegroundColor", "None")
node.paintAbility()   # "PAINT" | "VECTOR" | "CLONE" | "UNPAINTABLE" | "MYPAINTBRUSH_UNPAINTABLE"
```

**`paintLine` is the odd one out**: PyQt binds it to `QPoint`, and a `QPointF` raises
`TypeError: argument 1 has unexpected type 'QPointF'` — while `paintPolygon` accepts either
and the rect-based calls want `QRectF`. Convert with `.toPoint()` when your geometry is
float-based.

`strokeStyle` ∈ `None`, `ForegroundColor`, `BackgroundColor` (`None` on a line still uses
the foreground, since it would otherwise be invisible); `fillStyle` ∈ `None`,
`ForegroundColor`, `BackgroundColor`, `Pattern`.

These use *the active view's* preset, colour, size, opacity and blending mode, so set
them first (see [Views](#views-windows-actions)) — and they need a view: on a document
that was never added to a window, `paintAbility()` reports `UNPAINTABLE`. Check it before
a long stroke loop rather than wondering why nothing appeared.

For deterministic geometry that must not depend on the user's preset, draw with QPainter
and push pixels instead.

## Pixels: `QImage` in and out

```python
node.setPixelData(QByteArray, x, y, w, h)   # writes into paint layers and mask selections
node.pixelData(x, y, w, h)                  # copy of the layer's own pixels
node.pixelDataAtTime(x, y, w, h, time)      # animated layers
node.projectionPixelData(x, y, w, h)        # the node with its masks/children applied
```

Channel order depends on the colour space — **integer RGBA is B, G, R, A**; float RGBA is
R, G, B, A; GrayA is Gray, A; masks and selections are a single 0–255 channel. Bytes per
channel: `U8` 1, `U16`/`F16` 2, `F32` 4. `setPixelData` needs exactly
`channels × bytes × w × h` bytes and silently does nothing on group, file and clone layers.

Round-trip helpers for an 8-bit RGBA document — `QImage.Format_ARGB32` is BGRA in memory
on little-endian machines, which is why no channel swap appears here:

```python
def push(node, image, x=0, y=0):
    img = image.convertToFormat(QImage.Format_ARGB32)
    ptr = img.constBits(); ptr.setsize(img.byteCount())
    node.setPixelData(QByteArray(ptr.asstring()), x, y, img.width(), img.height())

def pull(node, x, y, w, h):
    return QImage(node.pixelData(x, y, w, h), w, h, QImage.Format_ARGB32).copy()
```

## Vector layers and shapes

```python
vec = doc.createVectorLayer("headline"); doc.rootNode().addChildNode(vec, None)
shapes = vec.addShapesFromSvg(svg_string)      # returns the created Shape objects
vec.shapes(), vec.toSvg()
vec.shapeAtPosition(QPointF), vec.shapesInRect(QRectF, omitHidden=True, contained=False)
vec.createGroupShape(name, [shapes])
vec.setAntialiased(True)
```

`Shape`: `name()/setName()`, `position()/setPosition(QPointF)`, `boundingBox()`,
`toSvg()`, `remove()`, `select()/deselect()`, `zIndex()/setZIndex(i)`, `update()`,
`type()`, `parentShape()`, `absoluteTransformation()`.

SVG is the practical way to place **text** — Krita has no text-object constructor in the
Python API. Give the `<svg>` element an explicit `width`/`height` matching the document so
coordinates land where you expect, and prefer fonts you know are installed.

## Filters

```python
f = app.filter("blur")               # keep the Filter in a variable — see below
cfg = f.configuration()
cfg.setProperty("halfWidth", 40); cfg.setProperty("halfHeight", 40)
f.setConfiguration(cfg)
f.apply(node, x, y, w, h)            # destructive, synchronous
f.startFilter(node, x, y, w, h)      # asynchronous — follow with doc.waitForDone()
```

**Never chain `app.filter("blur").configuration()`.** The `Filter` is a temporary, Python
drops it on the next line, and the `InfoObject` it owned dies with it —
`RuntimeError: wrapped C/C++ object of type InfoObject has been deleted`, at a line that
looks innocent. Bind the filter to a name and keep it alive as long as you use its config.

Filter ids are **not** identifier-shaped: it is `"gaussian blur"` with a space, and
`app.filter("gaussianblur")` silently returns `None` (then `AttributeError` on the next
call). The 52 ids in 5.3.3 include `blur`, `gaussian blur`, `motion blur`, `lens blur`,
`unsharp`, `sharpen`, `levels`, `perchannel`, `hsvadjustment`, `colorbalance`, `invert`,
`desaturate`, `posterize`, `threshold`, `pixelize`, `oilpaint`, `raindrops`, `noise`,
`edge detection`, `emboss`, `gradientmap`, `halftone`, `dodge`, `burn`, `roundcorners`,
`wave`, `palettize`. Print `sorted(app.filters())` for the rest.

Verified default configurations — the property names are what `setProperty` expects:

| filter | properties |
|---|---|
| `blur` | `halfWidth` 5, `halfHeight` 5, `rotate` 0, `strength` 0, `shape` 0, `lockAspect` True |
| `gaussian blur` | `horizRadius` 5, `vertRadius` 5, `lockAspect` True |
| `unsharp` | `halfSize` 1, `amount` 0.5, `threshold` 0, `lightnessOnly` True |
| `pixelize` | `pixelWidth` 10, `pixelHeight` 10, `keepAspect` True |
| `levels` | `blackvalue` 0, `whitevalue` 255, `gammavalue` 1.0, `outblackvalue` 0, `outwhitevalue` 255, `mode` `"lightness"` |
| `invert` | none |

For anything else, print `f.configuration().properties()` (with `f` bound!) — the defaults
tell you both the names and the value types.

Non-destructive equivalents: `doc.createFilterLayer(name, f, selection)` and
`doc.createFilterMask(name, f, selection_source)`.

## Selections

```python
from krita import Selection
sel = Selection()
sel.select(x, y, w, h, 255)          # value 0–255 = selectedness
sel.selectAll(node, 255)
doc.setSelection(sel)                # global selection; doc.selection() reads it back
```

Combine: `add`, `subtract`, `intersect`, `replace`, `symmetricdifference` (all take
another `Selection`). Shape: `invert`, `clear`, `grow(x, y)`, `shrink(x, y, edgeLock)`,
`contract(v)`, `border(x, y)`, `feather(r)`, `erode`, `dilate`, `smooth`, `move(x, y)`,
`resize(w, h)`, `duplicate()`. Geometry: `x()`, `y()`, `width()`, `height()`.
Pixels: `pixelData(x, y, w, h)` / `setPixelData(bytes, x, y, w, h)` — one channel.
Clipboard: `copy(node)`, `cut(node)`, `paste(destination, x, y)`.

## Animation

```python
doc.setFramesPerSecond(24)
doc.setFullClipRangeStartTime(0); doc.setFullClipRangeEndTime(47)
doc.setPlayBackRange(0, 47)
doc.setCurrentTime(t)                 # move the playhead, then draw into the layer
doc.currentTime(), doc.animationLength(), doc.framesPerSecond()
doc.importAnimation([files], firstFrame, step)

node.enableAnimation()                # make a paint layer animated before keying
node.hasKeyframeAtTime(frame)
node.animated()
node.pixelDataAtTime(x, y, w, h, time)
```

**Creating keyframes is not in the API.** `enableAnimation()` + `setCurrentTime(t)` +
`setPixelData(...)` looks like it works — the projection changes, the frames you save look
right — but `hasKeyframeAtTime(t)` stays `False` for every `t` except 0: you have been
overwriting one keyframe the whole time, and the saved `.kra` animates nothing. The frame
has to be created through the timeline action first:

```python
app.setActiveDocument(doc); doc.setActiveNode(layer)   # the action follows these
layer.enableAnimation()
for t in range(n):
    doc.setCurrentTime(t)
    if t:
        app.action("add_blank_frame").trigger()        # or "add_duplicate_frame"
    layer.setPixelData(frame_bytes, 0, 0, w, h)
    doc.refreshProjection(); doc.waitForDone()
```

Verified: `hasKeyframeAtTime` is then `True` for every frame. The action needs an **active
view**, so add the document to a window first. `render_animation` also exists as an action
but opens the render dialog — save each frame's projection and encode with ffmpeg instead,
see [recipes.md](recipes.md#animation-frames-and-turning-them-into-video).

## Colour: `ManagedColor`, profiles, palettes

```python
from krita import ManagedColor
c = ManagedColor.fromQColor(QColor("#ff6b35"))   # static, canvas argument optional
c2 = ManagedColor("RGBA", "U8", "")              # model, depth, profile
c2.setComponents([1.0, 0.42, 0.0, 1.0])          # 0.0–1.0, in the colour space's own order
qc = c.colorForCanvas(canvas)                    # back to QColor
c.toXML(), ManagedColor.fromXML(xml)
view.setForeGroundColor(c)                   # what the paint* calls use
```

`components()` returns the channels in the **colour space's** order, not RGBA — on an
8-bit RGBA document `ManagedColor.fromQColor(QColor("#ff3300")).components()` reads
`[0.0, 0.03, 1.0, 1.0]`, i.e. B, G, R, A. Same ordering rule as `pixelData`.

`Palette(resource)` / `PaletteView` expose swatch collections; `app.resources("palette")`
lists them.

## Resources and brush presets

```python
presets = app.resources("preset")            # {name: Resource} — 144 on a default 5.3.3
view.setCurrentBrushPreset(presets["b) Basic-5 Size"])
view.setBrushSize(40); view.setPaintingOpacity(0.8); view.setPaintingFlow(1.0)
view.setCurrentBlendingMode("multiply"); view.setEraserMode(False)
```

Preset names are exactly what the Brush Presets docker shows, prefixes and all
(`"a) Eraser Circle"`, `"b) Airbrush Soft"`, `"b) Basic-5 Size"`) — misspell one and the
`KeyError` is the only warning you get, so match against
`sorted(app.resources("preset"))` rather than typing a remembered name. The other resource
types that answer on 5.3.3: `pattern`, `gradient`, `brush`, `palette`, `workspace`.

## Views, windows, actions

```python
win = app.activeWindow()                     # None if Krita has no window open
view = win.addView(doc)                      # shows the document; returns the View
win.views(), win.activeView(), win.qwindow()
view.document(), view.canvas(), view.selectedNodes(), view.showFloatingMessage(...)
canvas = view.canvas(); canvas.setZoomLevel(1.0); canvas.setRotation(0)
app.action("edit_undo").trigger()            # any menu action, by id
```

`app.action(...)` reaches commands the API has no wrapper for, but it acts on the *active*
document and returns nothing — treat it as a last resort and verify the result afterwards.

## Export configuration (`InfoObject`)

```python
from krita import InfoObject
cfg = InfoObject()
cfg.setProperty("quality", 90)               # JPEG/WEBP
doc.exportImage(path, cfg)
```

`InfoObject()` with no properties uses each format's defaults, which is usually what you
want. Commonly used keys — PNG: `alpha`, `compression` (0–9), `indexed`, `interlaced`,
`forceSRGB`, `transparencyFillcolor`; JPEG: `quality` (0–100), `progressive`, `smoothing`,
`subsampling`, `saveProfile`. Unknown keys are ignored silently, so confirm the result by
checking the file size or re-reading the export rather than trusting the call.
