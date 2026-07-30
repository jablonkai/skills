# Blender scripting gotchas — verified on Blender 5.2.0 LTS (Python 3.13)

Everything here was reproduced through the bridge on this machine. Most of it contradicts
what older tutorials, forum answers, and pre-5.x training data will tell you — Blender's
Python API churns hard across releases, and 5.x moved several things wholesale.

## The five that will bite you first

### 1. `matrix_world` is stale until the depsgraph updates

Assigning `ob.location` / `rotation_euler` / `parent` does **not** update `ob.matrix_world`.
Read it in the same script and you silently get the old (often identity) matrix.

```python
ob.location = (3, 0, 1)
ob.matrix_world.translation      # -> <0, 0, 0>   WRONG
sync()                           # = bpy.context.view_layer.update()
ob.matrix_world.translation      # -> <3, 0, 1>   correct
```

Every bridge helper that reads transforms (`world_bounds`, `metrics`, `frame_view`) calls
`sync()` for you. Your own code must call it.

### 2. `Action.fcurves` no longer exists

Blender 4.4 introduced slotted actions and 5.x removed the legacy accessor entirely:

```python
ob.animation_data.action.fcurves          # AttributeError in 5.2
```

Curves now live under `action.layers[i].strips[j].channelbag(slot)`. Use the bridge helpers
`fcurves(ob)`, `fcurve(ob, data_path, index)`, `channelbag(ob)` — see
[animation-rigging.md](animation-rigging.md) for the raw path.

### 3. Geometry-nodes modifier inputs moved

The Blender 4.x idiom is gone:

```python
mod["Socket_2"] = 120.0        # TypeError: id properties not supported for this type
```

5.x routes them through a typed interface:

```python
mod.properties.inputs["Socket_2"]["value"] = 120.0
ob.update_tag()
```

### 4. A render can report success and write nothing

`bpy.ops.render.render(write_still=True)` returns `{'FINISHED'}` while producing no file when
an **empty compositor node group** or an **empty sequencer** is in the output path. Both are
easy to create by accident.

```python
scene.render.use_compositing = False   # or give the group a NodeGroupOutput
scene.render.use_sequencer = False     # or the VSE renders instead of the 3D scene
```

Always check the file exists. The bridge's `render()` / `snapshot()` raise a diagnostic
`RuntimeError` naming the likely cause instead of returning a phantom path.

### 5. Viewport navigation operators are no-ops from the bridge

`bpy.ops.view3d.view_all()` / `view_selected()` stage a *smooth view* transition that only
lands on the next region redraw — which never happens inside one timer callback. The value
does not change at all:

```python
rv3d.view_distance          # 24.167
bpy.ops.view3d.view_all()
rv3d.view_distance          # 24.167 — unchanged
```

Write `region_3d.view_location` / `view_rotation` / `view_distance` directly, or just call
`frame_view(objs, view="ISO")`.

## Context

- **Object-mode `bpy.ops` mostly work without an override.** The window and screen are
  inherited, so `bpy.ops.object.mode_set`, `modifier_apply`, `rigidbody.object_add`,
  `uv.smart_project` and friends run fine straight from a build script. Do not cargo-cult
  overrides everywhere.
- `bpy.context.area` and `bpy.context.space_data` are `None` in the pump. Operators that read
  an editor — `render.opengl`, everything under `view3d.*` — need `ui_override("VIEW_3D")`.
- Operators act on **selection and the active object**. Set both explicitly; never assume
  what a previous script left selected.
- Prefer the data API anyway: it is faster, order-independent, and does not depend on
  selection state. Reach for `bpy.ops` when there is no data-API equivalent (mode changes,
  `smart_project`, `rigidbody.*`, `nla.bake`, importers/exporters).

## Enum introspection lies

Two enums are populated dynamically and read back almost empty, even though assignment works:

