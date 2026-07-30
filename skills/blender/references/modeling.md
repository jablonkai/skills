# Modeling — bmesh, modifiers, curves, text, UV

Verified on Blender 5.2.0 LTS. All vertex/face counts below are the real numbers this code
produced.

## bmesh — the way to author geometry from script

`bmesh` builds meshes in memory with no operator, no mode switching and no selection state.
It is the fastest and most predictable path.

```python
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.15, segments=3, affect="EDGES")
me = bpy.data.meshes.new("Beveled")
bm.to_mesh(me)                       # -> 50 faces
bm.free()                            # always free
ob = bpy.data.objects.new("Beveled", me)
coll.objects.link(ob)
```

Primitives: `create_cube`, `create_uvsphere(u_segments=, v_segments=, radius=)`,
`create_icosphere(subdivisions=, radius=)`, `create_cone`, `create_circle`, `create_grid(
x_segments=, y_segments=, size=)`, `create_monkey`, `create_vert`.

Key operators: `bevel`, `subdivide_edges`, `subdivide_edgering`, `extrude_face_region`,
`extrude_edge_only`, `extrude_vert_indiv`, `inset_region`, `inset_individual`, `spin`,
`solidify`, `bridge_loops`, `triangulate`, `join_triangles`, `dissolve_faces`, `poke`,
`mirror`, `symmetrize`, `remove_doubles`, `recalc_face_normals`, `split_edges`, `wireframe`,
`convex_hull`, `smooth_vert`, `transform`, `translate`, `rotate`, `scale`, `delete`,
`duplicate`.

### Indexing needs a lookup table

```python
bm.faces.ensure_lookup_table()       # bm.faces[0] raises IndexError without this
bm.verts.ensure_lookup_table()
```

### Extrude and move the new geometry

`extrude_face_region` returns mixed geometry — filter it:

```python
res = bmesh.ops.extrude_face_region(bm, geom=[bm.faces[0]])
verts = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
bmesh.ops.translate(bm, verts=verts, vec=(0, 0, 1.0))
```

### Lathe / revolve with spin

```python
bm = bmesh.new()
v = [bm.verts.new((r, 0, z)) for r, z in [(0.5, 0), (0.8, 0.4), (0.4, 0.9)]]
for a, b in zip(v, v[1:]):
    bm.edges.new((a, b))
bmesh.ops.spin(bm, geom=list(bm.verts) + list(bm.edges), axis=(0, 0, 1),
               steps=24, angle=math.radians(360), cent=(0, 0, 0))    # -> 48 faces
```

### Editing an existing mesh

```python
bm = bmesh.new()
bm.from_mesh(ob.data)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.to_mesh(ob.data)
bm.free()
```

## Shading (smooth / flat)

```python
ob.data.shade_smooth()               # data API, no operator
ob.data.shade_flat()
```

Auto-smooth is no longer a mesh property. It is an operator that appends a geometry-nodes
`NODES` modifier ("Smooth by Angle"):

```python
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
[m.type for m in ob.modifiers]       # -> ['NODES']
```

Custom split normals: `me.normals_split_custom_set_from_vertices([(0,0,1)] * len(me.vertices))`.

## Modifiers

```python
a = ob.modifiers.new("Array", "ARRAY")
a.count = 4
a.relative_offset_displace[0] = 1.2
s = ob.modifiers.new("Sub", "SUBSURF"); s.levels = 1; s.render_levels = 2
b = ob.modifiers.new("Bev", "BEVEL"); b.width = 0.02; b.segments = 2
sol = ob.modifiers.new("Sol", "SOLIDIFY"); sol.thickness = 0.05
len(evaluated(ob).to_mesh().vertices)      # -> 1744
```

Reorder and apply (operators — set the active object first):

```python
bpy.context.view_layer.objects.active = ob
bpy.ops.object.modifier_move_to_index(modifier="Sol", index=0)
bpy.ops.object.modifier_apply(modifier="Sol")     # bakes into ob.data
```

