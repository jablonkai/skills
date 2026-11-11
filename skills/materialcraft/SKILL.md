---
name: materialcraft
description: 'Automate MaterialCraft, the Substance Designer-style procedural material app, headless with materialcraft-cli: .sbs packages from a template (empty, pbr, atomics) or a node graph built from a spec (primitive nodes, pixel-processor function graphs, filters, normal, outputs), exposed inputs (variants only within one build run, since 0.2.0 .sbs files drop bindings), edits to existing graphs, tileable PBR map export as PNG/EXR/TGA/TIF at 8/16/32-bit with a name pattern, .mcmat export for TextureCraft, 3D and 2D renders with a seam check, read back. Use when the user mentions MaterialCraft, materialcraft-cli, .sbs, .mcraft or .mcmat, or wants a procedural tileable material authored as a node graph: "make a tileable striped wood material", "expose a tint colour and export a red variant", "export the PBR maps as 16-bit PNG". Not for painting materials onto a mesh or baking (texturecraft), Blender shader nodes (blender), or editing 2D texture images (imagemagick, gimp, krita).'
summary: "automate MaterialCraft headless with materialcraft-cli — procedural .sbs material graphs from a node spec or the pbr template, primitive nodes and pixel-processor function graphs, exposed inputs, graph edits, tileable PBR map export in any format and bit depth with a seam check, .mcmat hand-off to TextureCraft, 3D and 2D renders, info and cook read-back verified"
category: 3d
compatibility: "Built for MaterialCraft 0.4.0 and materialcraft-cli 0.4.0 (b6f1aa0) on macOS (CPU renders, no GPU needed), Python 3.9+; the .mcmat hand-off does not load in TextureCraft 0.6.0 (d1ca3fd) either (still version 2 vs 1). Pre-1.0, so command and node ids may change."
risk: low
tags: [materialcraft, procedural, materials, pbr, node-graph, tileable, headless]
license: GPL-3.0-only
metadata:
  version: "2.0.2"
  author: "Tamás Jablonkai"
---

# MaterialCraft via materialcraft-cli

MaterialCraft is a node-based procedural material app in the style of Substance Designer. A
package (`.sbs`) holds one or more **graphs**; each graph is a set of nodes (primitives: bitmap/text/
FX-Map/pixel-processor generators, blend, levels, blur, warp, normal ...) wired into **output** nodes, one per
PBR map. A graph can **expose inputs** (bound to node parameters) and store **presets** of
their values. Everything runs headless through `materialcraft-cli`, with no window or GPU.
This skill builds and edits graphs headless and reads every result back. Verified against
**MaterialCraft 0.4.0 (b6f1aa0)**: 119 commands, 29 node entries (0.2.0 replaced the 222-node
procedural library with primitives and moved packages from `.mcraft` to `.sbs`). The software is pre-1.0, so if a
pinned id fails, look it up (`commands --filter WORD`, `nodes --filter WORD`) rather than
guessing.

```sh
materialcraft-cli --version     # materialcraft-cli 0.4.0 (b6f1aa0 2026-11-11); lives in ~/.local/bin
```

## Pick the route

| Task | Route |
|---|---|
| New material from a template | `materialcraft-cli new pbr OUT.sbs --size 1024 --name Oak` (templates: `empty`, `pbr` = six flat uniforms, `atomics` = the primitive sample; the 0.1.2 wood, brick, marble ... templates are gone) |
| Graph built node by node, or a template/package edited (wires, params, exposed inputs, presets) | `scripts/mc_build.py spec.json` ([recipes.md](references/recipes.md)) |
| What a package holds, and does it cook | `scripts/mc_inspect.py IN.sbs` (`--params` for values, `--graph N` for another graph) |
| PBR maps, checked | `scripts/mc_export.py IN.sbs DIR --format png --depth 16 --pattern '$(graph)_$(identifier)' [--set id=v]` |
| `.mcmat` for TextureCraft (**0.4.0 files do not load in TextureCraft 0.6.0**, [export.md](references/export.md)) | `scripts/mc_export.py IN DIR --mcmat OUT.mcmat --texturecraft-check` |
| Look at it / variants / tiling | `scripts/mc_render.py IN OUT.png --scene sphere --hq`, `--variants wear=0,0.5,1`, `--tile 3`, `--seam` |
| One command, one-off | `materialcraft-cli run IN ID 'JSON' -o OUT.sbs` (no `-o`, nothing is saved) |
| Find a node, its ports and params | `materialcraft-cli nodes --filter WORD` / `--category Noises` ([nodes.md](references/nodes.md)) |
| Find a command | `materialcraft-cli commands --filter WORD` ([commands.md](references/commands.md)) |

