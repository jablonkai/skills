---
name: blender
description: 'Remote-control a running Blender by Python script through a small local bridge — build and edit 3D scenes live: mesh and curve modeling with bmesh and modifiers, materials and shader node graphs, geometry nodes, lighting and cameras, keyframe animation, rigging, physics simulation, Grease Pencil, the video sequencer, and EEVEE/Cycles rendering, then measure the result, grab viewport screenshots, and export glTF / FBX / USD / Alembic / OBJ / STL. Use whenever the user wants to create or edit a 3D scene, model, animation, product shot, or .blend file, render an image or video, convert or export a 3D asset, or says "Blender", "3D model", "render this", "make a 3D animation", "Blender scene", "export to glTF" — even if they don''t mention scripting.'
category: 3d
risk: medium
tags:
    - blender
    - 3d
    - rendering
    - animation
    - modeling
    - scripting
---

# Blender Control

Blender (`/Applications/Blender.app`) is scriptable in **Python** against `bpy`, `bmesh` and
`mathutils`. Drive it through the **Blender Bridge** — a script running inside a *running*
Blender GUI that executes whatever build script is POSTed to `127.0.0.1:8736`. Because it
runs in the live session on the main thread, `bpy.data` writes are legal, the viewport
updates as you build, and viewport screenshots work. Everything documented here was executed
and verified on **Blender 5.2.0 LTS** (bundled Python 3.13).

- [scripts/blender-bridge.py](scripts/blender-bridge.py) — the bridge to run inside Blender.
- [scripts/blender-send.sh](scripts/blender-send.sh) — send a `.py` file (or `-c 'inline'`)
  and print its captured output; `--ping` checks it's up, `--state` dumps the scene as JSON.
- [scripts/example-product-shot.py](scripts/example-product-shot.py) — model → material →
  three-point light → camera → measure → render.
- [scripts/example-animated-logo.py](scripts/example-animated-logo.py) — text → keyframes →
  geometry-nodes scatter → frame sequence → video.

**Read [references/gotchas.md](references/gotchas.md) before writing anything.** Blender's
API changed substantially in 5.x and most of what a model has memorised — `action.fcurves`,
`scene.node_tree`, `mod["Socket_2"]`, `BLENDER_EEVEE_NEXT` — is now wrong.

## The control loop

1. **User starts the bridge** (one-time). This cannot be done remotely — if
   `bash scripts/blender-send.sh --ping` gets no answer, ask the user to do one of:
   - copy [scripts/blender-bridge.py](scripts/blender-bridge.py) to
     `~/Library/Application Support/Blender/5.2/scripts/startup/blender_bridge.py` and
     restart Blender — it then starts automatically on every launch (**recommended**), or
   - open the **Scripting** workspace, paste the file into the text editor, press
     **Run Script** (⌥P) — lasts for that session, or
   - install it as an add-on via Preferences ▸ Add-ons ▸ Install.

   A successful ping returns
   `{"ok": true, "bridge": "blender", "version": "5.2.0 LTS", "file": null, ...}`.
2. **Look before you build**: `bash scripts/blender-send.sh --state` returns objects and
   types, collections, materials, node groups, frame range, resolution, engine and whether
   the file has unsaved changes — cheaper than writing a script to ask.
3. **Write a build script** to the scratchpad, starting from the cheatsheet below and the
   right reference file.
4. **Send it**: `OUT=/path/to/outdir bash scripts/blender-send.sh /path/build.py`. The bridge
   runs it in the live session and returns the script's **captured stdout**; on error it
   returns the **traceback** and the sender exits non-zero. `BLENDER_SEND_TIMEOUT=900`
   (seconds) for heavy renders and bakes.
5. **Feedback**: returned stdout first; `metrics(...)` for structured geometry checks;
   `snapshot(...)` for a viewport PNG to Read; `render(...)` for the real thing.
6. **Iterate**: inspect, fix, re-send. Scripts must be **re-runnable** — build inside
   `stage("name")` so a re-send replaces its own output instead of stacking duplicates.

## Reference routing

| Task | Read |
|---|---|
| Anything, before you start | [gotchas.md](references/gotchas.md) |
| Data-blocks, transforms, collections, depsgraph, scenes | [api-reference.md](references/api-reference.md) |
| bmesh, modifiers, curves, text, UVs, booleans | [modeling.md](references/modeling.md) |
| Materials, shader nodes, textures, world/HDRI, lights, cameras | [shading.md](references/shading.md) |
| Procedural geometry, scattering, instancing, fields, zones | [geometry-nodes.md](references/geometry-nodes.md) |
| Keyframes, F-curves, drivers, NLA, armatures, IK, shape keys | [animation-rigging.md](references/animation-rigging.md) |
| Rigid body, cloth, soft body, particles, hair, fluid, bakes | [simulation.md](references/simulation.md) |
| EEVEE/Cycles settings, passes, compositor, output, video | [rendering.md](references/rendering.md) |
| 2D / toon linework, Line Art | [grease-pencil.md](references/grease-pencil.md) |
| Editing clips, titles, transitions, final cut | [vse.md](references/vse.md) |
| glTF, FBX, USD, Alembic, OBJ, STL, .blend append/link | [io-formats.md](references/io-formats.md) |