```python
RenderSettings.bl_rna.properties["engine"].enum_items   # ['BLENDER_EEVEE'] only
scene.render.engine = "CYCLES"                          # works anyway

view_settings.bl_rna.properties["view_transform"]       # ['NONE'] only
scene.view_settings.view_transform = "AgX"              # works anyway
```

Assign the value and catch the exception; do not gate on the enum list. Cycles is an add-on
(enabled by default), which is why it is missing from the engine enum.

## Renamed / moved in 5.x

| Old (≤4.x, what tutorials say) | Blender 5.2 |
|---|---|
| `scene.node_tree` (compositor) | `scene.compositing_node_group` — a real node group |
| `CompositorNodeComposite` output node | `NodeGroupOutput` inside that group |
| `glare.glare_type = "BLOOM"` | `glare.inputs["Type"]` — compositor settings became input sockets |
| `BLENDER_EEVEE_NEXT` (4.2–4.5) | `BLENDER_EEVEE` |
| `sky.sky_type = "NISHITA"` | `"SINGLE_SCATTERING"` / `"MULTIPLE_SCATTERING"` |
| object type `GPENCIL`, `bpy.ops.gpencil.*` | `GREASEPENCIL`, `bpy.data.grease_pencils` (Grease Pencil v3) |
| `sequence_editor.sequences` | `sequence_editor.strips` (`.strips_all` for nested) |
| `new_effect(..., frame_end=, seq1=, seq2=)` | `new_effect(..., length=, input1=, input2=)` |
| `bpy.ops.export_scene.obj` | `bpy.ops.wm.obj_export` (same for stl/ply/usd/alembic) |
| `mesh.auto_smooth_angle` | `bpy.ops.object.shade_auto_smooth()` — adds a `NODES` modifier |
| `particles.child_nbr` | `child_percent` (viewport) / `rendered_child_count` (render) |
| `mod["Socket_2"]` | `mod.properties.inputs["Socket_2"]["value"]` |
| `action.fcurves` | `action.layers[0].strips[0].channelbag(slot).fcurves` |

Only FBX and glTF still live under `bpy.ops.import_scene` / `export_scene`; everything else
moved to `bpy.ops.wm.*`. 5.x also adds a native `bpy.ops.wm.fbx_import`.

## Video output is gated behind `media_type`

`file_format = "FFMPEG"` raises unless you switch the media type first:

```python
img = scene.render.image_settings
img.media_type = "VIDEO"        # 'IMAGE' | 'MULTI_LAYER_IMAGE' | 'VIDEO'
img.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
```

## Geometry / evaluation

- **`to_mesh()` does not include instances.** A geometry-nodes scatter reports 8 verts (the
  base cube) until you add a **Realize Instances** node — then 43208. To count without
  realizing, walk `depsgraph.object_instances`.
- Modifier results only exist on the evaluated object: `evaluated(ob).to_mesh()`. The raw
  `ob.data` never changes. Call `ev.to_mesh_clear()` when done.
- `bm.verts[0]` raises `IndexError` until `bm.verts.ensure_lookup_table()`.
- `Render Result` reports `size == (0, 0)` and `has_data == False` even after a successful
  render, and `img.save_render()` on it can fail. Verify the file on disk instead.

## Live-session hygiene

- State persists between sends: open documents, imported assets, view settings, **and any
  scene property a previous script changed**. A stray `use_compositing = True` from an
  earlier run will break the next render. `stage()` isolates geometry, not scene settings.
- The user's file may hold **unsaved work**. Never call `bpy.ops.wm.read_homefile()` or
  `bpy.data.batch_remove` without asking.
- Long renders and bakes **block the main thread — the whole UI freezes** until they finish.
  Iterate at low samples and small resolutions; raise `BLENDER_SEND_TIMEOUT` for finals and
  warn the user the window will stop responding.
- Physics sims need frames stepped **in order from the start** (`for f in range(1, 41):
  frame(f)`). Jumping straight to frame 40 gives an unsimulated result.
