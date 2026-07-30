# Animation & rigging — keyframes, slotted actions, drivers, NLA, armatures

Verified on Blender 5.2.0 LTS. **Read the first section before writing any animation code** —
`Action.fcurves` no longer exists and almost every example online still uses it.

## Keyframes

Inserting is unchanged:

```python
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 48
for f, z in ((1, 0.0), (24, 3.0), (48, 0.0)):
    ob.location.z = z
    ob.keyframe_insert("location", index=2, frame=f)   # index=2 -> Z only; omit for all
```

Other data paths: `"rotation_euler"`, `"rotation_quaternion"`, `"scale"`,
`"hide_viewport"`, `"data.lens"`, `'["custom_prop"]'`, and for nested IDs the full path from
the owning ID (see the VSE example below).

## Slotted actions — where F-curves actually live

Blender 4.4 introduced action **slots** and **layers**; 5.x removed the flat accessor:

```python
act = ob.animation_data.action
act.fcurves                          # AttributeError: 'Action' object has no attribute 'fcurves'
[s.identifier for s in act.slots]    # ['OBAnim']
[l.name for l in act.layers]         # ['Layer']
```

The real path is action → layer → strip → channelbag(slot) → fcurves:

```python
ad  = ob.animation_data
act = ad.action
cb  = act.layers[0].strips[0].channelbag(ad.action_slot)
[(f.data_path, f.array_index, len(f.keyframe_points)) for f in cb.fcurves]
# [('location', 2, 3)]
```

The bridge wraps this:

```python
fcurves(ob)                          # list of F-curves, [] if unanimated
fcurve(ob, "rotation_euler", 2)      # one curve, created if missing
channelbag(ob)                       # the bag itself, for .fcurves.new()/.remove()
```

Building an action from scratch:

```python
a   = bpy.data.actions.new("Manual")
sl  = a.slots.new(id_type="OBJECT", name="Cube")
lay = a.layers.new("Layer")
st  = lay.strips.new(type="KEYFRAME")
cb  = st.channelbag(sl, ensure=True)
fc  = cb.fcurves.new("location", index=0)
fc.keyframe_points.insert(1, 0.0)
fc.keyframe_points.insert(30, 5.0)

ob.animation_data_create()
ob.animation_data.action = a
ob.animation_data.action_slot = sl   # binding the slot is required, or nothing animates
```

## Interpolation, easing, handles

```python
fc = fcurves(ob)[0]
for kp in fc.keyframe_points:
    kp.interpolation = "BEZIER"      # CONSTANT LINEAR BEZIER SINE QUAD CUBIC QUART
                                     # QUINT EXPO CIRC BACK BOUNCE ELASTIC
    kp.easing = "EASE_IN_OUT"        # AUTO EASE_IN EASE_OUT EASE_IN_OUT
    kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
    # kp.handle_left = (frame, value) for manual control
fc.update()                          # re-sort and recalculate handles

fc.evaluate(12)                      # sample the curve without changing the frame
```

F-curve modifiers for procedural motion:

```python
m = fc.modifiers.new("CYCLES")       # CYCLES GENERATOR FNGENERATOR NOISE LIMITS
                                     # STEPPED ENVELOPE
```

## Sampling animation

Physics and constraints need frames stepped in order; a bare `frame_set` to the end gives an
unsimulated result:

```python
for f in (1, 24, 48):
    frame(f)                         # scene.frame_set(n) + depsgraph update
    ob.matrix_world.translation.z    # 0.0, 3.0, 0.0
```

## Drivers

```python
fcu = dst.driver_add("rotation_euler", 2)
drv = fcu.driver
drv.type = "SCRIPTED"                # AVERAGE SUM SCRIPTED MIN MAX
var = drv.variables.new()
var.name = "z"
var.type = "TRANSFORMS"              # SINGLE_PROP TRANSFORMS ROTATION_DIFF LOC_DIFF
tgt = var.targets[0]
tgt.id = src
tgt.transform_type = "LOC_Z"
tgt.transform_space = "WORLD_SPACE"
drv.expression = "z * 2.0"
src.location.z = 1.0
sync()
dst.rotation_euler.z                 # 2.0
```

