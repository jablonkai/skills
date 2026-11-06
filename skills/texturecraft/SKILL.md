---
name: texturecraft
description: 'Automate TextureCraft, the Substance Painter-style PBR texture-painting app, headless with texturecraft-cli: new .tcraft projects from a mesh (glb, fbx, obj, usd) or a built-in, mesh-map bakes (AO, curvature, normal), high-poly to low-poly with a cage, fill-layer stacks with smart or MaterialCraft .mcmat materials, masks and edge-wear or dirt generators, edits to .tcraft projects, PBR texture export with engine presets (glTF, Unreal, Unity, Godot; PNG/TGA/EXR; OpenGL or DirectX normals), textured GLB/OBJ/USD export, 3D or UV renders, read back. Use when the user mentions TextureCraft, texturecraft-cli or a .tcraft file, or wants a model PBR-textured or mesh maps baked with TextureCraft: "texture this crate as rusty metal in TextureCraft", "bake AO and curvature", "export a glTF PBR set with DirectX normals", "bake the high poly onto the low poly with a cage". Not for Blender painting or baking (blender), 2D painting (krita, gimp), modeling (blender, freecad, solidcraft), or AI texture generation (comfyui).'
summary: "automate TextureCraft headless with texturecraft-cli — projects from meshes or built-ins, AO/curvature and high-poly bakes with a cage, fill-layer stacks with smart materials, masks and edge-wear generators, .tcraft edits, glTF/Unreal/Unity/Godot PBR texture export checked against the plan, textured GLB export, 3D and UV renders, info read-back verified"
category: 3d
compatibility: "Built for TextureCraft 0.4.0 (16e9d21) and texturecraft-cli 0.4.0 on macOS (Apple Silicon, Metal), Python 3.9+; pre-1.0, so command ids may change."
risk: low
tags: [texturecraft, pbr, texturing, baking, mesh-maps, gltf, headless]
license: GPL-3.0-only
metadata:
  version: "1.1.2"
  author: "Tamás Jablonkai"
---

# TextureCraft via texturecraft-cli

TextureCraft is a PBR texture-painting app in the style of Substance Painter. A project
(`.tcraft`, a zip) holds a mesh, one **texture set** per material, each with its own layer
stack (fill, paint and folder layers with masks and effects), baked mesh maps, and any
high-poly and cage meshes. Every tool is a command in one registry (172 in 0.4.0) that
runs headless through `texturecraft-cli`, with no window. This skill drives it headless
and reads every result back with `info`. Verified against **TextureCraft 0.4.0
(16e9d21)**. The software is pre-1.0, so if a pinned id fails, look it up with
`texturecraft-cli commands --filter WORD` rather than guessing.

```sh
texturecraft-cli --version     # TextureCraft 0.4.0 (16e9d21 2026-11-06); lives in ~/.local/bin
```

## Pick the route

