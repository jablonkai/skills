# FreeCAD Python API reference (condensed)

Verified against **FreeCAD 1.1.3** on macOS. Units are **millimetres** and **degrees**
by default. Scripts run inside a live FreeCAD GUI session via the bridge, so both the
modelling API and the `FreeCADGui` view/screenshot calls work. For anything beyond this digest, the authoritative
source is the FreeCAD Python wiki — <https://wiki.freecad.org/Python_scripting_tutorial>
and the per-workbench "Scripting" pages (e.g. `Part_scripting`, `Sketcher_scripting`,
`PartDesign_Scripting`, `Draft_API`, `TechDraw_API`, `Mesh_Scripting`) — grep those for
exact signatures.

## App / document model

```python
import FreeCAD as App
if "thing" in App.listDocuments():     # re-runnable: newDocument on a taken name
    App.closeDocument("thing")         # silently creates "thing1" instead of failing
doc = App.newDocument("thing")
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
`obj.Placement.Base` is the translation; `obj.Placement.Base = App.Vector(...)` and even
`obj.Placement.Base.x = 5` take effect (verified) — recompute afterwards.

## Part workbench — direct solids (`import Part`)

Primitives are objects with parametric attributes:

```python
box = doc.addObject("Part::Box", "Box");  box.Length, box.Width, box.Height = 40, 20, 10
cyl = doc.addObject("Part::Cylinder", "Cyl"); cyl.Radius, cyl.Height = 5, 10
sph = doc.addObject("Part::Sphere", "Sph"); sph.Radius = 8
con = doc.addObject("Part::Cone", "Cone"); con.Radius1, con.Radius2, con.Height = 6, 2, 12
tor = doc.addObject("Part::Torus", "Tor"); tor.Radius1, tor.Radius2 = 10, 3
```

Booleans take `Base` and `Tool`; `Part::MultiFuse` / `Part::MultiCommon` take `Shapes = [...]`:

```python
cut  = doc.addObject("Part::Cut", "Cut");     cut.Base, cut.Tool = box, cyl
fuse = doc.addObject("Part::Fuse", "Fuse");   fuse.Base, fuse.Tool = box, cyl
comm = doc.addObject("Part::Common", "Comm"); comm.Base, comm.Tool = box, cyl   # intersection
doc.recompute()
```

`Part::Cut`/`Fuse`/`Common` hide their inputs automatically; `Part::Fillet`/`Chamfer` do **not**
— hide the base yourself or it shows through in screenshots. Fillet / chamfer edges of an
existing feature (edge numbers are 1-based here):

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
shp.check()              # None if ok; raises on defects
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
Tangent, PointOnObject, Distance, DistanceX, DistanceY, Radius, Diameter, Angle, Symmetric`.
Geometry endpoints are addressed as `(geoId, pointPos)` with pointPos `1` = start, `2` = end,
`3` = centre. geoId `-1` is the sketch's H axis (its start point `(-1, 1)` is the origin),
`-2` the V axis.

```python
sk.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 30.0))  # point→point, X only
sk.addConstraint(Sketcher.Constraint("DistanceX", -1, 1, 0, 1, 5.0))  # origin → start of line 0
sk.addConstraint(Sketcher.Constraint("PointOnObject", 0, 1, -1))      # pin onto the H axis
sk.addConstraint(Sketcher.Constraint("Diameter", 4, 10.0))            # circle geoId 4
doc.recompute()
sk.FullyConstrained      # True once no degrees of freedom are left — check it for editable parts
sk.solve()               # 0 = solved; non-zero = conflicting/redundant constraints
```

**Placing a sketch.** An unattached sketch (`MapMode == "Deactivated"`) lies on the XY plane.
To sketch elsewhere, attach it — to a body origin plane or to a face of an earlier feature:

```python
plane = [f for f in body.Origin.OriginFeatures if f.Role == "XZ_Plane"][0]  # XY_/XZ_/YZ_Plane
sk.AttachmentSupport = [(plane, "")]; sk.MapMode = "FlatFace"
sk2.AttachmentSupport = [(pad, "Face6")]; sk2.MapMode = "FlatFace"  # a face; top of a Box / rectangle Pad = Face6
```