## Injected namespace

Pre-imported: `bpy`, `bmesh`, `mathutils`, `Vector`, `Matrix`, `Euler`, `Quaternion`,
`math`, `os`, `json`, plus `OUT` (from `$OUT`, also `os.environ["OUT"]`) and these helpers:

| Helper | Does |
|---|---|
| `stage(name)` | get-or-recreate a named collection, make it active — makes re-sends idempotent |
| `sync()` | `view_layer.update()`; **required before reading `matrix_world`** |
| `evaluated(ob)` | the depsgraph-evaluated object (modifier / geometry-nodes result) |
| `frame(n)` | `frame_set(n)` + depsgraph update |
| `metrics(objs, path=)` | dict + JSON: counts, verts/tris, world bbox, materials, frame range |
| `snapshot(path, view=, shading=, fit=)` | viewport PNG (fast visual check) |
| `render(path, engine=, samples=, ...)` | real EEVEE/Cycles still; restores every setting |
| `frame_view(objs, view=)` | aim the viewport (`ISO`/`FRONT`/`TOP`/`CAMERA`/…) |
| `world_bounds(objs)` | world-space `(min, max)` |
| `fcurves(ob)` / `fcurve(ob, path, i)` / `channelbag(ob)` | slotted-action F-curve access |
| `ui_override(area)` | context override for the few `bpy.ops` that need an editor |

## Cheatsheet

Units are **metres** and **radians**. Prefer the data API; `bpy.ops` is for mode changes,
`smart_project`, `rigidbody.*`, `nla.bake`, and importers/exporters.

### Build geometry (re-runnable)

```python
coll = stage("hero_v1")                       # owns its own output; safe to re-send
me = bpy.data.meshes.new("Body")
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=2.0)
bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.06, segments=3, affect="EDGES")
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("Body", me)
coll.objects.link(ob)
ob.location = (0, 0, 1)
sync()                                        # before ANY matrix_world read
```

### Material

```python
m = bpy.data.materials.new("Shell")
m.use_nodes = True
b = m.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.75, 0.2, 0.15, 1.0)
b.inputs["Roughness"].default_value = 0.35
b.inputs["Metallic"].default_value = 0.0      # no "Specular"/"Emission" inputs since 4.0
ob.data.materials.append(m)
```

### Camera aimed at the subject

```python
cd = bpy.data.cameras.new("Cam"); cd.lens = 50
cam = bpy.data.objects.new("Cam", cd); coll.objects.link(cam)
cam.location = (6, -6, 4)
cam.rotation_euler = (Vector((0, 0, 1)) - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam
```

### Feedback

```python
m = metrics([ob], path=OUT + "/metrics.json")
print("METRICS", json.dumps(m))               # comes straight back through the sender
print(snapshot(OUT + "/check.png", view="ISO"))
print(render(OUT + "/hero.png", engine="BLENDER_EEVEE", samples=64,
             width=1280, height=720))
```

### Keyframes

```python
for f, z in ((1, 0.0), (24, 3.0), (48, 0.0)):
    ob.location.z = z
    ob.keyframe_insert("location", index=2, frame=f)
for kp in fcurves(ob)[0].keyframe_points:     # NOT action.fcurves — that is gone
    kp.interpolation = "BEZIER"
    kp.easing = "EASE_IN_OUT"
```

### Export

```python
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT + "/hero.glb", export_format="GLB",
                          use_selection=True)
bpy.ops.wm.obj_export(filepath=OUT + "/hero.obj", export_selected_objects=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/hero.blend", copy=True)
```

## Verification

- **Returned stdout** is the immediate signal — `print(...)` comes straight back.
- **`metrics(...)`** is the structured check (object/vert/tri counts, world bbox, materials).
  Write it to `$OUT/metrics.json` and Read it to confirm geometry without eyeballing.
- **`snapshot(...)`** is the fast visual check — a viewport OpenGL PNG, no full render.
  `shading="RENDERED"` previews materials and lights.
- **`render(...)`** for the deliverable. It raises a diagnostic `RuntimeError` if Blender
  reported success but wrote nothing.
- **Hand-off**: a `.glb`/`.blend` in `$OUT` opens in whatever the user already has.

## Safety

- The bridge binds **127.0.0.1 only** and executes arbitrary Python in the user's session.
- The open file may hold **unsaved work**. Never call `bpy.ops.wm.read_homefile()` or
  `bpy.data.batch_remove` without asking. `stage()` is the non-destructive default; it
  isolates geometry but **not** scene-level settings.
- Renders, bakes and sims **block the main thread — the UI freezes** until they finish.
  Iterate small, and warn the user before anything long.
- Save into `$OUT`, not over the user's `.blend`; `save_as_mainfile(..., copy=True)` leaves
  the live session pointed at their own file.
