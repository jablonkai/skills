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


# ---- geometry: a rounded body on a backdrop ------------------------------------------
me = bpy.data.meshes.new("Body")
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.12, segments=6, affect="EDGES")
bm.to_mesh(me)
bm.free()
body = link("Body", me, (0, 0, 1.0))
body.data.shade_smooth()

sub = body.modifiers.new("Sub", "SUBSURF")
sub.levels, sub.render_levels = 1, 2

# a curved backdrop: a grid bent by a Simple Deform modifier
floor_me = bpy.data.meshes.new("Backdrop")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=32, size=6.0)
bm.to_mesh(floor_me)
bm.free()
floor = link("Backdrop", floor_me, (0, 2.0, 0))
bend = floor.modifiers.new("Bend", "SIMPLE_DEFORM")
bend.deform_method = "BEND"
bend.angle = math.radians(90)
bend.deform_axis = "X"

# ---- materials ------------------------------------------------------------------------
shell = bpy.data.materials.new("Shell")
shell.use_nodes = True
b = shell.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.72, 0.18, 0.14, 1.0)
b.inputs["Roughness"].default_value = 0.28
b.inputs["Metallic"].default_value = 0.0
b.inputs["Coat Weight"].default_value = 0.5
b.inputs["Coat Roughness"].default_value = 0.08
body.data.materials.append(shell)

paper = bpy.data.materials.new("Backdrop")
paper.use_nodes = True
pb = paper.node_tree.nodes["Principled BSDF"]
pb.inputs["Base Color"].default_value = (0.85, 0.85, 0.87, 1.0)
pb.inputs["Roughness"].default_value = 0.9
floor.data.materials.append(paper)

# ---- world: dim, so the lights do the work --------------------------------------------
world = bpy.data.worlds.new("StudioWorld")
bpy.context.scene.world = world
world.use_nodes = True
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
loose = [o for o in sc.collection.objects if not o.hide_render]
for lc in hidden:
    lc.exclude = True
for o in loose:
    o.hide_render = True

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
    for o in loose:
        o.hide_render = False

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTD, "product.blend"), copy=True)
print("BLEND   ", os.path.join(OUTD, "product.blend"))
