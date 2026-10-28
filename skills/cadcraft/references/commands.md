# Pinned command ids (CADCraft 0.14.0)

Run with `--cmd 'id {json}'`, a `{"cmd": id, "params": …}` session step, or a
`cc_build.py` draw item. Points are `[x, y]` in drawing units, y up; angles in degrees.
Check anything not listed with `scripts/cc_commands.py WORD`. "(i)" = also prompts in
the GUI; still headless-safe with complete params.

## Drawing setup

| id | params |
|---|---|
| `new` | `{metric? (default MEASUREINIT), template?}` (session: prefer the `new` step / `new_drawing` tool) |
| `units` | `{lunits?: 1..5, luprec?: 0..8, aunits?, auprec?, insunits?}` (insunits 4 = mm) |
| `setvar` (i) | `{name, value}` |

## Layers

| id | params |
|---|---|
| `layer.new` | `{name, color?, linetype?, lineweight? (mm), current?}` — error if it exists |
| `layer.set` | `{name, on?, frozen?, locked?, plot?, color?, linetype?, lineweight?, transparency?, description?, newName?}` |
| `layer.current` | `{name}` |
| `layer.delete` | `{name}` (not 0, Defpoints, the current one, or a layer with objects) |
| `laymch` | `{handles?, layer}` — moves the given objects (default: the selection) |
| `laymrg` (i) | `{from: [names], to}` — moves everything and deletes the from-layers |
| `layer` (i) | `{}` → all layers and states |

Colours: names (`Red`, `Yellow`, `Green`, `Cyan`, `Blue`, `Magenta`, `White`) or ACI numbers.

## Draw

| id | params |
|---|---|
| `line` (i) | `{points: [[x,y],…], closed?}` → one LINE per segment |
| `pline` (i) | `{vertices: [[x,y] | {p, bulge, startWidth, endWidth}], closed?, width?}` |
| `rectang` (i) | `{p1, p2 | dimensions: [l, w], rotation?, fillet?, chamfer?: [d1,d2], width?}` → closed LWPOLYLINE (fillet adds bulge vertices) |
| `circle` (i) | `{center, radius}` / `{center, diameter}` / `{p1, p2}` / `{p1, p2, p3}` |
| `arc` (i) | `{center, radius, start, end}` / `{p1, p2, p3}` / `{start, center, end}` |
| `fillet` (i) | `{h1, p1, h2, p2, radius?, trim?}` / `{handle, polyline: true, radius}` |
| `offset` (i) | `{handle, distance, side: [x,y], erase?, layer?}` |
| `hatch` (i) | `{points?: [[x,y]] internal points, handles?: closed objects, pattern?: "ANSI31", scale?, angle?, associative?}` (`SOLID` for fill) |
| `text` (i) | `{at, text, height?, rotation?, justify?: L|C|R|M|TL…BR}` — pass height |
| `mtext` (i) | `{at, text, height?, width?, justify?, …}` (`\P` = new paragraph) |

## Dimensions and annotation

| id | params |
|---|---|
| `dimlinear` (i) | `{p1, p2, at, rotation?, text?}` (horizontal/vertical from `at`) / `{object: handle, at}` (associative to that object) |
| `dimaligned` (i) | `{p1, p2, at, text?}` |
| `dimradius` / `dimdiameter` (i) | `{handle, at?}` (circle/arc only) or `{center, point}`; an `at` outside the circle puts the text there |
| `dimangular` (i) | `{vertex, p1, p2, at}` / `{lines: [h, h], at}` / `{arc: h, at}` |
| `qdim` (i) | `{handles?, at, mode?: continuous|baseline|ordinate|radius|diameter}` |
| `mleader` (i) | `{points: [[arrow], …, [landing]], text?}` |

`%%c` in text = Ø, `%%d` = °, `%%p` = ±. Metric drawings default to dim style `ISO-25`.

## Selection and inspection

| id | params |
|---|---|
| `select` (i) | `{handles}` / `{window, crossing?}` / `{at}` / `{clear: true}`, `add?` |
| `qselect` | `{type?, layer?, color?, property?, operator?, value?, mode?}` → `{handles, selected}` |
| `selectall` | `{}` |
| `entities` | `{type?, layer?, selected?, window?, crossing? (default true), limit?, offset?}` → `{count, entities}` |
| `usage` | `{type?: layers|blocks|textstyles|linetypes|all, limit?, offset?}` → per item `entities`, `references`, `used`/`unused` — read-only, run it before `purge` |
| `drawing.inspect` | `{entities?, limit?}` |
| `find` | `{find, replace?, matchCase?, wholeWord?}` — case-insensitive substring by default |
| `area` (i) | `{handle}` / `{points}` |
| `list` (i), `count` (i), `massprop` | inspection of the selection / handles |
| `properties` / `properties.set` | `{handles?, layer?, color?, linetype?, …, <geometry fields>}` |

## Blocks and attributes

| id | params |
|---|---|
| `attdef` (i) | `{tag, prompt?, default?, at, height?, invisible?}` |
| `block` (i) | `{name, base, handles?, keep?: convert|retain|delete}` — default selection; `convert` inserts one reference; any other `keep` is an error |
| `insert` (i) | `{name, at, scale?, rotation?, attribs?: {TAG: value}, file?, explode?}` |
| `attedit` (i) | `{handle, values: {TAG: value}}` (tags any case) → `{changed, unknownTags?}` |
| `-attedit` (i) | `{find, replace?, block?, tag?, value?, handles?}` — literal find text |
| `battman` (i) / `attsync` (i) | edit definitions / sync references after a definition change |
| `eattext` (i) / `dataextraction` (i) | `{blocks?, tags?, combine?}` → `{columns, rows}` of attribute values |
| `blocks.list` | `{}` |
| `wblock` | `{path, name? | handles?, base?}` |

## Cleanup and output

| id | params |
|---|---|
| `purge` (i) | `{type?: all|blocks|layers|…, names?}` → purged |
| `overkill` (i) | `{handles?, tolerance?}` — removes duplicates |
| `audit` (i) | `{fix?}` |
| `saveas` | `{path, version?: 2000…2018, binary?}` |
| `export` | `{path, format?}` |
| `exportpdf` / `plot` | `{path, layout?, paper?, landscape?, fit?, scale?: "1:50", plotArea?: extents|window|…, window?}` |
| `publish` | `{path: "NAME.pdf", layouts?}` — one PDF per sheet |
| `zoom.extents`, `view.set {center, height}` | affect `--view current` / `run --export` default |
