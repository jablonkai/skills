# Gotchas (CADCraft 0.14.0, each reproduced)

## Silent or surprising

- **New drawings are imperial.** `run` without `--metric`, and `new_drawing {}`, follow
  MEASUREINIT — out of the box `$INSUNITS = 1` (inches); a user who set MEASUREINIT in
  the app profile gets mm instead. Pass `--metric` / `{"metric": true}` for mm
  (`$INSUNITS = 4`, dim style ISO-25) rather than relying on the default.
  `cc_build.py` defaults to metric.
- **Default text height depends on the units:** `text`/`attdef` without `height` are 2.5
  in a new metric drawing (readable mm) but 0.2 in an imperial one, and an opened file
  uses its own TEXTSIZE. Pass `height`.
- **Unknown attribute tags are not an error.** `attedit {handle, values}` returns
  `{"changed": 1, "unknownTags": ["NOPE"]}` and exits 0 — check `unknownTags`.
  `cc_titleblock.py fill` fails on a tag no reference carries.
- **`run --export` framing follows the current view** once a command changed it; a
  `ZOOM`/`view.set` in the chain changes the image. Pass `--view`/`--window`.
- **Xrefs resolve beside the host drawing, not the cwd.** A relative xref path stored in
  a drawing (`a/part.dxf`) is looked up next to that drawing; copy the host elsewhere
  without its xref folder and `xref {}` reports `"status": "Not Found"` — `convert` still
  exits 0, the PDF/PNG just lacks that geometry. Stored paths to other computers,
  devices or URLs are not opened (`Unresolved`) unless a file of that name sits beside
  the host. Run `cadcraft-cli run IN --cmd 'xref {}'` on inputs that have xrefs before
  converting. Paths you pass to `xattach` are used as given.
- **Overwriting an input needs `--in-place` since 0.14.0.** `convert IN IN` and `run IN
  --save IN` now exit 2 ("is an input file ... pass --in-place") instead of overwriting.
  A `save` to the opened path inside an MCP session may still overwrite silently
  (not re-tested). The scripts refuse both; never pass `--in-place`.
- **Script `TEXT` swallows the following lines** as more text lines until a blank line; one-line `-LAYER`
  chains derail the rest of the script ([scr-syntax.md](scr-syntax.md)).
- **`-attedit {"find": "*"}` changes nothing** (`changed: 0`); `find` is literal text.
  Use `attedit {handle, values}`.
- **`find` with `total: 0`** is a no-op, not an error — check `total`.
- **Light colours on the PDF:** the PDF is white paper but keeps layer colours, so a
  Cyan/Yellow layer that reads well on the dark PNG is pale in print. Use darker
  colours (Blue, Red, Magenta, 7/White → black) for print layers if legibility matters.

## Errors you will see

| Message | Cause | Fix |
|---|---|---|
| `layer \`X\` already exists` | `layer.new` on an existing name | `layer.set` / `layer.current` |
| `invalid parameters for \`block\`: no objects selected` | no selection | `select {handles}` first |
| `object is not a circle or arc` (dimradius/dimdiameter) | a polyline fillet (bulge) | `{center, point}` |
| `\`handle\`: "XX" is not an object handle` | guessed handle | `query` / `qselect` / an `as` ref |
| `unknown command \`foo\`` | typo or alias not in 0.14.0 | `cc_commands.py foo` |
| `` `keep` must be "convert", "retain" or "delete" `` | other `block` keep value (0.8.0 silently deleted) | one of the three |
| `` `{last}` needs an earlier --cmd in this run to have returned a handle `` | `{last}` before any `--cmd` returned one | reorder, or use `cc_session.py` |
| `--window/--view need an image output` | framing with no `--export` | add `--export` or drop framing |

## Behaviour worth knowing

- `block` with default `keep: "convert"` replaces the objects with **one reference**; an
  additional `insert` makes a second copy. `cc_titleblock.py` uses `keep: "delete"` and
  inserts once with `attribs`.
- `select {window}` takes everything entirely inside the window — in a full drawing
  that includes neighbours. Select by handles you created.
- In one `run`, the selection carries from command to command (`qselect` → `laymch`),
  and `"{last}"` passes the most recent returned handle; any older handle needs a
  session (`cc_session.py`).
- `info` counts block references as `"Block Reference"`; `query_entities` accepts
  `Insert` or `Block Reference`.
- `rectang {fillet}` makes an 8-vertex LWPOLYLINE with bulge ≈ 0.4142 on the corners.
- `line {points}` with n points makes n−1 LINE entities, not a polyline.
