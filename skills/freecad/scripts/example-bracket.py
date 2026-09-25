# Example build sent to the FreeCAD Bridge with:
#   OUT=<dir> bash freecad-send.sh example-bracket.py
# It runs in the LIVE FreeCAD GUI session, so the viewport updates and the
# screenshot is taken inline — no separate render step. Demonstrates the full
# loop: build -> recompute -> check -> measure -> write metrics -> export -> screenshot.
# Also runs headless (freecadcmd example-bracket.py); the screenshot is skipped there.
#
# The bridge injects `OUT` (from the sender's $OUT) and also sets os.environ["OUT"].
# `App` / `FreeCAD` / `Gui` are pre-imported in the bridge namespace.
import os
import json
import FreeCAD as App
import Part
import Mesh

OUT = globals().get("OUT") or os.environ.get("OUT", os.path.expanduser("~/Desktop"))
Gui = globals().get("Gui")  # None under headless freecadcmd

# Re-runnable: newDocument on a taken name silently creates "bracket1", so drop
# the previous build first. Only close documents this script created.
if "bracket" in App.listDocuments():
    App.closeDocument("bracket")
doc = App.newDocument("bracket")

box = doc.addObject("Part::Box", "Plate")
box.Length, box.Width, box.Height = 40.0, 20.0, 10.0  # mm

hole = doc.addObject("Part::Cylinder", "Hole")
hole.Radius, hole.Height = 5.0, 10.0
hole.Placement.Base = App.Vector(20, 10, 0)  # centre of the plate

cut = doc.addObject("Part::Cut", "Bracket")
cut.Base, cut.Tool = box, hole
doc.recompute()  # ALWAYS recompute before measuring

# recompute() never raises — a failed feature is only marked Invalid.
bad = [(o.Name, o.State) for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
if bad:
    raise RuntimeError("recompute failed: %s" % bad)

shp = cut.Shape
bb = shp.BoundBox
metrics = {
    "objects": [o.Name for o in doc.Objects],
    "bbox_mm": [round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)],
    "volume_mm3": round(shp.Volume, 3),
    "valid": shp.isValid(),
    "solids": len(shp.Solids),
}
with open(os.path.join(OUT, "metrics.json"), "w") as f:
    json.dump(metrics, f, indent=2)

Part.export([cut], os.path.join(OUT, "bracket.step"))  # CAD interchange
Mesh.export([cut], os.path.join(OUT, "bracket.stl"))   # 3D printing / preview
doc.saveAs(os.path.join(OUT, "bracket.FCStd"))          # native, for re-editing

# We're in the live GUI — frame the part and grab a viewport PNG right here.
if Gui is not None:
    view = Gui.getDocument(doc.Name).activeView()
    # View changes animate; without this saveImage captures the camera mid-turn
    # (often a blank white frame).
    view.setAnimationEnabled(False)
    view.viewIsometric()
    view.fitAll()
    view.saveImage(os.path.join(OUT, "bracket.png"), 900, 675, "White")

# stdout is captured by the bridge and returned to the sender.
print("METRICS", json.dumps(metrics))
