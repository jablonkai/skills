# Core API — data-blocks, scene graph, transforms, depsgraph

Verified on Blender 5.2.0 LTS. `bpy`, `bmesh`, `mathutils`, `Vector`, `Matrix`, `Euler`,
`Quaternion`, `math`, `os`, `json` and the bridge helpers are pre-imported in every script.

## Data-blocks vs objects

Blender separates **data** (mesh, curve, light, camera) from the **object** that places it in
a scene. Creating anything is always two steps plus a link:

```python
me = bpy.data.meshes.new("Plate")          # the data-block
ob = bpy.data.objects.new("Plate", me)     # the object wrapping it
coll.objects.link(ob)                      # into a collection -> visible in the scene
```

`bpy.data.*` collections: `objects`, `meshes`, `curves`, `materials`, `images`, `lights`,
`cameras`, `armatures`, `actions`, `collections`, `scenes`, `worlds`, `node_groups`,
`grease_pencils`, `metaballs`, `particles`, `texts`, `fonts`, `libraries`.

```python
me.from_pydata([(0,0,0), (1,0,0), (1,1,0)], [], [(0,1,2)])   # verts, edges, faces
me.update()
me.validate()                                                 # False = no problems fixed
```

## Collections

```python
sub = bpy.data.collections.new("Sub")
coll.children.link(sub)                    # nest
sub.objects.link(ob)                       # an object may live in several collections
sub.objects.unlink(ob)
len(ob.users_collection)
```

Collection instancing (cheap repeats of a whole group):

```python
e = bpy.data.objects.new("Inst", None)
e.instance_type = "COLLECTION"
e.instance_collection = sub
coll.objects.link(e)
```

`stage("name")` returns a get-or-recreate collection and makes it the active one — use it as
the root of every build so re-sends replace their own output. See [SKILL.md](../SKILL.md).

## Transforms

```python
ob.location = (1, 2, 3)
ob.rotation_euler = (0.1, 0.2, 0.3)        # radians
ob.scale = (2, 2, 2)
ob.delta_location = (0, 0, 1)              # stacks on top of location
ob.rotation_mode = "QUATERNION"            # then use ob.rotation_quaternion
ob.matrix_world = Matrix.Translation((5, 0, 0))   # assigning the matrix works too
sync()                                     # REQUIRED before reading matrix_world
```

Aim an object at a point without an operator:

```python
direction = Vector((0, 0, 0)) - ob.location
ob.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
```

Parenting keeps the child in place only if you also set the inverse:

```python
child.parent = ob
child.matrix_parent_inverse = ob.matrix_world.inverted()
sync()
```

## Copies

```python
dup = ob.copy()                 # linked duplicate: dup.data is ob.data (shared)
coll.objects.link(dup)

deep = ob.copy()
deep.data = ob.data.copy()      # independent geometry
coll.objects.link(deep)

ob.data.users                   # how many objects share this data-block
```

## Selection and the active object

Operators act on these — set both explicitly before calling any `bpy.ops`:

```python
for o in bpy.context.selected_objects:
    o.select_set(False)
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
```

## Depsgraph — Blender's "recompute"

Modifier, geometry-nodes and constraint results live only on the **evaluated** copy:

```python
ev = evaluated(ob)              # ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = ev.to_mesh()
len(mesh.vertices)              # 26 with a subsurf; ob.data.vertices is still 8
ev.to_mesh_clear()              # release it
```

Instances (geometry-nodes scatters, collection instances) are **not** in `to_mesh()`:

```python
dg = bpy.context.evaluated_depsgraph_get()
sum(1 for i in dg.object_instances if i.is_instance)     # 3600
```

Add a **Realize Instances** node to fold them into real geometry.

## Scene and view layers

```python
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = 1, 48, 25
sc.unit_settings.system = "METRIC"
sc.unit_settings.length_unit = "METERS"
sc.view_layers.new("Extra")
bpy.data.scenes.new("Second")
bpy.context.window.scene = bpy.data.scenes["Second"]     # switch the active scene

ob.hide_viewport = True         # per-object visibility
ob.hide_render = True
```

## Custom properties and attributes

```python
ob["k"] = 7                                   # object custom property
ob.id_properties_ui("k").as_dict()["default"]

at = me.attributes.new(name="heat", type="FLOAT", domain="POINT")
at.data.foreach_set("value", [v.co.z for v in me.vertices])
```

Domains: `POINT`, `EDGE`, `FACE`, `CORNER`, `CURVE`, `INSTANCE`. Types include `FLOAT`,
`INT`, `FLOAT_VECTOR`, `FLOAT_COLOR`, `BOOLEAN`, `QUATERNION`.

`foreach_set` / `foreach_get` are the fast bulk path — use them instead of Python loops for
anything over a few thousand elements.

## Cleanup

```python
bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.orphans_purge(do_recursive=True)     # returns the number of data-blocks freed
```

## Reading the scene without writing a script

`bash scripts/blender-send.sh --state` returns objects with types, collections, materials,
images, node groups, frame range, resolution, engine and the dirty flag as JSON. Use it
before writing a build script against a scene the user already has open.
