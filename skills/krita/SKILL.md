---
name: krita
description: 'Remote-control a running Krita (the open-source digital painting app) by Python script through a small local bridge — build documents, paint real brush strokes with the current preset or push QPainter pixels, stack and blend layers, add vector/SVG text, run filters and masks, animate frames, and export PNG/JPEG/TIFF/.kra or batch-convert whole folders. Use whenever the user wants to create or edit a Krita document (.kra), composite or retouch a raster image, batch-export layers or files, script or automate Krita, render an animation frame sequence, or says "Krita", "paint layer", "krita script", "batch export from Krita", "open this .kra" — even if they don''t mention scripting. Also covers Hungarian: "csinálj egy képet Kritában", "vezéreld a Kritát", "rétegek", "exportáld PNG-be", "kötegelt export". Not for natural-media painting simulation (use rebelle), vector/layout design (use affinity), or keyframed motion graphics (use cavalry).'
summary: "remote-control a running Krita by Python through a local bridge — layer stacks, brush-engine strokes and QPainter pixels, SVG vector text, filters, masks, animation frames, and PNG/JPEG/.kra export or batch conversion in the running session"
category: design-automation
risk: medium
tags:
    - krita
    - painting
    - raster
    - layers
    - scripting
---

# Krita Control

Krita (`/Applications/krita.app`) embeds Python 3 and exposes its whole document model
through the **libkis** API (`from krita import *`), with **PyQt5** available for pixel work.
Drive it through the **Krita Bridge** — a pykrita plugin running inside a *live* Krita that
executes whatever script is POSTed to `127.0.0.1:8737`. Because the script runs in the
running session on the GUI thread, the canvas updates as you build, the user watches it
happen, and the main-thread-only parts of the API are safe. Every call below was run
against **Krita 5.3.3** (Python 3.13, PyQt5 5.15.11).

- [scripts/krita-install-bridge.sh](scripts/krita-install-bridge.sh) — install the bridge
  plugin into the user's resource folder and enable it in `kritarc` (one-time).
- [scripts/krita_bridge/](scripts/krita_bridge/krita_bridge.py) — the plugin itself; also
  pasteable into **Tools ▸ Scripts ▸ Scripter** for a one-off session.
- [scripts/krita-send.sh](scripts/krita-send.sh) — send a `.py` file (or `-c 'inline code'`)
  and print its captured output; `--ping` checks the bridge is up.
- [scripts/example-poster.py](scripts/example-poster.py) — a complete
  build → verify → export script to copy from.
- [references/api-reference.md](references/api-reference.md) — the version-checked libkis
  API (Krita, Document, Node, Selection, filters, animation, export). **Read it before
  writing anything past the cheatsheet below.**
- [references/recipes.md](references/recipes.md) — batch export, layer extraction,
  animation frames → video, why not to start a second Krita, and what the API cannot do.

## The control loop

1. **Make sure the bridge is up**: `bash scripts/krita-send.sh --ping` →
   `{"ok": true, "bridge": "krita", "version": "5.3.3 (git 858d352)", "documents": [...]}`.
   If nothing answers, either Krita isn't running (ask the user to start it — the bridge
   auto-starts with it once installed) or the plugin isn't installed yet:

   ```bash
   bash scripts/krita-install-bridge.sh     # Krita must be quit: it rewrites kritarc on exit
   ```

   The script copies the plugin into the pykrita folder and writes `enable_krita_bridge=true`
   into `kritarc`'s `[python]` group — the same thing the **Settings ▸ Configure Krita ▸
   Python Plugin Manager** checkbox does. Editing another app's config counts as a
   user-level change and some setups will refuse to let you run it; hand the user the
   one-liner instead of working around the refusal. For a session where nothing may be
   installed at all, they can paste
   [krita_bridge.py](scripts/krita_bridge/krita_bridge.py) into
   **Tools ▸ Scripts ▸ Scripter** and press Ctrl+R — same bridge, gone at quit.

