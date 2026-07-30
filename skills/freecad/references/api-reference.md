# FreeCAD Python API reference (condensed)

Verified against **FreeCAD 1.1.1** on macOS. Units are **millimetres** and **degrees**
by default. Scripts run inside a live FreeCAD GUI session via the bridge, so both the
modelling API and the `FreeCADGui` view/screenshot calls work. For anything beyond this digest, the authoritative
source is the FreeCAD Python wiki — <https://wiki.freecad.org/Python_scripting_tutorial>
and the per-workbench "Scripting" pages (e.g. `Part_scripting`, `Sketcher_scripting`,
`PartDesign_Scripting`, `Draft_API`, `TechDraw_API`, `Mesh_Scripting`) — grep those for
exact signatures.

## App / document model

```python
import FreeCAD as App
doc = App.newDocument("thing_v1")     # fresh, VERSIONED doc so re-runs don't collide
App.setActiveDocument(doc.Name)
App.ActiveDocument                     # current doc
obj = doc.addObject("Part::Box", "MyBox")   # type string, then object Name
doc.getObject("MyBox")                 # fetch by Name
doc.Objects                            # list of all objects
doc.removeObject("MyBox")
doc.recompute()                        # REQUIRED before measuring / exporting
doc.saveAs("/abs/path/thing.FCStd")    # native format
App.openDocument("/abs/path/x.FCStd")  # reopen
App.closeDocument(doc.Name)
App.Vector(x, y, z)                    # 3D vector; App.Rotation(axis, deg) for rotations
```

Placement: `obj.Placement = App.Placement(App.Vector(10,0,0), App.Rotation(App.Vector(0,0,1), 45))`.
`obj.Placement.Base` is the translation; assign a whole new `Placement` (don't mutate in place
and forget to reassign).

## Part workbench — direct solids (`import Part`)

Primitives are objects with parametric attributes:

```python
box = doc.addObject("Part::Box", "Box");  box.Length, box.Width, box.Height = 40, 20, 10
cyl = doc.addObject("Part::Cylinder", "Cyl"); cyl.Radius, cyl.Height = 5, 10
sph = doc.addObject("Part::Sphere", "Sph"); sph.Radius = 8
con = doc.addObject("Part::Cone", "Cone"); con.Radius1, con.Radius2, con.Height = 6, 2, 12
tor = doc.addObject("Part::Torus", "Tor"); tor.Radius1, tor.Radius2 = 10, 3
```

Booleans take `Base` and `Tool` (or a list for multi-fuse):

```python
cut  = doc.addObject("Part::Cut", "Cut");     cut.Base, cut.Tool = box, cyl
fuse = doc.addObject("Part::Fuse", "Fuse");   fuse.Base, fuse.Tool = box, cyl
comm = doc.addObject("Part::Common", "Comm"); comm.Base, comm.Tool = box, cyl   # intersection
doc.recompute()
```

Fillet / chamfer edges of an existing feature:

```python
fil = doc.addObject("Part::Fillet", "Fillet"); fil.Base = box
edges = [(i + 1, 2.0, 2.0) for i in range(len(box.Shape.Edges))]  # (edgeNumber, r1, r2)
fil.Edges = edges
box.Visibility = False
doc.recompute()
```

Scripted geometry without doc objects (then wrap in a `Part::Feature`):

```python
wire  = Part.makePolygon([App.Vector(0,0,0), App.Vector(10,0,0), App.Vector(10,10,0), App.Vector(0,0,0)])
face  = Part.Face(wire)
solid = face.extrude(App.Vector(0,0,5))
feat  = doc.addObject("Part::Feature", "Extruded"); feat.Shape = solid
```

## Measuring — the file-based feedback loop

```python
shp = obj.Shape          # the TopoShape; recompute() first
bb  = shp.BoundBox       # bb.XLength/YLength/ZLength, bb.XMin.., bb.Center
shp.Volume               # mm^3
shp.Area                 # surface area mm^2
shp.CenterOfMass
shp.isValid()            # topology sane?
shp.check()              # None if ok; raises/returns detail on defects
len(shp.Solids), len(shp.Faces), len(shp.Edges), len(shp.Vertexes)
```

Dump these to JSON and Read the file back — the CAD analog of a preview render:

```python
import json, os
m = {"bbox": [round(bb.XLength,3), round(bb.YLength,3), round(bb.ZLength,3)],
     "volume": round(shp.Volume,3), "valid": shp.isValid(), "solids": len(shp.Solids)}
with open(os.path.join(os.environ["OUT"], "metrics.json"), "w") as f: json.dump(m, f, indent=2)
```

## Sketcher — constrained 2D profiles (`import Sketcher`)