## Scripts

Set `S=<this skill>/scripts` and call each as `python3 $S/<script>`. Python 3.9+, standard
library only, full `--help` each. They find the CLI (`MATERIALCRAFT_CLI`, then PATH, then
`~/.local/bin`), never write to their input, refuse to overwrite outputs without
`--overwrite`, print JSON and exit 1 on any failed check.

- **`mc_build.py SPEC [--in F] [--save F] [--dry-run] [--overwrite]`** — SPEC names new
  nodes (`{"px": {"def": "pixel_processor", "params": {…}}}`) and refers to them by name in
  `wires` (`["px", "blend:mask"]`), `outputs` (`{"basecolor": {"from": "grad", "usage":
  "Base color"}}`), `params`, `exposed` (with `bind`) and `presets`; existing nodes are
  referred to by integer id. It checks every def, param key, port, usage and command key
  against the CLI's registries first, runs two batches (add nodes; then wire, configure,
  cook, save), selects nodes for the commands that need a selection, and reads the result
  back: nodes, wires, outputs, bindings, presets and a full cook with zero errors.
- **`mc_inspect.py IN [--graph N] [--params] [--no-cook]`** — graphs, nodes, wires as
  `id:port -> id:port`, outputs with their source, exposed inputs with what they are bound
  to, presets, cook errors. Warns about exposed inputs bound to nothing (in 0.4.0 that is every saved binding).
- **`mc_export.py IN DIR [--graph N] [--set ID=V]… [--format F] [--depth N] [--pattern P] [--mcmat F [--mcmat-size N]] [--texturecraft-check]`**
  — refuses unknown `--set` ids, unknown pattern tokens and depths the format cannot hold
  (the CLI would silently do something else), then checks one file per output at the graph
  size and the requested bit depth (PNG, EXR pixel type). With `--mcmat` it checks the
  zip's maps and parameter values; `--texturecraft-check` loads it into a fresh TextureCraft
  project and confirms the linked material layer.
- **`mc_render.py IN OUT.png [--view 3d|2d] [--scene S] [--node ID] [--hq] [--tiling N] [--set ID=V]… [--variants ID=V1,V2,…] [--tile N] | IN --seam [NODE…]`**
  — fails a flat 3D render and variants that look the same (the input drives nothing
  visible). `--tile N` writes an N×N 2D repeat of one map, assembled by the script. `--seam` renders each output at full size and scores the wrap-around edges
  (≤ 1.5 tiles; real seams score 4+).

## Workflow

1. **Inspect first.** `mc_inspect.py` on any input (or `info sample` for the built-in brick
   wall): node ids, what each output is fed by, exposed inputs and their bindings. Node ids
   are what every edit refers to.
2. **Look nodes up, don't guess.** `nodes --filter WORD` gives the exact def id, input and
   output port ids and parameter ids with defaults and ranges. Multi-output nodes
   (`pbr_base_material`, `height_normal_ao`, `material_blend`, `height_blend`) need the port:
   `"hna:normal"`.
3. **Write a spec and build with `mc_build.py`** ([recipes.md](references/recipes.md)). Start
   from a template when one is close; start from `empty` for a graph from scratch. For a
   value the user will tweak, add an **exposed input bound to the node parameter**
   ([exposed.md](references/exposed.md)); save named presets in the same spec.
4. **Variants without editing:** `--set id=value` on `cook`, `export` and `render` (and
   `mc_*` scripts) applies exposed-input values for that run only. Colours: `--set
   'tint="#aa7744"'` (JSON, so the quotes matter; the scripts add them).
5. **Export with `mc_export.py`** ([export.md](references/export.md)): `--format`,
   `--depth` and `--pattern` (tokens `$(graph)`, `$(identifier)`, `$(usage)` only). Add
   `--mcmat` (+ `--texturecraft-check`) when the material goes to TextureCraft.
