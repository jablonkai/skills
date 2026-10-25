# Gotchas (verified on 0.16.0)

Each of these was hit while building the skill. Most fail silently, so a read-back is the
only way to notice them.

## Layer names vs ids

Many commands accept a layer **name** in place of the numeric id, but not all of them
handle it the same way:

| Behaviour with `"layer": "Name"` | Commands |
|---|---|
| Resolves, and errors on an unknown name | `layer.setProps`, `layer.select`, `layer.hideLayers`, `layer.translate`, `layer.layerStyle.*` |
| **Silently ignores the name and edits the active layer** (exit 0), even a correct or unknown one | `type.edit` |
| Refuses names outright | `image.variables.define` ("a def needs `layer`") |

So always pass numeric ids:
- `photocraft-cli run`: `python3 scripts/pc_inspect.py ids FILE Title Badge` gives
  `{"Title": 6, "Badge": 8}`. These ids hold for that file on disk.
- `serve` / `pc_session.py`: write `"layer": "@layer:Title"`. The script resolves it from
  `doc.inspect` right before the step and fails on a missing or duplicate name.
- **Ids change after a save and re-open** (a PSD written with ids 6, 8, 10 reopens as
  6, 7, 8…). Look them up again after every open; never reuse ids from another file or
  an earlier session.

If you must work by name, `layer.select {"name": "Title"}` (0.10.0+; add `occurrence`
for a duplicate name) makes that layer active, so a following `type.edit` without
`layer` hits it. `type.edit` replies with the `layer` it edited; check it.

`layerComp.apply {"comp": "Unknown"}` fails with `no layer comp named …` (0.10.0+). Take
comp names from `info` first anyway.

## Layer comps override visibility edits

A comp records each layer's visibility, position and appearance (layer styles). Applying
it, which `file.export.layerCompsToFiles` does for every comp, **restores the recorded
state**. A layer you hid before exporting reappears in every comp that recorded it as
visible. Text content and pixels are not part of a comp, so text edits carry through.

To make a visibility change stick in the comps: for each comp, `layerComp.apply` it,
make the change, then `layerComp.update {"comp": name, "what": "visibility"}`.
Use `"what": "position"` or `"appearance"` for those kinds of change. See
[recipes.md](recipes.md#template-edit-and-layer-comps).

## Paths and roots

- `serve` rejects every file operation without `--automation-read-root` /
  `--automation-write-root`, and any path containing `..`, even an absolute one.
  `pc_session.py` and `pc_compose.py` set the roots and normalise paths.
- Under `serve`, commands that take raw paths are disabled ("uses ambient filesystem
  paths"). Use `doc.place`, `doc.replaceSmartObject`, `doc.exportLayers`,
  `doc.exportDataSets` and `doc.importDataSets`, or switch to `photocraft-cli run`, which
  is trusted local.
- The output's parent folder must exist (`mkdir -p` first). `doc.exportLayers` refuses
  to overwrite files.
- `run --out`, `convert <out>` and `batch --out` equal to the input are refused unless
  `--in-place` (`run` since 0.16.0, `convert` since 0.13.0). The engine's
  `file.saveACopy` likewise refuses the document's own file without `"overwrite": true`.

## Geometry

- **Bounds come in two shapes.** Command replies (`doc.place`, `type.create`,
  `type.edit`, `shape.create`) give `[x0, y0, x1, y1]`; `info` / `doc.inspect` give
  `[x, y, width, height]`.
- `type.create` `y` is the **baseline**, not the top. The text box's top sits roughly one
  cap height above it. Place text, read its bounds, then `layer.translate` to the target
  (`pc_compose.py` does this for `anchor`).
- `type.create` defaults to 12 pt Inter. Always pass `size` (and `font`/`color`).
- `doc.place` defaults to `fit: true`: an image larger than the canvas is shrunk to fit.
  Pass `fit: false` with an explicit `scale` (percent of its pixel size) when the size
  matters. `center` positions the layer's centre.
- `layer.smartObjects.replaceContents` (and `serve`'s `doc.replaceSmartObject`) keeps
  the old **scale**, not the old frame: a
  1600 px replacement in a slot placed at 40% lands 640 px wide. Refit it with
  `edit.transform {"layer": id, "quad": [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]}`, using a quad
  with the new image's aspect ratio inside the old box. Bicubic edges can add 1–2 px.
- Fill layers report `bounds: null`. A fill created without a selection covers the
  canvas; one created from a selection draws its shape through the **mask**. To measure
  the shape, run `select.loadSelection {"channel": "mask", "layer": id}` and then read
  `selectionBounds` (`[x, y, w, h]`) from `doc.inspect`. `layer.translate` moves the fill
  together with its mask.
- Duplicate layer names make every name lookup ambiguous. Don't name a new layer
  "Background" or reuse an existing name; `pc_compose.py` warns when the result has
  duplicates.

## Values and scales

- `layer.setProps` `opacity` is 0..1; layer-style `opacity` is 0..100. Opacity is stored
  in 8 bits, so 0.35 reads back as 0.349.
- CLI `--quality` and `doc.save` `quality` are 1..100 (`doc.save` rejects anything
  else since 0.12.0). Engine `quality` params
  (`file.saveACopy`, `file.export.*`, droplets, `file.automate.batch`) are **0..12**.
- WebP written with a quality is lossy (VP8); without one it is lossless (VP8L).
  `scripts/pc_verify.py files DIR --webp lossy` checks which one you got.
- `type.edit {"text": …}` replaces the whole text and keeps the existing character
  styles (0.16.0+). Use `replace` or `runs` to restyle part of it.
- `file.export.dataSetsAsFiles` rejects colliding file names before writing anything;
  add `{index}` to `naming` when set names may repeat.
- `layer.hideLayers` toggles: it shows the layers if they are all hidden already. Use
  `layer.setProps {"visible": false}` for an idempotent hide.
- Data-set CSVs: the first column names the sets only when its header is exactly
  `dataSet`. With `name` or `Name` it is treated as a variable, and the sets come out as
  "Data Set 1…" and `Data_Set_1.png…`.

## Process

- Running the app binary (`PhotoCraft.app/Contents/MacOS/PhotoCraft --help`) opens the
  GUI. Use `photocraft-cli <sub> --help` to read flags.
- `pc_live.py stop` (`app.quit`) discards unsaved edits without a prompt. Save first.
- A failing `run` exits 1 and writes nothing. A failing `batch` file is reported per
  file, and the others still run.
- The batch warning `lossy compression` is informational. WebP keeps the resolution
  since 0.16.0, so the old `resolution (DPI) not supported` warning is gone.
- `photocraft-cli batch` does not recurse into subfolders. Use `file.automate.batch`
  with `"includeSubfolders": true` for a tree.
- Export presets (`file.export.presets.save`) live in the process that saved them: a
  later `photocraft-cli run` lists none. Save and use a preset within one `run` or one
  `serve` session.
