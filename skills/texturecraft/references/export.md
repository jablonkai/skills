# Exporting textures (0.2.0)

Always run `export.plan` first (`tc_export.py --plan-only`): it lists exactly the files an
export will write, per set, after dropping maps for channels the project doesn't have
(Emissive, Clearcoat, Sheen…).

## Built-in presets

| Preset | Files per set (`$mesh_$textureSet_…`) | Normal |
|---|---|---|
| `glTF PBR Metal Roughness` | `BaseColor` (RGB, plus A from Opacity if present), `OcclusionRoughnessMetallic` (R=AO mixed, G=roughness, B=metallic), `Normal`; Emissive/Clearcoat/Sheen when present | OpenGL |
| `Unreal Engine (Packed)` | `BaseColor` (+A opacity), `OcclusionRoughnessMetallic`, `Normal` | **DirectX** |
| `Unity HDRP (Mask Map)` | `BaseMap` (+A opacity), `MaskMap` (R metallic, G AO, B 0, A smoothness), `Normal` | OpenGL |
| `Unity Standard (Metallic Smoothness)` | `Albedo` (+A opacity), `MetallicSmoothness` (R metallic, A smoothness), `Normal`, `Occlusion` (gray) | OpenGL |
| `Blender (Principled BSDF)` | BaseColor, Metallic, Roughness, Normal, Height (16-bit), Emission, Specular | OpenGL |
| `Godot 4 (ORM)` | `albedo`, `orm`, `normal`, `emission` | OpenGL |
| `OpenPBR (separate maps)` | `base_color`, `base_metalness`, `specular_roughness`, `geometry_normal`, `height`… | OpenGL |
| `Separate maps` | one file per document channel (`$channel`) | the project setting |
| `Document channels + Normal + AO` (default) | each channel, plus `normal` and `ambientOcclusion` | the project setting |
| `Mesh maps` | the baked maps ([bake.md](bake.md)) | — |

`run P export.preset.get '{"name": "…"}'` shows a preset's exact channel packing.

## Normal convention (OpenGL Y+ or DirectX Y−)

- Presets that name `NormalOpenGl` or `NormalDirectX` fix the convention: glTF, Blender,
  Godot and OpenPBR use OpenGL, and Unreal uses DirectX.
- `textureSet.settings {"normalFormat": "directX"}` is stored **project-wide** (as
  `normal_format` in `project.json`). It affects only the presets that export the plain
  `Normal` channel: Separate maps and the Document default.
- The export param `normalFormat: "directX"` overrides every preset. That is
  `tc_export.py --normal directx`, which also proves the result by comparing the green
  channel with the opposite convention's export. A flat normal map (nothing baked, no
  height) is identical in both conventions, and the check reports that.

## Sizes, formats, padding

- `size` resamples every map, so a 2048² set can be exported at 1024². Without it each set
  exports at its own resolution.
- `format`: `png` (8/16-bit), `jpg`, `tga`, `tif`, `exr` (`bitDepth` 16 or 32). It
  overrides the preset's format for every map.
- `padding`: `dilation` (the preset default), `dilationDefault`, `infinite`, or `none`.
  `dilation` sets the width in pixels.
- TGA is written **RLE-compressed** (type 10, origin top-left). ImageMagick, `sips` and the
  engines read it, but Pillow fails with "buffer overrun", so check TGAs with `magick
  identify` or `tc_export.py` (which reads the header).
- BaseColor comes out **RGB** unless the set has an `opacity` channel
  (`textureSet.channel.add {"channel": "opacity"}`).

## File names and custom presets

Tokens: `$project` (the project name), `$mesh` (`crate` for a built-in, but `mesh` for
an imported file), `$textureSet`, `$channel`. A preset object can be passed inline, so no
user preset gets written to the app's config:

```json
{"name": "RMA packed", "maps": [
  {"file": "$project_$textureSet_RMA", "format": "Png", "bit_depth": 8, "channels": [
    ["R", {"Channel": {"channel": "Roughness", "component": 0}}],
    ["G", {"Channel": {"channel": "Metallic",  "component": 0}}],
    ["B", {"Virtual": {"map": "AoMixed",       "component": 0}}]]}]}
```

Save it as `rma.json` and run `tc_export.py P DIR --preset rma.json`. Channel names are
capitalised (`BaseColor`, `Roughness`, `Metallic`, `Height`, `Opacity`, `Emissive`…).
Virtual maps: `AoMixed`, `NormalOpenGl`, `NormalDirectX`, `Glossiness`, `SheenTint`.
A constant is `{"Constant": 0.0}`. A single-channel (gray) file uses the channel key `"L"`.

## Textured meshes

`file.exportMesh {"path": "model.glb"}` writes the mesh with its materials and textures:
`.glb` embeds them, `.usda`/`.usdc` write them alongside, and `.obj` writes **geometry
only** (no `.mtl`, no textures; export the textures separately). `tc_export.py --mesh` re-imports the result with `info`, compares its triangle
count with the project's mesh, and for `.glb` checks that every material links a base
colour texture.
