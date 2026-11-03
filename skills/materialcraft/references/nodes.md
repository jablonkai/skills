# Node library (0.1.0, 222 nodes)

Don't guess node ids, ports or parameter ids — ask the library:

```sh
materialcraft-cli nodes --filter normal                 # any id/label containing the text
materialcraft-cli nodes --category "Weathering"         # one category
materialcraft-cli nodes --filter edge_wear | python3 -c 'import json,sys
for n in json.load(sys.stdin): print(n["id"], [i["id"] for i in n["inputs"]], [o["id"] for o in n["outputs"]], [p["id"] for p in n["params"]])'
```

Port kinds: `Gray`, `Color`, `Any`. A `Gray` output into a `Color` input is fine; the engine
converts.

## Categories

| Category | Count | Examples |
|---|---|---|
| Texture generators/Noises | 51 | `perlin_noise`, `clouds_1/2/3`, `fractal_sum_base`, `voronoi`, `cells_1…4`, `grunge_map_1…3`, `dirt`, `crackle`, `cracks`, `stones`, `wood_grain`, `marble`, `concrete`, `bark`, `leather`, `anisotropic_noise` (does not tile on X) |
| Texture generators/Patterns | 38 | `brick_generator`, `tile_generator`, `tile_sampler`, `planks`, `hexagons`, `weave`, `basketweave`, `herringbone`, `checker`, `stripes`, `shape`, `splatter`, `scratches_generator` |
| Filters/Adjustments | 25 | `levels`, `histogram_scan`, `auto_levels`, `invert`, `threshold`, `colorize`, `hsl`, `gamma`, `contrast_luminosity`, `replace_color` |
| Atomic nodes | 24 | `blend`, `gradient_map`, `uniform`, `normal`, `warp`, `directional_warp`, `blur`, `transformation`, `bitmap`, `fx_map`, `pixel_processor`, `svg`, `text` |
| Filters/Effects | 20 | `ambient_occlusion`, `curvature`, `bevel`, `edge_detect`, `erosion`, `highpass` |
| Filters/Blending | 10 | `height_blend`, `lerp`, `multiply`, `add`, `subtract`, `maximum`, `minimum`, `switch` |
| Filters/Normal map | 10 | `height_to_normal`, `normal_from_height_hq`, `normal_blend`, `normal_combine`, `normal_invert` |
| Filters/Flood fill | 8 | `flood_fill` + `flood_fill_to_random_grayscale/color/gradient/…` |
| Material filters/Weathering | 7 | `edge_wear`, `dirt_mask`, `dust_mask`, `rust`, `moss`, `leaks`, `edge_damage` |
| Material filters/PBR utilities | 6 | `pbr_base_material`, `height_normal_ao`, `albedo_safe`, `metallic_mask`, `metal_base_color`, `material_color_adjust` |
| Filters/Blurs, /Tiling, /Transforms, /Channels | 16 | `slope_blur`, `make_it_tile`, `tile_random`, `safe_transform`, `mirror`, `rgba_merge`, `rgba_split` |
| Material filters/Blending | 2 | `material_blend`, `material_height_blend` |
| Graph items | 5 | `output`, `input_color`, `input_grayscale`, `graph_instance`, `dot` |

## Core nodes (ports and params, 0.1.0)

| def | inputs → outputs | params |
|---|---|---|
| `output` | `input` → — | `identifier` (text, the export name), `usage` (enum 0–9: Base color, Normal, Roughness, Metallic, Height, Ambient occlusion, Emissive, Opacity, Specular, Any) |
| `perlin_noise` | — → `output` | `scale`, `disorder` |
| `clouds_2`, `fractal_sum_base` | — → `output` | `scale`, `roughness` (+ `octaves`) |
| `uniform` | — → `output` | `color`, `mode` (0 Color, 1 Grayscale) |
| `levels` | `input` → `output` | `in_low`, `in_mid`, `in_high`, `out_low`, `out_high` |
| `histogram_scan` | `input` → `output` | `position`, `contrast`, `invert` |
| `gradient_map` | `input` → `output` | `gradient`, `mode` (0 Color, 1 Grayscale) |
| `colorize` | `input` → `output` | `dark`, `light` |
| `blend` | `foreground`, `background`, `mask` → `output` | `mode` (0 Copy, 1 Add, 2 Subtract, 3 Multiply, 4 Add Sub, 5 Max, 6 Min, 7 Switch, 8 Divide, 9 Overlay, 10 Screen, 11 Soft light, …), `opacity`, `alpha` |
| `lerp` | `input_a`, `input_b`, `mask` → `output` | `position` |
| `height_to_normal` / `normal` | `input` → `output` | `intensity`, `format` |
| `height_normal_ao` | `height` → `normal`, `ambient_occlusion` | `normal_intensity`, `ao_spread`, `ao_depth` |
| `ambient_occlusion` | `height` → `output` | `spread`, `intensity` |
| `curvature` | `normal` → `output` | `intensity` |
| `height_blend` | `top`, `bottom`, `mask` → `height`, `blend_mask` | `offset`, `contrast` |
| `edge_wear` | `height`, `curvature` → `output` | `width`, `amount`, `noise_scale`, `noise_amount`, `contrast` |
| `dirt_mask` | `height`, `ao` → `output` | `spread`, `amount`, `noise_scale`, `noise_amount`, `contrast` |
| `rust` / `leaks` | `mask` → `output` | `amount`, `scale`, `spread`, `pitting`, `contrast` / `length`, `streaks`, … |
| `moss` | `height` → `output` | `style`, `amount`, `scale`, `height_bias`, `contrast` |
| `pbr_base_material` | — → `base_color`, `normal`, `roughness`, `metallic`, `height`, `ambient_occlusion` | `base_color`, `roughness`, `metallic`, `height`, `ao` |
| `material_blend` | `base_color_1…height_1`, `base_color_2…height_2`, `mask` → `base_color`, `normal`, `roughness`, `metallic`, `height` | `opacity` |
| `make_it_tile` | `input` → `output` | `blend` |
| `tile_sampler` | `pattern`, `scale_map` → `output` | `x_amount`, `y_amount`, `scale`, `scale_random`, `offset`, `position_random`, `rotation_random`, `lum_random`, `blend` |
| `bitmap` | — → `output` | `resource` (a name from `file.importBitmap`) |

Every node also has **base** settings (`graph.node.base`): `sizeMode`
(relativeToInput / relativeToParent / absolute), `size` (log2 offset or log2 size),
`format`, `seed`, `tiling`.
