# Krita recipes

Patterns that come up repeatedly, and the boundaries of what the API can do. All of these
run through the bridge (`krita-send.sh`) unless a recipe says otherwise.

## Contents

- [Batch-process a folder](#batch-process-a-folder)
- [Export every layer separately](#export-every-layer-separately)
- [Don't launch a second Krita](#dont-launch-a-second-krita)
- [Animation frames, and turning them into video](#animation-frames-and-turning-them-into-video)
- [Probing what you don't know yet](#probing-what-you-dont-know-yet)
- [Editing the user's open document safely](#editing-the-users-open-document-safely)
- [Long jobs and timeouts](#long-jobs-and-timeouts)
- [A send hangs or times out](#a-send-hangs-or-times-out)
- [What the API cannot do](#what-the-api-cannot-do)

## Batch-process a folder

Open → edit → export → **close**, one file at a time. Closing matters: every open document
holds its whole image in memory, and a hundred left open will bring the session down.

```python
import glob, os, json
from krita import Krita, InfoObject

app = Krita.instance()
was_batch = app.batchmode(); app.setBatchmode(True)   # app-wide: restore it for the user
report = []
try:
    for path in sorted(glob.glob("/photos/*.kra")):
        doc = app.openDocument(path)             # no view: stays off the user's screen
        doc.setBatchmode(True)
        doc.scaleImage(1600, int(1600 * doc.height() / doc.width()),
                       int(doc.xRes()), int(doc.yRes()), "Bicubic")   # ints, not floats
        doc.refreshProjection(); doc.waitForDone()
        out = os.path.join(OUT, os.path.splitext(os.path.basename(path))[0] + ".jpg")
        cfg = InfoObject(); cfg.setProperty("quality", 88)
        ok = doc.exportImage(out, cfg)
        doc.setModified(False); doc.close()      # frees the image, never asks to save
        report.append({"src": path, "out": out, "ok": ok})
finally:
    app.setBatchmode(was_batch)
print(json.dumps(report, indent=1))
```

`OUT` is injected by the bridge. `app.setBatchmode` is application-wide, so a script that
leaves it on silently suppresses dialogs in the user's own session afterwards.

Report per-file success and print it: `exportImage` returns a bool, and a batch that
silently skipped three files is the failure mode worth catching.

## Export every layer separately

`node.save()` exports one layer, using an explicit rect — pass the image bounds when the
layers must line up in whatever composites them afterwards.

```python
doc = Krita.instance().activeDocument()
doc.setBatchmode(True)
bounds = doc.bounds()
for node in doc.rootNode().childNodes():
    if not node.visible():
        continue
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in node.name())
    node.save(f"{OUT}/{safe}.png", doc.xRes(), doc.yRes(), InfoObject(), bounds)
```

Passing an empty `QRect()` instead saves each layer's own `bounds()` — tighter files, but
they no longer share an origin.

## Don't launch a second Krita

Krita's command line can convert files on its own (`--export`, `--export-sequence`), and
this skill does **not** use it. One machine gets one Krita: a second instance contends with
the running one over the resource database and `kritarc`, and the loser is the session the
user has their artwork open in. A background app also grabs focus on macOS and swallows its
own errors, so a "quick" headless batch turns into an invisible failure.

Route conversion through the bridge instead — the
[batch recipe](#batch-process-a-folder) above is the same work in the session that is
already running, and it is faster besides, because it pays the startup cost once. If Krita
isn't running at all, ask the user to start it rather than starting one yourself; the
bridge comes up with it.

## Animation frames, and turning them into video

Generating frames from Python:

```python
app.setActiveDocument(doc); doc.setActiveNode(layer)   # add_blank_frame follows these
doc.setFramesPerSecond(24)
layer.enableAnimation()
for t in range(48):
    doc.setCurrentTime(t)
    if t:
        app.action("add_blank_frame").trigger()   # without this no keyframe is made
        doc.waitForDone()                         # without this pixels land a frame early
    push(layer, draw_frame(t))                    # your QImage per frame
    doc.refreshProjection(); doc.waitForDone()
    doc.projection(0, 0, doc.width(), doc.height()).save(f"{OUT}/frames{t:04d}.png")
doc.setFullClipRangeStartTime(0); doc.setFullClipRangeEndTime(47)
doc.saveAs(OUT + "/anim.kra")
print("keyframes:", all(layer.hasKeyframeAtTime(t) for t in range(48)))
# content check: frame t must hold what draw_frame(t) drew, not frame t+1's image
print("frame 0 pixel:", bytes(layer.pixelDataAtTime(0, 0, 1, 1, 0).toHex()))
```

Keep both checks. Without `add_blank_frame` the loop writes plausible PNGs and a `.kra`
that animates nothing, which `hasKeyframeAtTime` catches; without the `waitForDone()` after
it, every key exists but holds the next frame's pixels, which only a content check catches.

Leave the animated document **open** at the end of the script: closing it in the same send
that created the keyframes crashes Krita a moment later (5.3.4). If it has to go, close it
from a separate send.

The video encoders are a GUI feature (Krita shells out to ffmpeg), not part of the Python
API. Write each frame out inside the loop — `doc.projection(0, 0, doc.width(),
doc.height()).save(f"{OUT}/frames{t:04d}.png")` right after the refresh — and encode them
yourself:

```bash
ffmpeg -framerate 24 -i frames%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 anim.mp4
```

## Probing what you don't know yet

Filter properties, preset names and blend-mode ids are data, not documentation. Ask the
running Krita instead of guessing — a two-line probe script beats three failed attempts:

```python
app = Krita.instance()
print(sorted(app.filters()))                  # ids are literal: "gaussian blur", not
f = app.filter("gaussian blur")               # "gaussianblur" (which returns None)
print(f.configuration().properties())         # bind f — a chained temporary dies first
print(sorted(app.resources("preset"))[:40])
print(app.activeDocument().activeNode().paintAbility())
print([n.name() for n in app.activeDocument().rootNode().childNodes()])   # localized names
print(hasattr(app.activeDocument().activeNode(), "setPinnedToTimeline"))  # instance, not class
```

Check members with `hasattr` on a **live object**: PyQt resolves methods lazily, so the
same check on the class (`hasattr(Node, ...)`) can report `False` for a method that works.

## Editing the user's open document safely

Scripted edits are not reliably undoable step by step, so treat the user's artwork as
precious:

- work on `app.activeDocument()` only when the task is explicitly about the open file;
- duplicate what you are about to change (`node.duplicate()`, then add the copy) or add a
  new layer instead of overwriting an existing one;
- prefer filter *masks* and filter *layers* over `filter.apply()` when the user may want
  to dial the effect back later;
- `doc.saveAs()` a copy before destructive whole-image operations (`flatten`, `scaleImage`,
  `setColorSpace`).

## Long jobs and timeouts

`krita-send.sh` waits `KRITA_SEND_TIMEOUT` seconds (default 120) for the whole script, and
the bridge runs it on the GUI thread — so a five-minute script means a five-minute frozen
UI. For big jobs: raise the timeout (`KRITA_SEND_TIMEOUT=900`), split the work into
several sends (per file, per frame batch), and print progress so a partial run is still
informative. `doc.lock()` / `doc.unlock()` around a burst of edits avoids recomposing
after every single change.

## A send hangs or times out

When `krita-send.sh` reports a timeout, first suspect a **modal dialog** — an unsaved-changes
prompt from `close()`, a format-options box from an export without batch mode. A modal
dialog runs its own nested event loop, so the bridge keeps answering, and it can tell you
what is on screen:

```python
from PyQt5.QtWidgets import QApplication, QLabel
m = QApplication.activeModalWidget()
print(m and (type(m).__name__, [l.text() for l in m.findChildren(QLabel)]))
```

Tell the user what the dialog asks rather than clicking it blind; if it is your own
unsaved-changes prompt on a scratch document, `m.button(QMessageBox.No)` (or `Discard`)
dismissed via `QTimer.singleShot(0, button.click)` releases the stuck script. Then fix the
cause — `setModified(False)` before `close()`, `setBatchmode(True)` before export.

If the bridge doesn't answer at all, check whether Krita is still running: a crash leaves
no traceback, only a report in `~/Library/Logs/DiagnosticReports/krita-*.ips` on macOS.
The known triggers are `paint*`/`paintAbility()` without a view and closing a freshly
animated document.

## What the API cannot do

- **No tool or canvas input**: the transform tool, assistants, gradients-as-drawn, and
  everything else that lives in a tool option is unreachable; `app.action(id).trigger()`
  can fire the menu command but gives no result back and acts on the active document.
- **No video encoding**, no render-animation dialog (see above).
- **No G'MIC or plugin filters** beyond what `app.filters()` lists.
- **Undo is not a scripting primitive** — see the safety notes above.
- **Layer styles** go in and out as ASL strings only (`layerStyleToAsl`,
  `setLayerStyleFromAsl`).

If a task needs real natural-media simulation (water flow, pigment granulation), the
`rebelle` skill drives an app built for it; for vector/layout work use `affinity`, and for
keyframed motion graphics `cavalry`.
