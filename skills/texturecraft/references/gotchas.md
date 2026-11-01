# Gotchas (TextureCraft 0.2.0)

Each of these was reproduced against texturecraft-cli 0.2.0.

## Silent failures

- **Unknown param keys are dropped, and the command still succeeds.**
  `layer.add.fill {"colour": [1,0,0]}` adds a fill with *no* base colour source.
  `tc_build.py` refuses any key the registry signature doesn't name.
- **Colour values are not clamped.** `[255, 0, 0]` is stored as 255, which renders blown
  out. Use 0–1 floats or `"#rrggbb"`.
- **Generators on unbaked sets render as nothing.** An edge-wear mask on an unbaked crate
  exports with 0 % rust pixels; after an AO and curvature bake it is about 4 %. The same
  goes for smart materials, which use generators inside. `tc_build.py` checks the bake
  state before it runs.
- **Layer, mask and effect commands act on the active texture set only.** After
  `new builtin:crate`, the active set is `Crate`, so a stack built without selecting a set
  leaves `Lid` and `Handle` bare. The render shows it, but the CLI doesn't.
- **The glTF, Blender, Godot and OpenPBR presets ignore the project's DirectX setting.**
  `textureSet.settings {"normalFormat": "directX"}` doesn't change a glTF-preset normal
  map. Only the export's `normalFormat` does.
- **Importing a mesh imports no materials.** `baseColorFactor`, textures and
  roughness/metallic factors of a GLB are not turned into layers. Each set gets one empty
  paint layer, `Layer 1`.

## Saving and overwriting

- `run` without `-o` changes nothing on disk. A chain of `run` calls each starts from the
  file again, so use one `batch` (or `tc_build.py`).
- `new`, `run -o`, `batch` `save`, and `export` into a non-empty folder all overwrite
  without asking. The scripts refuse unless given `--overwrite`.
- `bake IN` with no `-o` saves the project **in place**.
- A failed batch step stops the batch, saves nothing and exits 1. The JSON names the step
  index and its error.

## Ids and names

- `textureSet.select` takes an integer index. `{"ts": "Lid"}` is an error.
  (`tc_build.py` maps set names to indices.)
- Mesh map ids are long (`ambient_occlusion`, not `ao`). Generator ids are camelCase
  (`edgeWear`, `thinAreas`). Smart material and smart mask ids are snake_case
  (`iron_rusted`, `edge_wear`). Preset names are full titles with parentheses.
- Layer ids are unique across all sets. The add commands return them as `{"layer": N}`,
  and effects as `{"effect": N}`.
- `info` lists only the active set's `layers`. Use `layer.list {"ts": N}` for the others.

## Reading back

- `info builtin:<id>` fails with an I/O error. Create the project first.
- A project's `info` has `uv: null`. The UV report is in `info` of the mesh file
  (`overlapRatio`, `uvOutOfRange`, `zeroAreaUvTriangles`, `uvsGenerated`, `warnings`).
- The normal format isn't in `info`, and `textureSet.settings` returns `null`. Read
  `normal_format` from `project.json` in the zip (`tc_inspect.py` does).
- Export file names use `$mesh`, which is `mesh` for any imported file.
- TGA exports are RLE-compressed, which Pillow can't decode ("buffer overrun"). Read
  them with ImageMagick (`magick in.tga out.png`) or `sips`.

## Resolution

- `new` defaults to 2048 for a mesh file but **1024 for a built-in** (`new builtin:crate`).
  Pass `--resolution` (or `"resolution"` in a `tc_build.py` spec, which defaults to 2048).
- Bake resolution defaults to 1024 regardless of texture resolution.

## Baking

- `bake.run` and `bake.settings` without `ts` act on the active set only. The `bake`
  subcommand bakes all of them.
- `--maps`/`maps` sets which maps are baked from then on. A later plain `bake.run` bakes
  only those maps.

## Rendering

- `render` needs a GPU or a software adapter. Without one, use `--cpu --samples 16`
  (`tc_render.py` falls back to that by itself).
- The default camera frames the whole mesh from the front-right (yaw ≈ 34°, pitch ≈ 14°).
  Use `--yaw 215` to see the back.
- The 2D view lays every texture set's UV square side by side, so an untextured set
  stands out there.
