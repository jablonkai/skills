# Baking mesh maps (0.2.0)

## Map ids

| Id | What it holds | Read by |
|---|---|---|
| `normal_base` | Tangent-space normal from the high poly (flat without one) | the Normal output (mixed with layer height) |
| `world_space_normals` | World normals | `direction` generator |
| `id` | Colour per part or material | `mask.add.colorSelection` |
| `ambient_occlusion` | AO | `dirt`, `ambientOcclusion` generators; `AoMixed` in ORM exports |
| `curvature` | Convex and concave edges | `edgeWear`, `curvature` generators |
| `position` | Position in the bounding box | `position` generator |
| `thickness` | Thickness | `thinAreas` generator |

The ids are long. `ao` gives ``unknown mesh map "ao"``, and the error doesn't list the
valid ones. The default `maps` setting holds all seven.

## Settings that matter

- `resolution` defaults to **1024 per set, separate from the texture resolution**.
  Exports resample, so bake at the texture size when the user names one.
- `maps` limits what is baked. `bake --maps a,b` and `bake.run {"maps": […]}` also store
  the list in the settings.
- `ts`: `bake.settings` and `bake.run` act on the **active set** unless given `"all"`, an
  index or a list. The `bake` subcommand bakes every set.
- `antialiasing` (1/2/4/8), `dilation` (16 px), `ao: {rays: 32, maxDistance: 0.25,
  spread: 180}`, `curvatureStrength`, `curvatureRadius`.
- `cpu: true` on `bake.run` skips the GPU, for when there is no adapter.
- `baked` in `info` records `{maps, resolution}` per set; that is the read-back.

## High poly onto low poly, with a cage

```json
{"in": "low.obj", "resolution": 2048, "steps": [
  {"id": "bake.highPoly.add", "params": {"path": "high.obj"}},
  {"id": "bake.cage.set",     "params": {"path": "cage.obj"}},
  {"id": "bake.run", "params": {"ts": "all", "resolution": 2048}}
], "save": "low_baked.tcraft"}
```

- Adding a high poly turns `useLowAsHigh` off. Without a high poly, the low poly bakes onto
  itself, which gives a flat `normal_base` and AO and curvature from the low poly.
- The cage must have **the low poly's triangles** (same count and order), pushed outward.
  Without a cage, the ray distance comes from `maxFrontal` and `maxRear` (0.01 by default),
  which can miss high-poly detail that stands out further than that.
- `matching: "byMeshName"` with `lowSuffix` and `highSuffix` (`_low`/`_high`) pairs parts
  by name for multi-part models. The default `always` lets every low part hit every high part.
- The high poly needs no UVs. Its base colour textures (glTF, embedded FBX media, usdz, or
  images next to a .gltf or USD layer) feed the baked colour map.
- The high-poly and cage files are **copied into the `.tcraft`**, so moving the source
  files later doesn't break re-bakes.
- Check it: `info` gives `bakeMeshes.highPoly` and `cage`, and each set's `baked`. Export
  with the `Mesh maps` preset and look at `*_normal_base.png`: a high-poly bake shows
  detail away from flat (128,128,255) where the shapes differ.

## Exporting the maps themselves

`tc_export.py P DIR --preset "Mesh maps"` writes `$mesh_$textureSet_<map id>.png`: RGB
maps at 8-bit, and AO, curvature and thickness as 16-bit grayscale.
