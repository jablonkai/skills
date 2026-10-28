---
name: tiled
description: 'Author, edit, validate and export Tiled maps headless from the CLI — build .tmx/.tmj maps and .tsx tilesets from a JSON spec through Tiled''s own JS API (ASCII tile rows, objects, typed and object-reference properties), bulk-set properties on objects by class or name, validate and debug maps (gid out of range, missing tilesets), and export to JSON, Lua, CSV, GameMaker or Godot 4 .tscn with a headless Godot import check, plus custom export formats as Tiled extensions. Use whenever the user wants a tilemap or level made, changed or converted in Tiled, says Tiled, .tmx, .tmj, .tsx, tilemap or level editor, wants a level exported for Godot, LÖVE, Phaser or the web, needs properties added across many map objects, or wants a Tiled extension or custom map format. Not for Godot work without a Tiled map (use godot); painting the tile art itself (krita, gimp); geographic maps (qgis); diagrams or floor plans (drawio); 3D levels (blender); LDtk, Unity or other level editors.'
summary: "author, edit and export Tiled maps headless — maps and tilesets from a JSON spec via Tiled's JS API, bulk typed object properties, TMX/TMJ/TSX validation, JSON/Lua/Godot .tscn export with a Godot import check, and custom export formats as extensions"
category: game-dev
compatibility: "Built for Tiled 1.12.2, with Godot 4.7.2 for the import check, on macOS."
risk: low
tags:
    - tiled
    - tilemap
    - tmx
    - level-editor
    - godot
    - gamedev
metadata:
  version: "1.0.2"
  author: "Tamás Jablonkai"
---

# Tiled Control

Drive [Tiled](https://www.mapeditor.org/) **headless**:
- Maps and tilesets are built and edited by running JavaScript against Tiled's own
  scripting API (`Tiled --evaluate`), so Tiled writes every file itself and
  serialization details such as GIDs, encodings and ids are always right.
- Exports go through Tiled's CLI (`--export-map`, `--export-tileset`).
- No GUI, no bridge, no network listener: one short-lived Tiled process per step.
- Verified on **Tiled 1.12.2** and **Godot 4.7.2**, macOS.

`B=<this skill>/scripts`. Call each script as `bash "$B/<script>" …` (`python3` for
the `.py` one); run any of them with `-h` for its options.

| Script | Does |
|---|---|
| `tiled.sh --check` | Tiled path, version, export formats, extensions folder. Exit 2: not installed (`brew install --cask tiled`). |
| `td-build.sh spec.json` | JSON spec → `.tmx`/`.tmj` (plus `.tsx` and placeholder tile art if asked), then validates it. |
| `td-props.sh map.tmx rules.json [--dry-run] [--out f]` | Set or remove typed properties on objects matched by class, name glob, layer or existing property; lists every change. |
| `td-verify.py map.tmx [--ascii] [--json]` | Validates without Tiled and summarises layers, tiles used and objects by class. `--ascii` draws tile layers as text. |
| `td-export.sh in.tmx out.ext [--format F] [--standalone]` | Export via Tiled's CLI; format from the extension. `--standalone` makes the output folder self-contained. `.tscn` gets a Godot preflight. |
| `td-godot-check.sh GODOT_DIR res://x.tscn --map in.tmx` | Imports in headless Godot, instantiates the scene, compares cells and instances with the map. |
| `td-extension.sh try\|install\|list\|remove` | Run a custom-format extension once without installing it, or install it into Tiled. |
| `tiled.sh eval script.js args…` | Run your own script with the full JS API, failing properly on exceptions. |

## Workflow

1. `tiled.sh --check`. For an existing map, run `td-verify.py map.tmx --ascii` first.
   It shows the size, tilesets, layers, tile ids and object classes you'll be
   working with.
2. **New map:** write a spec (format in [references/spec.md](references/spec.md)) and
   run `td-build.sh`.
   - Tile layers are ASCII `rows` plus a `legend` mapping each character to
     `tileset:id`.
   - For anything procedural (a dungeon layout, noise, mazes), generate the rows
     with a short Python script, then feed them into the spec. Don't type 30 rows of
     40 characters by hand.
   - Without tile art, a tileset can `generate` flat-colour placeholder tiles.
3. **Bulk property edits:** `td-props.sh` with a rules file.
   - Run `--dry-run` first and check the matched counts.
   - Rules apply in order, so put the general rule first and the exceptions after it.
4. **Anything else** (moving tiles, renaming layers, wang/terrain sets, templates):
   write a small script and run it with `tiled.sh eval`. Use
   [references/scripting-api.md](references/scripting-api.md) for the headless-safe
   API and the read → modify → write pattern.
5. **Check the result:** `td-verify.py --ascii`. Then look at the layout and confirm
   it is what was asked: room count, connectivity, object placement. A valid file can
   still be the wrong level.
6. **Export:** `td-export.sh`. For Godot, follow the next section.

## Godot 4 export (.tscn)

Tiled's built-in `tscn` exporter writes a scene with a `TileMap` node (one Godot
layer per tile layer) and an embedded TileSet. It has three hard rules. The first
two make it fail; the third makes it drop data silently:
- **The `.tscn` must be written inside the Godot project.** The exporter looks for
  `project.godot` above the output file.
