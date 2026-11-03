# Recipes (mc_build.py specs, verified on 0.1.0)

Run each with `python3 $S/mc_build.py spec.json` (add `--dry-run` to see the two batches
first). New nodes are named; existing nodes are integer ids from `mc_inspect.py`.

## 1. A tileable PBR graph from an empty package

Noise → height and normal; a colour ramp for base colour; levels for roughness, exposed.

```json
{
  "template": "empty", "size": 1024, "name": "Sandstone",
  "nodes": {
    "noise":  {"def": "perlin_noise", "params": {"scale": 8}},
    "normal": {"def": "height_to_normal", "params": {"intensity": 2}},
    "ramp":   {"def": "gradient_map", "params": {"gradient": {"t": "gradient", "v": {"keys": [
                 {"pos": 0, "color": [0.20, 0.12, 0.06, 1]}, {"pos": 1, "color": [0.75, 0.60, 0.42, 1]}]}}}},
    "rough":  {"def": "levels", "params": {"out_low": 0.5, "out_high": 0.9}}
  },
  "wires": [["noise", "normal"], ["noise", "ramp"], ["noise", "rough"]],
  "outputs": {
    "basecolor": {"from": "ramp",   "usage": "Base color"},
    "normal":    {"from": "normal", "usage": "Normal"},
    "roughness": {"from": "rough",  "usage": "Roughness"},
    "height":    {"from": "noise",  "usage": "Height"}
  },
  "exposed": [{"id": "roughness", "label": "Roughness", "default": 0.9, "min": 0, "max": 1,
               "bind": {"node": "rough", "param": "out_high"}}],
  "save": "sandstone.mcraft"
}
```

Then: `mc_render.py sandstone.mcraft --seam` (all outputs ≤ 1.5) and
`mc_render.py sandstone.mcraft tile.png --tile 3` (a real 3×3 repeat of the base colour).

Gradient colours are linear 0–1. For an AO output add `{"ao": {"def": "ambient_occlusion"}}`
wired `["noise", "ao"]` (its input is `height`, the first input, so a plain wire works).

## 2. Insert a node into a template (tint the wood)

The `wood` template's base colour is node 12 → output 15. Insert a multiply with a uniform
colour, and expose the colour:

```json
{
  "in": "wood.mcraft",
  "nodes": {
    "tintcol": {"def": "uniform", "params": {"mode": 0, "color": "#ffffff"}},
    "tintmul": {"def": "blend", "params": {"mode": 3}}
  },
  "wires": [["tintcol", "tintmul:foreground"], [12, "tintmul:background"], ["tintmul", 15]],
  "exposed": [
    {"id": "tint", "label": "Tint", "default": "#ffffff", "bind": {"node": "tintcol", "param": "color"}},
    {"id": "roughness", "label": "Roughness", "default": 0.55, "min": 0, "max": 1,
     "bind": {"node": 13, "param": "out_high"}}
  ],
  "presets": [{"name": "walnut", "values": {"tint": "#8a5a3c", "roughness": 0.4}}],
  "save": "wood_tint.mcraft"
}
```

`["tintmul", 15]` replaces the old 12 → 15 wire. Both blend inputs are wired explicitly:
with only `connectFrom`, the colour would go into `foreground` and the multiply would read
an empty background (black, no error).

Find the insert point with `mc_inspect.py`: the output's `source` is the node to tap.

## 3. Weathering on a height map

```json
{
  "in": "rusty.mcraft",
  "nodes": {
    "hna":  {"def": "height_normal_ao"},
    "curv": {"def": "curvature"},
    "wear": {"def": "edge_wear", "params": {"amount": 0.5}},
    "mix":  {"def": "blend", "params": {"mode": 0}},
    "bare": {"def": "uniform", "params": {"color": [0.6, 0.6, 0.62, 1]}}
  },
  "wires": [[5, "hna"], ["hna:normal", "curv"], [5, "wear:height"], ["curv", "wear:curvature"],
            ["bare", "mix:foreground"], [9, "mix:background"], ["wear", "mix:mask"], ["mix", 15]],
  "exposed": [{"id": "wear", "label": "Wear", "default": 0.5, "min": 0, "max": 1,
               "bind": {"node": "wear", "param": "amount"}}],
  "save": "rusty_worn.mcraft"
}
```

Ids 5, 9 and 15 are the `rusty_metal` template's height source, base-colour source and
base-colour output; for another graph read them with `mc_inspect.py`. Multi-output nodes need the port on the source side:
`"hna:normal"`, `"hna:ambient_occlusion"`.

## 4. A whole material from one node

`pbr_base_material` has six outputs; wire each to an output node:

```json
"nodes": {"mat": {"def": "pbr_base_material", "params": {"base_color": "#b04a2a", "roughness": 0.35}}},
"outputs": {"basecolor": {"from": "mat:base_color", "usage": "Base color"},
            "normal": {"from": "mat:normal", "usage": "Normal"},
            "roughness": {"from": "mat:roughness", "usage": "Roughness"}}
```

Two materials blended by a mask: `material_blend` (inputs `base_color_1…height_1`,
`base_color_2…height_2`, `mask`; outputs `base_color, normal, roughness, metallic, height`).

## 5. Fix a seam

`mc_render.py IN --seam` names the outputs that don't tile. Walk upstream (`mc_inspect.py`
wires) to the generator — in 0.1.0 usually `anisotropic_noise` — and either swap it for a
tileable noise or insert `make_it_tile` right after it (`[N, "mit"], ["mit", M]`, where M is
what N fed). Re-run `--seam`.

## 6. Raw steps

Anything the spec keys don't cover goes in `steps`; `"@name"` becomes a new node's id:

```json
"steps": [
  {"id": "graph.node.base", "params": {"id": "@noise", "seed": 7}},
  {"id": "graph.seed", "params": {"seed": 42}},
  {"id": "graph.attributes", "params": {"author": "Studio", "tags": "stone,tileable"}}
]
```

`mc_build.py` adds the `graph.select` that `graph.node.*`/`edit.*` commands need.
