# Pinned command ids (VectorCraft 0.20.0)

Look up anything not listed here with `python3 scripts/vc_commands.py WORD…`
(`--id ID` prints the full signature). Lengths are document units, coordinates are
document points (y down), and ids are integers from `find`/`inspect`/a command result.

## Document and artboards

| Id | Key params |
|---|---|
| `file.new` | `{width, height, units: "Pixels"…, artboards: n, artboardLayout, name, preset}` |
| `file.documentColorMode` | `{mode: "cmyk"\|"rgb", convert?}` |
| `artboard.new` | `{x?, y?, width?, height?, name?}` (default: right of the last) |
| `artboard.setProps` | `{index, name?, x?, y?, width?, height?}` |
| `artboard.fitToArt` / `artboard.rearrange` / `artboard.delete` | `{index}` / `{layout, columns, spacing}` / `{index}` |
| `document.find` | `{name?, kind?: "Type"\|"Path"\|"Group"\|"Image"…, text?, within?/intersects?: [x, y, w, h], min/max Width\|Height\|Area\|Anchors?, select?, limit? (100; 0 counts only)}` → `{matches: [{id, kind, name, path}], total}`. Give at least one filter. |
| `document.node` | `{id, summary: true}` → bounds, fill, stroke, `text` for type, `visible` |
| `document.inspect` | `{depth?}` layer tree (`doc_inspect` tool in a session) |
| `document.export` | `{path, format?, artboard?, range?, scale?, …}` |
| `document.exportForScreens` | `{folder, artboards?, formats?, …}` multi-size batch (`document.exportPresets.list`) |
| `document.exportPdf` | `{path, preset?, artboards?, standard?: pdfX1a…}` |

## Drawing

| Id | Key params |
|---|---|
| `shape.rectangle` / `shape.ellipse` | `{x, y, width, height, radius?, rotation?}` → `{id}` |
| `shape.polygon` / `shape.star` | `{cx, cy, radius, sides}` / `{cx, cy, radius1, radius2, points}` |
| `shape.line` | `{x1, y1, x2, y2}` |
| `path.create` | `{anchors: [{x, y, in?, out?}], closed?}` or `{d: "M…"}` |
| `text.create` | `{x, y (baseline), text, size?, font?, style?, color?, justify?, area?: {width, height, fit}}` |
| `paint.setFill` / `paint.setStroke` | `{color?: "#rrggbb", none?: true, swatch?: name, gradient?}` on the selection |
| `stroke.set` | weight, dash, cap, join (see `--id stroke.set`) |
| `object.setProps` | `{id\|ids, name?, visible?, locked?, opacity?, blend?}` |
| `select.set` / `select.all` / `select.none` | `{ids}` |

The session tools `draw_shape` / `draw_path` take paint inline: `fill`, `stroke`,
`strokeWidth`, `name`, `opacity`, `effects`. They also return the id directly.

## Text

| Id | Key params |
|---|---|
| `text.setText` | `{id\|ids, text}`. It keeps the first run's style and returns `overflow` for area type that no longer fits. |
| `text.setStyle` / `charStyle.*` / `paraStyle.*` | font, size, tracking, `justify`: `--prefix text.` |
| `type.createOutlines` | `{}` on the selected text → compound paths |

## Colour

| Id | Key params |
|---|---|
| `swatch.new` | `{name, color, global?, spot?, group?}` |
| `swatch.edit` | `{name, color?, newName?}`: a global swatch recolours everything linked to it |
| `swatch.list` | `{}` |
| `swatch.addUsedColors` | `{global?: true}`: turns the colours in use into (global) swatches |
| `recolor.colors` | `{}` → the unique colours of the selection (`select.all` first) |
| `recolor.apply` | `{map: {"#from": "#to"}}` on the selection, fills and strokes |

## Layers, symbols, styles

| Id | Key params |
|---|---|
| `layer.new` | `{name, top?}` → `{id}` |
| `layer.setProps` | `{id, name?, visible?, locked?}` |
| `layer.setCurrent` | `{id}`: new art goes there |
| `symbol.new` | `{name, ids}` |
| `symbol.place` | `{name, x, y}` |
| `symbol.list` | `{}` |
| `graphicStyle.new` | `{name, id}` |
| `graphicStyle.apply` | `{name, ids}` |

## Variables and data sets

| Id | Key params |
|---|---|
| `variable.define` | `{name, kind: text\|visibility\|image\|graph}` |
| `variable.bind` | `{variable, ids}` |
| `variable.list` | `{}` |
| `dataset.import` | `{csv \| path \| data \| dataBase64}`. Header: `name`, then the variable names. An unknown header defines an unbound variable: `#Name` visibility, `@Name` image, otherwise text. A row whose name exists is replaced. Visibility values are `true`/`false`. → `{imported, updated, names, defined}` |
| `dataset.select` | `{name}`: applies a row → `{applied, skipped, overflow?, warning?}`. `warning` means no bound object took a value, so nothing changed. |
| `variable.loadLibrary` | `{path \| xml \| dataBase64}`: replaces the variables and data sets with an Illustrator variable library's (text variables only, the rest named in `skipped`) |
| `dataset.list` | `{}` |
| `dataset.export` | `{path?}` |

Data sets are saved inside `.vectorcraft` and `.vctemplate`.