| Task | Route |
|---|---|
| New textured project: bake, layer stack, save | `scripts/tc_build.py spec.json --expect-layer all:NAME --expect-baked all:ambientOcclusion,curvature` |
| Edit a copy of an existing `.tcraft` | `scripts/tc_build.py spec.json --in OLD.tcraft --save NEW.tcraft` |
| What a project or mesh holds (sets, layers, bakes, UV report) | `scripts/tc_inspect.py F` (`--full` for fill and mask settings) |
| Export textures, checked against `export.plan` | `scripts/tc_export.py P.tcraft DIR --preset "glTF PBR Metal Roughness" [--size N] [--normal directx] [--ts SET]` |
| Textured mesh (GLB/OBJ/USD), re-imported to check | `scripts/tc_export.py P.tcraft DIR --preset … --mesh DIR/model.glb` |
| Look at it | `scripts/tc_render.py P.tcraft out.png --uv` (then Read the PNGs) |
| One command, one-off | `texturecraft-cli run IN ID 'JSON' -o OUT.tcraft` (no `-o`, nothing is saved) |
| Find a command and its params | `texturecraft-cli commands --filter WORD` |
| Smart materials, smart masks, presets, filters | `run P material.list` / `mask.smart.list` / `export.presets` / `filter.list` |
| A MaterialCraft material (`.mcmat`/`.mcraft`) as a live layer | `material.load {path}` in a spec, then `material.link.set {id, value}` / `.preset {name}` ([commands.md](references/commands.md#smart-materials)) |

## Scripts

Set `S=<this skill>/scripts` and call each as `python3 $S/<script>`. They need Python 3.9+
and the standard library only, and each has a full `--help`. They find the CLI
(`TEXTURECRAFT_CLI`, then PATH, then `~/.local/bin`), never write to their input, refuse to
overwrite outputs without `--overwrite`, print JSON and exit 1 on any failed check.

- **`tc_build.py SPEC [--in F] [--save F.tcraft] [--resolution N] [--expect-layer SET:NAME] [--expect-baked SET:MAPS] [--dry-run]`**
  - SPEC is `{"in", "resolution", "steps": [{"id", "params"}…], "save"}`. A step can be a
    group, `{"sets": "all" | ["Lid", 2], "steps": […]}`, which selects each set and runs its
    steps there.
  - Before running, it checks every id and **every param key** against the registry, and
    it refuses generators or smart materials on a set whose needed maps aren't baked. All
    steps then run as one `batch`, and the result is read back with `info` and `layer.list`.
- **`tc_inspect.py F [--full] [--json-out J]`**: for a project, the normal format, then per
  set the resolution, baked maps and layer tree with masks and linked MaterialCraft
  materials (graph, exposed values, presets). For a mesh file or `builtin:<id>`, the sets,
  triangles and UV report, plus the embedded textures of a `.glb`.
- **`tc_export.py P DIR [--preset NAME|preset.json] [--ts SET] [--format F] [--bit-depth N] [--size N] [--padding M] [--normal directx|opengl] [--mesh OUT] [--plan-only]`**
  - It runs `export.plan`, then exports. It checks that the written files equal the plan
    and that each file decodes at the expected size.
  - With `--normal`, it proves the convention by comparing green channels against the
    opposite one.
  - With `--mesh`, it re-imports the mesh and checks the triangle count and embedded
    textures.
- **`tc_render.py IN OUT.png [--uv] [--view 3d|2d] [--size WxH] [--yaw D --pitch D] [--samples N] [--cpu]`**:
  renders and checks that each image isn't blank. If the viewport needs a GPU it doesn't
  have, it falls back to the CPU path tracer.

## Workflow

1. **Inspect first.** Run `tc_inspect.py` on the input: for a mesh, its texture sets
   (one per material) and UV report (overlaps, out-of-range UVs, generated unwraps); for a
   `.tcraft`, its layer stacks and what's baked. The set names drive everything after.
2. **Bake before you layer.** Edge wear, dirt, curvature and thin-area generators read the
   baked maps, and so do most smart materials. On an unbaked set they render as nothing, and
   nothing reports it. Bake in the same spec, before the layers: `bake.run {"ts": "all",
   "resolution": 2048, "maps": ["ambientOcclusion", "curvature"]}`. Bake resolution is
   separate from texture resolution (it defaults to 1024).
3. **Write the stack as a spec** ([recipes.md](references/recipes.md)): fill layers (`color`
   as 0–1 floats or `"#rrggbb"`, `metallic`, `roughness`), `mask.add.black` plus
   `effect.add.generator`, or `material.apply` with a smart material. Wrap the layer steps
   in a `{"sets": …}` group: **layer commands only touch the active texture set.**
4. **Build with `tc_build.py`** using `--expect-layer` and `--expect-baked`. If a check
   fails, fix the spec and rerun it to the same `--save` with `--overwrite`. The input
   stays untouched.
5. **Export with `tc_export.py`**. Pick the preset for the target engine by its exact
   title: `glTF PBR Metal Roughness`, `Unreal Engine (Packed)`, `Unity HDRP (Mask Map)`,
   `Godot 4 (ORM)` and others ([export.md](references/export.md)). Pass `--normal` and
   `--size` when the user named them, and `--mesh` for a textured model.
6. **Look at it.** Run `tc_render.py OUT.tcraft preview.png --uv` and Read both PNGs. A
   mask on the wrong set, or a generator that rendered nothing, shows only in the picture.
   The UV view covers set 0 only; judge the other sets in the 3D view.
7. **Report** the files, the read-back numbers (sets, layers, baked maps, sizes) and
   anything you could not check.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **Unknown param keys are dropped silently.** `"colour"` gives a fill with no base colour
  and the step still "succeeds". `tc_build.py` checks the keys; with plain `run`/`batch`,
  copy the keys from `commands --filter`.
- **Layer, mask, effect and smart-material commands act on the active set only.** Use
  `{"sets": "all"}` in the spec, or `textureSet.select {"ts": INDEX}` (an index, not a
  name), or `layer.instantiateAll {"copy": true}` after building one set.
- **Generators need baked maps** (see step 2), and the map ids are long:
  `ambientOcclusion`, `curvature`, `thickness`, `normal`, `worldNormal`,
  `position`, `id`. A short id like `ao` is an error.
- **The normal convention lives in the export, not the project.** Presets fix it: glTF,
  Blender, Godot and OpenPBR use OpenGL; Unreal uses DirectX. Only the export's
  `normalFormat` overrides a preset (`tc_export.py --normal`). The project-wide
  `textureSet.settings normalFormat` only affects the plain `Normal` channel of the
  Document and Separate presets.
- **`run` without `-o` saves nothing**, and `new` and `-o` overwrite existing files without
  asking. Chain edits in one `batch` or through `tc_build.py`.
- **Importing a mesh doesn't import its materials.** Each set starts as one empty
  `Layer 1`. To recolour a set, add a fill layer on that set.
- **A project's `info` has no UV report.** Inspect the mesh file or `builtin:<id>` for that
  (`info builtin:crate` works since 0.3.0).
- **A MaterialCraft 0.2.0 `.mcmat` does not load.** It is `version 2`; TextureCraft 0.4.0
  reads up to 1 (`material.load` fails with `unsupported`). See
  [recipes.md](references/recipes.md#6-a-materialcraft-material-on-one-set-tuned-and-re-cooked-in-place).
- **The 2D render shows only the first texture set.** A saved project always reopens on
  set 0, so `render --view 2d` (and `tc_render.py --uv`) can't show a bare `Lid` or
  `Handle`; check every set in the 3D render, with `--yaw 215` for the back.

## The running app (optional)

`texturecraft-cli mcp --bridge PORT` and `serve` can drive a running TextureCraft started
with `--control PORT`. This skill works headless on files. Use the live route only when
the user wants their open project changed, and read
[security.md](references/security.md) first.

## References

- [references/cli.md](references/cli.md): subcommands, flags, batch format, `info` JSON, exit codes.
- [references/commands.md](references/commands.md): command ids and params by task, pinned to 0.4.0, and registry lookup.
- [references/bake.md](references/bake.md): mesh-map ids, bake settings, high-poly and cage bakes.
- [references/export.md](references/export.md): built-in presets and their packing, preset objects, file-name tokens, formats, normals.
- [references/recipes.md](references/recipes.md): rusty crate, recolouring a set of an imported GLB, high-to-low bake with cage, smart materials on every set, a MaterialCraft material re-cooked in place.
- [references/gotchas.md](references/gotchas.md): silent failures and surprises.
- [references/security.md](references/security.md): file access, `serve`/`mcp` and the app's control channel.
