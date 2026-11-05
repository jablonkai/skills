# Command registry (0.1.2, 68 commands)

Look up the live list rather than trusting this page after an update:

```sh
materialcraft-cli commands --filter exposed     # id, label, params signature
```

Signatures: `key?` is optional; anything **not** in the signature is ignored without an
error. Commands marked ◆ refuse to run when nothing is selected — even with `id`/`ids` —
so run `graph.select {"ids": [N]}` first (the `id` given is then honoured).

## file

| id | params |
|---|---|
| `file.new` | `{name?, template?, size?}` adds a graph to the package and opens it |
| `file.newPackage` | `{name?}` replaces the session with an empty package |
| `file.open` / `file.save` / `file.saveAs` | `{path}` / `{path?}` / `{path}` |
| `file.export` | `{dir, format?, pattern?, depth?, graph?}` — same as the `export` subcommand |
| `file.exportMaterial` | `{path, graph?, size?, values? {input: value}, inputs? {identifier: image path}}` → `.mcmat` |
| `file.sendToTextureCraft` | `{graph?}` writes the `.mcmat` into `~/Documents/TextureCraft/library` (TextureCraft's shelf) |
| `file.importBitmap` | `{path, name?}` embeds an image as a package resource |
| `graph.templates` | `{}` the template ids for `file.new` |

## graph (package and graph level)

`graph.open {graph: index|name}`, `graph.rename {name, graph?}`, `graph.delete {graph?}`,
`graph.duplicate {graph?}`, `graph.size {width, height}` (powers of two 16–8192) or
`{log2: [w, h]}`, `graph.seed {seed}`, `graph.format {format: u8|u16|f16|f32}`,
`graph.cook {full?}`, `graph.attributes {category?, description?, author?, tags?}`,
`graph.createFromSelection {name?, ids?}`.

Inputs and presets: `graph.exposed.add {id, label?, default, min?, max?, group?, bind?: {node, param}}`,
`graph.exposed.set {id, value}`, `graph.exposed.delete {id}`, `graph.preset.save {name}`
(stores the current values), `graph.preset.apply {name}`, `graph.preset.delete {name}`,
`graph.input.bind {identifier, resource? | path?}` / `graph.input.unbind {identifier}`
(images on `input_color`/`input_grayscale` nodes, e.g. a baked mesh map).

## graph.node and wiring

| id | params |
|---|---|
| `graph.node.add` | `{def, at? [x,y], params? {id: value}, connectFrom? {node, port?}, label?}` → `{id}`. `connectFrom` wires into the **first** input. |
| `graph.connect` | `{from, fromPort? (default output), to, toPort? (default first input)}` — replaces an existing wire into that input |
| `graph.disconnect` | `{to, toPort}` |
| ◆ `graph.node.param` | `{id?, param, value}` |
| ◆ `graph.node.reset` | `{id?, param?}` |
| ◆ `graph.node.base` | `{id?, sizeMode?, size?, format?, seed?, tiling?}` |
| ◆ `graph.node.bind` | `{id?, param, input}` (`input: null` unbinds) |
| ◆ `graph.node.function` | `{id?, param, function? {nodes, output}, remove?}` |
| ◆ `graph.node.rename` / `graph.node.move` / `graph.node.disable` | `{id?, label}` / `{ids?, by?, to?}` / `{ids?, disabled?}` |
| `graph.select` | `{ids, add?}` |
| `graph.selectUpstream` / `graph.selectDownstream` | `{ids?}` |
| `graph.align` | `{mode, ids?}` |
| `graph.frame.*`, `graph.comment.*`, `graph.pin.*` | layout annotations |

## edit, view, library, session

◆ `edit.delete {ids?}`, ◆ `edit.deleteRelink {ids?}` (joins what fed the first input to what
it fed), ◆ `edit.copy/cut/duplicate {ids?}`, `edit.paste {at?, clip?}`, `edit.undo`,
`edit.redo`, `edit.selectAll`, `edit.selectNone`.

`view.2d {node?, port?, tiled?, channel?, histogram?}`, `view.3d {scene?, tiling?, yaw?, pitch?,
distance?, environment?, …}`, `view.3d.loadMesh {path}`, `view.3d.reset`, `view.previewSize
{size}` — these change the app's views; headless, use `render` instead.

`library.list {filter?, category?}` (= `nodes`), `session.inspect {graph?}` (= `info` for any
graph).