```python
sk = body.newObject("Sketcher::SketchObject", "Sketch")   # or doc.addObject(...)
V = App.Vector
sk.addGeometry(Part.LineSegment(V(0,0,0), V(30,0,0)), False)   # False = not construction geo
sk.addGeometry(Part.Circle(V(0,0,0), V(0,0,1), 5), False)      # centre, normal, radius
# close a 4-line rectangle with coincidences (endpoint index 2 → start index 1):
for i in range(4):
    sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i+1) % 4, 1))
sk.addConstraint(Sketcher.Constraint("Horizontal", 0))
sk.addConstraint(Sketcher.Constraint("Distance", 0, 30.0))     # dimensional
doc.recompute()
```

Constraint kinds: `Coincident, Horizontal, Vertical, Parallel, Perpendicular, Equal,
Tangent, Distance, DistanceX, DistanceY, Radius, Diameter, Angle, Symmetric`. Geometry
endpoints are addressed as `(geoId, pointPos)` with pointPos `1` = start, `2` = end, `3` = centre.

## PartDesign — parametric feature modelling

Everything lives inside a **Body**; features chain off the current `Tip`:

```python
body = doc.addObject("PartDesign::Body", "Body")
sk   = body.newObject("Sketcher::SketchObject", "Sketch")   # sketch the profile (above)
# ... geometry + constraints ...
doc.recompute()
pad  = body.newObject("PartDesign::Pad", "Pad");   pad.Profile = sk; pad.Length = 10
doc.recompute()
```

Feature types: `Pad` (`Length`, `Reversed`, `Midplane`), `Pocket` (`Length` / `ThroughAll`),
`Revolution` (`Angle`, `ReferenceAxis`), `Groove`, `Loft`, `Sweep`,
`Fillet`/`Chamfer` (`Base` = list of edges), and patterns `LinearPattern` / `PolarPattern`
/ `Mirrored`. `body.Tip` is the final feature; `body.Shape` is its solid.

## Draft — 2D drafting & helpers (`import Draft`)

FreeCAD 1.x uses snake_case (older camelCase aliases may still exist):

```python
import Draft
Draft.make_circle(radius, placement=None)
Draft.make_rectangle(length, height)
Draft.make_polygon(nsides, radius)
Draft.make_wire([App.Vector(0,0,0), App.Vector(10,0,0), App.Vector(10,10,0)], closed=True)
Draft.make_text(["line 1", "line 2"], App.Vector(0,0,0))
arr = Draft.make_array(base, App.Vector(10,0,0), App.Vector(0,10,0), 3, 2)   # ortho array
```

## Mesh — tessellated geometry (`import Mesh`, `import MeshPart`)

```python
import Mesh, MeshPart
mesh = doc.addObject("Mesh::Feature", "Mesh")
mesh.Mesh = MeshPart.meshFromShape(Shape=solid, LinearDeflection=0.1, AngularDeflection=0.5)
Mesh.export([obj], "/abs/out.stl")       # obj can be a solid feature; auto-tessellates
```

## Import / Export — verified format matrix

| Call | Formats confirmed working (1.1.1) |
|------|-----------------------------------|
| `Part.export([objs], path)` | `.step` / `.stp`, `.iges` / `.igs`, `.brep` |
| `Mesh.export([objs], path)` | `.stl`, `.obj`, `.ply` (also `.off`, `.amf`) |
| `Import.open(path)` / `Import.insert(path, docName)` | STEP / IGES into a document |
| `Mesh.insert(path, docName)` | STL / OBJ / PLY into a document |

`importDXF`, `importSVG` (2D), and `importOBJ` submodules exist for those niche formats.
`Part.export`/`Mesh.export` pick the exporter from the file extension.

## GUI & screenshots (live — `Gui` is pre-imported by the bridge)

```python
view = Gui.activeDocument().activeView()
view.viewIsometric(); view.viewFront(); view.viewTop()   # standard views
Gui.SendMsgToActiveView("ViewFit")                       # frame all visible objects
view.fitAll(); Gui.updateGui()
view.saveImage("/abs/shot.png", 1000, 750, "White")      # w, h, background
```

Objects you create in the session are visible by default, so `ViewFit` + `saveImage`
capture them directly. TechDraw pages (`TechDraw::DrawPage` + `DrawViewPart`) produce 2D
technical drawings and can be exported to SVG/PDF — see the `TechDraw_API` wiki page.

## Gotchas

- **`doc.recompute()` before every measure or export** — attributes set on parametric
  objects don't propagate to `.Shape` until recompute.
- **Placement is value-typed**: assign a fresh `App.Placement(...)`; mutating
  `obj.Placement.Base.x` in place may not trigger an update without a reassignment + recompute.
- **Sketcher indices**: geometry is 0-based; the external `-1`/`-2` geoIds are the sketch axes.
- **Units are mm/deg**; angles for `App.Rotation(axis, angle)` are degrees.
- **Booleans consume their inputs' visibility**, not the objects — the `Base`/`Tool` still
  exist in the tree (hide them with `Visibility = False` if exporting only the result).
- **`Part.export` vs `Mesh.export`** are different modules for solid (B-rep) vs mesh output;
  pick by the target format above.
