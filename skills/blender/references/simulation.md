# Simulation — rigid body, cloth, soft body, particles, fluid

Verified on Blender 5.2.0 LTS. Physics is one of the areas where operators are unavoidable:
`rigidbody.*` and `ptcache.*` have no data-API equivalent.

Every sim needs frames **stepped in order from the start**. Jumping to the last frame gives
an unsimulated result.

```python
for f in range(1, 41):
    frame(f)
```

Because the bridge runs on the main thread, a long bake freezes the UI. Keep resolutions and
frame ranges small while iterating.

## Rigid body

The world must exist before any body can be added:

```python
bpy.ops.rigidbody.world_add()
rw = bpy.context.scene.rigidbody_world
rw.point_cache.frame_start = 1
rw.point_cache.frame_end = 60

def activate(ob):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

activate(floor)
bpy.ops.rigidbody.object_add(type="PASSIVE")
floor.rigid_body.collision_shape = "MESH"

activate(box)
bpy.ops.rigidbody.object_add(type="ACTIVE")
box.rigid_body.mass = 2.0
box.rigid_body.friction = 0.6
box.rigid_body.restitution = 0.3          # bounciness
box.rigid_body.collision_shape = "BOX"    # CONVEX_HULL MESH BOX SPHERE CAPSULE
                                          # CYLINDER CONE COMPOUND
box.rigid_body.kinematic = False          # True = animated, drives other bodies
```

Verified falling: three boxes at z = 2.0 / 3.2 / 4.4 land at z = 0.44 by frame 40.

Read simulated positions off the **evaluated** object:

```python
frame(40)
evaluated(box).matrix_world.translation.z
```

Constraints (hinges, springs) go through `bpy.ops.rigidbody.constraint_add()` then
`ob.rigid_body_constraint.type = "HINGE"` / `"GENERIC_SPRING"` / `"POINT"` etc.

## Cloth

```python
m = cloth_obj.modifiers.new("Cloth", "CLOTH")
st = m.settings
st.quality = 5                      # solver steps per frame
st.mass = 0.3
st.tension_stiffness = 15
st.compression_stiffness = 15
st.bending_stiffness = 0.5
st.air_damping = 1.0
m.collision_settings.use_self_collision = True
m.collision_settings.distance_min = 0.015
m.point_cache.frame_end = 60
```

Colliders are a separate modifier on the *other* object:

```python
sphere.modifiers.new("Collision", "COLLISION")
sphere.collision.thickness_outer = 0.02
```

Pinning uses a vertex group as the "mass" group:

```python
vg = cloth_obj.vertex_groups.new(name="Pin")
vg.add([v.index for v in cloth_obj.data.vertices if v.co.y > 1.9], 1.0, "REPLACE")
m.settings.vertex_group_mass = "Pin"
```

Presets worth copying: `st.use_pressure` for inflatables, `st.shrink_min` for shrink-wrap
effects, and a `SUBSURF` modifier *after* Cloth to smooth the result cheaply.

## Soft body

```python
m = ob.modifiers.new("Soft", "SOFT_BODY")
ob.soft_body.mass = 2.0
ob.soft_body.use_goal = True
ob.soft_body.goal_spring = 0.6      # how strongly it returns to its rest shape
ob.soft_body.goal_default = 0.7
```

## Particles

```python
ob.modifiers.new("Particles", "PARTICLE_SYSTEM")
st = ob.particle_systems[-1].settings
st.type = "EMITTER"                 # EMITTER | HAIR
st.count = 500
st.frame_start, st.frame_end = 1, 30
st.lifetime = 40
st.physics_type = "NEWTON"          # NO NEWTON KEYED BOIDS FLUID
st.particle_size = 0.05
st.render_type = "OBJECT"           # NONE HALO LINE PATH OBJECT COLLECTION
st.instance_object = some_object
st.effector_weights.gravity = 1.0
```

Hair — note the child-count attribute names (`child_nbr` does not exist):

```python
ob.modifiers.new("Hair", "PARTICLE_SYSTEM")
st = ob.particle_systems[-1].settings
st.type = "HAIR"
st.count = 200
st.hair_length = 0.6
st.hair_step = 5
st.child_type = "INTERPOLATED"      # NONE SIMPLE INTERPOLATED
st.child_percent = 10               # viewport
st.rendered_child_count = 50        # render
st.child_length = 1.0
st.use_hair_bspline = True
```

## Force fields

```python
bpy.ops.object.effector_add(type="WIND", location=(0, -4, 2))
eff = bpy.context.object
eff.field.strength = 5.0
eff.field.noise = 1.0
eff.field.flow = 0.0
```

Types: `FORCE WIND VORTEX MAGNET HARMONIC CHARGE LENNARDJ TEXTURE GUIDE BOID TURBULENCE
DRAG FLUID_FLOW`. Per-system response lives in `settings.effector_weights.*`.

## Mantaflow fluid / smoke

Domain and flow are both `FLUID` modifiers with different `fluid_type`:

```python
activate(domain)
bpy.ops.object.modifier_add(type="FLUID")
domain.modifiers["Fluid"].fluid_type = "DOMAIN"
ds = domain.modifiers["Fluid"].domain_settings
ds.domain_type = "GAS"              # GAS | LIQUID
ds.resolution_max = 32              # keep this LOW while iterating
ds.use_adaptive_domain = True
# GAS:    ds.alpha (buoyancy), ds.beta, ds.vorticity, ds.use_noise
# LIQUID: ds.use_flip_particles, ds.particle_radius, ds.use_mesh

activate(flow)
bpy.ops.object.modifier_add(type="FLUID")
flow.modifiers["Fluid"].fluid_type = "FLOW"
fs = flow.modifiers["Fluid"].flow_settings
fs.flow_type = "SMOKE"              # SMOKE | FIRE | BOTH | LIQUID
fs.flow_behavior = "INFLOW"         # INFLOW | OUTFLOW | GEOMETRY
```

Effectors use `fluid_type = "EFFECTOR"` and `effector_settings.effector_type`.

Baking is expensive and blocking — do it deliberately, at low resolution, and tell the user
the UI will freeze:

```python
with ui_override("PROPERTIES"):
    bpy.ops.fluid.bake_all()
```

## Point caches

Every sim writes to a point cache. Bake and free them explicitly rather than relying on the
live cache:

```python
with ui_override("PROPERTIES"):
    bpy.ops.ptcache.bake_all(bake=True)
    # bpy.ops.ptcache.free_bake_all()
```

The per-modifier cache is at `mod.point_cache` (`frame_start`, `frame_end`, `is_baked`,
`use_disk_cache`, `name`).

## Dynamic paint

```python
m = ob.modifiers.new("DynPaint", "DYNAMIC_PAINT")
# then bpy.ops.dpaint.type_toggle(type='CANVAS') / 'BRUSH' to configure
```

## Verifying a sim without watching it

```python
before = [round(evaluated(o).matrix_world.translation.z, 3) for o in bodies]
for f in range(1, 41):
    frame(f)
after = [round(evaluated(o).matrix_world.translation.z, 3) for o in bodies]
print(json.dumps({"frame1": before, "frame40": after}))
```

Then `snapshot(OUT + "/sim.png", view="FRONT")` at a couple of frames for the visual check.
