# Gotchas (MaterialCraft 0.4.0)

## Silent successes that did the wrong thing

| What you do | What happens | Do instead |
|---|---|---|
| A misspelled **command** key (`conectFrom`, `colour`) | Ignored; the step reports success | Copy keys from `commands --filter`; `mc_build.py` rejects them. (Unknown node defs, node param ids and port ids *are* errors.) |
| `graph.node.add {connectFrom}` into `blend`/`lerp`/`height_blend` | Wires the **first** input (`foreground`, `input_a`, `top`); the other stays empty and the result is black or flat, with no cook error | Wire both inputs with explicit `toPort`s |
| `graph.connect` into an input that already has a wire | Replaces it | Use it to insert nodes; check `mc_inspect.py` wires afterwards |
| Export `--pattern` with an unknown token (`$(name)`, `$(size)`) | Becomes `_name_` in the file name | Tokens are `$(graph)`, `$(identifier)`, `$(usage)` only |
| A pattern without `$(identifier)`/`$(usage)` | Every output writes the same file; the last wins | Keep one of them |
| `--depth 16` on jpg/webp/tga/bmp, `--depth 32` on png/tif, `--depth 8/16` on exr | Ignored: 8-bit, 16-bit, 32-bit float respectively | See export.md; `mc_export.py` refuses |
| An exposed input with no `bind` | Exists, saves into presets and the `.mcmat`, drives nothing | `mc_inspect.py` warns; `mc_render.py --variants` fails on identical renders |
| `graph.node.bind` / `graph.preset.save`, then **save** | The `.sbs` keeps the exposed input but **not the binding or the preset**; a reload shows `bindings: {}`, `presets: []`, and `--set` changes nothing | Bind, set and export in one `batch` (recipes.md §3); `mc_build.py` reports the loss as a failed read-back |
| `--set id="#rrggbb"` for an exposed colour | `takes a float4`: after a reload the input is a float4 and hex is rejected | Pass the array: `--set tint=[0.7,0.02,0.02,1]` |
| A path that is neither `.sbs` nor `.mcraft` (`-o t.foo`, `new`, `batch` `save`) | Writes `t.foo.sbs`; `t.foo` then doesn't exist (`.mcraft` is kept and written as a zip of `package.sbs`, since 0.3.0) | Write `.sbs`; `mc_build.py` normalises its `save` |
| A float default bound to an enum param | `bad default` error | Bind floats to float/int params |
| A float exposed input bound to a float4 param (`levels`) | The cook fails: `variable ... has the wrong type for get_float4` | Add the input with a typed default `{"t": "float4", "v": [..]}` |
| `graph.function.set` with an unknown `op` | Fails (`unknown function`), saves nothing | Use the ops listed in nodes.md |
| `render --view 2d --tiling 3` | Same PNG as without `--tiling`: no repeat | `mc_render.py --tile 3` |
| `render --view 2d` of a node that cooks black | A black PNG, exit 0 | Read the PNG; `mc_render.py` reports flat images |
| `cook` without `--full` | Nodes cooked at open time show `cached: true`, `ms: 0` | Use `--full` when the cook report is your check |

## Commands that need a selection

`graph.node.rename`, `.move`, `.disable`
and `edit.delete`, `.deleteRelink`, `.copy`, `.cut`, `.duplicate` fail with
`not available: no node is selected` when the selection is empty — **even when `id`/`ids` is
given**. (Since 0.4.0 `graph.node.param`, `.reset`, `.base` and `.bind` run without a selection; selecting first is still harmless, and `mc_build.py` keeps doing it.) With any selection they act on the `id`/`ids` you pass. Headless runs start with
nothing selected, so:

```json
{"id": "graph.select", "params": {"ids": [13]}},
{"id": "graph.node.param", "params": {"id": 13, "param": "out_high", "value": 0.4}}
```

`graph.exposed.add {bind}` and `graph.connect` don't need a selection.

## Colours

- Hex (`"#rrggbb"`) is **sRGB**; typed colours `{"t": "color", "v": [r, g, b, a]}` are
  **linear**. `graph.exposed.set` / `--set` / `graph.node.param` linearise hex
  (`#8a5a3c` → `[0.254, 0.102, 0.045]`).
- `graph.exposed.add` rejects a hex `default` (`invalid default`; `bad default` before 0.4.0); give the typed linear value. The
  saved input comes back as a **float4** (sRGB-encoded), so later `exposed.set` / `--set` take an array, not hex.
- `--set` values are JSON: `--set 'tint="#aa7744"'` (shell quotes around JSON quotes).
  `--set tint=#aa7744` is not valid JSON.

## Tiling

- The 0.1.2 `anisotropic_noise` seam is gone with the old library (no noise nodes in 0.4.0). A
  `pixel_processor` function tiles when it has a whole number of periods across the pixel
  position; the Atomic sample's height (an FX-Map) scores x=2.41 (not seamless).
- Node `base.tiling` (`graph.node.base {tiling: false}`) does not change what a generator
  produces; it is not a seam fix.
- `render --view 2d --tiling N` is still ignored in 0.4.0 — the PNG is byte-identical to the
  untiled one (so is `view.2d {tiled: true}`). In 3D (`--scene plane --tiling 3`) it repeats
  the UVs. `mc_render.py --tile N` writes a real N×N 2D repeat so you can *see* seams;
  `mc_render.py --seam` gives the number.

## Files

- `new`, `run -o`, `batch` `save` and `export` overwrite without asking; `export` into a
  folder that holds an earlier export mixes old and new files. The `mc_*` scripts refuse
  existing outputs unless `--overwrite`.
- `run` without `-o` saves nothing — the change is lost. Chain edits in one `batch` or
  through `mc_build.py`.
- A failed `batch` stops at the failing step, exits 1 and saves nothing (`failed.index` names
  the step).
- `info` shows the package's open graph — graph 0 after a reload. Another graph:
  `session.inspect {"graph": I}` or `--graph I` on `cook`/`export`/`render`/scripts.
- Node ids are never reused: after a delete, the next node gets max-ever + 1. Read ids from
  the `batch` results, never compute them.
- New packages default to 1024×1024 and 16-bit (`u16`) — pass `--size`; maps export at the
  graph size.

## Version drift

Pinned to 0.4.0: 119 commands (86 in 0.2.0, 112 in 0.3.0, every old id kept), 29 node entries (0.1.2 had 68 and 222: the old procedural library
was removed in favour of primitives, and the packages moved from `.mcraft` to `.sbs`). After an update,
re-run `materialcraft-cli commands` and `nodes` and compare before trusting these pages.
