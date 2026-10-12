# Gotchas

Observed on Tiled 1.12.2 and Godot 4.7.2 (macOS). Each one names the script that
handles it, if any.

## Tiled CLI

- **`--evaluate` always exits 0**, after an uncaught exception, a syntax error or a
  failed write alike. The error only appears in the output, localized. `tiled.sh eval`
  wraps the script in try/catch, adds a completion marker and exits 1 when either
  check fails.
- **`--export-map` / `--export-tileset` do exit 1** on a missing input, an unknown
  format or a failed write. An unknown format prints "format not recognized (see
  --export-formats)" in the UI language.
- **The UI language comes from the system locale.** `LANG`/`LC_ALL` don't change it,
  and neither does `LANG=C` (which only adds a Qt warning). The export-format list is
  the one stable piece of output: one name per line, indented by one space.
- **Arguments for `--evaluate` scripts pass through Tiled's option parser.** A bare
  `-` is rejected ("lonely dash"), and an empty string can shift the rest. Use
  `key=value` arguments.
- **No `timeout` on macOS.** The scripts use `perl -e 'alarm N; exec …'`. A Tiled
  killed that way exits 142, which `tiled.sh` reports as 124.
- **Headless runs leave no window and need no display.** Tiled still writes
  `Install.RunCount` and similar keys to `~/Library/Preferences/org.mapeditor.Tiled.plist`;
  that is harmless.
- **"TilesetManager: There are still N tilesets loaded at exit!"** is exit-time
  chatter, not an error.

## JS API headless

- **`tiled.open()` throws** "editor not available". Use `tiled.mapFormat(f).read()`.
- **Tilesets lose their file link** when created or read on their own
  (`fileName` is empty), so a map embeds them. Load the `.tsx` through a stub map
  (scripting-api.md; td-build does this for you).
- **Whole-number floats are written as int**, and there is no API to force float.
  td-build/td-props patch marker strings after saving.
- **`map.resize()` throws on read maps** ("not supported for detached maps"). Build a
  new map and copy the cells.
- **`write()` returns `undefined` on success** and an error string on failure. It
  doesn't throw, so check the return value.
- **`TextFile` needs `commit()`** in WriteOnly mode. `close()` discards the write.
- **`cell.tileset` is undefined.** Use `layer.tileAt(x, y).tileset`.
- **`ObjectGroup.objects` is in drawing order.** Sort by `id` when the order matters.
- **`tiled.filePath(p)` stores `p` as given.** It isn't made relative to the map.

## Files and paths

- **Paths are relative to the file that contains them.** A map copied without its
  `.tsx` and images breaks. `td-verify.py` lists every unresolved reference.
- **Exports also write paths relative to the output.** A `.tmj` exported to `dist/`
  can point at `../../art/tiles.tsx`, and an embedded tileset still points at
  `../../art/tiles.png`. Use `td-export.sh --standalone` for anything shipped.
  td-export warns otherwise.
- **`version="1.10"` vs `"1.11"`:** Tiled writes the lowest format version that can
  hold the map. A custom class property bumps it to 1.11. Both are normal.
- **Rewriting a map normalizes it.** An empty embedded `<grid>` is dropped, attributes
  are reordered, and the layer data encoding is kept. Compare maps semantically
  (td-verify `--json`), not byte by byte.
- **The object class attribute is `type`** in both XML and JSON at format 1.10. A
  reader that looks only for `class` sees no classes.

## Godot (.tscn) export

- **"No .godot project found in the path of …tiles.png"** means the output or a
  tileset image is outside a folder tree containing `project.godot`. Copy the map,
  tilesets and images into the project. td-export catches this first.
- **Objects without a `resPath` string property vanish** from the scene, silently.
  So does every image layer. td-export warns and counts them.
- **Instances are placed at the object's centre**, `x + w/2, y + h/2`, not its
  top-left.
- **The node is the legacy `TileMap`**, one Godot layer per Tiled tile layer. It
  still loads in 4.7. Godot's editor can convert it (select the TileMap ▸ "Extract
  TileMap layers as individual TileMapLayer nodes").
- **Tile layers inside a group layer** are flattened into the same `TileMap` under
  their own name (no group prefix), so two `walls` layers in different groups
  collide. td-godot-check matches by the last name component.
- **Headless Godot prints leak errors at exit** ("resources still in use",
  "RID allocations … leaked"). They are noise; td-godot-check filters them.

## Extensions

- **Only `~/Library/Preferences/Tiled/extensions/` is loaded** by the CLI. A
  project's `extensionsPath` works in the GUI but not for headless `--export-map`.
- **A broken extension fails silently at startup.** Its format just doesn't appear in
  `--export-formats`. Use `td-extension.sh try` to see the error.
- **`extension` is one suffix without the dot.** For `*.rl.txt`, use `"txt"`; the
  output filename carries the rest.
- **Installing changes the user's Tiled setup** for every session and the GUI. Install
  only when asked, say where the file went, and remove eval or test leftovers.
