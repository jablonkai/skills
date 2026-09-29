# Gotchas (Godot 4.7 headless)

Each item below was hit or confirmed on Godot 4.7.2 on macOS.

## Silent failures

- **The exit code is 0 after script errors.** This covers runtime errors, a parse
  error in a script the scene loads, and `--check-only` on a broken script. Judge a
  run by its log (`^(SCRIPT ERROR|ERROR|USER ERROR)`) and by `quit(code)` from a test
  script. Never report "it runs" on the strength of exit 0 alone.
- **A script error aborts the current function but not the process.** A test that
  errors before `quit()` hangs forever. Always pass a timeout (the skill's scripts do)
  and start test scripts with a watchdog timer (see the recipes).
- **`--check-only` without `--script` does not check anything.** It runs the main
  scene with no end. Use `gd-run.sh --check`, which parse-checks every `.gd` file in
  one process.
- **Unknown flags are ignored without a warning.** With `--export-releas` (a typo),
  Godot skips the export and runs the game with no end. Always use a timeout.
- **A run without `--quit-after` or `--quit` never ends** headless, since there is no
  window to close.
- **A `[connection]` to a method that doesn't exist is completely silent.** No error
  is logged at load or at emit, and the signal just does nothing. Only
  `gd-verify.py` (also run by `gd-run.sh`) catches it.
- **A wrong `parent=` path is only a `WARNING`**
  (`Parent path './Bx' for node 'Btn' has vanished`), and the node is dropped.
  `gd-run.sh` counts it as an error.
- **A hand-written `export_presets.cfg` with missing keys** (`include_filter`,
  `exclude_filter`, or an empty options section) logs `Couldn't find the given
  section` errors, and the export may still succeed. Write every key shown in
  [formats.md](formats.md#export_presetscfg).

## Rendering and capture

- **`--headless` renders nothing.** `--write-movie` under `--headless` writes only the
  `.wav`. Frames need a real display driver, and `gd-capture.sh` uses a minimized
  window.
- **Don't pass `--resolution` to a capture.** The docs say that with the `disabled`
  and `canvas_items` stretch modes the window size sets the output size. On 4.7.2
  (macOS, Retina) we observed something else: a 320×180 window gave a 1152×648 frame
  with the content magnified 3.6×. Set `display/window/size/viewport_width/height`
  instead. The frame then comes out at exactly that size.
- A game with no input stays still in a capture. Drive it from user args
  (`-- --demo`, `OS.get_cmdline_user_args()`), as in the recipes.
- `gl_compatibility` is the renderer to use for 2D, Web and fast captures. Web export
  supports no other renderer.

## Scenes and scripts

- **`:=` on an untyped value is a parse error.** `var ok := ui.count == 2` fails with
  *Cannot infer the type of "ok"* when `ui` is typed as `Control`, because `count`
  lives on its script. Use `var ok: bool = …`, or type `ui` as the script's
  `class_name`.
- **Parents before children** in `.tscn`, with `parent` paths relative to the root
  (`"Coins/Coin1"`, not `"Main/Coins/Coin1"`).
- Godot writes `uid="uid://…"` into `ext_resource` lines and `.gd.uid` files next to
  scripts. When you move a script, move its `.uid` too. When you hand-write an
  `ext_resource`, leave the uid out rather than invent one.
- `$Node` / `get_node()` in `_ready()` sees only nodes that already exist. A node you
  add in code after `_ready()` isn't there yet.
- Physics callbacks (`body_entered`) fire in the physics step, so a test has to
  `await physics_frame`. `process_frame` alone may not advance physics.

## Project and import

- **New or changed assets need `--import`** before a headless run can load them.
  `gd-run.sh` imports by default, and `--no-import` skips it when only scripts
  changed.
- **Build output inside the project gets imported.** Godot then imports
  `index.png` and friends from a Web build, and packs them into the next export. Keep
  builds in a folder with a `.gdignore` file (`gd-new.sh` creates `build/.gdignore`,
  and `gd-export.sh` adds one when it's missing).
- **Localized editor output.** The editor's language setting localizes import and
  export messages, e.g. into Hungarian. The skill passes `-l en`, and so should you
  on raw calls.
- **macOS export needs `import_etc2_astc=true`.** Without it:
  *Cannot export … ETC2 ASTC texture format is disabled*. `gd-new.sh` sets it.
- **Export templates are per exact version.** Templates for 4.7.1 do not serve 4.7.2.
  `godot.sh --check` names the folder it expects.
- The exported `.app` is named after `config/name`, not after the output file.

## Scope

- **C#/.NET**: a `Godot_mono` build is detected (`build: .NET`), but C# projects need
  the .NET SDK and `--build-solutions`, and this skill doesn't cover them. GDScript
  works in both builds.
- **Godot 3.x** is rejected by `godot.sh`: `format=2` scenes, `KinematicBody2D`,
  `export var` and `yield` are 3.x syntax, and don't work in 4.x.