2. **Write a build script** to the scratchpad and send it:
   `OUT=/path/to/outdir bash scripts/krita-send.sh /path/build.py`. `Krita` and `OUT` are
   pre-injected into the script's namespace (`OUT` also as `os.environ["OUT"]`), and
   `KRITA_SEND_TIMEOUT=600` (seconds) covers slow exports.

3. **Read the feedback.** The bridge returns the script's captured stdout/stderr, and on
   failure the Python traceback — so `print(...)` is your channel back. Nothing else
   reports: Krita's own log window stays inside the app.

4. **Look at the result.** `doc.projection(0, 0, w, h)` hands back a `QImage` of the merged
   canvas — save it and Read the PNG. That is cheaper and more honest than a screenshot,
   because it is exactly what an export would produce.

5. **Iterate, then deliver**: fix the script, re-send. Scripts must be **re-runnable** —
   create a fresh document per version rather than mutating the one already open, so a
   re-send can't stack layers onto the previous attempt.

**Everything goes through the live session.** Don't launch a second Krita from the shell —
no `krita --export`, no `--export-sequence`, no headless instance in the background. Two
Krita processes fight over the same resource database and `kritarc`, and the one the user
is working in loses; a batch job that pops up its own app also steals focus and hides its
failures from both of you. Plain format conversion is a bridge script too — open, export,
close, in the session that is already running (see
[references/recipes.md](references/recipes.md#batch-process-a-folder)).

## Scripting cheatsheet

`Krita.instance()` is the application; everything hangs off it. Sizes are pixels, colours
depend on the document's colour space, and `doc.setBatchmode(True)` is what stops export
and save calls from popping dialogs at the user.

### Document and layer stack

```python
from krita import Krita, InfoObject
app = Krita.instance()
doc = app.createDocument(1200, 1600, "poster_v1", "RGBA", "U8", "", 300.0)
app.activeWindow().addView(doc)          # show it — the user sees the build happen
doc.setBatchmode(True)                   # no dialogs on export/save

layer = doc.createNode("background", "paintlayer")   # grouplayer, filterlayer,
doc.rootNode().addChildNode(layer, None)             # filllayer, clonelayer, …
layer.setBlendingMode("multiply")        # Krita's blend-mode ids, not CSS names
layer.setOpacity(180)                    # 0–255, not a percentage
```

A new document already contains one paint layer, **named in the user's language**
(`Háttér` on a Hungarian Krita) — take it as `doc.rootNode().childNodes()[0]`, never by
name. Work on the open document instead with `doc = app.activeDocument()`, or open a file
with `doc = app.openDocument(path)` (add a view to make it visible), and `doc.close()`
when a batch is done — every open document keeps its whole image in memory.

### Brush strokes with the real paint engine

`Node.paint*` runs the current brush preset through the same paint ops as a tablet stroke,
so textured, watercolour and pattern presets behave as they do by hand:

```python
from krita import ManagedColor
from PyQt5.QtCore import QPoint, QRectF
from PyQt5.QtGui import QColor

view = app.activeWindow().addView(doc)           # paint* needs a view
presets = app.resources("preset")
view.setCurrentBrushPreset(presets["b) Basic-5 Size"])   # names include the "b) " prefix
view.setBrushSize(40); view.setPaintingOpacity(0.9)
view.setForeGroundColor(ManagedColor.fromQColor(QColor("#ff6b35")))

print(layer.paintAbility())              # expect "PAINT" before a long stroke loop
layer.paintLine(QPoint(120, 200), QPoint(900, 640), 1.0, 0.3, "ForegroundColor")
layer.paintEllipse(QRectF(300, 300, 400, 400), "ForegroundColor", "None")
```

`paintLine` takes **`QPoint`** — a `QPointF` raises `TypeError`, even though the rect-based
calls want `QRectF`. Without a view `paintAbility()` reports `UNPAINTABLE` and nothing is
drawn, and everything inherits the user's active preset, colour and blending mode, so set
what matters explicitly. For geometry that must look identical every run, draw it with
QPainter instead:

### Pixels: paint with QPainter, push once

Deterministic imagery is drawn into a `QImage` and pushed into a paint layer in one go.
Krita's RGBA8 space expects **BGRA** bytes, which is exactly the in-memory layout of
`QImage.Format_ARGB32` on little-endian machines, so no channel swapping is needed:

```python
from PyQt5.QtCore import QByteArray, QPointF, Qt
from PyQt5.QtGui import QColor, QImage, QPainter

img = QImage(doc.width(), doc.height(), QImage.Format_ARGB32)
img.fill(Qt.transparent)
p = QPainter(img)
p.setRenderHint(QPainter.Antialiasing)
p.setBrush(QColor("#ff6b35")); p.setPen(Qt.NoPen)
p.drawEllipse(QPointF(600, 500), 260, 260)
p.end()

ptr = img.constBits(); ptr.setsize(img.byteCount())
layer.setPixelData(QByteArray(ptr.asstring()), 0, 0, img.width(), img.height())
```

`node.pixelData(x, y, w, h)` reads the same buffer back, so an existing layer can be
round-tripped through `QImage` for analysis or retouching.

### Vector and text

Text is vector work in Krita, and the reliable way in is SVG:

```python
vec = doc.createVectorLayer("headline")
doc.rootNode().addChildNode(vec, None)
vec.addShapesFromSvg('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1600">'
                     '<text x="90" y="1320" fill="#f5f5f5" font-family="Helvetica" '
                     'font-size="150">KRITA</text></svg>')
```

### Filters, selections, masks

```python
f = app.filter("blur")                   # bind it: a chained temporary takes its
cfg = f.configuration()                  # InfoObject down with it (see below)
cfg.setProperty("halfWidth", 40); cfg.setProperty("halfHeight", 40)
f.setConfiguration(cfg)
f.apply(layer, 0, 0, doc.width(), doc.height())    # destructive, on that node

from krita import Selection
sel = Selection(); sel.select(100, 100, 400, 400, 255)   # x, y, w, h, selectedness
doc.setSelection(sel)                    # filters and edits then respect it
```

Filter ids are literal strings from `app.filters()` and several contain spaces
(`"gaussian blur"`); a wrong id returns `None` rather than raising. Property names differ
per filter — `f.configuration().properties()` prints the defaults, which is the fastest way
to learn one. A non-destructive alternative is a filter mask or filter layer
(`doc.createFilterMask` / `doc.createFilterLayer`) — see the API reference.

### Refresh before you look

Krita composites asynchronously. Anything that reads or writes the merged image —
`projection()`, `thumbnail()`, `exportImage()`, `save()` — needs the projection to be
current first:

```python
doc.refreshProjection()
doc.waitForDone()
```

### Export and save

```python
doc.projection(0, 0, doc.width(), doc.height()).save(OUT + "/check.png")   # for you to Read
doc.exportImage(OUT + "/poster.png", InfoObject())    # PNG/JPEG/TIFF/WEBP by extension
doc.saveAs(OUT + "/poster.kra")                       # re-editable, keeps the layer stack
doc.waitForDone()
```

Animation, per-layer export, and batch folder processing are in
[references/recipes.md](references/recipes.md).

## Verification

- **Returned stdout** is the immediate signal — `print(...)` comes straight back through
  the sender; a failure returns the traceback and exits non-zero.
- **A projection PNG** is the visual check: save `doc.projection(...)` (scaled down is
  fine) into `$OUT` and Read it. Do this at the end of every build script — it is one line
  and it catches the errors that no assertion will.
- **Numbers**: dump size, resolution, and the layer list (name, type, bounds, blend mode,
  opacity) as `metrics.json` and Read it, rather than eyeballing the stack.
- **Hand-off**: the exported PNG/JPEG opens anywhere; the saved `.kra` keeps every layer
  editable for the user.

## Gotchas

- **The bridge runs in the live session**, so state persists between sends: open documents,
  the active view, and selections all stick. Version your documents
  (`createDocument(..., "poster_v2", ...)`) so a re-send doesn't fight the previous one.
- **`setBatchmode(True)` before any export or save** — otherwise Krita may block on a
  format-options dialog that nobody is there to click, and the send times out.
- **`refreshProjection()` + `waitForDone()`** before every read/export; without it you can
  export a canvas that is one composite behind.
- **Opacity is 0–255**, blend modes are Krita's own ids (`"normal"`, `"multiply"`,
  `"add"`, `"erase"`, …). There is no API listing them in 5.3.3 — `app.blendingModes()`
  exists only on master, so take ids from the Layers docker.
- **Don't chain `app.filter("x").configuration()`** — the `Filter` temporary is collected
  and its `InfoObject` dies with it: `RuntimeError: wrapped C/C++ object of type
  InfoObject has been deleted`, on a line that looks fine. Bind the filter to a name.
- **Ints where you expect floats**: `xRes()`/`yRes()` return floats but `scaleImage` and
  `setResolution` take ints and PyQt raises `TypeError` instead of rounding — `int(...)`.
- **`node.save()` returns `None`**, not the documented bool; check the file exists.
- **Keyframes can't be created from the API** — `setCurrentTime` + `setPixelData` just
  overwrites frame 0 while every save *looks* right. Trigger `add_blank_frame` per frame;
  see [references/api-reference.md](references/api-reference.md#animation).
- **`setPixelData` wants the node's colour space**, not RGBA-in-any-order: with `"RGBA"` /
  `"U8"` documents the `Format_ARGB32` buffer works as-is; for U16/F32 documents build the
  bytes to match, or convert the document first.
- **Layer bounds are not the document** — a paint layer's `bounds()` is the painted extent
  and can be empty until pixels land; use `doc.width()/height()` for full-canvas work.
- **Krita rewrites `kritarc` when it quits**, so installing/enabling the plugin while it
  runs gets silently reverted — quit Krita first (the installer refuses otherwise).
- **Env vars don't reach a GUI-launched Krita** (`open -a krita`), so
  `KRITA_BRIDGE_PORT` only takes effect when Krita is started from a terminal.
- **`paint*` needs a view and inherits the user's brush state** — preset, size, opacity,
  blending mode and foreground colour all come from the active view, so set what matters
  and check `paintAbility() == "PAINT"` first. `paintLine` insists on `QPoint` while the
  rect calls take `QRectF`. Tools, the transform widget and canvas input stay
  unscriptable; `app.action(id).trigger()` is the only door to menu commands, it acts on
  the active document, and it reports nothing back.
- **Scripted edits aren't reliably undoable** — duplicate a layer or save a copy before
  destructive work on the user's own document; see
  [references/recipes.md](references/recipes.md).

## Security

Installing the bridge means running a **code-execution server** on the user's machine. Say
so before asking them to install it.

- The bridge binds `127.0.0.1:8737` (`KRITA_BRIDGE_PORT`) and executes any Python POSTed to
  it inside the live session — the user's privileges, the user's open documents. Requests
  carry **no authentication**: every local process, and every other user on a shared
  machine, can drive Krita through it.
- Web pages **cannot**. Requests carrying an `Origin` header or a cross-site
  `Sec-Fetch-Site` are rejected with 403, so a page in the user's browser can't reach the
  bridge. That check is the only gate — there is no token.
- **The install choice decides how long the port stays open.** `krita-install-bridge.sh`
  enables a pykrita plugin, so *every* Krita launch listens from then on, whether or not an
  agent is driving it. The Scripter paste lasts only until Krita quits — offer it when the
  user doesn't want a permanent listener.
- **To stop the bridge, quit Krita**; to remove it, untick **Krita Bridge** in Settings ▸
  Configure Krita ▸ Python Plugin Manager. There is no remote shutdown.