Common types: `ARRAY BEVEL BOOLEAN BUILD DECIMATE EDGE_SPLIT NODES MASK MIRROR MULTIRES
REMESH SCREW SKIN SOLIDIFY SUBSURF TRIANGULATE WELD WIREFRAME ARMATURE CAST CURVE DISPLACE
HOOK LATTICE SHRINKWRAP SIMPLE_DEFORM SMOOTH CORRECTIVE_SMOOTH SURFACE_DEFORM WARP WAVE
CLOTH COLLISION DYNAMIC_PAINT EXPLODE FLUID OCEAN PARTICLE_INSTANCE PARTICLE_SYSTEM
SOFT_BODY LINEART MESH_TO_VOLUME VOLUME_TO_MESH DATA_TRANSFER UV_PROJECT UV_WARP
WEIGHTED_NORMAL NORMAL_EDIT VERTEX_WEIGHT_EDIT VERTEX_WEIGHT_MIX VERTEX_WEIGHT_PROXIMITY`
plus the `GREASE_PENCIL_*` family.

### Boolean

```python
m = a.modifiers.new("Bool", "BOOLEAN")
m.operation = "DIFFERENCE"           # UNION | DIFFERENCE | INTERSECT
m.object = b
m.solver = "EXACT"                   # EXACT is robust; FLOAT is faster
b.hide_render = True                 # keep the cutter out of renders
```

## Curves

```python
cu = bpy.data.curves.new("Bez", type="CURVE")
cu.dimensions = "3D"
sp = cu.splines.new("BEZIER")        # BEZIER | POLY | NURBS
sp.bezier_points.add(2)              # add(n) gives n+1 points total
for i, co in enumerate([(0,0,0), (2,1,0), (4,0,1)]):
    p = sp.bezier_points[i]
    p.co = co
    p.handle_left_type = p.handle_right_type = "AUTO"
cu.bevel_depth = 0.08                # round profile -> tube
cu.bevel_resolution = 4
cu.extrude = 0.05                    # flat extrusion
cu.fill_mode = "FULL"
cu.resolution_u = 24
cu.use_fill_caps = True
ob = bpy.data.objects.new("Bez", cu); coll.objects.link(ob)
len(evaluated(ob).to_mesh().vertices)      # -> 300
```

POLY / NURBS use `.points` with 4-component coordinates:

```python
sp = cu.splines.new("POLY")
sp.points.add(3)
sp.points[0].co = (0, 0, 0, 1)       # x, y, z, w
sp.use_cyclic_u = True
```

## Text

```python
cu = bpy.data.curves.new("Txt", type="FONT")
cu.body = "BLENDER"
cu.size = 1.0
cu.extrude = 0.06
cu.bevel_depth = 0.01
cu.align_x = "CENTER"                # LEFT RIGHT CENTER JUSTIFY FLUSH
cu.align_y = "CENTER"
cu.space_character = 1.0
cu.font                              # 'Bfont Regular' is the built-in default
ob = bpy.data.objects.new("Txt", cu); coll.objects.link(ob)
```

Convert to a real mesh (4116 verts for "BLENDER" at these settings):

```python
me = bpy.data.meshes.new_from_object(evaluated(ob))
```

Load a font: `bpy.data.fonts.load("/path/Inter.ttf")` then `cu.font = ...`.

## Metaballs

```python
mb = bpy.data.metaballs.new("Meta")
mb.resolution = 0.15
for x in (-0.6, 0.0, 0.6):
    el = mb.elements.new()           # BALL CAPSULE PLANE ELLIPSOID CUBE
    el.co = (x, 0, 0)
    el.radius = 0.9
```

## UVs

```python
uv = me.uv_layers.new(name="UVMap")
for i, loop in enumerate(me.loops):
    uv.data[i].uv = (u, v)           # one entry per LOOP, not per vertex
```

Smart project needs edit mode (this is one of the operator-only paths):

```python
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(66))
bpy.ops.object.mode_set(mode="OBJECT")
```

## Vertex groups and material slots

```python
vg = ob.vertex_groups.new(name="Top")
vg.add([v.index for v in me.vertices if v.co.z > 0], 1.0, "REPLACE")

me.materials.append(mat_a)
me.materials.append(mat_b)
for i, poly in enumerate(me.polygons):
    poly.material_index = i % 2      # per-face slot assignment
```
