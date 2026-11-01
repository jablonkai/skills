# texturecraft-cli reference (0.2.0)

`texturecraft-cli` is a headless TextureCraft. It opens no window. It reads and writes
`.tcraft` projects (zip archives holding `project.json`, the mesh, baked maps, layer
pixels, and any high-poly and cage meshes). In 0.2.0 it installs to `~/.local/bin`; the app
is `/Applications/TextureCraft.app` (bundle id `ai.storyteller.texturecraft`). The vendor's
`docs/control-protocol.md` is **not** shipped in the app bundle, so `--help`, `commands`
and `info` are the ground truth.

## Inputs

`<input>` is any of:
- a `.tcraft` project;
- a mesh file: `.glb .gltf .fbx .dae .usd .usda .usdc .usdz .abc .obj .ply .stl`;
- `builtin:<id>`, one of `material_ball sphere cube rounded_cube cylinder torus plane
  crate udim_plane`. This works for `new`, `run`, `batch`'s `open` and `render`, but **not**
  for `info`.

Relative paths, including those inside command params such as `bake.highPoly.add {path}`,
resolve against the current directory.

## Subcommands

| Command | What it does | Notes |
|---|---|---|
| `--version` | `TextureCraft 0.2.0 (e01dac2 2026-11-01)` | |
| `info F` | JSON for a project or a mesh | See below. Mesh files get a UV report; projects get `uv: null`. |
| `commands [--filter T]` | One line per command: `id  label  {params}` | No JSON form. The filter matches the id and label. |
| `run IN ID [JSON] [-o OUT]` | Runs one command and prints its JSON result | **Without `-o` nothing is saved.** `-o` overwrites without asking. |
| `batch SCRIPT.json` | `{"open": IN, "steps": [{"id","params"}…], "save": OUT}`, or a bare list of steps (on an empty project) | Stops at the first failing step, saves nothing, exits 1. Prints `{completed, failed: {id,index,error}, results}`. |
| `bake IN [-o OUT] [--resolution N] [--maps a,b]` | Bakes every texture set | Without `-o` a project is **saved in place**. `--maps` takes mesh-map ids ([bake.md](bake.md)). |
| `export IN DIR [--preset P] [--format F] [--padding M] [--size N]` | Exports every set | The default preset is `Document channels + Normal + AO`. It has no flag for the set or the normal convention: use `run IN file.exportTextures` or `tc_export.py`. |
| `render IN OUT.png [--size WxH] [--view 3d\|2d] [--yaw D] [--pitch D] [--samples N] [--bounces N] [--cpu]` | Viewport render, or path traced with `--samples` | The viewport needs a GPU or software adapter. `--cpu` uses the CPU path tracer. It prints `wrote X (WxH, adapter, s)` to stderr. |
| `new MESH\|builtin:ID OUT.tcraft [--resolution N] [--sample]` | New project | The default resolution is **2048 for a mesh file but 1024 for a built-in**, so pass `--resolution`. `--sample` bakes and applies a smart material to every set. It overwrites OUT without asking. |
| `mcp [--bridge PORT] [--token T] [--read-root D] [--write-root D]` | MCP server on stdio | See [security.md](security.md). |
| `serve [--port P] [--read-root D] [--write-root D]` | JSON lines (`{"id","method","params"}`) on stdio, or on 127.0.0.1:P with a token | See [security.md](security.md). |

Exit status: 0 on success. On an error it exits 1 and writes
`texturecraft-cli <sub>: error: …` to stderr, e.g. ``unknown command `x` ``,
``unknown mesh map "ao"``, ``valid `ts` index required``, ``no layer 999``.

Typical timings on an M1 Pro: `new builtin:crate` 0.1 s; a 2048² AO and curvature bake of
the crate's 3 sets 7 s; a 3-set glTF export at 2048² 2.5 s; a 768² viewport render 2–3 s; a
256² CPU path trace at 16 samples 1 s.

## `info` JSON

Project (`kind: "project"`):
- `project`: the project name, used as `$project` in export file names.
- `mesh`: `{source, materials, triangles, vertices}`. `source` is `builtin:crate`, or
  `mesh.glb` for an imported mesh, whose `$mesh` token then expands to `mesh`.
- `textureSets[]`: `{index, name, resolution, size, channels[{channel, format}], baked:
  {maps, resolution} | null, layers (count), parts, uvTiles, visible, active}`.
- `layers`: the **active** set's stack only, top first. Use `run P layer.list {"ts": N}` for
  another set.
- `bakeMeshes`: `{highPoly: [{name, parts, triangles}], cage: {…} | null}`.
- `activeTextureSet`, `selectedLayer`, `camera`, `display`, `history`, `modified`.
- The normal format is not in `info`. It is `normal_format` in `project.json` inside the
  zip, which `tc_inspect.py` reads.

Mesh (`kind: "mesh"`): `textureSets` (names), `materials`, `triangles`, `vertices`, `uv:
{materials, triangles, vertices, overlapRatio, uvOutOfRange, zeroAreaUvTriangles,
uvsGenerated, warnings}`. `uvsGenerated: true` means the mesh had no UVs and TextureCraft
unwrapped it automatically; the warning names the number of charts.

## Layer JSON (`layer.list`)

`{id, name, kind: fill|paint|group, visible, channels: {ch: {mode, opacity}}, fill:
{projection, sources: {baseColor: {uniform: [r,g,b]} | {procedural, scale, seed, …}}},
mask: {background: black|white, enabled, effects: [{id, kind: Generator|Fill|Levels|…,
name, blend, opacity, generator: {type: EdgeWear|Dirt|…, level, softness, noise}}]},
children: [...]}`. Layer ids are unique across all sets. Smart materials arrive as a
`group` with `children`.
