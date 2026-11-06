# Recipes (mc_build.py specs, verified on 0.2.0)

Run each with `python3 $S/mc_build.py spec.json` (add `--dry-run` to see the two batches
first). New nodes are named; existing nodes are integer ids from `mc_inspect.py`. Save paths
get `.sbs` appended by the CLI, so write `.sbs` yourself.

0.2.0 has no noise or pattern nodes and only three templates (`empty`, `pbr`, `atomics`), so
procedural detail comes from a `pixel_processor` **function graph** ([nodes.md](nodes.md)).

## 1. A tileable PBR graph from an empty package

Stripes from a function (`sin(x * 25.13) * 0.5 + 0.5`, four periods, so it tiles) -> height,
normal and a colour ramp for base colour; a flat roughness.

```json
{
  "template": "empty", "size": 256, "name": "Stripes",
  "nodes": {
    "px":     {"def": "pixel_processor", "params": {"color_mode": false}},
    "normal": {"def": "normal", "params": {"intensity": 3}},
    "ramp":   {"def": "gradient_map", "params": {"gradient": {"t": "gradient", "v": {"keys": [
                 {"pos": 0, "color": [0.20, 0.12, 0.06, 1]}, {"pos": 1, "color": [0.75, 0.60, 0.42, 1]}]}}}},
    "rough":  {"def": "uniform", "params": {"color": [0.7, 0.7, 0.7, 1], "color_mode": false}}
  },
  "wires": [["px", "normal"], ["px", "ramp"]],
  "outputs": {
    "basecolor": {"from": "ramp",   "usage": "Base color"},
    "normal":    {"from": "normal", "usage": "Normal"},
    "roughness": {"from": "rough",  "usage": "Roughness"},
    "height":    {"from": "px",     "usage": "Height"}
  },
  "steps": [{"id": "graph.function.set", "params": {
    "target": {"kind": "parameter", "node": "@px", "parameter": "function"},
    "function": {"output": 8, "nodes": [
      {"id": 1, "op": "get_float2",   "inputs": [],     "pos": [0, 0],   "type_code": 512, "value": {"t": "text", "v": "$pos"}},
      {"id": 2, "op": "swizzle1",     "inputs": [1],    "pos": [140, 0], "type_code": 256, "value": {"t": "int", "v": 0}},
      {"id": 3, "op": "const_float1", "inputs": [],     "pos": [280, 0], "type_code": 256, "value": {"t": "float", "v": 25.13}},
      {"id": 4, "op": "mul",          "inputs": [2, 3], "pos": [420, 0], "type_code": 256},
      {"id": 5, "op": "sin",          "inputs": [4],    "pos": [560, 0], "type_code": 256},
      {"id": 6, "op": "const_float1", "inputs": [],     "pos": [560, 0], "type_code": 256, "value": {"t": "float", "v": 0.5}},
      {"id": 7, "op": "mul",          "inputs": [5, 6], "pos": [700, 0], "type_code": 256},
      {"id": 8, "op": "add",          "inputs": [7, 6], "pos": [840, 0], "type_code": 256}]}}}],
  "save": "stripes.sbs"
}
```

Then: `mc_render.py stripes.sbs --seam` (all outputs <= 1.5) and
`mc_render.py stripes.sbs tile.png --tile 3` (a real 3x3 repeat of the base colour).
Gradient colours are linear 0-1.

## 2. Edit the `pbr` template (flat material)

`new pbr` makes six `uniform` -> `output` pairs: base colour (node 1), normal (3), roughness (5),
metallic (7), height (9), ambient occlusion (11). Change values with `params`:

```json
{
  "in": "p.sbs",
  "params": [{"node": 1, "param": "color", "value": "#b04a2a"},
             {"node": 5, "param": "color", "value": [0.35, 0.35, 0.35, 1]}],
  "save": "brick_flat.sbs"
}
```

Insert a node on an existing wire by connecting into the occupied input
(`graph.connect` replaces the wire): `[N, "new"], ["new", M]` where M is what N fed. Wire
both `blend` inputs explicitly, as `connectFrom` only reaches the first one.

## 3. Exposed input and variants (one process)

Bindings and presets are **not saved in `.sbs`** in 0.2.0 (gotchas.md), so a variant is made
in a single `batch`: bind, set, export.

```json
{"open": "tint.sbs", "steps": [
  {"id": "graph.select", "params": {"ids": [1]}},
  {"id": "graph.node.bind", "params": {"id": 1, "param": "color", "input": "tint"}},
  {"id": "graph.exposed.set", "params": {"id": "tint", "value": [0.7, 0.02, 0.02, 1]}},
  {"id": "file.export", "params": {"dir": "/abs/red", "format": "png", "depth": 8}}]}
```

`tint` must already exist as an exposed input (`mc_build.py` `exposed` without `bind`, or
`graph.exposed.add`); the exposed input itself is saved. Run `materialcraft-cli batch FILE`.

## 4. Fix a seam

`mc_render.py IN --seam` names the outputs that don't tile. A function that uses `$pos`
tiles when it has a whole number of periods across 0..1. Walk upstream (`mc_inspect.py`
wires) to the generator and fix its frequency, or put a `transformation` / `warp` with
a tileable input before it.

## 5. Raw steps

Anything the spec keys don't cover goes in `steps`; `"@name"` becomes a new node's id:

```json
"steps": [
  {"id": "graph.node.base", "params": {"id": "@px", "seed": 7}},
  {"id": "graph.seed", "params": {"seed": 42}},
  {"id": "graph.attributes", "params": {"author": "Studio", "tags": "stone,tileable"}}
]
```

`mc_build.py` adds the `graph.select` that `graph.node.*`/`edit.*` commands need.
