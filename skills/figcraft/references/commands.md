# Pinned command ids (FigCraft 0.14.0)

The registry is the authority: `python3 scripts/fc_commands.py --id <id>` prints the full
params. `*` there marks commands that change the document. Ids below were checked against
0.14.0; if one is rejected, search by word (`fc_commands.py instance`).

## Layers

| Id | Key params |
|---|---|
| `frame.create` | `x, y, width, height, parent?, name?, props?, preset?` (`frame.presets` lists them) |
| `node.create` | `type: rectangle\|ellipse\|polygon\|star\|line\|arrow\|vector\|text\|frame\|section\|component\|slice`, `x, y, width, height, parent?, index?, name?, text?, path?, props?` |
| `node.set` | `ids?` + any property: `name, visible, x, y, width, height, fill, fills, stroke, strokeWeight, cornerRadius, opacity, effects, characters, fontFamily, fontStyle, fontSize, lineHeight, textAlign, textAutoResize, …` |
| `node.get` | `{id}` |
| `image.place` | `path\|data, x, y, width, height, parent?, mode? fill\|fit\|crop\|tile` |
| `edit.delete`, `edit.duplicate` | `{ids?}`; duplicate takes `dx, dy` |
| `object.group`, `object.ungroup` | `{ids?, name?}` |
| `edit.findReplace` | `{find, replace?, layerNames?}` — text across the document |
| `object.batchRename` | `{ids?, find?, regex?, replace?, name?}` with `$n`, `$&` codes |

## Auto layout (props on frames and components)

`layout: horizontal|vertical|grid|null`, `gap`, `crossGap`, `padding` (n or `[t,r,b,l]`),
`mainAlign: min|center|max|spaceBetween`, `crossAlign: min|center|max|baseline`, `wrap`,
children `sizingH`/`sizingV: fixed|hug|fill`, `absolute`. Also `layout.add {ids, direction}`
and `layout.remove`.

## Components

| Id | Key params |
|---|---|
| `node.create {type: "component"}` | a new main component (children via `parent`) |
| `component.create` | `{ids?}` — turn a frame/group (or several layers) into a component |
| `instance.create` | `{component, x?, y?, parent?}` |
| `component.combineVariants` | `{ids}` — wrap mains in a component set |
| `component.addProperty` | `{id?, name, type: boolean\|text\|instanceSwap\|variant\|slot, default?, layer?}` |
| `instance.setProperties` | `{ids?, properties {name: value}}` |
| `instance.swap` | `{ids?, component}` |
| `component.detach` | `{ids?}` |

Override an instance's text with `node.set {ids: [child id], characters}` on the copy's
text layer (find it with `get_node`, or `@name:Login/Label`-style refs).

## Styles and variables

| Id | Key params |
|---|---|
| `style.create` | `{type: paint\|text\|effect\|grid, name, from? (node id), value?}` — `value` for paint is `"#hex"` or a paints list; for text `{fontFamily, fontStyle, fontSize, lineHeight?, letterSpacing?}` |
| `style.apply` | `{ids?, style (id or name), target? fill\|stroke}` |
| `style.list`, `style.update`, `style.delete` | |
| `variable.createCollection`, `variable.create` | `{collection, name, type: color\|number\|string\|boolean, value \| values {mode: v}}` |
| `variable.bind` | `{ids?, field: fill\|stroke\|width\|gap\|cornerRadius\|…, variable}` |

## Pages and document

`page.add {name?}`, `page.list`, `page.select`, `page.rename`, `text.missingFonts`,
`text.loadFont {path}` (a font file for this session only), `file.colorProfile`.

## Export and inspect

| Id | Key params |
|---|---|
| `file.export` | `{ids?, format?, scale? \| size?, path?, bleed?, cropMarks?, bleedMarks?, cmyk?}` |
| `export.add` | `{ids?, setting {size, suffix?, format?}}` — stored export settings |
| `file.exportLayers` | `{ids?, dir?, assets?}` — every layer once per stored export setting |
| `inspect.properties` | `{id?}` — what the Inspect panel shows |
| `inspect.code` | `{id?, language: css\|html\|react\|swiftui\|compose}` |
