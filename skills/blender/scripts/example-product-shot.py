# Product shot: model -> material -> three-point light -> camera -> measure -> render.
#
#   OUT=/tmp/out bash scripts/blender-send.sh scripts/example-product-shot.py
#
# Re-runnable: everything lives in the "product_v1" collection, which stage() clears on
# every send, so re-sending replaces the build instead of stacking duplicates.

coll = stage("product_v1")
OUTD = OUT or "/tmp"


def link(name, data, location=(0, 0, 0)):
    ob = bpy.data.objects.new(name, data)
    coll.objects.link(ob)
    ob.location = location
    return ob


# ---- geometry: a rounded body on a sweep backdrop -------------------------------------
me = bpy.data.meshes.new("Body")
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.18, segments=5, profile=0.5,
                affect="EDGES")
bm.to_mesh(me)
bm.free()
body = link("Body", me, (0, 0, 1.0))
body.data.shade_smooth()
# Weighted normals keep the flat faces flat and the bevels round, without a subsurf
# pass that would bloat the silhouette.
wn = body.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL")
wn.keep_sharp = True

# A photo-studio sweep: floor -> quarter-circle cove -> wall, as a profile in YZ that is
# extruded along X. Building it in bmesh beats bending a plane with a deform modifier,
# whose result depends on the grid's orientation and origin.
profile = [(y, 0.0) for y in (-8.0, -4.0, 0.0, 2.0)]
R = 3.0
for i in range(1, 12):
    a = math.radians(90 * i / 12)
    profile.append((2.0 + R * math.sin(a), R - R * math.cos(a)))
profile += [(2.0 + R, R), (2.0 + R, 10.0)]
floor_me = bpy.data.meshes.new("Backdrop")
bm = bmesh.new()
left = [bm.verts.new((-16.0, y, z)) for y, z in profile]
right = [bm.verts.new((16.0, y, z)) for y, z in profile]
for i in range(len(profile) - 1):
    bm.faces.new((left[i], left[i + 1], right[i + 1], right[i]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(floor_me)
bm.free()
floor = link("Backdrop", floor_me)
floor_me.shade_smooth()

# ---- materials ------------------------------------------------------------------------
shell = bpy.data.materials.new("Shell")
b = shell.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.72, 0.18, 0.14, 1.0)
b.inputs["Roughness"].default_value = 0.28
b.inputs["Metallic"].default_value = 0.0
b.inputs["Coat Weight"].default_value = 0.5
b.inputs["Coat Roughness"].default_value = 0.08
body.data.materials.append(shell)

paper = bpy.data.materials.new("Backdrop")
pb = paper.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = (0.85, 0.85, 0.87, 1.0)
pb.inputs["Roughness"].default_value = 0.9
floor.data.materials.append(paper)

# ---- world: dim, so the lights do the work --------------------------------------------
world = bpy.data.worlds.new("StudioWorld")
bpy.context.scene.world = world
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.02, 0.02, 0.025, 1.0)
bg.inputs["Strength"].default_value = 1.0

# ---- three-point lighting --------------------------------------------------------------
for name, kind, energy, size, loc in (
    ("Key",   "AREA", 600, 3.0, (3.5, -3.5, 4.0)),
    ("Fill",  "AREA", 150, 4.0, (-4.0, -2.0, 2.0)),
    ("Rim",   "AREA", 400, 1.5, (-1.5, 3.5, 3.0)),
):
    ld = bpy.data.lights.new(name, type=kind)
    ld.energy = energy
    ld.shape = "SQUARE"
    ld.size = size
    ld.color = (1.0, 0.97, 0.94) if name == "Key" else (0.9, 0.94, 1.0)
    lo = link(name, ld, loc)
    aim = lo.constraints.new("TRACK_TO")
    aim.target = body
    aim.track_axis = "TRACK_NEGATIVE_Z"
    aim.up_axis = "UP_Y"

# ---- camera -----------------------------------------------------------------------------
cd = bpy.data.cameras.new("Cam")
cd.lens = 50
cd.dof.use_dof = True
cd.dof.focus_object = body
cd.dof.aperture_fstop = 3.2
cam = link("Cam", cd, (7.5, -8.5, 4.2))
aim = cam.constraints.new("TRACK_TO")
aim.target = body
aim.track_axis = "TRACK_NEGATIVE_Z"
aim.up_axis = "UP_Y"
bpy.context.scene.camera = cam

sync()  # flush transforms + constraints before anything reads matrix_world

# ---- render settings --------------------------------------------------------------------
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.use_compositing = False   # an unterminated compositor group swallows the output
sc.render.use_sequencer = False     # so does a stray sequencer
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"

# ---- isolate: hide whatever else the live session already had open -----------------------
# A live Blender may hold the user's own objects. Excluding the other top-level collections
# from this view layer keeps them out of the shot without deleting anything, and we put it
# all back afterwards.
root = bpy.context.view_layer.layer_collection
hidden = [lc for lc in root.children if lc.collection is not coll and not lc.exclude]
# snapshot() is an OpenGL VIEWPORT render (obeys hide_viewport); render() obeys hide_render.
loose = [(o, o.hide_render, o.hide_viewport) for o in sc.collection.objects
         if not (o.hide_render and o.hide_viewport)]
for lc in hidden:
    lc.exclude = True
for o, _, _ in loose:
    o.hide_render = o.hide_viewport = True

try:
    # ---- verify --------------------------------------------------------------------------
    m = metrics([body, floor], path=os.path.join(OUTD, "metrics.json"))
    print("METRICS", json.dumps(m))

    print("VIEWPORT", snapshot(os.path.join(OUTD, "product_viewport.png"),
                               view="ISO", shading="MATERIAL", objs=[body, floor]))
    print("RENDER  ", render(os.path.join(OUTD, "product.png"),
                             engine="BLENDER_EEVEE", samples=64, width=1280, height=800))
finally:
    for lc in hidden:
        lc.exclude = False
    for o, was_render, was_viewport in loose:
        o.hide_render, o.hide_viewport = was_render, was_viewport

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTD, "product.blend"), copy=True)
print("BLEND   ", os.path.join(OUTD, "product.blend"))
