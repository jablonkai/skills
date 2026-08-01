# GIMP 3 Python API reference

Every call here was run against **GIMP 3.2.4** through the bridge described in
[SKILL.md](../SKILL.md). GIMP 3 dropped the old `gimpfu` module: scripts now talk to
libgimp through GObject Introspection, which means real classes and methods instead of
`pdb.gimp_image_new(...)` strings.

Contents:

- [Preamble and types](#preamble-and-types)
- [Colour — the linear/sRGB trap](#colour--the-linearsrgb-trap)
- [Images, layers, groups](#images-layers-groups)
- [Selections](#selections)
- [Drawing: fills, gradients, brushes, paths](#drawing-fills-gradients-brushes-paths)
- [Text layers](#text-layers)
- [Filters — GEGL, destructive and not](#filters--gegl-destructive-and-not)
- [Masks and channels](#masks-and-channels)
- [Calling PDB procedures directly](#calling-pdb-procedures-directly)
- [Resources: fonts, brushes, patterns, gradients](#resources-fonts-brushes-patterns-gradients)
- [Reading pixels back](#reading-pixels-back)
- [Loading, saving, exporting](#loading-saving-exporting)
- [Displays, undo, progress](#displays-undo-progress)

## Preamble and types

```python
import gi
gi.require_version("Babl", "0.1")
gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")
from gi.repository import Babl, Gegl, Gimp, Gio, GLib

Gegl.init(None)          # needed before GEGL colours and buffers behave
```

`python-fu-eval` already imports `Gimp`, `Gegl`, `Babl`, `Gio` and `GLib` into the
namespace your script inherits, but import them yourself anyway — a script that only
works because of the host's imports is a script that breaks the first time it is run
anywhere else.

Types worth knowing:

| Type | What it is |
|---|---|
| `Gimp.Image` | a document; owns layers, channels, paths, the selection |
| `Gimp.Layer` / `Gimp.GroupLayer` / `Gimp.TextLayer` | layer kinds, all `Gimp.Drawable` |
| `Gimp.Channel` | a channel, also usable as a stored selection / mask |
| `Gimp.Path` | vector path (GIMP 2 called these Vectors) |
| `Gimp.DrawableFilter` | a live GEGL filter attached to a drawable |
| `Gegl.Color` | a colour; **stores linear RGB** (see below) |
| `Gio.File` | every file argument — `Gio.File.new_for_path("/abs/path")` |
| `Gimp.Unit` | `Gimp.Unit.pixel()`, `Gimp.Unit.inch()`, … |

## Colour — the linear/sRGB trap

`Gegl.Color` holds **linear** RGB. The two ways in are not equivalent, and picking the
wrong one silently washes every colour out:

```python
Gegl.Color.new("#1a73e8")            # parses sRGB/CSS — what you almost always want
c = Gegl.Color.new("black")
c.set_rgba(0.10, 0.45, 0.85, 1.0)    # LINEAR components — #1a73e8 is NOT (0.1,0.45,0.85)
```

`Gegl.Color.new("#1a73e8").get_rgba()` returns `(0.0103, 0.1714, 0.807, 1.0)` — the
linear form of that sRGB triple. So read colours back through Babl rather than
`get_rgba()`:

```python
srgb_u8 = Babl.format("R'G'B'A u8")
list(colour.get_bytes(srgb_u8).get_data())      # [26, 115, 232, 255] == #1a73e8
```

`get_bytes` insists on a `Babl.Object`; passing the format as a plain string raises
`TypeError: argument format: Expected Babl.Object, but got str`.

Foreground/background live on the context and every fill and stroke reads them:

```python
Gimp.context_set_foreground(Gegl.Color.new("#ffb703"))
Gimp.context_set_background(Gegl.Color.new("#0d1b2a"))
Gimp.context_set_opacity(100.0)      # 0–100
```

## Images, layers, groups

```python
image = Gimp.Image.new(1000, 1400, Gimp.ImageBaseType.RGB)   # or GRAY, INDEXED
layer = Gimp.Layer.new(image, "background", 1000, 1400,
                       Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
image.insert_layer(layer, None, 0)        # parent=None -> top level, position 0 = top
```

`Gimp.ImageType`: `RGB_IMAGE`, `RGBA_IMAGE`, `GRAY_IMAGE`, `GRAYA_IMAGE`,
`INDEXED_IMAGE`, `INDEXEDA_IMAGE`. Layer opacity is **0–100 float**, not 0–255.

```python
image.get_layers()                        # top-level layers, topmost first
layer.set_opacity(70.0)
layer.set_mode(Gimp.LayerMode.SCREEN)     # MULTIPLY, OVERLAY, ADDITION, …
layer.set_offsets(120, 300)               # position on the canvas
layer.get_offsets()                       # -> (True, x, y): success flag first
layer.set_visible(False)
layer.set_name("headline")

group = Gimp.GroupLayer.new(image, "chrome")
image.insert_layer(group, None, 0)
image.insert_layer(child, group, 0)       # into the group

copy = layer.copy(); image.insert_layer(copy, None, 0)
image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
image.flatten()
image.scale(500, 700)
image.resize(1200, 1600, 100, 100)        # canvas resize, layer keeps its size
layer.resize_to_image_size()
layer.transform_rotate_simple(Gimp.RotationType.DEGREES90, True, 0, 0)
```

Several getters return a leading success flag (`get_offsets`, `pick_color`,
`selection.bounds`, `histogram`). Unpack, don't index blindly.

## Selections

Selections belong to the image and every fill, filter and edit respects them, so
clearing up after yourself matters:

```python
image.select_rectangle(Gimp.ChannelOps.REPLACE, x, y, w, h)
image.select_round_rectangle(Gimp.ChannelOps.REPLACE, x, y, w, h, 20, 20)
image.select_ellipse(Gimp.ChannelOps.ADD, x, y, w, h)
image.select_polygon(Gimp.ChannelOps.REPLACE, [10.0, 10.0, 100.0, 10.0, 50.0, 90.0])
image.select_color(Gimp.ChannelOps.REPLACE, drawable, Gegl.Color.new("#1a73e8"))
image.select_contiguous_color(Gimp.ChannelOps.REPLACE, drawable, 40.0, 40.0)
image.select_item(Gimp.ChannelOps.REPLACE, path_or_layer)

Gimp.Selection.feather(image, 12.0)
Gimp.Selection.grow(image, 5); Gimp.Selection.shrink(image, 3)
Gimp.Selection.invert(image)
Gimp.Selection.all(image); Gimp.Selection.none(image)

ok, non_empty, x1, y1, x2, y2 = image.get_selection().bounds(image)
```

`Gimp.ChannelOps`: `ADD`, `SUBTRACT`, `REPLACE`, `INTERSECT`.

## Drawing: fills, gradients, brushes, paths

```python
layer.fill(Gimp.FillType.FOREGROUND)        # whole layer, ignores the selection
layer.edit_fill(Gimp.FillType.FOREGROUND)   # respects the selection
layer.edit_clear()
layer.edit_bucket_fill(Gimp.FillType.FOREGROUND, 15.0, False, False, 0, 100.0, 100.0)
```

`Gimp.FillType`: `FOREGROUND`, `BACKGROUND`, `WHITE`, `TRANSPARENT`, `PATTERN`,
`CIELAB_MIDDLE_GRAY`.

```python
Gimp.context_set_gradient_fg_bg_rgb()
layer.edit_gradient_fill(Gimp.GradientType.LINEAR, 0.0, False, 1.0, 0.0, True,
                         x1, y1, x2, y2)   # RADIAL, BILINEAR, CONICAL_SYMMETRIC, …
```

Paint tools take **one drawable and a flat `[x1, y1, x2, y2, …]` list** — passing a list
of drawables raises `TypeError: Expected Gimp.Drawable, but got list`:

```python
Gimp.context_set_brush(Gimp.Brush.get_by_name("2. Hardness 100"))
Gimp.context_set_brush_size(20.0)
Gimp.paintbrush_default(layer, [40.0, 40.0, 200.0, 200.0, 360.0, 60.0])
Gimp.pencil(layer, [20.0, 280.0, 380.0, 280.0])
Gimp.airbrush(layer, 60.0, [30.0, 150.0, 370.0, 150.0])
```

Paths, and stroking them:

```python
path = Gimp.Path.new(image, "outline")
image.insert_path(path, None, 0)
# BEZIER points come in triples per node: control-in, anchor, control-out.
path.stroke_new_from_points(Gimp.PathStrokeType.BEZIER,
                            [80.0, 80.0,  80.0, 80.0,  80.0, 80.0,
                             320.0, 80.0, 320.0, 80.0, 320.0, 80.0,
                             200.0, 240.0, 200.0, 240.0, 200.0, 240.0], True)
Gimp.context_set_line_width(6.0)
Gimp.context_set_stroke_method(Gimp.StrokeMethod.LINE)   # or PAINT_METHOD
layer.edit_stroke_item(path)
```

## Text layers

```python
font = Gimp.context_get_font()                    # the safe default
font = Gimp.Font.get_by_name("Sans-serif")        # returns None if absent!
text = Gimp.TextLayer.new(image, "GIMP\nBRIDGE", font, 150.0, Gimp.Unit.pixel())
image.insert_layer(text, None, 0)
text.set_color(Gegl.Color.new("#f8f9fa"))
text.set_justification(Gimp.TextJustification.CENTER)
text.set_line_spacing(-18.0); text.set_letter_spacing(2.0)
text.set_font_size(52.0, Gimp.Unit.pixel())
text.set_text("new copy")                          # relays out the layer
text.set_markup('<b>bold</b> and <i>italic</i>')   # Pango markup
text.set_offsets((image.get_width() - text.get_width()) // 2, 300)
```

A text layer sizes itself to its content, so centre it *after* setting the text, size
and spacing — `get_width()` before that measures the old layout. `Gimp.Font.get_by_name`
returning `None` surfaces much later as
`TypeError: Argument 2 does not allow None as a value` inside `TextLayer.new`; check the
font or use the context one.

## Filters — GEGL, destructive and not

GIMP 3's headline feature is non-destructive filters, and they are fully scriptable.
The user can still open, retune or delete them afterwards, which is why they are the
better default when working on someone's own artwork:

```python
blur = Gimp.DrawableFilter.new(layer, "gegl:gaussian-blur", "glow blur")
config = blur.get_config()
config.set_property("std-dev-x", 90.0)
config.set_property("std-dev-y", 90.0)
blur.update()                       # push config changes into the filter
blur.set_blend_mode(Gimp.LayerMode.NORMAL)
blur.set_opacity(0.6)               # 0–1 here, unlike layer opacity
layer.append_filter(blur)

layer.get_filters()                 # live filters, e.g. [<DrawableFilter 'glow blur'>]
blur.get_operation_name()           # 'gegl:gaussian-blur'
blur.delete()                       # remove it again
layer.merge_filters()               # bake every attached filter into pixels
```

To apply one destructively in a single step, skip `append_filter`:

```python
pixelize = Gimp.DrawableFilter.new(layer, "gegl:pixelize", "px")
pixelize.get_config().set_property("size-x", 20)
pixelize.update()
layer.merge_filter(pixelize)
```

Discover operations and their properties instead of guessing — GIMP 3.2 ships 261 GEGL
ops and the legacy `plug-in-gauss` style procedures are gone:

```python
[op for op in Gegl.list_operations() if "blur" in op]
[(p.name, p.value_type.name) for p in Gegl.Operation.list_properties("gegl:gaussian-blur")]
[p.name for p in Gimp.DrawableFilter.new(layer, "gegl:unsharp-mask", "s").get_config().list_properties()]
```

Useful ops: `gegl:gaussian-blur`, `gegl:unsharp-mask`, `gegl:dropshadow`,
`gegl:pixelize`, `gegl:brightness-contrast`, `gegl:hue-chroma`, `gegl:levels`,
`gegl:noise-reduction`, `gegl:motion-blur-linear`, `gegl:long-shadow`,
`gegl:color-overlay`, `gegl:edge-sobel`, `gegl:waterpixels`.

## Masks and channels

```python
mask = layer.create_mask(Gimp.AddMaskType.WHITE)   # BLACK, ALPHA, SELECTION, COPY…
layer.add_mask(mask)
mask.fill(Gimp.FillType.BACKGROUND)                # masks are drawables too
layer.remove_mask(Gimp.MaskApplyMode.APPLY)        # or DISCARD

channel = Gimp.Channel.new(image, "stored selection", w, h, 100.0,
                           Gegl.Color.new("#ffffff"))
image.insert_channel(channel, None, 0)
image.select_item(Gimp.ChannelOps.REPLACE, channel)
```

## Calling PDB procedures directly

Anything without a direct binding — script-fu scripts, file plug-ins, third-party
plug-ins — goes through the PDB with a config object:

```python
proc = Gimp.get_pdb().lookup_procedure("script-fu-drop-shadow")
config = proc.create_config()
config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
config.set_property("image", image)
config.set_core_object_array("drawables", [layer])     # NOT set_property
result = proc.run(config)
status = result.index(0)                               # Gimp.PDBStatusType
```

Two things bite here:

- **Arrays of GIMP objects need `set_core_object_array`.** `set_property("drawables",
  [layer])` raises `TypeError: could not convert [...] to type 'GimpCoreObjectArray'`.
- **Read them back with `result.get_core_object_array(i)`.** `result.index(i)` hands you
  an opaque `GBoxed` that is not iterable.

Introspect an unfamiliar procedure before calling it:

```python
proc = Gimp.get_pdb().lookup_procedure("file-jpeg-export")   # None if it doesn't exist
[(a.name, a.value_type.name) for a in proc.get_arguments()]
proc.get_blurb()
Gimp.get_pdb().query_procedures("", "", "", "", "", "", "", "")   # eight empty strings
```

Script-Fu-registered procedures inherit useless argument names (`adjustment`,
`adjustment-2`, `toggle`); `get_blurb()` and the GIMP *Procedure Browser* are the way to
find out what they mean.

## Resources: fonts, brushes, patterns, gradients

```python
def resource_names(procedure_name):
    proc = Gimp.get_pdb().lookup_procedure(procedure_name)
    config = proc.create_config()
    config.set_property("filter", "")
    return [r.get_name() for r in proc.run(config).get_core_object_array(1)]

resource_names("gimp-fonts-get-list")       # 2855 on a stock macOS GIMP 3.2
resource_names("gimp-brushes-get-list")
resource_names("gimp-patterns-get-list")
resource_names("gimp-gradients-get-list")
```

Resource names are **localised**: on a Hungarian GIMP the first gradient is
`Előtérből háttérbe (RGB)`, not `FG to BG (RGB)`. Look names up from this list rather
than hard-coding English ones, or use `Gimp.context_get_*` and the `*_fg_bg_*` helpers,
which are language-independent.

## Reading pixels back

```python
ok, colour = image.pick_color(image.get_layers(), 40.0, 40.0, True, False, 0.0)
#              ^ a LIST of drawables            x     y   sample_merged
list(colour.get_bytes(Babl.format("R'G'B'A u8")).get_data())

ok, mean, std_dev, median, pixels, count, percentile = layer.histogram(
    Gimp.HistogramChannel.VALUE, 0.0, 1.0)        # values on a 0–255 scale

buffer = layer.get_buffer()                       # GeglBuffer
extent = buffer.get_extent()                      # .width/.height — there is no get_width()
data = buffer.get(Gegl.Rectangle.new(0, 0, 4, 1), 1.0,
                  "R'G'B'A u8", Gegl.AbyssPolicy.NONE)
```

`get_buffer()` returns a live buffer: writing to it edits the layer, and
`drawable.update(x, y, w, h)` then tells GIMP what changed.

## Loading, saving, exporting

Every file argument is a `Gio.File`, and format is chosen by extension:

```python
image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(src))
Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image,
               Gio.File.new_for_path("/out/poster.xcf"), None)   # .png/.jpg/.tif/.webp too
```

There is no `Gimp.file_export`; `file_save` covers both, and `.xcf` is the one that keeps
layers, masks and non-destructive filters editable. For format options, call the export
plug-in directly:

```python
proc = Gimp.get_pdb().lookup_procedure("file-jpeg-export")
config = proc.create_config()
config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
config.set_property("image", image)
config.set_property("file", Gio.File.new_for_path("/out/photo.jpg"))
config.set_property("quality", 0.85)          # 0–1
proc.run(config)
```

Flatten a **duplicate** for flat exports so the live image keeps its stack:

```python
flat = image.duplicate(); flat.flatten()
Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, flat, Gio.File.new_for_path(png), None)
flat.delete()
```

## Displays, undo, progress

```python
Gimp.Display.new(image)      # make the image visible — the point of a live session
Gimp.displays_flush()        # repaint after scripted edits; nothing updates without it

image.undo_group_start()     # one undo step for the whole build
...
image.undo_group_end()

Gimp.progress_init("rendering")
Gimp.progress_update(0.5)
Gimp.message("something the user should see")   # status bar / error console

Gimp.get_images()            # every open image
image.delete()               # close it (discards unsaved changes — see recipes.md)
```
