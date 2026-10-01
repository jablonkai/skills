# KiCad IPC API (kicad-python / kipy) and the SWIG fallback

KiCad 9 introduced a protobuf API over a local nng socket; KiCad 10 extends it. The
Python client is `kicad-python` (import `kipy`), 0.8.0 at the time of writing, Python ≥ 3.9.
It talks to a **running KiCad GUI**. There is no headless mode.

## Setup

```bash
python3 -m venv ~/.venvs/kicad
~/.venvs/kicad/bin/pip install kicad-python
```

- KiCad › Preferences › Plugins › **Enable KiCad API** (stored as
  `api.enable_server` in `~/Library/Preferences/kicad/10.0/kicad_common.json`; off by default).
- Socket: `ipc:///tmp/kicad/api.sock` (override with `KICAD_API_SOCKET`).
- Open the board in the PCB editor. `kipy` returns the first open PCB document.

## Core calls

```python
import math
from kipy import KiCad
from kipy.geometry import Vector2, Angle

kicad = KiCad(timeout_ms=5000)          # raises kipy.errors.ConnectionError if API off
print(kicad.get_version())
board = kicad.get_board()               # ApiError if no PCB is open

fps = {fp.reference_field.text.value: fp for fp in board.get_footprints()}
fp = fps["D1"]
print(fp.position.x / 1e6, fp.position.y / 1e6, fp.orientation.degrees)  # nm -> mm

commit = board.begin_commit()           # groups everything into one undo step
fp.position = Vector2.from_xy_mm(125, 105)   # setter also shifts pads/fields/graphics
fp.orientation = Angle.from_degrees(90)      # CCW seen from top, normalised to ±180
board.update_items([fp])                # send the modified items
board.push_commit(commit, "Move D1")    # or board.drop_commit(commit) on error
board.save()                            # write the .kicad_pcb
```

Other useful `Board` methods (kipy 0.8.0):

| Need | Call |
|------|------|
| Items by type | `get_tracks()`, `get_vias()`, `get_pads()`, `get_zones()`, `get_shapes()`, `get_text()` |
| Nets | `get_nets()`, `get_items_by_net(net)` |
| Create / delete | `create_items(items)`, `remove_items(items)` |
| Flip to other side | `flip_items(items)` |
| Selection | `get_selection()`, `add_to_selection()`, `clear_selection()` |
| Title block | `get_title_block_info()` / `set_title_block_info(tb)` (`title`, `date`, `revision`, `company`, `comments{1..9}`) |
| Origins | `get_origin(type)` / `set_origin(type, Vector2)` |
| Layers | `get_copper_layer_count()`, `get_enabled_layers()`, `set_enabled_layers()`, `get_layer_by_name()` |
| Stackup | `get_stackup()` |
| Zones | `refill_zones(block=True)` |
| Whole file text | `get_as_string()` |

**Not available in kipy 0.8.0:** a call that loads a footprint from a library into the
board. Footprints come from "Update PCB from Schematic" (F8) in the GUI. Scripts move, rotate and edit what
is already there.

## Pitfalls

- Coordinates: nanometres, **Y down**. A point at angle θ (CCW, math convention) around
  `(cx, cy)` is `(cx + r cos θ, cy - r sin θ)`.
- Modify `fp.position` via the kipy setter. Copying protos by hand doesn't move children.
- `update_items` outside a commit makes one undo step per call.
- KiCad answers `AS_BUSY` ("busy performing an operation") while it is mid-operation,
  e.g. an interactive move or a running tool. Ask the user to finish it (Esc), then retry once.
- Errors: `kipy.errors.ConnectionError` (API off / KiCad closed), `ApiError` with
  "no handler available" (the process owning the socket has no PCB editor; open the board there).

## SWIG fallback

The legacy `pcbnew` module ships inside KiCad's bundled Python. It is **deprecated since
9.0 and expected to be removed in KiCad 11**. It works headless, so it suits a
CI-style edit when no GUI can run. Run it with KiCad's interpreter (prints harmless wx
debug lines on stderr):

```bash
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$PY - <<'EOF'
import math, pcbnew
b = pcbnew.LoadBoard("board.kicad_pcb")
for i in range(8):
    fp = b.FindFootprintByReference(f"D{i+1}")
    t = math.radians(90 - i * 45)
    fp.SetPosition(pcbnew.VECTOR2I_MM(125 + 20 * math.cos(t), 125 - 20 * math.sin(t)))
    fp.SetOrientationDegrees(90 - i * 45 + 90)
b.Save("board.kicad_pcb")
EOF
```

Verified on 10.0.6: pads move with the footprint. Never run this on a board that is open
in KiCad: the GUI overwrites the file on its next save.
