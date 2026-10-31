# Gotchas (VectorCraft 0.19.0)

## Paint and geometry

- **The default new-art appearance is a white fill with a 1 pt black stroke.** Shapes
  from `shape.*`, `draw_shape` or `path.create` get it unless you set paint. Lines start
  with no fill.
  - Fix it with `"stroke": "none"` in `draw_shape`/`draw_path`, or
    `paint.setStroke {"none": true}` after a `shape.*` (new objects are selected).
  - `set_paint` also changes the default for the next art.
- **Coordinates are document points, y down.** The origin is the top-left of the first
  artboard.
  - `artboard.new` without `x` places the next artboard right of the last, with a
    20 pt gap.
  - `vc_build.py` lays artboards out with its own `spacing` and offsets object x/y by
    the artboard's position.
- **Text `y` is the baseline.** `size` defaults to the current character size (12 pt),
  so always set it. `justify: "center"` centres point type on `x`. For area type, pass
  `area: {width, height, fit: "autoHeight"}`.
- **Fonts:** a missing family is substituted silently. `info.fonts[].status` is `exact`
  only when the font resolved. Check it with `vc_verify.py doc --fonts-ok`, and name
  installed families. `Helvetica` (macOS) and `Source Sans 3` (bundled, the default)
  resolve.
- **Units:** `file.new` takes `units`. Rasters render 1 pt = 1 px at scale 1 (Pixels
  documents are 1 px = 1 pt). For other units, check the exported pixel size rather
  than assuming it.

## Ids and names

- Ids are integers per document. Imported files number layers and groups too, so ids
  can't be guessed. Use `find`/`inspect` or `@name:` refs.
- Ids survive save and reopen of a `.vectorcraft`. An SVG or AI re-import renumbers them.
- An untitled text object's **name is its content**: `find {"name": "ACME"}` stops
  matching once the text changes. Give text an explicit name (`object.setProps
  {"id", "name"}`; `vc_build.py` does this for `"name"`) when later steps need to find
  it.
- `document.find` `name`/`text` are **substring** matches. `vclib` prefers exact name
  matches, and an `@…:` ref fails when more than one object matches. Narrow the ref
  instead of guessing.
- Several documents can be open in a session, and commands act on the **active**
  (last opened or created) one. Use `document.activate {"index"}` to switch.

## Export and save

- PNG/JPG/SVG export the **first artboard** by default. PDF and `.ai` default to all
  artboards (`range`/`artboard` narrow them). EPS covers the art's bounds unless
  `useArtboards`.
- SVG text stays `<text>` unless `outlineText: true` (session export) or
  `--outline-text` (convert). PDF has its own switch, `options.advanced.outlineText`.
- `save_file` with a non-native extension changes the document's own path and format.
  `export` writes a copy and leaves the document as it was. Prefer `export` for
  deliverables, and `save` once for the `.vectorcraft`.
- `convert IN IN` and a plain `save` overwrite the source **without asking**. Only when
  IN was read lossily does `convert` refuse (until `--replace-lossy`).
- Read the `warnings` of every export result. They name a font style drawn in another
  style, an image that couldn't be decoded, and EMF/WMF type or pattern fills written
  as outlines or tiles.
- PNG export leaves areas without art transparent. Add a background shape that fills
  the artboard if the user wants a solid one.
- WebP export is lossless only.

## Sessions

- File access fails closed:
  - A path outside the read or write root is rejected (`automation path rejected`).
  - A root left out grants nothing.
  - Path params of engine commands must be absolute. The session's file tools resolve
    relative paths against the server's working directory, and the scripts absolutize
    `path`/`folder` keys anyway.
- `command_run` errors come back as `isError` with a message (unknown command, missing
  param). Some unknown params are ignored silently, so check the signature with
  `vc_commands.py --id`.
- `command_batch` stops on the first error by default. Its `"$N.id"` refs only work
  inside that one batch, and the index must be digits (`"$0.ids[1]"`, never
  `"$0.ids[x]"`). `run` resolves the same refs across its steps.

## Imports

- `info.warnings` (in `convert`, `importWarnings`) lists what didn't come in: an EPS read
  from its preview, `.ai` editing data skipped in favour of the PDF part, unreadable
  hidden layers, or text drawn as outlines. Surface it to the user every time; it means
  the output can differ from the source.
- A `.ai` holds both a PDF part and editing data. By default VectorCraft reads the
  editing data only when it draws the same as the PDF part. `--editing-data` forces it.
- PDF import gives one artboard per page (`document.open {"pages": "2-3"}` for a
  subset).
