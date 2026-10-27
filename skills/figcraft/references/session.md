# The headless session (figcraft-cli mcp)

`figcraft-cli mcp` is an MCP server over stdio holding one or more open documents.
`scripts/fclib.py`'s `Session` speaks its JSON-RPC directly, so no MCP client has to be
configured; `scripts/fc_session.py` turns a JSON step list into tool calls.

## Tools (0.11.2)

| Tool | Use |
|---|---|
| `open_file {path, variables?}` | `.figcraft`, `.json` (FigCraft or REST), `.fig`, `.svg`, image → active document; result `opened.warnings` = what an import skipped |
| `save_file {path?}` | `.figcraft`; a `.fig` path writes an experimental copy and keeps the document's own path |
| `run_command {command, params}` | any registry command |
| `batch {commands, label?}` | one undo step, `{"$step": n}` refs, all-or-nothing |
| `create_node`, `set_properties` | `node.create` / `node.set` with inspected results |
| `inspect_document {depth?, allPages?, maxBytes?}` | the layer tree, styles, selection, undo history |
| `get_node {id, depth?, offset?}` | one subtree |
| `export {ids?, path?, format?, scale?\|size?, bleed?, cropMarks?, bleedMarks?, cmyk?, svgOutlineText?, svgIdAttribute?, contentsOnly?}` | several ids are composited into one image |
| `screenshot {ids?, maxSize?, scale?}` | PNG image content of layers or the page |
| `select`, `undo`, `redo`, `pointer`, `key`, `type_text`, `inspect_ui`, `list_commands` | interactive-style control; rarely needed headless |

## fc_session.py refs

Strings in params are replaced before the call:

- `"@name:Title"` — the one layer named Title (any page).
- `"@name:Home/Headline"` — Headline under the top-level frame Home (used only when no
  layer is literally named `Home/Headline`).
- `"@text:Sign in"` — the one text layer whose characters contain "Sign in".
- `"@type:COMPONENT"` — the one layer of that type.

Zero or several matches stop the run with the candidates listed. Use a `find` step first
when unsure. Relative paths are made absolute against the **current directory**, so run
the script from the folder that holds the files (or pass absolute paths); the `--root`
only confines access.

## Inspect fields

Each layer: `id, name, type (FRAME, TEXT, RECTANGLE, COMPONENT, COMPONENT_SET, INSTANCE,
GROUP, VECTOR, …), x, y (relative to the parent frame), width, height, absoluteBounds,
fills, strokes, effects, cornerRadius, clip, layout {mode, gap, padding, mainAlign,
crossAlign, …}, sizing {horizontal, vertical}, children`. Text adds `characters,
fontFamily, fontStyle, fontSize, lineHeight, letterSpacing, textAlign, textAutoResize,
textStyleRanges`. Instances add `mainComponent` (the main's id). Applied styles appear
under `styles {fill, stroke, text, effect, grid}` as style ids (`S:1`); the document's
`styles` list maps ids to names. Large documents come back shallower with a `truncated`
object — read subtrees with `get_node`.