For `SINGLE_PROP` set `tgt.id_type`, `tgt.id` and `tgt.data_path` instead.
Remove with `dst.driver_remove("rotation_euler", 2)`.

## NLA

```python
ad = ob.animation_data
act = ad.action
ad.action = None                     # push the active action off the stack first
tr = ad.nla_tracks.new()
tr.name = "Base"
strip = tr.strips.new("Jump", 1, act)          # (name, start frame, action)
strip.blend_type = "REPLACE"                   # REPLACE COMBINE ADD SUBTRACT MULTIPLY
strip.influence = 1.0
strip.repeat = 2.0
strip.extrapolation = "HOLD"                   # NOTHING HOLD HOLD_FORWARD
```

## Shape keys

```python
basis = ob.shape_key_add(name="Basis", from_mix=False)   # always create Basis first
key   = ob.shape_key_add(name="Squash", from_mix=False)
for p in key.data:
    p.co = p.co * Vector((1.4, 1.4, 0.4))
key.slider_min, key.slider_max = 0.0, 1.5
key.value = 0.0; key.keyframe_insert("value", frame=1)
key.value = 1.0; key.keyframe_insert("value", frame=24)
[k.name for k in ob.data.shape_keys.key_blocks]          # ['Basis', 'Squash']
```

## Armatures

Edit bones only exist in edit mode — this is one of the operator-only workflows:

```python
arm = bpy.data.armatures.new("Rig")
rig = bpy.data.objects.new("Rig", arm)
coll.objects.link(rig)

bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
prev = None
for i, (head, tail) in enumerate([((0,0,0), (0,0,1)),
                                  ((0,0,1), (0,0,2)),
                                  ((0,0,2), (0,0,3))]):
    eb = arm.edit_bones.new("bone%d" % i)
    eb.head, eb.tail = head, tail
    if prev:
        eb.parent = prev
        eb.use_connect = True
    prev = eb
bpy.ops.object.mode_set(mode="OBJECT")   # edit_bones become arm.bones here
```

`eb.roll` controls the bone's twist. After leaving edit mode the `EditBone` references are
invalid — re-fetch through `arm.bones[...]` or `rig.pose.bones[...]`.

## Pose bones and constraints

```python
pb = rig.pose.bones["bone1"]
pb.rotation_mode = "XYZ"                 # default is QUATERNION
pb.rotation_euler = (0.3, 0, 0)
pb.keyframe_insert("rotation_euler", frame=1)

ik = rig.pose.bones["bone2"].constraints.new("IK")
ik.target = target_object
ik.chain_count = 3
# ik.pole_target / ik.pole_angle for knee/elbow direction

lim = rig.pose.bones["bone0"].constraints.new("LIMIT_ROTATION")
lim.use_limit_x = True
lim.min_x, lim.max_x = math.radians(-30), math.radians(30)
sync()
```

Bone collections replaced bone layers (`arm.layers` is gone):

```python
bc = arm.collections.new("Controls")
bc.assign(arm.bones["bone0"])
```

## Skinning

```python
mod = body.modifiers.new("Armature", "ARMATURE")
mod.object = rig
for b in rig.data.bones:
    vg = body.vertex_groups.new(name=b.name)     # group name must match the bone name
    vg.add([v.index for v in body.data.vertices], weight, "REPLACE")
```

Automatic weights need the operator: select the mesh, make the armature active, then
`bpy.ops.object.parent_set(type="ARMATURE_AUTO")`.

## Object constraints

```python
for kind in ("COPY_LOCATION", "COPY_ROTATION", "TRACK_TO", "LIMIT_DISTANCE",
             "FOLLOW_PATH", "CHILD_OF", "DAMPED_TRACK", "SHRINKWRAP"):
    c = ob.constraints.new(kind)
ob.constraints.remove(ob.constraints[-1])
```

## Baking constraints and drivers into keys

```python
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.nla.bake(frame_start=1, frame_end=10, only_selected=True,
                 visual_keying=True, clear_constraints=False,
                 bake_types={"OBJECT"})          # or {"POSE"}
```
