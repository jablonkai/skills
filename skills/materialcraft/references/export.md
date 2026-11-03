# Export (0.1.0)

`export` cooks the graph at its full size and writes **one file per output node**. The
graph size is the map size (`new --size`, `graph.size`); there is no per-export resize except
for `.mcmat` (`size`).

```sh
python3 $S/mc_export.py IN.mcraft maps/ --format png --depth 16 --pattern '$(graph)_$(identifier)'
materialcraft-cli export IN.mcraft maps/ --format exr --depth 32 --set wear=0.8
```

## Formats and depths

| `--format` | depth actually written | notes |
|---|---|---|
| `png` (default) | 8, 16 | colour maps RGBA, grey maps grey |
| `tif` | 8, 16 | `--depth 32` writes 16-bit |
| `exr` | 32 (float) | always 32-bit float RGB, whatever `--depth` says (grey maps too); tiled, RLE |
| `hdr` | 32 (RGBE) | |
| `jpg`, `bmp`, `tga`, `webp` | 8 | `--depth 16` writes 8-bit |

A depth the format can't write is **ignored silently**. `mc_export.py` refuses such a depth
and checks each file's real depth (PNG IHDR, TIFF BitsPerSample, EXR channel pixel type).

## File names

`--pattern` default is `$(graph)_$(identifier)` → `Wood_planks_basecolor.png`. Tokens:

| token | value |
|---|---|
| `$(graph)` | graph name (`Wood_planks`) |
| `$(identifier)` | the output node's `identifier` (`basecolor`, `roughness`, …) |
| `$(usage)` | the output's usage in camelCase (`baseColor`, `ambientOcclusion`) |

Any other token (`$(name)`, `$(size)`, `$(format)`) is **not an error**: it becomes `_name_`
in the file name. Characters such as `|` are replaced by `_`. A pattern without
`$(identifier)` or `$(usage)` makes every output write the same file. `mc_export.py` rejects
unknown tokens and colliding names.

The identifiers come from the output nodes; rename one with
`graph.select` + `graph.node.param {"id": N, "param": "identifier", "value": "albedo"}`.

## Variants

`--set id=value` (repeatable) cooks with those exposed-input values for this export only.
Export each variant to its own folder — `export` overwrites files with the same name.

## `.mcmat` — portable material for TextureCraft

```sh
python3 $S/mc_export.py IN.mcraft maps/ --mcmat oak.mcmat --set wear=0.3 --texturecraft-check
materialcraft-cli run IN.mcraft file.exportMaterial '{"path": "oak.mcmat", "size": 1024, "values": {"wear": 0.3}}'
```

A zip: `material.json` (`format: craft-material`, `version 1`, `name`, `graph`, `size`, `maps
[{usage, file, colorSpace}]`, `parameters [{id, label, default, min, max, value}]`, `inputs`,
`presets`, `source`), `maps/<usage>.png` (one per output usage; base colour sRGB, the rest
linear) and `source.mcraft` (the package, so TextureCraft can re-cook it).

- `values` sets exposed inputs for the cooked maps and records them as each parameter's
  `value`; `size` (power of two) overrides the graph size; `inputs` binds image files to
  graph input nodes (e.g. a mesh map baked in TextureCraft).
- `file.sendToTextureCraft {graph?}` writes the `.mcmat` straight into
  `~/Documents/TextureCraft/library`, where TextureCraft's shelf lists it. That writes into
  the user's library — do it only when asked.

### Opening it in TextureCraft (verified with TextureCraft 0.3.0)

```sh
texturecraft-cli new builtin:sphere t.tcraft
texturecraft-cli run t.tcraft material.load '{"path": "/abs/oak.mcmat"}' -o t2.tcraft   # → {"layer": N}
texturecraft-cli run t2.tcraft layer.list            # a fill layer with fill.link.graph = the graph name
```

`material.load` also takes a `.mcraft` directly. The linked layer keeps the material live:
`material.link.set {id, value}`, `material.link.preset {name}`, `material.link.cook` and
`material.link.saveSource {path}` change and re-cook it inside TextureCraft (see the
`texturecraft` skill). `mc_export.py --texturecraft-check` runs the load into a temporary
project and confirms the linked layer.
