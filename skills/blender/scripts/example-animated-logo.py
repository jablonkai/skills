# Animated logo sting: extruded text -> keyframed reveal -> geometry-nodes sparkle scatter
# -> viewport check -> MP4.
#
#   OUT=/tmp/out bash scripts/blender-send.sh scripts/example-animated-logo.py
#
# Rendering blocks Blender's main thread, so the UI freezes for the duration. This renders
# 24 frames at 640x360 — raise BLENDER_SEND_TIMEOUT before scaling it up.

coll = stage("logo_v1")
OUTD = OUT or "/tmp"
sc = bpy.context.scene
START, END = 1, 24


def link(name, data, location=(0, 0, 0)):
    ob = bpy.data.objects.new(name, data)
    coll.objects.link(ob)
    ob.location = location
    return ob


# ---- extruded text ---------------------------------------------------------------------
cu = bpy.data.curves.new("Logo", type="FONT")
cu.body = "BLENDER"
cu.size = 1.0
cu.extrude = 0.08
cu.bevel_depth = 0.012
cu.bevel_resolution = 2
cu.align_x = "CENTER"
cu.align_y = "CENTER"
cu.space_character = 1.05
text = link("Logo", cu, (0, 0, 0))

gold = bpy.data.materials.new("Gold")
gold.use_nodes = True
g = gold.node_tree.nodes["Principled BSDF"]
g.inputs["Base Color"].default_value = (0.95, 0.72, 0.28, 1.0)
g.inputs["Metallic"].default_value = 1.0
g.inputs["Roughness"].default_value = 0.18
cu.materials.append(gold)

# ---- keyframed reveal: rise + settle ----------------------------------------------------
# Text objects are authored FLAT in the XY plane, so "upright" is rotation_euler.x = 90deg.
UPRIGHT = math.radians(90)
for f, (z, rx) in ((START, (-1.4, UPRIGHT - math.radians(70))),
                   (14,    (0.12, UPRIGHT + math.radians(6))),
                   (END,   (0.0, UPRIGHT))):
    text.location.z = z
    text.rotation_euler.x = rx
    text.keyframe_insert("location", index=2, frame=f)
    text.keyframe_insert("rotation_euler", index=0, frame=f)

# Action.fcurves is gone in 5.x — fcurves() walks the slotted-action channelbag.
for fc in fcurves(text):
    for kp in fc.keyframe_points:
        kp.interpolation = "BEZIER"
        kp.easing = "EASE_OUT"
    fc.keyframe_points[-1].interpolation = "BACK"
    fc.update()

# ---- geometry-nodes sparkle scatter over a backing plane --------------------------------
plane_me = bpy.data.meshes.new("Sparkles")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.8)
bm.to_mesh(plane_me)
bm.free()
plane = link("Sparkles", plane_me, (0, 0.4, -0.62))