6. **Look at it.** `mc_render.py OUT.png --scene sphere --hq` (≈4 s) for a beauty shot,
   `--tile 3` for a 3×3 repeat of the base colour, `--seam` for a number. Read the PNGs: a wrong colour
   ramp or an inverted roughness only shows in the picture.
7. **Report** files, the read-back (nodes, outputs, exposed inputs, presets, cook errors,
   map sizes and depths, seam scores) and anything you could not check.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **Unknown command keys are ignored silently** (`conectFrom` adds an unwired node and
  "succeeds"). Node defs, node param keys and ports are checked by the engine; command keys
  are not. `mc_build.py` checks them; with raw `run`/`batch` copy keys from `commands`.
- **`graph.node.rename`/`.move`/`.disable` and `edit.*` commands refuse to run with an empty selection**,
  even when given `id`/`ids` ("not available: no node is selected"; `.param`, `.reset`, `.base` and `.bind` no longer need one since 0.4.0). Put `graph.select {"ids": [N]}`
  first; the `id` is then honoured. `mc_build.py` does this for you.
- **`connectFrom` wires into the node's first input** — for `blend` that is `foreground`,
  for `lerp` `input_a`. Wire the second input explicitly, or the blend multiplies against
  nothing (a black output that cooks without error).
- **`graph.connect` into an occupied input replaces the wire** — that is how you insert a
  node between two others (connect A→new, new→B).
- **Hex colours are sRGB, typed colours are linear.** `graph.exposed.add` rejects
  `"#rrggbb"` as a default (use `{"t": "color", "v": [r, g, b, a]}`, linear);
  `graph.exposed.set` and `--set` accept hex and linearise it. `mc_build.py` converts.
- **No noise or pattern nodes in 0.4.0.** Detail comes from a `pixel_processor` function
  graph (recipes.md §1) or an `fx_map`; `nodes --filter perlin` prints `[]`. Old specs with
  `perlin_noise`, `height_normal_ao`, `edge_wear` or the `wood`/`bricks` templates fail the
  `mc_build.py` pre-check.
- **Bindings and presets are not saved in `.sbs`** in 0.4.0: a reload shows exposed inputs
  bound to nothing, so `--set` and `--variants` do nothing. Bind, set and export in one
  `batch` ([exposed.md](references/exposed.md), recipes.md §3).
- **The CLI appends `.sbs`** to any save path that is not `.sbs` or `.mcraft` (`t.foo` becomes
  `t.foo.sbs`). `.mcraft` is written again since 0.3.0, as a zip holding one `package.sbs`; it still
  loses bindings and presets. Write `.sbs`.
- **`.mcmat` is `version 2` and TextureCraft 0.6.0 reads up to 1**, so `--texturecraft-check` fails.
- **`render --view 2d --tiling N` does not repeat anything** in 0.4.0 (the PNG is identical to
  `--tiling 1`); in 3D `--tiling` repeats the UVs. For a tiled 2D view use `mc_render.py
  --tile N`.
- **Nothing asks before overwriting**: `new`, `-o`, `batch` `save` and `export` into an
  existing folder replace files. A failed `batch` saves nothing.

## The running app (optional)

`materialcraft-cli mcp --bridge PORT` and `serve --port` can drive a running MaterialCraft
started with `materialcraft --control PORT`. This skill works headless on files. Use the
live route only when the user wants their open document changed, and read
[security.md](references/security.md) first.

## References

- [references/cli.md](references/cli.md): subcommands, flags, batch format, value syntax, `info` JSON, exit codes.
- [references/commands.md](references/commands.md): the 119 command ids by group, pinned to 0.4.0, and registry lookup.
- [references/nodes.md](references/nodes.md): node categories, the core nodes with ports and params, library lookup.
- [references/recipes.md](references/recipes.md): graph from scratch, template tint insert, weathering, multi-output nodes, fixing tiling.
- [references/exposed.md](references/exposed.md): exposed inputs, bindings, presets, `--set` variants, parameter functions.
- [references/export.md](references/export.md): formats and depths, pattern tokens, `.mcmat` and the TextureCraft hand-off (broken in 0.4.0).
- [references/gotchas.md](references/gotchas.md): silent failures and surprises.
- [references/security.md](references/security.md): file access, `serve`/`mcp` and the app's control channel.
