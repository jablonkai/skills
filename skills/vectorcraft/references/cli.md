# vectorcraft-cli 0.20.0 reference

`vectorcraft-cli` is a universal binary in `~/.local/bin`. It renders headless, with no
window and no GPU. The app (`/Applications/VectorCraft.app`, bundle id
`ai.storyteller.vectorcraft`) is not needed for anything in this skill.

## Subcommands

### `run`: one-shot command chain

```sh
vectorcraft-cli run [--in FILE] [--cmd ID [--params JSON] | --commands FILE|-]... [--export FILE]... [--scale N]
```

- It opens FILE (any readable format) or starts with no document; give
  `--cmd file.new --params '{…}'` first in that case. It runs the commands in order,
  then exports each `--export` path in the format its extension picks.
- `--commands FILE` reads steps from a file, `--commands -` from stdin: a JSON array
  of `{"command": ID, "params": {…}}` (`"id"` works for `"command"`), or one such object
  per line (JSONL). Limits: 64 MiB, 100000 steps. It can sit between `--cmd` steps.
- `"$N.id"` in params refers to step N's result (0-based, counting every `--cmd` and
  `--commands` step), with `--cmd` and `--commands` alike. Errors name the step as `$N`.
  ```sh
  printf '%s\n' \
    '{"command":"file.new","params":{"width":200,"height":200,"units":"Pixels"}}' \
    '{"command":"text.create","params":{"text":"Hi","x":20,"y":100,"size":30}}' \
    '{"command":"object.setProps","params":{"id":"$1.id","name":"Greeting"}}' \
    | vectorcraft-cli run --commands - --export out.svg
  ```
  Refs only reach earlier results. Finding an object by name or text still needs a
  session (`vc_session.py`).
- It prints one JSON line per step: `{"step":"open"|"cmd"|"export", "command", "result"}`.
- `--export` writes the first artboard for rasters and SVG, and every artboard for PDF.
  A `.ait` export is a template of every artboard. For another artboard use
  `--cmd document.export --params '{"path": "/abs/out.png", "artboard": 1, "scale": 2}'`.
- Without `--export`, nothing is written, so it works as a dry run of a command chain.

### `convert`: one file to another format

```sh
vectorcraft-cli convert IN OUT [--scale N] [--artboard I | --range R] [--outline-text]
    [--decimals N] [--replace-lossy] [--editing-data] [--preserve-editing] [--ai-version 7|pdf]
    [--hidden-objects layer|omit|visible] [--transparent-images flatten|omit]
```

| Flag | Meaning |
|---|---|
| `--artboard I` | 0-based artboard (rasters, SVG, PDF) |
| `--range "1-3,5"` | 1-based artboards (PDF pages) |
| `--scale N` | raster scale: 2 → @2x pixels |
| `--outline-text` | SVG: text as paths (no `<text>` left); `.ai` v7: type as outlines |
| `--decimals N` | SVG coordinate precision 1–7 (default 3) |
| `--replace-lossy` | allow OUT == IN even though reading IN dropped things — only with the user's consent |
| `--editing-data` | open a `.ai` from its editing copy even when it draws differently from its PDF part |
| `--preserve-editing` | PDF: embed the native VectorCraft document as an attachment (default: omitted; the app's Save As PDF keeps it). The warnings say when it was written; it is left out for `--artboard`/`--range` without every artboard |
| `--ai-version 7` | legacy AI v7 output (one file per artboard: `OUT-<n>.ai`) |
| `--hidden-objects layer\|omit\|visible` | AI v7 only: hidden objects go on a hidden layer above their layer (default), are dropped, or are written visible |
| `--transparent-images flatten\|omit` | AI v7 only: flatten transparent images with the art under them (default) or drop them |

The defaults:

- A PDF gets every artboard; EPS gets the bounds of the art; other formats get the first
  artboard.
- A `.ait` OUT is a template of every artboard, as `file.saveAsTemplate` writes it. It
  refuses `--artboard`/`--range`.
- Hidden layers and objects are kept (written hidden in SVG/PSD), as are live effects.

It prints `{"bytes", "format", "path", "warnings", "importWarnings"?}`. When IN is not
lossy, `convert IN IN` **silently overwrites** IN.

### `info`: the read-back oracle

`vectorcraft-cli info FILE` prints JSON:

- `artboards`: `[{name, rect: [x, y, w, h]}]` in document units.
- `info`: title, `colorMode` (`rgb`/`cmyk`), `units`, `objects`, created and modified,
  and metadata.
- `kinds`: counts per kind, such as `Layer`, `Group`, `Path`, `Ellipse`, `Type` and
  `Symbol` (an instance). A star or polygon counts as `Path`, and so does SVG-imported
  art. When checking shapes, sum the shape kinds rather than expecting one name.
- `fonts`: `[{family, style, status: exact|substituted…, missing, missingGlyphs, objects}]`.
- `warnings`: the **import warnings**, meaning what didn't come in as it was (for
  example an EPS read from its preview, and why).

