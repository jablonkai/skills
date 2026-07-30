# Grease Pencil v3 — 2D drawing in 3D space

Verified on Blender 5.2.0 LTS. Grease Pencil was rewritten for 4.3; everything from the
legacy API is gone:

| Legacy (≤4.2) | Blender 5.2 |
|---|---|
| object type `GPENCIL` | `GREASEPENCIL` |
| `bpy.ops.gpencil.*` | removed entirely |
| `layer.frames[i].strokes.new()` | `frame.drawing.add_strokes([n])` |
| `stroke.points.add(n)` then `.co` | pre-sized points with `.position` |

Note the data-block collection is `bpy.data.grease_pencils` (there is no
`grease_pencils_v3`), but the type it holds is the new `GreasePencil`.

## Creating

```python
gp = bpy.data.grease_pencils.new("GP")
ob = bpy.data.objects.new("GP", gp)
coll.objects.link(ob)
ob.type                                  # 'GREASEPENCIL'
```

Or from a preset (this also sets up a default material and layers):

```python
bpy.ops.object.grease_pencil_add(type="MONKEY")   # EMPTY | STROKE | MONKEY | LINEART …
ob = bpy.context.object
```

## Layers and frames

```python
layer = gp.layers.new("Lines")
layer.opacity = 1.0
layer.blend_mode = "REGULAR"             # REGULAR HARDLIGHT ADD SUBTRACT MULTIPLY DIVIDE
layer.use_onion_skinning = True
frm = layer.frames.new(1)                # keyframe at frame 1
frm.frame_number
```

Each `layer.frames[i]` holds one `drawing`. Add a frame per pose to animate.

## Drawing strokes

`add_strokes` takes a list of point counts — one entry per stroke — and pre-allocates them:

```python
drawing = layer.frames[0].drawing
pts = [(math.cos(i / 12 * math.tau) * 1.5,
        math.sin(i / 12 * math.tau) * 1.5, 0) for i in range(12)]
drawing.add_strokes([len(pts)])          # [12] -> one stroke of 12 points
stroke = drawing.strokes[0]
for p, co in zip(stroke.points, pts):
    p.position = co                      # NOT .co
    p.radius = 0.05
    p.opacity = 1.0
drawing.tag_positions_changed()          # flush after moving points
```

Several strokes at once: `drawing.add_strokes([12, 8, 30])`.

Stroke-level flags live on the stroke: `stroke.cyclic`, `stroke.material_index`,
`stroke.softness`, `stroke.start_cap`, `stroke.end_cap`.

Other `drawing` methods: `remove_strokes`, `resize_strokes`, `reorder_strokes`,
`set_types`, `attributes`, `color_attributes`, `curve_offsets`, `vertex_group_assign`,
`set_vertex_weights`.

Because strokes expose `attributes`, everything a mesh can do with named attributes works
here too — useful for driving geometry nodes off stroke data.

## Materials

Grease Pencil materials need their GP data attached explicitly:

```python
mat = bpy.data.materials.new("GPStroke")
bpy.data.materials.create_gpencil_data(mat)      # required
ob.data.materials.append(mat)
mat.grease_pencil.color = (0.1, 0.6, 1.0, 1.0)   # stroke colour
mat.grease_pencil.fill_color = (1.0, 0.9, 0.2, 1.0)
mat.grease_pencil.show_stroke = True
mat.grease_pencil.show_fill = False
mat.grease_pencil.mode = "LINE"                  # LINE | DOTS | BOX
mat.grease_pencil.stroke_style = "SOLID"         # SOLID | TEXTURE
mat.grease_pencil.fill_style = "SOLID"           # SOLID | GRADIENT | TEXTURE
```

Assign per stroke with `stroke.material_index`.

## Modifiers

All Grease Pencil modifiers are prefixed:

```python
m = ob.modifiers.new("Noise", "GREASE_PENCIL_NOISE")
```

Available: `GREASE_PENCIL_NOISE SMOOTH THICKNESS SUBDIV SIMPLIFY ARRAY BUILD LENGTH MIRROR
MULTIPLY OUTLINE ENVELOPE DASH OFFSET HOOK LATTICE ARMATURE SHRINKWRAP TIME TINT COLOR
OPACITY TEXTURE VERTEX_WEIGHT_ANGLE VERTEX_WEIGHT_PROXIMITY` (each as
`GREASE_PENCIL_<NAME>`), plus `LINEART` which is unprefixed.

## Line Art — 3D geometry as 2D linework

```python
gp = bpy.data.grease_pencils.new("LineArtGP")
ob = bpy.data.objects.new("LineArtGP", gp)
coll.objects.link(ob)
gp.layers.new("LA")

mat = bpy.data.materials.new("LAMat")
bpy.data.materials.create_gpencil_data(mat)
gp.materials.append(mat)

m = ob.modifiers.new("LineArt", "LINEART")
m.source_type = "SCENE"              # SCENE | COLLECTION | OBJECT
m.target_layer = "LA"                # both targets are REQUIRED or it renders nothing
m.target_material = mat
# m.source_collection / m.source_object for the narrower modes
# edge types: m.use_contour, use_crease, use_material, use_edge_mark,
#             use_intersection, use_light_contour
m.thickness = 25
```

Line Art re-evaluates the scene, so it is slow on heavy scenes and updates only on frame
change or an explicit `ob.update_tag()`.

## Animating

Draw a new frame per keyframe:

```python
for f, radius in ((1, 1.0), (12, 1.6), (24, 1.0)):
    frm = layer.frames.new(f)
    d = frm.drawing
    d.add_strokes([24])
    for i, p in enumerate(d.strokes[0].points):
        a = i / 24 * math.tau
        p.position = (math.cos(a) * radius, math.sin(a) * radius, 0)
        p.radius = 0.04
    d.tag_positions_changed()
```

Layer opacity, tint and modifier values are ordinary animatable properties — keyframe them
via `fcurve(ob, ...)` (see [animation-rigging.md](animation-rigging.md)).

## Export

```python
bpy.ops.wm.grease_pencil_export_svg(filepath=OUT + "/lines.svg")
bpy.ops.wm.grease_pencil_export_pdf(filepath=OUT + "/lines.pdf")
bpy.ops.wm.grease_pencil_import_svg(filepath="/path/logo.svg")
```
