---
name: freecad
description: 'Remote-control a running FreeCAD (the open-source parametric CAD app) by Python script through a small local bridge — build and edit 3D models live: box/cylinder primitives and booleans, filleted/chamfered solids, constrained Sketcher profiles, parametric PartDesign features (pad, pocket, revolution, patterns), 2D Draft geometry, meshes, and TechDraw drawings, then measure them, grab viewport screenshots, and export STEP / IGES / BREP / STL / OBJ. Use whenever the user wants to create or edit a CAD model, 3D part, mechanical component, enclosure, bracket, or .FCStd file, convert or export a model to STEP/STL/IGES/OBJ, or says "FreeCAD", "CAD model", "parametric part", "make a 3D part", "export to STEP", "STL for printing" — even if they don''t mention scripting. Also covers Hungarian: "csinálj egy CAD modellt", "3D alkatrész", "parametrikus alkatrész", "exportáld STEP-be", "STL nyomtatáshoz".'
category: cad
risk: medium
tags:
    - freecad
    - cad
    - parametric-modeling
    - 3d
    - scripting
---

# FreeCAD Control

FreeCAD (`/Applications/FreeCAD.app`) is scriptable in **Python** against the `FreeCAD` /
`FreeCADGui` / `Part` / `Sketcher` / `PartDesign` / `Draft` / `Mesh` / `TechDraw` modules.
Drive it through the **FreeCAD Bridge** — a small script running inside a *running* FreeCAD
GUI that executes whatever build script is POSTed to `127.0.0.1:8735`. Because the script
runs in the live session on the GUI thread, the viewport updates as you build and
`Gui.*` / `saveImage` work directly. Everything below was proven on FreeCAD 1.1.1.

- [scripts/freecad-bridge.py](scripts/freecad-bridge.py) — the bridge to run inside FreeCAD.
- [scripts/freecad-send.sh](scripts/freecad-send.sh) — send a `.py` file (or `-c 'inline code'`)
  to the bridge and print its captured output; `--ping` checks it's up.
- [scripts/example-bracket.py](scripts/example-bracket.py) — a complete build→measure→export→
  screenshot script to copy from.
- [references/api-reference.md](references/api-reference.md) — condensed, version-checked
  Python API (App/document, Part, Sketcher, PartDesign, Draft, Mesh, Import/Export, GUI).
  **Read it before writing anything past the cheatsheet below.**

## The control loop

1. **User starts the bridge** (one-time per session): FreeCAD must be running with
   `freecad-bridge.py` executed inside it. This cannot be done remotely — if
   `bash scripts/freecad-send.sh --ping` gets no answer, ask the user to open FreeCAD and run
   the bridge, one of:
   - paste the contents of [scripts/freecad-bridge.py](scripts/freecad-bridge.py) into the
     **Python console** (View ▸ Panels ▸ Python console) and press Enter, or
   - copy it into the FreeCAD **Macro** folder (`~/Library/Application Support/FreeCAD/Macro/`,
     verify via Macro ▸ Macros… ▸ *User macros location*) and run **Macro ▸ Macros ▸
     freecad-bridge ▸ Execute**.

   A successful ping returns `{"ok": true, "bridge": "freecad", "version": "1.1.1"}`.
2. **Write a build script** to the scratchpad — Python against the API (start from
   [references/api-reference.md](references/api-reference.md) and
   [scripts/example-bracket.py](scripts/example-bracket.py)).
3. **Send it**: `OUT=/path/to/outdir bash scripts/freecad-send.sh /path/build.py`. The bridge
   runs it in the live session and returns the script's **captured stdout**; on error it
   returns the **traceback** and the sender exits non-zero. `FREECAD_SEND_TIMEOUT=600`
   (seconds) for heavy builds. `App` / `FreeCAD` / `Gui` are pre-imported in the script's
   namespace, and `OUT` is injected (from `$OUT`) as both a global and `os.environ["OUT"]`.
4. **Feedback**: the returned stdout is your first signal. For structured data write a
   `metrics.json` (bounding box, volume, `isValid()`, solid count) and Read it; for a picture,
   call `Gui.activeDocument().activeView().saveImage(path, w, h, "White")` in the same script
   and Read the PNG. Export STEP/STL/FCStd into `$OUT` for the deliverable.
5. **Iterate**: inspect output/PNG, fix the script, re-send. Scripts must be **re-runnable** —
   create a fresh `App.newDocument("thing_v2")` per version so re-sends don't collide with a
   document already open in the session.

A failed send prints the Python traceback the bridge captured. The bridge stays up across
sends; if it becomes unresponsive, ask the user to re-run the bridge script.