It has no layer tree, object names or text. Get those from a session (`find`,
`inspect`, `document.node`) or from `vc_verify.py doc --text/--has-text/--color`.

### `commands`

The whole catalogue as JSON: `[{id, label, menu, params, shortcut?, enabled, disabled_reason?}]`.
`params` is a one-line signature with `→ {result}`. Query it with `vc_commands.py`.

### `mcp`: the session server

```sh
vectorcraft-cli mcp --headless --automation-read-root DIR --automation-write-root DIR
```

- It is an MCP server on stdio. `vclib.Session` speaks its JSON-RPC directly, so no MCP
  client configuration is needed.
- A root left out grants **no** access of that kind. Each flag may be repeated; a path
  inside any of its folders is allowed. Either flag implies `--headless`.
- Paths must be inside a root; anything else is refused. The file tools (`open_file`,
  `save_file`, `export`) resolve relative paths against the server's working directory,
  but path params of `command_run` don't, so keep passing absolute paths (the scripts
  do).
- Without `--headless` it first tries a running app at `127.0.0.1:7979`. Don't do that:
  see [security.md](security.md).

Its tools, as used by the scripts:

| Tool | Use |
|---|---|
| `command_run {id, params}` / `command_batch {steps, atomic}` | any engine command; batch steps may be `draw_shape`/`draw_path` and use `"$N.id"` refs |
| `open_file {path}` | opens as a new active document (several can be open; edits go to the active one) |
| `save_file {path, compress?, version?, preview?}` | `.vectorcraft`, `.vctemplate`, `.pdf`, `.svg`, `.svgz`, `.ai` |
| `export {path, artboard?, range?, scale?, outlineText?, options?, selection?}` | every writable format |
| `draw_shape` / `draw_path` / `add_text` / `set_paint` / `transform` / `pathfinder` / `apply_effect` | convenience tools with paint params |
| `doc_inspect {depth}` | artboards, layer tree (ids, names, kinds, bounds, fill/stroke), current layer, history |
| `render_preview {artboard, max_side}` | inline PNG (the scripts export a PNG file instead) |

### `bench` / `perf`

These are render timing and performance budgets: diagnostics only, and never part of
a job.

## Formats

- **Readable:** .vectorcraft .drawcraft .svg .svgz .pdf .ai .ait .png .jpg .jpeg .gif
  .webp .tif .tiff .bmp .tga .vda .icb .vst .psd .psb .vctemplate .dxf .emf .wmf .eps
  .epsf .ps .af .afdesign .afpub
- **Writable:** .vectorcraft .svg .svgz .pdf .ai .png .jpg .gif .webp .tif .bmp
  .vctemplate .txt .dxf .eps .emf .wmf .tga .psd, plus `.ait` (an Illustrator template)
  from `run --export` and `convert`

Notes on specific formats:

- `.ai` output is PDF-compatible and reopens editable.
- `.vctemplate` opens as a new untitled document.
- WebP export is lossless only.
- `document.export {format}` also takes `png8` (indexed PNG) and `tiff`.
- PDF and `.ai` output is reproducible when `SOURCE_DATE_EPOCH` is set, which helps
  when the outputs are hash-compared.
- `document.formats` (a command) lists each format's options.
- Raster pixel size = artboard size in px × `scale`. A document in Points renders 1 pt
  = 1 px at scale 1.