gn = bpy.data.node_groups.new("SparkleScatter", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
dens = gn.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
dens.default_value = 30.0

gin = gn.nodes.new("NodeGroupInput");  gin.location = (-600, 0)
gout = gn.nodes.new("NodeGroupOutput"); gout.location = (600, 0)
dist = gn.nodes.new("GeometryNodeDistributePointsOnFaces"); dist.location = (-350, 0)
ico = gn.nodes.new("GeometryNodeMeshIcoSphere");            ico.location = (-350, -260)
ico.inputs["Radius"].default_value = 0.022
ico.inputs["Subdivisions"].default_value = 1
inst = gn.nodes.new("GeometryNodeInstanceOnPoints");        inst.location = (-80, 0)
real = gn.nodes.new("GeometryNodeRealizeInstances");        real.location = (180, 0)

L = gn.links.new
L(gin.outputs["Geometry"], dist.inputs["Mesh"])
L(gin.outputs["Density"], dist.inputs["Density"])
L(dist.outputs["Points"], inst.inputs["Points"])
L(ico.outputs["Mesh"], inst.inputs["Instance"])
L(inst.outputs["Instances"], real.inputs["Geometry"])
L(real.outputs["Geometry"], gout.inputs["Geometry"])

mod = plane.modifiers.new("Scatter", "NODES")
mod.node_group = gn

# 5.x socket assignment — mod["Socket_2"] = ... raises TypeError.
density_id = [it.identifier for it in gn.interface.items_tree
              if it.item_type == "SOCKET" and it.name == "Density"][0]
mod.properties.inputs[density_id]["value"] = 90.0
plane.update_tag()

glow = bpy.data.materials.new("Glow")
glow.use_nodes = True
gb = glow.node_tree.nodes["Principled BSDF"]
gb.inputs["Emission Color"].default_value = (1.0, 0.85, 0.5, 1.0)
gb.inputs["Emission Strength"].default_value = 12.0
plane_me.materials.append(glow)

# ---- world, light, camera ----------------------------------------------------------------
world = bpy.data.worlds.new("LogoWorld")
sc.world = world
world.use_nodes = True
bgn = world.node_tree.nodes["Background"]
bgn.inputs["Color"].default_value = (0.01, 0.012, 0.02, 1.0)
bgn.inputs["Strength"].default_value = 1.0

ld = bpy.data.lights.new("Key", type="AREA")
ld.energy, ld.size = 500, 4.0
key = link("Key", ld, (2.5, -3.0, 3.0))
aim = key.constraints.new("TRACK_TO")
aim.target = text
aim.track_axis = "TRACK_NEGATIVE_Z"
aim.up_axis = "UP_Y"

cd = bpy.data.cameras.new("Cam")
cd.lens = 50
cam = link("Cam", cd, (0, -6.2, 1.1))
cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam

sync()

# ---- scene / render settings --------------------------------------------------------------
sc.frame_start, sc.frame_end = START, END
sc.render.fps = 24
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 16
sc.render.use_compositing = False     # an unterminated compositor group eats the output
sc.render.use_sequencer = False       # so does a stray sequencer
sc.view_settings.view_transform = "AgX"

# ---- isolate from whatever else the live session has open ----------------------------------
root = bpy.context.view_layer.layer_collection
hidden = [lc for lc in root.children if lc.collection is not coll and not lc.exclude]
# snapshot() is an OpenGL VIEWPORT render, so it obeys hide_viewport; render() obeys
# hide_render. Set both or leftovers from the live session leak into one of the two.
loose = [o for o in sc.collection.objects if not (o.hide_render and o.hide_viewport)]
for lc in hidden:
    lc.exclude = True
for o in loose:
    o.hide_render = o.hide_viewport = True

try:
    frame(END)
    print("METRICS", json.dumps(metrics([text, plane],
                                        path=os.path.join(OUTD, "logo_metrics.json"))))
    print("POSE   ", [round(v, 3) for v in evaluated(text).matrix_world.translation])
    print("CHECK  ", snapshot(os.path.join(OUTD, "logo_check.png"),
                              view="CAMERA", shading="RENDERED", fit=None))

    # ---- video ----------------------------------------------------------------------------
    r = sc.render
    saved = (r.filepath, r.image_settings.media_type, r.image_settings.file_format,
             r.resolution_x, r.resolution_y)
    try:
        r.resolution_x, r.resolution_y = 640, 360
        r.image_settings.media_type = "VIDEO"        # REQUIRED before FFMPEG
        r.image_settings.file_format = "FFMPEG"
        r.ffmpeg.format = "MPEG4"
        r.ffmpeg.codec = "H264"
        r.ffmpeg.constant_rate_factor = "MEDIUM"
        r.filepath = os.path.join(OUTD, "logo.mp4")
        bpy.ops.render.render(animation=True)
    finally:
        (r.filepath, r.image_settings.media_type, r.image_settings.file_format,
         r.resolution_x, r.resolution_y) = saved

    made = sorted(f for f in os.listdir(OUTD) if f.startswith("logo") and f.endswith(".mp4"))
    print("VIDEO  ", made, [os.path.getsize(os.path.join(OUTD, f)) for f in made])
finally:
    for lc in hidden:
        lc.exclude = False
    for o in loose:
        o.hide_render = o.hide_viewport = False

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTD, "logo.blend"), copy=True)
print("BLEND  ", os.path.join(OUTD, "logo.blend"))
