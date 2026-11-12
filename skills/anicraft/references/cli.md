# anicraft-cli 0.2.1

| Subcommand | Does |
|---|---|
| `new --out F [--width W] [--height H] [--fps F]` | empty document (default 1280×720; 1 frame, one `Layer 1`) |
| `info F` | JSON: stage, scenes, layers → keyframes (0-based `start`, `duration`, element **count**, `tween` name, `motion` props, `script`, `sound`), library symbols, selection, history |
| `exec F CMD ['{json}'] [--save OUT]` | one command; prints its result. Without `--save` nothing is written |
| `run F script.json [--save OUT]` | a list of `{"cmd","params"}`; stops at the first error. Results can't feed later steps |
| `serve F` | JSON lines: `{"id","cmd","params"}` in → `{"id","ok","result"|"error","frame","revision"}` out. Keeps going after an error. First line is `{"ready":true,"version":…}` |
| `mcp [F]` | Model Context Protocol server on stdio (not used by this skill) |
| `render F --out f.png [--frame N] [--scale S]` | one frame, **1-based** |
| `render-seq F --out-dir D [--from A] [--to B] [--scale S]` | `frame_00001.png`…, 1-based |
| `gif F --out a.gif [--from A] [--to B] [--scale S] [--overwrite yes]` | quick GIF, 1-based |
| `commands` | registry JSON: `id, label, menu, mutates, params, shortcut` (use `ac_commands.py`) |
| `bench [--check yes]` | performance probe |
| `--plugins DIR` / `ANICRAFT_PLUGINS` | load WebAssembly plug-ins; **off by default** so headless runs are repeatable |

`F` can be `--sample` (the demo) for experiments — never by accident: a missing path is
an error, but forgetting `F` in a script that substitutes it would silently use nothing.

## Frame bases

| Where | Base |
|---|---|
| `render --frame`, `render-seq/gif --from/--to`, PNG sequence file names, sprite-sheet frame names | 1 |
| command params `frame` (all groups), `file.export_* from/to`, `timeline.move_keyframes from/to` | 0 |
| `info`/`doc.info` `start`, `frame`; `motion.info` keys; `actions.list` `frame`; `test_movie` `state.frame`; the file | 0 |
| `ac_build.py` specs, `ac_inspect.py` and `ac_verify.py` | 1 (converted) |

`timeline.insert_frame {frame: 29}` extends a 1-frame layer to 30 frames; on a layer that
already reaches index 29 it inserts one more frame instead.

## Results worth knowing

- `draw.*` → `{element, kind}`; the shape is selected.
- `modify.convert_to_symbol` → `{symbol, instance, layer, name, folder}`.
- `layer.new` → `{layer}`; `file.import` → `{bitmap, layer, …}` (a new layer, made active);
  `file.import_to_library` → `{bitmap}` or `{sound}`.
- `bone.add` → `{bone, layer, created}`; `text.create` → `{element, font, width, height}`.
- `timeline.create_motion_tween` → `{motion, target, frames}`; `create_tween` / `create_shape_tween` → `{tween, kind, easing}`.
- Exports → `{written, frames, bytes, …}` plus format specifics (`width/height/fps/audio`,
  sprite `columns/rows/map`, Lottie/HTML `notes` and `report` on what was approximated).
