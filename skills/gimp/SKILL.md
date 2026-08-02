---
name: gimp
description: 'Remote-control a running GIMP (the open-source image editor) by Python script through its built-in Script-Fu server — build documents and layer stacks, fill, gradient and brush-stroke drawables, add text layers, attach non-destructive GEGL filters, cut out with masks and selections, retouch photos, and export PNG/JPEG/TIFF/GIF/.xcf or batch-convert whole folders in the session the user is looking at. Use whenever the user wants to create or edit a GIMP document (.xcf), composite, retouch or resize a raster image, batch-process a folder of images, script or automate GIMP, export layers separately, or says "GIMP", "xcf", "gimp script", "batch resize these photos", "open this in GIMP" — even if they do not mention scripting. Also covers Hungarian: "csinálj egy képet GIMP-ben", "vezéreld a GIMP-et", "rétegek", "exportáld PNG-be", "kötegelt átméretezés". Not for natural-media painting (use krita or rebelle), vector and layout design (use affinity), or keyframed motion graphics (use cavalry).'
summary: "remote-control a running GIMP by Python through its built-in Script-Fu server — layer stacks, selections and masks, brush and gradient drawing, text layers, non-destructive GEGL filters, and PNG/JPEG/.xcf export or batch conversion in the live session"
category: design-automation
risk: medium
tags:
    - gimp
    - raster
    - image-editing
    - layers
    - scripting
---

# GIMP Control

GIMP (`/Applications/GIMP.app`) embeds Python 3 and exposes its whole document model
through **libgimp** over GObject Introspection (`gi.repository.Gimp`), with **GEGL** for
pixels and filters. Drive it through GIMP's own **Script-Fu server** — a TCP endpoint
GIMP ships with, so there is nothing to install — which hands each script to GIMP's
`python-fu-eval`. The script runs against the *live* GIMP: the canvas updates, the layer
stack is the one the user is looking at, and nothing happens headless. Every call in
this skill was run against **GIMP 3.2.4**.

- [scripts/gimp-send.sh](scripts/gimp-send.sh) — send a `.py` file (or `-c 'inline code'`)
  and print its captured output; `--ping` checks the connection, `--scheme` evaluates
  raw Script-Fu.
- [scripts/gimp-start.sh](scripts/gimp-start.sh) — launch the GIMP GUI with the
  Script-Fu server listening, and wait until it answers.
- [scripts/gimp_client.py](scripts/gimp_client.py) — the wire protocol, used by both.
- [scripts/example-poster.py](scripts/example-poster.py) — a complete
  build → verify → export script to copy the shape from.
- [references/api-reference.md](references/api-reference.md) — the version-checked
  libgimp API (images, layers, selections, drawing, text, GEGL filters, PDB calls,
  pixel readback, export). **Read it before writing anything past the cheatsheet below.**
- [references/recipes.md](references/recipes.md) — working on the user's own image,
  batch folders, per-layer export, masks, animation, and what the API cannot do.

## The control loop

1. **Check the connection**: `bash scripts/gimp-send.sh --ping` →
   `{"ok": true, "bridge": "gimp", "port": 10008, "reply": "3.2.4 | open images: 2"}`.

   If nothing answers, there are two different situations and they need different moves:

   - **GIMP is not running** → `bash scripts/gimp-start.sh` starts the GUI with the
     server switched on and waits for it. This opens a window on the user's screen, so
     say that you are doing it.
   - **GIMP is running without the server** → you cannot switch it on remotely, and you
     must not start a second instance to get around that: two GIMPs share one config
     directory and the user's unsaved work is in the one already open. Ask them for one
     click: **Filters ▸ Development ▸ Script-Fu ▸ Start Server…**, listening on
     `127.0.0.1`, port `10008`. (*Development* stays English on a localised GIMP; on a
     Hungarian one the path reads Szűrők ▸ Development ▸ Script-Fu ▸ Kiszolgáló
     indítása….)

2. **Write a build script** to the scratchpad and send it:
   `OUT=/path/to/outdir bash scripts/gimp-send.sh /path/build.py`. `OUT` arrives both as
   a global and as `os.environ["OUT"]`; `GIMP_SEND_TIMEOUT=600` (seconds) covers batches
   and big exports.

3. **Read the feedback.** The sender returns the script's captured stdout/stderr, and on
   failure the Python traceback, exiting non-zero — so `print(...)` is your channel back.
   Nothing else reports: GIMP's own error console stays inside the app.

4. **Look at the result.** `image.get_thumbnail(w, h, Gimp.PixbufTransparency.SMALL_CHECKS)`
   renders the composited image straight to a PNG you can Read. Do this at the end of
   every build script — one line, and it catches what no assertion will.

5. **Iterate, then deliver.** Fix the script and re-send. Scripts must be
   **re-runnable**: create a fresh image per version rather than mutating the one already
   open, so a re-send cannot stack layers onto the previous attempt.

