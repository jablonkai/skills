# Example build sent to the FreeCAD Bridge with:
#   OUT=<dir> bash freecad-send.sh example-bracket.py
# It runs in the LIVE FreeCAD GUI session, so the viewport updates and the
# screenshot is taken inline — no separate render step. Demonstrates the full
# loop: build -> recompute -> measure -> write metrics -> export -> screenshot.
#
# The bridge injects `OUT` (from the sender's $OUT) and also sets os.environ["OUT"].
# `App` / `FreeCAD` / `Gui` are pre-imported in the bridge namespace.
import os
import json
import Part
import Mesh

OUT = globals().get("OUT") or os.environ.get("OUT", os.path.expanduser("~/Desktop"))

# Fresh, versioned document so re-sends don't collide with a stale one.
doc = App.newDocument("bracket_v1")

box = doc.addObject("Part::Box", "Plate")
box.Length, box.Width, box.Height = 40.0, 20.0, 10.0  # mm

hole = doc.addObject("Part::Cylinder", "Hole")
hole.Radius, hole.Height = 5.0, 10.0
hole.Placement.Base = App.Vector(20, 10, 0)  # centre of the plate

cut = doc.addObject("Part::Cut", "Bracket")
cut.Base, cut.Tool = box, hole
doc.recompute()  # ALWAYS recompute before measuring

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
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    Gui.updateGui()
    Gui.activeDocument().activeView().saveImage(os.path.join(OUT, "bracket.png"), 900, 675, "White")

# stdout is captured by the bridge and returned to the sender.
print("METRICS", json.dumps(metrics))
