# GIMP bridge recipes

Working patterns for the bridge in [SKILL.md](../SKILL.md). Each one assumes the
preamble from [api-reference.md](api-reference.md) and an `OUT` directory.

- [Work on the image the user already has open](#work-on-the-image-the-user-already-has-open)
- [Batch-process a folder](#batch-process-a-folder)
- [Export every layer as its own file](#export-every-layer-as-its-own-file)
- [Photo adjustments as a non-destructive stack](#photo-adjustments-as-a-non-destructive-stack)
- [Cut something out with a mask](#cut-something-out-with-a-mask)
- [Learn an unfamiliar filter or procedure](#learn-an-unfamiliar-filter-or-procedure)
- [Animation and layer-per-frame GIFs](#animation-and-layer-per-frame-gifs)
- [The Script-Fu escape hatch](#the-script-fu-escape-hatch)
- [Why not to start a second GIMP](#why-not-to-start-a-second-gimp)
- [What the API cannot do](#what-the-api-cannot-do)

## Work on the image the user already has open

This is the case that makes a live session worth driving, and the one where a mistake
costs someone real work. Scripted edits go into GIMP's undo history only if you group
them, and a mis-aimed script can still be hard to unpick — so branch first:

```python
images = Gimp.get_images()
if not images:
    raise SystemExit("no image open in GIMP — ask the user to open one")
source = images[0]                      # most recently active first
print("working on:", source.get_name(), source.get_file() and source.get_file().get_path())

work = source.duplicate()               # the user's original is left untouched
work.set_file(Gio.File.new_for_path(os.path.join(OUT, "retouched.xcf")))
Gimp.Display.new(work)
work.undo_group_start()
...
work.undo_group_end()
Gimp.displays_flush()
```

Editing `source` in place is fine when the user asked for exactly that — wrap it in
`undo_group_start()` / `undo_group_end()` so one Ctrl+Z reverses the whole thing, and say
in your reply which image you touched.

`image.delete()` closes an image and **discards unsaved changes without asking**. Only
ever call it on images your own script created.

## Batch-process a folder

Still through the live session — open, edit, export, close, one file at a time so
memory does not grow without bound:

```python
import glob, os

sources = sorted(glob.glob("/photos/*.jpg"))
results = []
for index, path in enumerate(sources):
    image = Gimp.file_load(Gimp.RunMode.NONINTERACTIVE, Gio.File.new_for_path(path))
    image.flatten()
    image.scale(1600, int(1600 * image.get_height() / image.get_width()))

    layer = image.get_layers()[0]
    sharpen = Gimp.DrawableFilter.new(layer, "gegl:unsharp-mask", "sharpen")
    sharpen.get_config().set_property("std-dev", 1.5)
    sharpen.update()
    layer.merge_filter(sharpen)

    out = os.path.join(OUT, os.path.splitext(os.path.basename(path))[0] + "_web.jpg")
    proc = Gimp.get_pdb().lookup_procedure("file-jpeg-export")
    config = proc.create_config()
    config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
    config.set_property("image", image)
    config.set_property("file", Gio.File.new_for_path(out))
    config.set_property("quality", 0.85)
    proc.run(config)

    image.delete()                       # ours, so closing it is safe
    results.append(out)
    Gimp.progress_update((index + 1) / len(sources))

print(json.dumps({"written": results}, indent=1))
```

Batches outrun the default send timeout long before they outrun GIMP: set
`GIMP_SEND_TIMEOUT` to something generous (`600`) for anything over a handful of files.
Don't add `Gimp.Display.new` inside the loop — a hundred windows is not a feature.

## Export every layer as its own file

```python
image = Gimp.get_images()[0]
written = []
for index, layer in enumerate(image.get_layers()):
    single = image.duplicate()
    # Index, not name: layer names are not unique, and "bg" would export twice.
    for position, other in enumerate(single.get_layers()):
        other.set_visible(position == index)
    single.flatten()
    safe = layer.get_name().replace("/", "_").strip() or "layer_%02d" % index
    path = os.path.join(OUT, "%02d_%s.png" % (index, safe))
    Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, single,
                   Gio.File.new_for_path(path), None)
    single.delete()
    written.append(path)
print(written)
```

`image.get_layers()` is top level only — recurse through `group.get_children()` when the
document has groups. `flatten()` composites onto the image's background, so layers with
transparency come out on white; keep the alpha by exporting the duplicate without
flattening it, or by adding an alpha-preserving flatten
(`single.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)`).

## Photo adjustments as a non-destructive stack

Filters the user can still retune are strictly better than baked pixels on their own
photos, and it costs nothing to build them that way:

```python
layer = image.get_layers()[0]
for op, props in [
    ("gegl:brightness-contrast", {"brightness": 0.05, "contrast": 1.12}),
    ("gegl:hue-chroma",          {"chroma": 8.0}),
    ("gegl:unsharp-mask",        {"std-dev": 1.2, "scale": 0.6}),
]:
    f = Gimp.DrawableFilter.new(layer, op, op.split(":")[1])
    config = f.get_config()
    for name, value in props.items():
        config.set_property(name, value)
    f.update()
    layer.append_filter(f)
Gimp.displays_flush()
```

Then `layer.merge_filters()` only if the user asked for a flattened result.

## Cut something out with a mask

```python
image.select_contiguous_color(Gimp.ChannelOps.REPLACE, layer, 5.0, 5.0)   # sample the bg
Gimp.Selection.invert(image)
Gimp.Selection.feather(image, 2.0)
mask = layer.create_mask(Gimp.AddMaskType.SELECTION)
layer.add_mask(mask)
Gimp.Selection.none(image)
```

`AddMaskType.SELECTION` is the reliable route: it turns whatever is selected into a mask
instead of trying to erase pixels, so the cut-out stays adjustable.

## Learn an unfamiliar filter or procedure

Don't guess property names — GEGL will accept a wrong one silently in some builds and
raise in others:

```python
print([op for op in Gegl.list_operations() if "shadow" in op])
print([(p.name, p.value_type.name, p.get_blurb())
       for p in Gegl.Operation.list_properties("gegl:dropshadow")])

proc = Gimp.get_pdb().lookup_procedure("script-fu-drop-shadow")
print(proc.get_blurb())
print([(a.name, a.value_type.name, a.get_blurb()) for a in proc.get_arguments()])
```

One probe send costs a second and saves a round of confused debugging. The same query
run from GIMP's own **Filters ▸ Development ▸ Procedure Browser** shows the identical
data if the user prefers to look.

## Animation and layer-per-frame GIFs

GIMP models animation as one layer per frame, with timing in the layer name:

```python
for index, frame in enumerate(frames):
    layer = Gimp.Layer.new(image, "frame %02d (100ms) (replace)" % index,
                           W, H, Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
    image.insert_layer(layer, None, 0)
    ...

proc = Gimp.get_pdb().lookup_procedure("file-gif-export")
config = proc.create_config()
config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
config.set_property("image", image)
config.set_property("file", Gio.File.new_for_path(os.path.join(OUT, "anim.gif")))
config.set_property("as-animation", True)
config.set_property("loop", True)
proc.run(config)
```

Check the argument list first — GIF export options have moved between GIMP versions.
For anything beyond a short loop, export PNG frames and hand them to ffmpeg.

## The Script-Fu escape hatch

The transport speaks Script-Fu natively, so when a query is awkward through GObject
Introspection it is often one line of Scheme:

```bash
bash scripts/gimp-send.sh --scheme '(car (gimp-version))'
bash scripts/gimp-send.sh --scheme '(vector-length (car (gimp-get-images)))'
```

In GIMP 3's Script-Fu a PDB call returns its values as a plain list — `(car
(gimp-version))` is the version string. GIMP 2 tutorials show an extra leading status
element; that is gone, and following them produces
`Error: car: argument 1 must be: pair`.

Keep real work in Python: Scheme has no exception handling worth the name here, and the
server returns only the last value.

## Why not to start a second GIMP

`gimp --no-interface --batch ...` looks like the obvious way to run a conversion, and it
is the wrong move whenever a GIMP is already open. Two instances share one config
directory and one set of resource files; the second one to exit overwrites the first
one's settings, and plug-in and font caches get rebuilt under both. The user's session —
the one with unsaved work in it — is the one that loses. Everything in this skill,
including plain format conversion, runs in the session that is already there.

The one legitimate use for a separate process is when **no** GIMP is running and the
user explicitly wants a headless job. Even then, prefer starting the GUI with
`scripts/gimp-start.sh` and driving it: you get to look at what you built.

## What the API cannot do

- **Tools are not scriptable.** There is no API for the transform widget, the free
  select tool, warp, or anything that lives in the tool options. Paint operations
  (`Gimp.paintbrush_default`, `Gimp.pencil`, `Gimp.airbrush`), fills, and GEGL filters
  are the whole vocabulary.
- **No menu-action trigger.** Unlike Krita, GIMP has no `action(id).trigger()`; anything
  in a menu is reachable only if it is registered in the PDB.
- **Legacy `plug-in-*` filters are gone.** GIMP 3 removed `plug-in-gauss` and friends in
  favour of `gegl:` operations; scripts copied from 2.10 tutorials fail with a `None`
  from `lookup_procedure`.
- **No persistent state between sends.** Each send is a fresh `python-fu-eval` process.
  Anything you want to keep lives in the image, in a file, or nowhere.
- **`Gimp.Image.get_name()` is a display name**, localised and possibly `[Névtelen]` /
  `[Untitled]`. Identify images by `get_file()` or by the id you created them with.