- **Every tileset image must be inside that same project.** If the map lives
  elsewhere, copy the map, its `.tsx` and its images into the project (for example
  `res://tiled/`), keeping their relative layout, and export from that copy.
- **Objects are exported only if they have a string property `resPath`**
  (`res://enemy.tscn`). They become instances of that scene, placed at the object's
  **centre**. Every other object, and every image layer, is dropped without a
  warning. Add `resPath` with `td-props.sh`.

`td-export.sh` checks all three before calling Tiled. Then run
`td-godot-check.sh GODOT_DIR res://levels/x.tscn --map the-exported.tmx`. It must
print `PASS`, which means:
- the import is clean;
- each tile layer's cell count equals its tile count in the map;
- one instance exists per `resPath` object.

Other details:
- Layer options are set as custom properties: `noExport`, `zIndex`, `ySortEnabled`
  and `tilesetOnly` on layers, and `tilesetResPath` on the map to write the TileSet
  to a shared `.tres`. Tile custom properties become TileSet custom data layers.
- `TileMap` is deprecated in Godot 4.3+ but still loads. If the user wants
  `TileMapLayer` nodes, tell them to use Godot's built-in converter (TileMap ▸
  "Extract TileMap layers").

## Other exports and formats

- `json` (`.tmj`) is the format for web engines (Phaser, Excalibur, PixiJS) and the
  most portable choice. `lua` is for LÖVE/Corona (STI reads it). `csv` writes one
  file per tile layer. `gmx` and `yy` are GameMaker.
- **Anything that gets deployed or copied elsewhere:** pass `--standalone`
  (json/lua/tmx). It embeds tilesets, detaches templates, copies every referenced
  image into `images/` next to the output, and rewrites the paths. JSON layer data
  becomes plain arrays, because Phaser skips compressed layers. A plain export
  keeps `../../` paths back to the source tilesets and images, and those break as
  soon as the folder moves.
- `--embed-tilesets` alone inlines external tilesets, which Phaser needs, but it
  keeps the image paths relative to the source.
- `--resolve-types-and-properties` bakes project class defaults into the output.
  Pass it when the target engine doesn't know Tiled projects.
- [references/formats.md](references/formats.md) covers TMX/TMJ structure, GID flip
  bits, property encoding and each exporter's quirks.

## Custom export formats (extensions)

Start from [assets/map-format-template.js](assets/map-format-template.js):
`tiled.registerMapFormat(shortName, {name, extension, write})`.
1. `td-extension.sh try my-format.js map.tmx out.ext` runs it once without
   installing. Iterate until the output is right.
2. Install only when the user wants the format available in Tiled itself:
   `td-extension.sh install my-format.js`. It copies the file to
   `~/Library/Preferences/Tiled/extensions/` and confirms that Tiled lists the
   format.
3. After that, both `td-export.sh map.tmx out.ext --format shortName` and the GUI's
   Export As can use it.

The headless CLI ignores a project's `extensionsPath`. Tell the user what you
installed and how to remove it (`td-extension.sh remove`).

## What Tiled won't tell you

The scripts handle all of these; keep them in mind when calling `Tiled` directly.
- **`--evaluate` exits 0 even when the script throws or doesn't parse.** Use
  `tiled.sh eval`, which wraps the script and exits 1 on any exception.
  `--export-map` does exit 1 on failure.
- **Tiled's messages follow the UI language** (often not English), and `LANG`
  doesn't change it. Never grep Tiled's own text; print your own markers with
  `tiled.log`.
- **`tiled.open()` doesn't work headless** ("editor not available"). Read files with
  `tiled.mapFormat("tmx").read(path)` and write them with `.write(map, path)`.
- **A tileset read on its own gets embedded** into any map it's added to. To keep a
  `.tsx` external, load it through a map that references it (`td-build.sh` does this
  for you).
- **Whole-number floats become ints** through the JS API (`2.0` → `type="int"`).
  `td-build`/`td-props` patch `{"type": "float"}` values after saving; raw scripts
  need the same fix (see scripting-api.md).
- **Tiled's argument parser eats `-` and empty arguments** meant for
  `scriptArguments`. Pass `key=value` arguments instead.

More in [references/gotchas.md](references/gotchas.md).

## Before you report success

- `td-verify.py` is clean, and you checked the `--ascii` view against the request.
- Every export exited 0 and its file exists. For Godot, `td-godot-check.sh` printed
  `PASS`.
- When asked for an exact format (an extension's output), you compared it with the
  spec line by line.

Report:
- the Tiled (and Godot) version, and what each check showed;
- anything left unverified, for example that the level was never opened in the
  game itself.

Work on copies, or on the files the user named. Never overwrite a map that is open
with unsaved changes in the Tiled GUI.

## References (read only the part you need)

- [spec.md](references/spec.md): the `td-build` spec and the `td-props` rules format,
  with every field. Read it before writing a spec.
- [scripting-api.md](references/scripting-api.md): the JS API subset verified
  headless, with patterns for your own `tiled.sh eval` scripts.
- [formats.md](references/formats.md): TMX/TMJ/TSX structure, GIDs and flip flags,
  properties, and the exporters (json, lua, tscn, csv).
- [recipes.md](references/recipes.md): a tested procedural dungeon, a Godot handoff,
  and a custom export format, end to end.
- [gotchas.md](references/gotchas.md): the longer list. Read it when something
  behaves unexpectedly.