## Modeling cheatsheet (proven patterns)

Units are **mm** and **degrees**. `App` = `FreeCAD` (both pre-imported by the bridge). Always
`recompute()` before measuring.

### Solid via primitives + boolean (verified: plate with a bored hole)

```python
import os, json, Part, Mesh
OUT = globals().get("OUT") or os.environ["OUT"]
doc = App.newDocument("bracket_v1")                 # fresh, versioned
box = doc.addObject("Part::Box", "Plate"); box.Length, box.Width, box.Height = 40, 20, 10
hole = doc.addObject("Part::Cylinder", "Hole"); hole.Radius, hole.Height = 5, 10
hole.Placement.Base = App.Vector(20, 10, 0)          # centre of the plate
cut = doc.addObject("Part::Cut", "Bracket"); cut.Base, cut.Tool = box, hole
doc.recompute()                                      # REQUIRED before measuring
```

### Measure + screenshot (the live feedback)

```python
shp = cut.Shape; bb = shp.BoundBox
m = {"bbox": [round(bb.XLength,3), round(bb.YLength,3), round(bb.ZLength,3)],
     "volume": round(shp.Volume,3), "valid": shp.isValid(), "solids": len(shp.Solids)}
json.dump(m, open(OUT+"/metrics.json","w"), indent=2)
print("METRICS", json.dumps(m))                      # returned to the sender

Gui.activeDocument().activeView().viewIsometric()    # live GUI — snapshot inline
Gui.SendMsgToActiveView("ViewFit"); Gui.updateGui()
Gui.activeDocument().activeView().saveImage(OUT+"/check.png", 900, 675, "White")
```

### Export (pick the module by format — see the reference's matrix)

```python
Part.export([cut], OUT+"/bracket.step")   # B-rep: .step/.stp .iges/.igs .brep
Mesh.export([cut], OUT+"/bracket.stl")    # mesh: .stl .obj .ply
doc.saveAs(OUT+"/bracket.FCStd")          # native, re-editable
```

### Parametric route (Sketcher → PartDesign, verified: rectangle → pad)

```python
import Part, Sketcher
body = doc.addObject("PartDesign::Body", "Body")
sk = body.newObject("Sketcher::SketchObject", "Sketch")
V = App.Vector
for a, b in [((0,0),(30,0)), ((30,0),(30,20)), ((30,20),(0,20)), ((0,20),(0,0))]:
    sk.addGeometry(Part.LineSegment(V(*a,0), V(*b,0)), False)
for i in range(4):
    sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i+1) % 4, 1))
doc.recompute()
pad = body.newObject("PartDesign::Pad", "Pad"); pad.Profile = sk; pad.Length = 10
doc.recompute()
```

Feature types, constraint kinds, Draft/Mesh/TechDraw calls, and the full export matrix are in
[references/api-reference.md](references/api-reference.md).

## Verification

- **Returned stdout** is the immediate signal — `print(...)` in the script comes straight back
  through the sender.
- **metrics.json** (bbox / volume / `isValid()` / solid count) is the structured check — write
  it and Read it to confirm geometry without eyeballing.
- **Inline screenshot**: because the bridge runs in the live GUI, `saveImage(...)` in the same
  script produces a viewport PNG to Read — no separate render step.
- **Hand-off**: an exported `.stl`/`.step` opens in any slicer/CAD tool the user already has.

## Gotchas (hard-won on this machine)

- **The bridge runs in the live session**, so state persists between sends: an open document,
  imported assets, and view settings all stick. Version your docs (`newDocument("x_v2")`) so a
  re-send doesn't stack objects onto a document already open.
- **`Gui` is live here** — `saveImage`, `viewIsometric`, `ViewFit` all work. (This is the whole
  reason for the bridge over headless `-c`, where there is no viewport.)
- **`print()` and captured stdout** come back in the response; `App.Console.PrintMessage` goes
  to FreeCAD's Report view, *not* to the sender — use `print()` for anything you want returned.
- **`recompute()` before every measure or export** — parametric attributes don't reach
  `.Shape` until then.
- **Placement is value-typed** — assign a fresh `App.Placement(...)` (or reassign after
  mutating) and recompute; in-place edits can silently no-op.
- **PySide binding**: FreeCAD 1.1 ships **PySide6** (Qt6); the bridge imports it with a
  PySide2 fallback. If you script Qt directly, import the same way.
- **Booleans keep their inputs in the tree** (hidden) — `cut.Base`/`cut.Tool` still exist;
  export only the result feature.
- Save the native `.FCStd` from the script so parametric work survives and can be re-edited.
