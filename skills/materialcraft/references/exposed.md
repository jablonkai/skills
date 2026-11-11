# Exposed inputs, presets and variants (0.4.0)

An **exposed input** is a graph-level parameter (the sliders a user of the material sees).
It does nothing until it is **bound** to one or more node parameters. Presets store named
sets of exposed-input values. Templates ship with no exposed inputs; add them.

> **Limitation since 0.2.0 (still in 0.4.0):** the `.sbs` save keeps the exposed inputs but drops **bindings and
> presets**. After a reload nothing is bound, so `--set`, `mc_render.py --variants` and
> `mc_export.py --set` change nothing, and `mc_build.py` reports `bind ...` / `preset ...` as
> failed read-backs. Everything below works **inside one process**: do the bind, `exposed.set`
> and `file.export` in one `batch` (recipes.md §3). 0.1.2 saved both.

## Adding and binding

```json
{"id": "graph.exposed.add", "params": {"id": "wear", "label": "Wear", "default": 0.4,
  "min": 0, "max": 1, "group": "Weathering", "bind": {"node": 2, "param": "position"}}}
```

- `default` is a number or a typed value. Colours must be typed and **linear**:
  `{"t": "color", "v": [1, 0.5, 0.2, 1]}` — `"#rrggbb"` is rejected (`invalid default`; `bad default` before 0.4.0).
  `mc_build.py` accepts hex and converts it (sRGB → linear, as the engine does for `--set`).
- `bind` takes one `{node, param}`. To drive more parameters from the same input, add
  `graph.node.bind {id, param, input}` per extra parameter (after `graph.select`, see
  gotchas). In `mc_build.py`, `bind` may be a list.
- Match the types: a float input on a float/int param, a colour input on a `color` param, and a
  float4 input (typed default `{"t": "float4", "v": [..]}`) on a float4 param such as
  `levels.out_high`. A float input on a float4 param cooks with `has the wrong type for get_float4`.
  A float default bound to an enum is rejected (`bad default`), and a colour bound to a
  `gradient` is accepted without doing anything useful. To tint a gradient-mapped colour, put
  a `uniform` + `blend` (multiply) after the gradient map (recipes.md §2).
- `graph.node.function {id, param, function?: {nodes, output}}` drives a parameter with a
  function graph of the inputs (without `function`: a constant of the current value). Its
  node format is the one `graph.function.set` takes (nodes.md); to invert or remap an input,
  bind it plainly and put a `levels` or `curve` node in the graph instead.

The current values live in the graph's `inputs` (`{"wear": {"t": "float", "v": 0.4}}`)
and are saved with the package; `exposed[].default` is only the default.

Read back: `mc_inspect.py` lists each exposed input with `bound_to: ["2.position"]` and warns
when an input is bound to nothing. In raw `info` JSON the binding sits on the node:
`"bindings": {"position": "wear"}`.

## Presets

```json
{"id": "graph.exposed.set", "params": {"id": "wear", "value": 0.9}},
{"id": "graph.preset.save", "params": {"name": "heavy"}}
```

`graph.preset.save` stores the **current** values of all exposed inputs, replacing a preset
of the same name. Set the values first, save, then set them back to the defaults if the
package should open on its defaults — `mc_build.py` `presets` does exactly this.
`graph.preset.apply {name}` loads one; presets travel into the `.mcmat` and TextureCraft can
apply them (`material.link.preset`).

## Variants without editing the package

`--set id=value` on `cook`, `export` and `render` applies values for that run only:

```sh
materialcraft-cli render rusty.sbs v_lo.png --scene sphere --set wear=0.1
materialcraft-cli export rusty.sbs maps_hi --set wear=0.9 --set 'tint="#aa7744"'
python3 $S/mc_render.py rusty.sbs v.png --scene sphere --variants wear=0.1,0.5,0.9
```

`--set` values are JSON (`0.4`, `[1,0,0,1]`). An unknown id is an error (exit 1). Hex colours
were accepted in 0.1.2; in 0.4.0 an exposed colour is a float4 and hex fails with `takes a float4`. `mc_render.py --variants` writes `v_wear-0.1.png`, … and
fails when two variants look the same — the input is bound to nothing visible.

There is no `--preset` flag on `render`/`export`: to render a preset, pass its values as
`--set`s (read them from `mc_inspect.py` `presets`), or `run IN graph.preset.apply
'{"name": "heavy"}' -o tmp.sbs` and render that copy (the applied values are saved in
its `inputs`).
