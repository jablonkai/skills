# Node library (0.2.0, 30 entries)

0.2.0 removed the old procedural library (222 nodes in 0.1.2: noises, patterns, material filters,
`perlin_noise`, `height_normal_ao`, `edge_wear`, `pbr_base_material`, ...). What is left is a
set of **primitives**: 25 atomic nodes and 5 graph items. Patterns and noises are built from
`pixel_processor` / `fx_map` functions. Don't guess ids, ports or parameter ids; ask the library:

```sh
materialcraft-cli nodes --filter blur                   # any id/label containing the text
materialcraft-cli nodes --category "Atomic nodes"       # or "Graph items"
materialcraft-cli nodes --filter emboss | python3 -c 'import json,sys
for n in json.load(sys.stdin): print(n["id"], [i["id"] for i in n["inputs"]], [o["id"] for o in n["outputs"]], [p["id"] for p in n["params"]])'
```

An unmatched filter prints `[]`. Port kinds: `Gray`, `Color`, `Any`.

## Atomic nodes (25)

| def | inputs | params (default) |
|---|---|---|
| `uniform` | - | `color` (0.5 grey), `color_mode` (true = colour, false = grayscale) |
| `bitmap` | - | `resource` (name from `file.importBitmap`), `colour_space`, `color_mode` |
| `svg` | `background` | `resource`, `color_mode`, `background` |
| `text` | `background` | `text`, `fontsize`, `position`, `matrix`, `alignment`, `fontdata`, `color_mode`, `background` |
| `fx_map` | `background`, `pattern0` | `pattern` (a `patternGraph`, edit with `graph.pattern.set/edit`), `opacity`, `color_mode`, `background` |
| `pixel_processor` | `input0` | `function` (a function graph, `$pos` is the pixel position), `color_mode` |
| `value_processor` | `input0` | `function` (computes one value, no image) |
| `blend` | `foreground`, `background`, `mask` | `mode` (enum), `opacity`, `alpha` |
| `levels` | `input` | `in_low`, `in_mid`, `in_high`, `out_low`, `out_high`: **float4** each |
| `curve` | `input` | `curve` |
| `gradient_map` | `input` (Gray) | `gradient`, `color_mode` |
| `gradient_dynamic` | `input` (Gray), `gradient` | `position`, `orientation` |
| `hsl` | `input` (Color) | `hue`, `saturation`, `lightness` (0.5 = unchanged) |
| `grayscale_conversion` | `input` (Color) | `red`, `green`, `blue`, `alpha`, `flatten_alpha`, `matte` |
| `channels_shuffle` | `input1`, `input2` | `red`, `green`, `blue`, `alpha` (enum sources) |
| `normal` | `input` (Gray) | `intensity`, `opengl`, `height_alpha` |
| `emboss` | `input`, `height` | `intensity`, `light_angle`, `highlight`, `shadow` |
| `blur` / `sharpen` | `input` | `intensity` |
| `directional_blur` / `motion_blur` | `input` | `intensity`, `angle` / `shiftangle` |
| `warp` | `input`, `gradient` | `intensity` |
| `directional_warp` | `input`, `intensity_input` | `intensity`, `angle` |
| `distance` | `mask`, `source` | `distance`, `combine` |
| `transformation` | `input` | `offset`, `matrix` (float4), `filtering`, `matte` |

`levels` params are float4 (`[r, g, b, a]`), so a plain float exposed input cannot be bound to
them (see exposed.md). `normal` and `emboss` set the look of a height map; there is no
ambient-occlusion, curvature or edge-wear node any more.

## Graph items (5)

| def | inputs -> outputs | params |
|---|---|---|
| `output` | `input` -> - | `identifier` (text, the export name), `usage` (enum 0-9: Base color, Normal, Roughness, Metallic, Height, Ambient occlusion, Emissive, Opacity, Specular, Any) |
| `input_color` / `input_grayscale` | - -> `output` | `identifier`, `usage`, `default` (colour); an image can be bound with `graph.input.bind` |
| `input_value` | - -> `output` | `identifier`, `usage`, `default` (float); read it in a function with `get_float1 "<identifier>"` |
| `dot` | `input` -> `output` | none (a reroute) |

## Function graphs (pixel_processor, value_processor)

A function graph is `{"nodes": [{"id", "op", "inputs": [ids], "pos": [x, y], "type_code",
"value"?}], "output": id}`. Set one with `graph.function.set {target: {kind: "parameter",
node: N, parameter: "function"}, function}`. `type_code` is 256 for a float and 512 for a
float2. Ops verified in 0.2.0: `get_float2` (value `"$pos"`, the pixel position in 0..1),
`get_float1` (value = an `input_value` identifier), `swizzle1` (value = component index),
`const_float1`, `mul`, `add`, `sin`. An unknown op fails with `unknown function` and the step
saves nothing. The built-in **Atomic sample** (`new atomics`) shows the format; read its
`pixel_processor` with `mc_inspect.py --params` or `info`.

Every node also has **base** settings (`graph.node.base`): `sizeMode`
(relativeToInput / relativeToParent / absolute), `size` (log2 offset or log2 size),
`format`, `seed`, `tiling`.
