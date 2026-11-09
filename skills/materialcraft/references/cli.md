# materialcraft-cli reference (0.3.0)

`materialcraft-cli` is the headless MaterialCraft: the same engine and command registry as the
app, no window, no GPU. It lives in `~/.local/bin` (the app bundle is
`/Applications/MaterialCraft.app`, bundle id `ai.storyteller.materialcraft`). There is no
per-subcommand `--help` (`mcp --help` is an error); `materialcraft-cli` or `--help` alone prints the usage.
The vendor's `docs/control-protocol.md` is not installed with the app — `commands` and `nodes`
are the reference. Packages are native **SBS** (`.sbs`, XML) since 0.2.0; the CLI keeps `.sbs` and `.mcraft` (a zip holding `package.sbs`, writable again in
0.3.0) and appends `.sbs` to any other save path (`new x t.foo` writes `t.foo.sbs`).

| Subcommand | What it does |
|---|---|
| `--version` | `materialcraft-cli 0.3.0 (ac6dc55 2026-11-09)` |
| `info IN` | The whole session as JSON (see below). `IN` is a `.sbs` or `sample` (the built-in atomic sample). |
| `commands [--filter T]` | JSON list `[{id, label, params}]`; `params` is a signature string. |
| `nodes [--filter T] [--category T]` | JSON list of node definitions: `id, label, category, description, inputs[{id, kind}], outputs[{id, kind}], params[{id, label, default{t,v}, min, max, options}]`. |
| `run IN ID [JSON] [-o OUT]` | One command; prints its JSON result. Without `-o` nothing is saved. |
| `batch SCRIPT.json` | `{"open": IN, "steps": [{"id", "params"}…], "save": OUT}` (or a bare list of steps). Stops at the first error, prints `{completed, failed: {index, id, error}, results}`, exits 1 and saves nothing. |
| `new TEMPLATE OUT [--size PX] [--name N]` | New package with one graph (templates: `empty`, `pbr`, `atomics`; any other id fails with `unknown template`). Size defaults to 1024 (power of two). Overwrites `OUT`. |
| `cook IN [--graph I] [--set K=V]… [--full]` | Cook; prints `{ms, nodes: [{id, def, ms, size, cached, error}]}`. Without `--full`, nodes cooked when the package was opened are reported as `cached: true` (≈0 ms); `--full` re-cooks every node, which is the check to trust. |
| `export IN DIR [--graph I] [--set K=V]… [--format F] [--depth 8\|16\|32] [--pattern P] [--size PX]` | Cook at full size (or `--size`, rounded down to a power of two: 100 gives 64, 512 re-cooks at 512) and write every output node; prints `{files}`. Creates `DIR`; overwrites files in it. |
| `render IN OUT.png [--size WxH] [--view 3d\|2d] [--scene S] [--node ID] [--yaw D] [--pitch D] [--graph I] [--set K=V]… [--full] [--tiling N] [--hq [--displacement R]]` | CPU render. 3D default 1024×768 on `rounded_cube`; scenes `rounded_cube, cube, sphere, cylinder, plane, torus, material_ball`. 2D shows one node's output (`--node`); `--tiling N` repeats the UVs in 3D but is **ignored in 2D** (identical PNG) — use `mc_render.py --tile N`. `--hq` adds real displacement from the height output, AO and a key light (≈4 s at 1024×768). |
| `mcp [--bridge PORT] [--token T] [--read-root D] [--write-root D]` | MCP server on stdio — headless (file access only below the roots) or bridged to a running app. |
| `serve [--port P] [--read-root D] [--write-root D]` | JSON lines `{"id","method","params"}` on stdio, or on `127.0.0.1:P` with a token. |

## Values

- `--set K=V`: `V` is JSON. Numbers bare (`--set roughness=0.4`), colours quoted
  (`--set 'tint="#aa7744"'`), vectors as arrays. An unknown `K` fails with exit 1
  (`no input K`). The value applies to that run only; the package is not changed.
- Node parameters (`graph.node.param` value, `graph.node.add` `params`): numbers, `[x, y]`,
  `"#rrggbb"`, an enum **index**, `true/false`, or a typed value `{"t": T, "v": V}`. Types:
  `float, int, enum, bool, color (linear RGBA 0–1), float2, text, gradient, curve, function`.
  A gradient: `{"t": "gradient", "v": {"keys": [{"pos": 0, "color": [r,g,b,a]}, …]}}`.
- Node ids are integers, allocated as max-ever + 1 and never reused after a delete. `batch`
  returns them in `results` (`{"id": N}` per `graph.node.add`).

## `info` JSON (top level)

`package {name, path, modified, resources}`, `graphs [{index, kind, name, nodes}]`,
`openGraph`, `graph` (the open graph, in full), `view2d`, `view3d`, `previewSize`,
`selection`, `history`, `log`, `cookMs`, `dirty`, `canUndo`, `canRedo`.

`graph`: `index, name, size [w,h], format (u8|u16|f16|f32), seed, attributes, nodes, connections
[{from, fromPort, to, toPort}], exposed [{id, label, default, min, max}], presets [{name,
values}], inputs, frames, comments, pins`. Each node: `id, def, label, pos, disabled, params
{id: {t, v}}` (only non-default values), `base {sizeMode, size, format, seed, tiling}`,
`bindings {param: exposed id}`, `functions`, `inputs`, `outputs`, `cooked {size, kind, mean,
ms, error}`.

`info` always shows the package's open graph (saved packages reopen on graph 0). For another
graph use `run IN session.inspect '{"graph": I}'` (same shape) or `mc_inspect.py --graph I`.

## Exit codes

0 on success; 1 on any command error (message on stderr as `materialcraft-cli: …`). A failed
`batch` also prints its JSON with `failed` on stdout.