Each send is a fresh `python-fu-eval` process, so nothing persists between sends except
what is in GIMP (open images) or on disk. Round-trip is roughly a second — cheap enough
to probe with a throwaway send rather than guess an API.

## Scripting cheatsheet

```python
import gi
gi.require_version("Babl", "0.1"); gi.require_version("Gegl", "0.4")
gi.require_version("Gimp", "3.0")
from gi.repository import Babl, Gegl, Gimp, Gio
Gegl.init(None)
```

### Image and layer stack

```python
image = Gimp.Image.new(1000, 1400, Gimp.ImageBaseType.RGB)
layer = Gimp.Layer.new(image, "background", 1000, 1400,
                       Gimp.ImageType.RGBA_IMAGE, 100.0, Gimp.LayerMode.NORMAL)
image.insert_layer(layer, None, 0)      # parent=None -> top level; 0 = topmost
layer.set_opacity(70.0)                 # 0–100 float, not 0–255
layer.set_mode(Gimp.LayerMode.SCREEN)
Gimp.Display.new(image)                 # show it — the user watches the build happen
Gimp.displays_flush()                   # nothing repaints without this
```

To work on what the user already has: `Gimp.get_images()[0]`, most recently active
first. Duplicate it before destructive work — see
[recipes.md](references/recipes.md#work-on-the-image-the-user-already-has-open).

### Colour: sRGB in, sRGB out

`Gegl.Color` stores **linear** RGB, so the constructor and the setter are not the same
thing and the difference is a visibly washed-out image:

```python
Gegl.Color.new("#1a73e8")                 # parses sRGB — use this
colour.set_rgba(0.10, 0.45, 0.85, 1.0)    # LINEAR components — rarely what you meant
list(colour.get_bytes(Babl.format("R'G'B'A u8")).get_data())   # [26,115,232,255]
Gimp.context_set_foreground(Gegl.Color.new("#ffb703"))
```

### Selections, fills, drawing

```python
image.select_rectangle(Gimp.ChannelOps.REPLACE, x, y, w, h)   # also ellipse, polygon,
layer.edit_fill(Gimp.FillType.FOREGROUND)                      # round_rectangle, color
Gimp.Selection.none(image)               # every later edit respects the selection

layer.fill(Gimp.FillType.FOREGROUND)     # whole layer, ignores the selection
Gimp.context_set_gradient_fg_bg_rgb()
layer.edit_gradient_fill(Gimp.GradientType.LINEAR, 0.0, False, 1.0, 0.0, True,
                         x1, y1, x2, y2)

Gimp.context_set_brush(Gimp.Brush.get_by_name("2. Hardness 100"))
Gimp.context_set_brush_size(20.0)
Gimp.paintbrush_default(layer, [40.0, 40.0, 200.0, 200.0])   # ONE drawable, flat x/y list
```

### Text

```python
font = Gimp.context_get_font()                 # safer than naming one: get_by_name
text = Gimp.TextLayer.new(image, "GIMP", font, 150.0, Gimp.Unit.pixel())
image.insert_layer(text, None, 0)
text.set_color(Gegl.Color.new("#f8f9fa"))
text.set_justification(Gimp.TextJustification.CENTER)
text.set_offsets((image.get_width() - text.get_width()) // 2, 300)   # measure AFTER
```

### Filters — prefer non-destructive

GIMP 3 filters stay live and editable, which is the right default on someone else's
artwork:

```python
blur = Gimp.DrawableFilter.new(layer, "gegl:gaussian-blur", "glow blur")
config = blur.get_config()
config.set_property("std-dev-x", 90.0); config.set_property("std-dev-y", 90.0)
blur.update()                            # push config into the filter
layer.append_filter(blur)                # or layer.merge_filter(blur) to bake it in
```

Discover ops and property names instead of guessing — `Gegl.list_operations()` and
`Gegl.Operation.list_properties("gegl:gaussian-blur")`. The legacy `plug-in-gauss`
family is gone in GIMP 3.

### Anything without a binding: the PDB

```python
proc = Gimp.get_pdb().lookup_procedure("script-fu-drop-shadow")   # None if absent
config = proc.create_config()
config.set_property("run-mode", Gimp.RunMode.NONINTERACTIVE)
config.set_property("image", image)
config.set_core_object_array("drawables", [layer])     # NOT set_property
result = proc.run(config)
```

### Export

```python
Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, image,
               Gio.File.new_for_path(OUT + "/poster.xcf"), None)   # .png/.jpg/... too
flat = image.duplicate(); flat.flatten()                 # flatten a copy, not the original
Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, flat,
               Gio.File.new_for_path(OUT + "/poster.png"), None)
flat.delete()
```

`.xcf` keeps every layer, mask and live filter editable for the user; ship it alongside
the flat export unless they said otherwise. Format options (JPEG quality, GIF timing)
come from calling the export plug-in through the PDB — see
[api-reference.md](references/api-reference.md#loading-saving-exporting).

## Verification

- **Returned stdout** is the immediate signal — `print(...)` comes straight back and a
  failure returns the traceback with a non-zero exit.
- **A thumbnail PNG** is the visual check: save
  `image.get_thumbnail(500, 700, Gimp.PixbufTransparency.SMALL_CHECKS)` into `$OUT` and
  Read it. It is the composited image, so it is honest about blend modes and filters in
  a way a layer-by-layer description is not.
- **Numbers**: `image.pick_color([...], x, y, True, False, 0.0)` sampled through
  `Babl.format("R'G'B'A u8")` proves a colour landed exactly; `layer.histogram(...)`
  gives mean/median on a 0–255 scale. Dump size, layer names, offsets, modes and
  attached filters as `metrics.json` and Read that rather than eyeballing the stack.
- **Hand-off**: the exported PNG/JPEG opens anywhere; the `.xcf` keeps the work editable.

## Gotchas

- **`Gegl.Color.set_rgba` is linear, `Gegl.Color.new("#hex")` is sRGB.** Mixing them up
  silently lightens every colour; read values back through
  `get_bytes(Babl.format("R'G'B'A u8"))`, not `get_rgba()`.
- **`set_core_object_array` for arrays of GIMP objects.** `config.set_property(
  "drawables", [layer])` raises `could not convert [...] to type 'GimpCoreObjectArray'`,
  and reading one back needs `result.get_core_object_array(i)` — `result.index(i)`
  returns a `GBoxed` that will not iterate.
- **Paint calls take one drawable, not a list** (`Gimp.paintbrush_default(layer, pts)`),
  while `pick_color` takes a *list* of drawables. The asymmetry is real.
- **`Gimp.Font.get_by_name` returns `None` for a missing font**, and the failure only
  surfaces inside `TextLayer.new` as `Argument 2 does not allow None as a value`. Use
  `Gimp.context_get_font()` unless the user named a font, and check the return.
- **Text layers resize themselves** — centre and position them after setting text, size
  and spacing, or you are measuring the previous layout.
- **`Gimp.displays_flush()` after edits**, or the user stares at a stale canvas and you
  both think the script did nothing.
- **Success flags come first** in `get_offsets`, `pick_color`, `histogram` and
  `selection.bounds`. Unpack the tuple; don't index into it blindly.
- **Resource names are localised** — on a Hungarian GIMP the gradients are
  `Előtérből háttérbe (RGB)`, not `FG to BG (RGB)`. List them at runtime
  (`gimp-*-get-list` via the PDB) instead of hard-coding English names.
- **`image.delete()` discards unsaved changes without asking.** Call it only on images
  your own script created; never on the user's.
- **Group edits with `image.undo_group_start()` / `undo_group_end()`** so one Ctrl+Z
  undoes the whole build rather than four hundred individual operations.
- **No state survives a send** — each one is a new `python-fu-eval` process. Version
  your images (`"poster_v2"`) so re-runs don't fight the previous attempt.
- **`--batch` needs `--batch-interpreter` in GIMP 3**; without it GIMP prints a list of
  interpreters and quits. `gimp-start.sh` already passes it.
- **A dead GIMP can leave the port bound.** The `script-fu-server` plug-in is its own
  process and outlives a quitting GIMP for a while, so a bare port check says "up" when
  nothing is behind it. `--ping` sees through this (the connection closes mid-reply, and
  the orphan then exits) — if it reports that, just start GIMP again.
- **GIMP 2.10 tutorials do not port.** `gimpfu`, `pdb.gimp_*`, RGB tuples and the
  `plug-in-gauss` filters are all gone; check `lookup_procedure` for `None` before
  trusting a procedure name you read somewhere.
- **Tools are not scriptable** — no transform widget, no free select, no menu-action
  trigger. Fills, paint calls, selections and GEGL filters are the whole vocabulary; see
  [recipes.md](references/recipes.md#what-the-api-cannot-do).

## Security

There is nothing to install here, but starting the Script-Fu server still turns GIMP into
a **code-execution server**. Say so before asking for that click.

- The server listens on `127.0.0.1:10008` and hands whatever arrives to `python-fu-eval` —
  arbitrary Python with the user's privileges, over the user's open images. It carries **no
  authentication**: every local process, and every other user on a shared machine, can
  drive GIMP through it.
- **Always 127.0.0.1.** The Start Server dialog accepts any listen address, and a server
  bound to `0.0.0.0` or a LAN address is remote code execution for the whole network.
  `gimp-start.sh` pins loopback; if the user starts it by hand, tell them the address.
- It is not HTTP — the protocol is length-prefixed with a `G` magic byte, so a browser's
  request is rejected at the first byte. That is a side effect of the wire format, not an
  origin check.
- **To stop it, quit GIMP.** The port can stay bound briefly after GIMP exits while the
  plug-in process winds down, so a port check is not proof anything is live — `--ping`
  is (`gimp-send.sh --ping`).
