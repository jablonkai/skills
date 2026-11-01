# Command ids by task (pinned to TextureCraft 0.2.0)

The registry holds 135 commands. These are the ones a headless texturing job needs. For
anything else, or when a pinned id fails after an update:

```sh
texturecraft-cli commands --filter mask     # id, label and the full param signature
```

`?` marks an optional param. `layer?` defaults to the selected layer, and `ts?` to the
active texture set. **Keys outside the signature are dropped silently**, so copy them
exactly (`tc_build.py` checks them).

## Texture sets

| Id | Params | Notes |
|---|---|---|
| `textureSet.list` | `{}` | |
| `textureSet.select` | `{ts}` | Takes an **integer index** only; a name is an error. |
| `textureSet.inspect` | `{ts?}` | Resolution, channels, layers count, baked, UDIM tiles. |
| `textureSet.resolution` | `{ts?, resolution}` | 128–8192, a power of two. |
| `textureSet.channel.add` / `.remove` | `{ts?, channel}` | e.g. `emissive`, `opacity`. |
| `textureSet.settings` | `{ts?, description?, heightStrength?, normalFormat?: openGl\|directX}` | `normalFormat` is project-wide; see [export.md](export.md). |
| `textureSet.parts` | `{ts?}` | Mesh part names, for `layer.set {geometryMask}`. |
| `textureSet.rename` / `.visible` | | |

## Layers (act on the active set)

| Id | Params |
|---|---|
| `layer.add.fill` | `{name?, color?, roughness?, metallic?}`. `color` is `[r,g,b]` in 0–1, or `"#rrggbb"`. Only the channels you give get a source. |
| `layer.add.paint` / `layer.add.group` | `{name?}` |
| `layer.add.image` | `{name, channel?: baseColor, projection?: uv\|triplanar\|planar, scale?}`, from an imported resource. |
| `layer.fill.set` | `{layer?, channel, color?\|value?\|procedural?: kind, scale?, seed?, contrast?, balance?, invert?, low?, high?\|image?}`. Sets one channel's source; `procedural` is a noise kind such as `noise`. |
| `layer.fill.projection` | `{layer?, projection: uv\|triplanar\|planar\|spherical\|cylindrical, scale?, rotation?}` |
| `layer.blend` | `{layer?, channel?: id\|all, mode?, opacity?: 0..1, enabled?}` |
| `layer.list` | `{ts?}`, top first. |
| `layer.rename` / `.visible` / `.remove` / `.duplicate` / `.move` / `.group` | `{layer?, …}`. `layer` takes an id or a name. |
| `layer.instantiateAll` | `{layer?, copy?: bool}`. Puts the layer on top of every other set: linked instances, or independent copies with `copy: true`. |
| `layer.set` | `{layer?, heightMask?, geometryMask?: [part names]}` |

## Masks and effects

| Id | Params |
|---|---|
| `mask.add.black` / `mask.add.white` | `{layer?}`. A black mask hides the layer until effects reveal it. |
| `mask.add.colorSelection` | `{layer?, color?: [r,g,b] ID colour, tolerance?}`, using the baked `id` map. |
| `mask.smart.list` / `mask.smart.apply` | `{name, layer?}`: `edge_wear edge_chipped dirt_cavities dust_top ground_dirt rust_leaks scratches grunge paint_chips fingerprints edges_soft edges_sharp exposed thin_areas dust_cavities moss_top water_stains sun_faded` |
| `mask.invert` / `.toggle` / `.clear` / `.remove` | `{layer?}` |
| `effect.add.generator` | `{layer?, name?, generator?: edgeWear\|dirt\|thinAreas\|curvature\|ambientOcclusion\|position\|direction, level?, softness?, noise?, invert?}`. Goes into the mask; **needs baked maps** ([bake.md](bake.md)). |
| `effect.add.fill` | `{layer?, target?: mask\|content, name?, value?\|procedural?, scale?, seed?}`. A procedural noise in the mask breaks up a generator. |
| `effect.add.levels` | `{layer?, target?, inLow?, inHigh?, gamma?, outLow?, outHigh?}` |
| `effect.add.filter` | `{layer?, target?, filter?: id from filter.list}`: blur, threshold, invert, hsl, gradientMap… |
| `effect.set` / `effect.remove` | `{effect: id, …}`. The effect id comes from the add result `{"effect": N}`. |

## Smart materials

| Id | Params |
|---|---|
| `material.list` | `{}`: 75 ids, such as `steel rust iron_rusted steel_painted_worn copper_patina wood_oak wood_weathered concrete_dirty plastic_scuffed leather_worn …` |
| `material.apply` | `{material: id or label, above?, inside?, index?}`. Adds a group to the active set and returns `{"layer": id}`. |
| `material.save` / `material.load` | `.tcmat` files |

## Bake, export, files

| Id | Params |
|---|---|
| `bake.settings` | `{ts?, resolution?, antialiasing?: 1\|2\|4\|8, dilation?, maps?: [ids], ao?: {rays?, maxDistance?, …}, useLowAsHigh?, maxFrontal?, maxRear?, averageNormals?, matching?: always\|byMeshName, …}`. With only `ts` it returns the current settings. |
| `bake.run` | `{ts?: index\|[indices]\|"all"\|"selected", cpu?: true, …any bake.settings key}`. Settings given here persist. |
| `bake.highPoly.add` / `.remove` / `.list` | `{path}` / `{index?\|name?\|all?}` |
| `bake.cage.set` / `bake.cage.clear` | `{path}`, a mesh with the low poly's triangles. |
| `export.plan` | `{preset?, ts?, format?, bitDepth?, size?}`, giving `[{ts, map, file, format, bitDepth, warnings}]`. |
| `export.presets` / `export.preset.get` / `.save` / `.remove` | `.save` writes a user preset (app config). Prefer passing a preset object inline. |
| `file.exportTextures` | `{dir, preset?, ts?: index\|"all", format?, bitDepth?, padding?: none\|dilation\|dilationDefault\|infinite, dilation?, size?, normalFormat?: openGl\|directX}`, giving `{files, warnings}`. |
| `file.exportMesh` | `{path, format?: obj\|glb\|usda\|usdc\|usdz}`. A GLB embeds the textures; usda and usdc write them next to the file. |
| `file.new` / `project.new` | `{mesh, resolution?, name?, uvTiles?, template?}` / `{mesh?: builtin, …}` |
| `file.save` / `file.saveAs` / `file.saveCopy` / `file.reimportMesh` | |
| `resource.import` | `{path}`: an image for `layer.add.image`, a stencil or a decal. |

Painting (`tool.*`: `tool.select`, `tool.brush`, `tool.material`, `tool.strokeUv
{points: [[u,v]…]}`, `tool.stroke` in viewport pixels) works headless too, but fills with
masks are the reliable way to build a material from a spec.
