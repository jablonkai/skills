# Nuke Python under Non-commercial

Python runs inside Nuke in two ways:

- `nk.py render … --py HOOK.py`: after the script loads and before `--set` and the
  render. `nuke` is already imported.
- A full `Nuke --nc -t driver.py` you write yourself. It is rarely needed.

Nuke 17.1v2 bundles Python 3.11. The system `python3` that runs `nk.py` cannot
`import nuke`.

## The 10-node limit

Non-commercial mode gives Python **at most 10 `Node` objects** per script session.

- After the 10th, `nuke.nodes.X()`, `nuke.createNode()`, `nuke.toNode()` and
  `nuke.allNodes()` return `None` or a truncated list, and log "The Non-Commercial mode
  10-node limit for Node objects accessible in Python has been reached".
- The limit counts Python handles, not graph size: a 29-node `.nk` loaded with
  `scriptReadFile` renders fine.
- `nuke.scriptClear()` resets the count.

So:

- Build graphs as `.nk` text, never node by node from Python.
- Touch only the few nodes a hook really needs, by name: `nuke.toNode("Matte")`.
- Render by name: `nuke.execute("Write_EXR", 1001, 1048)` takes a name and costs no handle.
- Change knobs with `nk.py render --set Node.knob=value` instead of a hook where you can.

## Loading and saving

| Call | Under NC |
|---|---|
| `nuke.scriptReadFile(path)` | loads plain `.nk` text and `.nknc` (what nk.py uses) |
| `nuke.nodePaste(path)` | loads `.nk` text into the current graph (Root knobs are not applied) |
| `nuke.scriptOpen(path)` | `.nknc` only. It refuses `.nk` with "Please specify an existing .nknc script" |
| `nuke.scriptSaveAs(path)` | always writes **encrypted** `.nknc`, even if named `.nk` |
| `nuke.nodeCopy(path)` | also encrypted — no way to get plain text out of NC |

## Rendering

```python
nuke.execute("Write_EXR", 1001, 1048)        # name, first, last[, step]
nuke.execute("G.Write1", 1, 10, 2)           # inside a Group: dotted name
```

`execute` raises `RuntimeError` with Nuke's message ("h264 codecs are disabled…",
"The bounding box exceeds the maximum resolution…"). Each Write is executed separately,
so one failure does not stop the others; `nk.py` reports each.

## Roto shapes (hook example)

Roto curves have no hand-writable text form under NC, so add shapes from a hook. Put an
empty `Roto { inputs 0  output alpha  name Matte }` in the `.nk` and run:

```python
import nuke
import nuke.rotopaint as rp

roto = nuke.toNode("Matte")              # 1 of the 10 handles
curves = roto["curves"]
shape = rp.Shape(curves, name="Garbage")
pts = [(100, 100), (260, 100), (260, 260), (100, 260)]     # pixels, origin bottom-left
for x, y in pts:
    shape.append(rp.ShapeControlPoint(x, y))
for frame, dx in ((1001, 0), (1048, 270)):                 # animate: keys per point
    for i, (x, y) in enumerate(pts):
        shape[i].center.addPositionKey(frame, nuke.math.Vector2(x + dx, y))
curves.rootLayer.append(shape)
```

- Invert: `shape.getAttributes().set("inv", 1)`.
- For a soft edge, add a `Blur { channels alpha  size 20 }` after the Roto in the `.nk`.
- Use simple matte geometry (box, ellipse, gradient) without curves where you can:
  Rectangle, Radial, Ramp. Those are plain text nodes.

## Useful one-liners in a hook

```python
nuke.root()["first_frame"].setValue(1001)
nuke.toNode("BG")["file"].setValue("/plates/sh020/bg.####.exr")
nuke.toNode("Grade1")["white"].setValue([1.1, 1.0, 0.9, 1.0])
nuke.toNode("Text1")["message"].setValue("v002")
k = nuke.toNode("Transform1")["translate"]; k.setAnimated(); k.setValueAt(0, 1001, 0); k.setValueAt(300, 1048, 0)
print(nuke.NUKE_VERSION_STRING, nuke.env["nc"])
```