Look up origin features by `Role`, not by name — a second body's planes are `XZ_Plane001`.
On an XZ-attached sketch, sketch X is world X and sketch Y is world Z.

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

Feature types and the properties that actually drive them (verified):

```python
pad.Length = 10; pad.Reversed = True; pad.Midplane = True
pk = body.newObject("PartDesign::Pocket", "Pocket"); pk.Profile = sk2
pk.Type = "ThroughAll"            # enum: Length, ThroughAll, UpToFirst, UpToFace, TwoLengths, UpToShape
                                  # (there is no ThroughAll bool property)
rev = body.newObject("PartDesign::Revolution", "Rev"); rev.Profile = sk
rev.ReferenceAxis = (sk, ["V_Axis"]); rev.Angle = 360   # or (sk, ["H_Axis"]), or an origin axis
fil = body.newObject("PartDesign::Fillet", "Fillet")
fil.Base = (pk, ["Edge1", "Edge2"]); fil.Radius = 1     # (feature, [edge names]); Chamfer: .Size

# Patterns: newObject does NOT move the Tip onto a pattern — set it, or body.Shape still
# shows the unpatterned solid and the next newObject is inserted *before* the pattern.
lp = body.newObject("PartDesign::LinearPattern", "LP")
lp.Originals = [pk]; lp.Direction = (sk, ["H_Axis"]); lp.Length = 48; lp.Occurrences = 2
body.Tip = lp                                           # Length = first→last distance
z = [f for f in body.Origin.OriginFeatures if f.Role == "Z_Axis"][0]
pp = body.newObject("PartDesign::PolarPattern", "PP")
pp.Originals = [pk]; pp.Axis = (z, [""]); pp.Angle = 360; pp.Occurrences = 6  # or (sk, ["N_Axis"])
body.Tip = pp
doc.recompute()
```

**Pick edges and faces by geometry, not by guessed index.** `Edge1` of a cylinder-like solid
is often the seam line, and filleting/chamfering a seam leaves the feature `Invalid`:

```python
edges = [i + 1 for i, e in enumerate(feat.Shape.Edges)
         if e.Curve.TypeId == "Part::GeomCircle" and abs(e.Curve.Radius - 20) < 1e-6]
top = [i + 1 for i, f in enumerate(feat.Shape.Faces)
       if f.Surface.TypeId == "Part::GeomPlane" and abs(f.CenterOfMass.z - 5) < 1e-6]
```

Also `Groove` (subtractive revolution, same props as `Revolution`), `Loft`, `Sweep`,
`Chamfer` (`Size`), `Mirrored`, `Hole`. `body.Tip` is the final feature; `body.Shape` is the
solid. A sketch revolved about its own `V_Axis` must stay on one side of it — a profile that
crosses the axis makes the feature `Invalid`.

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
| `Mesh.export([objs], path)` | `.stl`, `.obj`, `.ply`, `.3mf`, `.amf`, `.off` |
| `Import.insert(path, docName)` | STEP / IGES into an existing document (verified); `Import.open(path)` opens a new document but returns `None` — find it via `App.ActiveDocument` |
| `Part.read(path)` | STEP / IGES / BREP straight to a `TopoShape`, no document objects |
| `Mesh.insert(path, docName)` | STL / OBJ / PLY into a document |

`importDXF`, `importSVG` (2D), and `importOBJ` submodules exist for those niche formats.
`Part.export`/`Mesh.export` pick the exporter from the file extension. In the live GUI
`Mesh.export` reuses the coarse display tessellation (796 facets for a part that gets 4060
headless), so its resolution depends on view settings; for a finer STL build the mesh explicitly with
`MeshPart.meshFromShape(Shape=..., LinearDeflection=0.05, AngularDeflection=0.2)` and
`mesh.write(path)`.

## GUI & screenshots (live — `Gui` is pre-imported by the bridge)

```python
view = Gui.getDocument(doc.Name).activeView()            # this doc's view, not whichever is active
view.setAnimationEnabled(False)   # REQUIRED before scripted shots: view changes animate, and
                                  # saveImage right after would capture the camera mid-turn
view.viewIsometric(); view.viewFront(); view.viewTop()   # standard views
view.fitAll()                                            # frame all visible objects
view.saveImage("/abs/shot.png", 1000, 750, "White")      # w, h, background
```

