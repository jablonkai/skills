# Import / export

Verified on Blender 5.2.0 LTS — every export below was run and produced a non-empty file.

## Where each operator lives

Most importers/exporters moved to `bpy.ops.wm.*` in recent releases. Only FBX and glTF are
still add-ons under `import_scene` / `export_scene`.

| Format | Export | Import |
|---|---|---|
| OBJ | `bpy.ops.wm.obj_export` | `bpy.ops.wm.obj_import` |
| STL | `bpy.ops.wm.stl_export` | `bpy.ops.wm.stl_import` |
| PLY | `bpy.ops.wm.ply_export` | `bpy.ops.wm.ply_import` |
| USD (`.usd/.usda/.usdc/.usdz`) | `bpy.ops.wm.usd_export` | `bpy.ops.wm.usd_import` |
| Alembic (`.abc`) | `bpy.ops.wm.alembic_export` | `bpy.ops.wm.alembic_import` |
| glTF / GLB | `bpy.ops.export_scene.gltf` | `bpy.ops.import_scene.gltf` |
| FBX | `bpy.ops.export_scene.fbx` | `bpy.ops.import_scene.fbx` or `bpy.ops.wm.fbx_import` |
| BVH (motion capture) | `bpy.ops.export_anim.bvh` | `bpy.ops.import_anim.bvh` |
| SVG (as curves) | — | `bpy.ops.import_curve.svg` |
| Grease Pencil SVG/PDF | `bpy.ops.wm.grease_pencil_export_svg` / `_pdf` | `bpy.ops.wm.grease_pencil_import_svg` |

`bpy.ops.wm.fbx_import` is the new native importer added in 5.x; the add-on version still
works and is more permissive with odd files.

## Selection-only export

Each family spells the flag differently — this is the usual source of "it exported the whole
scene":

```python
def activate(ob):
    for o in bpy.context.selected_objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

activate(ob)
bpy.ops.wm.obj_export(filepath=p,     export_selected_objects=True)
bpy.ops.wm.stl_export(filepath=p,     export_selected_objects=True)
bpy.ops.wm.ply_export(filepath=p,     export_selected_objects=True)
bpy.ops.wm.usd_export(filepath=p,     selected_objects_only=True)
bpy.ops.wm.alembic_export(filepath=p, selected=True)
bpy.ops.export_scene.gltf(filepath=p, use_selection=True, export_format="GLB")
bpy.ops.export_scene.fbx(filepath=p,  use_selection=True)
```

Verified output sizes for a single textured cube: obj 730 B, stl 684 B, ply 752 B,
glb 1960 B, fbx 15148 B, usdc 3038 B, abc 3185 B.

## Format notes

**glTF / GLB** — the best general interchange target for web and real-time. Exports
Principled BSDF cleanly; other shader graphs get baked or dropped.

```python
bpy.ops.export_scene.gltf(
    filepath=OUT + "/model.glb",
    export_format="GLB",              # GLB | GLTF_SEPARATE | GLTF_EMBEDDED
    use_selection=True,
    export_apply=True,                # apply modifiers
    export_animations=True,
    export_draco_mesh_compression_enable=False,   # Draco is available in this build
    export_yup=True,                  # Y-up for the glTF convention
)
```

**FBX** — for DCC/game-engine round trips.

```python
bpy.ops.export_scene.fbx(
    filepath=OUT + "/model.fbx",
    use_selection=True,
    apply_scale_options="FBX_SCALE_ALL",
    axis_forward="-Z", axis_up="Y",
    bake_anim=True,
    add_leaf_bones=False,             # usually what game engines want
    mesh_smooth_type="FACE",
)
```

**USD** — scene-graph interchange, keeps hierarchy and instancing.

```python
bpy.ops.wm.usd_export(filepath=OUT + "/scene.usdc",
                      selected_objects_only=True,
                      export_materials=True,
                      export_animation=False)
```

**Alembic** — baked geometry caches, ideal for handing off simulations.

```python
bpy.ops.wm.alembic_export(filepath=OUT + "/cache.abc",
                          selected=True, start=1, end=48, flatten=False)
```

**OBJ / STL / PLY** — geometry only. STL is triangles with no colour, materials or UVs;
use it for 3D printing and nothing else.

```python
bpy.ops.wm.obj_export(filepath=p, export_selected_objects=True,
                      export_materials=True, export_uv=True,
                      export_normals=True, apply_modifiers=True,
                      forward_axis="NEGATIVE_Z", up_axis="Y")
```

**SVG** imports as curve objects into a new collection — good for turning a logo into
extrudable geometry:

```python
bpy.ops.import_curve.svg(filepath="/path/logo.svg")
```

## Import round trip

```python
before = set(bpy.data.objects.keys())
bpy.ops.wm.obj_import(filepath=OUT + "/exp.obj")
added = sorted(set(bpy.data.objects.keys()) - before)   # ['ExportMe.001']
```

Imports land in the **active collection**, so call `stage("import_v1")` first to keep them
out of the user's tree.

## .blend files

```python
bpy.ops.wm.save_as_mainfile(filepath=OUT + "/scene.blend", copy=True)
```

`copy=True` writes the file without repointing the session at it — the safe choice against a
live session, since it leaves the user's own file association alone. Drop it when the user
actually wants to keep working in the saved file.

Append or link from another .blend:

```python
with bpy.data.libraries.load(path, link=False) as (src, dst):   # link=True to keep a link
    dst.objects = [n for n in src.objects if n.startswith("Prop_")]

for ob in dst.objects:
    if ob is not None:
        coll.objects.link(ob)        # loading does NOT put them in a collection
```

The same pattern works for `src.materials`, `src.node_groups`, `src.collections`,
`src.actions`, `src.worlds`.

## Images and video

```python
img = bpy.data.images.load("/path/tex.png")
img.filepath_raw = OUT + "/copy.png"
img.file_format = "PNG"
img.save()
```

Rendered stills and sequences go through the render settings — see
[rendering.md](rendering.md).

## Paths

Always hand the operators **absolute** paths. Inside Blender, `//` prefixes are relative to
the .blend, and an unsaved session has no base directory:

```python
os.path.abspath(p)
bpy.path.abspath("//textures/x.png")   # resolve a Blender-relative path
```

Write everything into `$OUT` (injected as the `OUT` global) so the deliverable lands where
the caller expects it.
