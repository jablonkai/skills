# Recipes (verified on TextureCraft 0.2.0)

`S=<skill>/scripts`. Each spec below was run through `tc_build.py` as written.

## 1. Rusty metal crate with edge wear, glTF set and preview

```json
{"in": "builtin:crate", "resolution": 2048, "steps": [
  {"id": "bake.run", "params": {"ts": "all", "resolution": 2048, "maps": ["ambient_occlusion", "curvature"]}},
  {"sets": "all", "steps": [
    {"id": "layer.add.fill", "params": {"name": "Steel base", "color": [0.55, 0.56, 0.58], "metallic": 1.0, "roughness": 0.35}},
    {"id": "layer.add.fill", "params": {"name": "Rust", "color": [0.45, 0.20, 0.08], "metallic": 0.0, "roughness": 0.85}},
    {"id": "mask.add.black", "params": {}},
    {"id": "effect.add.generator", "params": {"generator": "edgeWear", "name": "Edge wear", "level": 0.6}}
  ]}
], "save": "out/crate_rust.tcraft"}
```

```sh
python3 $S/tc_build.py crate.json --expect-layer all:Rust --expect-baked all:ambient_occlusion,curvature
python3 $S/tc_export.py out/crate_rust.tcraft out/textures --preset "glTF PBR Metal Roughness"
python3 $S/tc_render.py out/crate_rust.tcraft out/crate_preview.png --uv
```

This makes 3 sets (Crate, Lid, Handle) × BaseColor, OcclusionRoughnessMetallic and Normal
at 2048². The rust shows only at the edges. To make the rust come from a smart material
instead, put `{"id": "material.apply", "params": {"material": "iron_rusted"}}` in the
group, or use `steel_painted_rust`.

To break up the wear, add `{"id": "effect.add.fill", "params": {"target": "mask",
"procedural": "noise", "scale": 6}}` after the generator, and then `effect.set` its
`blend` to `Multiply`.

## 2. Imported GLB: UV report, recolour one set, export at 1024 with DirectX normals

```sh
python3 $S/tc_inspect.py model.glb            # sets Body, Trim; uv: overlapRatio, uvOutOfRange, warnings
```

```json
{"in": "model.glb", "resolution": 1024, "steps": [
  {"sets": ["Trim"], "steps": [
    {"id": "layer.add.fill", "params": {"name": "Trim colour", "color": "#b31212"}}
  ]}
], "save": "out/model.tcraft"}
```

```sh
python3 $S/tc_build.py recolour.json --expect-layer Trim:"Trim colour"
python3 $S/tc_export.py out/model.tcraft out/textures --preset "glTF PBR Metal Roughness" --size 1024 --normal directx
```

- The import doesn't bring in the GLB's material colours: each set starts empty and
  exports TextureCraft's default material. To keep a set's original colour, add a fill
  with it.
- A fill with only `color` sets only the base colour; the set's roughness and metallic are
  untouched.
- The export's files come out as `mesh_<Set>_…`, because `$mesh` is `mesh` for an
  imported file. For `<project>_<Set>_…`, use a preset object with `$project`
  ([export.md](export.md)).

## 3. High poly onto low poly with a cage, textured GLB that re-imports

```json
{"in": "low.obj", "resolution": 2048, "steps": [
  {"id": "bake.highPoly.add", "params": {"path": "high.obj"}},
  {"id": "bake.cage.set", "params": {"path": "cage.obj"}},
  {"id": "bake.run", "params": {"ts": "all", "resolution": 2048}},
  {"sets": "all", "steps": [{"id": "material.apply", "params": {"material": "steel_painted_worn"}}]}
], "save": "out/low_baked.tcraft"}
```

```sh
python3 $S/tc_build.py bake.json --expect-baked all:normal_base,ambient_occlusion,curvature
python3 $S/tc_inspect.py out/low_baked.tcraft          # bakeMeshes.highPoly / cage set
python3 $S/tc_export.py out/low_baked.tcraft out/maps --preset "Mesh maps"    # look at *_normal_base.png
python3 $S/tc_export.py out/low_baked.tcraft out/tex --preset "glTF PBR Metal Roughness" --mesh out/low_textured.glb
```

The `--mesh` check re-imports the GLB, compares its triangle count with the low poly, and
confirms that each material embeds its textures. To be thorough, also run `texturecraft-cli
new out/low_textured.glb /tmp/check.tcraft`.

## 4. One smart material on every set of a bigger model

```json
{"in": "robot.fbx", "resolution": 2048, "steps": [
  {"id": "bake.run", "params": {"ts": "all", "resolution": 2048}},
  {"sets": "all", "steps": [{"id": "material.apply", "params": {"material": "aluminium_scratched"}}]}
], "save": "out/robot.tcraft"}
```

The other way is to build the stack on set 0 and then run `layer.instantiateAll {"layer":
ID, "copy": true}`. Leave out `copy` to get linked instances, where editing one changes
all of them.

## 5. A quick look at someone else's project

```sh
python3 $S/tc_inspect.py their.tcraft --full > their.json   # stacks, masks, fill sources
python3 $S/tc_render.py their.tcraft /tmp/their.png --yaw 215 --uv
```