Objects you create in the session are visible by default, so `ViewFit` + `saveImage`
capture them directly.

## TechDraw — 2D technical drawings (verified: views + dimensions → PDF/SVG)

```python
import os, time, TechDraw, TechDrawGui
page = doc.addObject("TechDraw::DrawPage", "Page")
tmpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
tmpl.Template = os.path.join(App.getResourceDir(), "Mod", "TechDraw", "Templates", "ISO",
                             "A4_Landscape_ISO5457_minimal.svg")   # frame + title block, 297 x 210
page.Template = tmpl         # (Default_Template_A4_Landscape.svg is an empty sheet, no frame)
texts = {k: "" for k in tmpl.EditableTexts}   # the ISO templates ship sample values
texts.update(title="Bracket", drawing_number="BR-001", scale="2:1")   # ("B. Hecate", ...)
tmpl.EditableTexts = texts   # a copy comes back — edit the dict, then assign it whole
# keys: title, creator, drawing_number, scale, part_material, date_of_issue, revision_index, ...
top = doc.addObject("TechDraw::DrawViewPart", "Top"); page.addView(top)
top.Source = [part]; top.Direction = App.Vector(0, 0, 1)   # front: (0,-1,0), right: (1,0,0)
top.X, top.Y = 90, 140                                     # view centre on the page (mm)
top.ScaleType = "Custom"; top.Scale = 2   # ScaleType defaults to "Page": Scale is IGNORED otherwise
doc.recompute()

# View geometry is computed in a BACKGROUND THREAD: wait for it before dimensioning,
# or every dimension references nothing and measures 0.0.
t0 = time.time()
while not top.getVisibleEdges() and time.time() - t0 < 20:
    Gui.updateGui(); time.sleep(0.1)
for i, e in enumerate(top.getVisibleEdges()):              # find the edge to dimension:
    print(i, round(e.Length, 2), e.Curve.TypeId)           # index i == "Edge<i>"; lengths are
                                                           # SCALED (a 50 mm edge at 2:1 = 100)

dim = doc.addObject("TechDraw::DrawViewDimension", "DimW")
dim.Type = "DistanceX"                   # DistanceX/DistanceY/Distance/Radius/Diameter/Angle
dim.References2D = [(top, "Edge1")]; page.addView(dim)
dim.X, dim.Y = 0, -40                    # label offset from the view centre (page mm) — left at
                                         # 0,0 every dimension piles up in the middle of the view
doc.recompute()
print(dim.getRawValue())                 # model units, independent of view Scale — 0.0 = wrong ref
# ISO first-angle projection: the front view sits ABOVE the top view.

# The template (frame, title block) is only rendered once the page has been opened in the GUI;
# export before that and the PDF/SVG contains the views but no frame.
page.ViewObject.doubleClicked()
for _ in range(10):
    Gui.updateGui(); time.sleep(0.05)
TechDrawGui.exportPageAsPdf(page, OUT + "/drawing.pdf")
TechDrawGui.exportPageAsSvg(page, OUT + "/drawing.svg")
```

A `DistanceX` on a vertical edge is legitimately `0.0` — pick edges by printing their length
and curve type (circles: `Part::GeomCircle`, use `Diameter`). Check the exported PDF with
`qlmanage -t -s 1000 -o <dir> drawing.pdf` and Read the PNG.

## Gotchas

- **`doc.recompute()` before every measure or export** — attributes set on parametric
  objects don't propagate to `.Shape` until recompute.
- **Failed features don't raise**: `recompute()` returns normally and the feature's `State`
  contains `"Invalid"`. Scan `doc.Objects` for it before measuring.
- **TechDraw is asynchronous**: wait for `view.getVisibleEdges()` before adding dimensions.
- **Sketcher indices**: geometry is 0-based; the external `-1`/`-2` geoIds are the sketch axes.
- **Units are mm/deg**; angles for `App.Rotation(axis, angle)` are degrees.
- **Booleans hide their inputs**, they don't consume them — `Base`/`Tool` still exist in the
  tree; export only the result feature.
- **`Part.export` vs `Mesh.export`** are different modules for solid (B-rep) vs mesh output;
  pick by the target format above.
