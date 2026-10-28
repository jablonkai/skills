# solidcraft-cli 0.25.1

Use the CLI inside the app (`/Applications/SolidCraft.app/Contents/MacOS/solidcraft-cli`).
A separately installed copy (`~/.local/bin/solidcraft-cli`, from the artcraft-cli
installer) can be older. On the test machine it was 0.22.1, with 461 commands instead of
493. `sclib.cli()` picks `SOLIDCRAFT_CLI`, then the app's copy, then PATH, and warns when
PATH is older.

```sh
SC=/Applications/SolidCraft.app/Contents/MacOS/solidcraft-cli
$SC --version          # solidcraft-cli 0.25.1
$SC --help             # the full usage text below
```

## Script format

```json
{"commands": [
  {"command": "sketch.create", "params": {"plane": "XY", "name": "Outline"}},
  {"command": "sketch.rectangle.two_point", "params": {"p0": [0, 0], "p1": [60, 40]}},
  {"command": "sketch.finish", "params": {}},
  {"command": "solid.extrude", "params": {"distance": "thickness", "body_name": "Plate"}}
]}
```

`solidcraft-cli script design.solidcraft --out s.json` writes a design's history in this
format. `eval` and `run` replay it.

## Subcommands

| Command | What it does |
|---|---|
| `run SCRIPT [--in DESIGN] [--out F]… [--save F.solidcraft] [--quiet] [--results] [--timings] [--json-out F] [--allow-errors]` | Replays the script on a new design, or on `--in`. A failing feature exits 1 and writes nothing unless `--allow-errors` is given. `--out` exports by extension. `--results` prints every step's reply, which is very large; prefer `--quiet` followed by `eval`. |
| `run --in F --out G…` | Converts with no script, for example STEP → STL/3MF. |
| `eval FILE [--json-out F]` (alias `inspect`) | Measures a design, part (STEP/STL/3MF/OBJ) or script and returns JSON. This is the read-back oracle. |
| `eval SCRIPT --in DESIGN` | Runs the script on DESIGN, measures the result and saves nothing. Use it to preview an edit. |
| `script DESIGN [--out s.json]` | The feature history as a replayable script. |
| `snapshot SCRIPT\|DESIGN [--in F] --out shot.png [--width W --height H] [--view V \| --camera JSON] [--no-grid] [--no-axes] [--body NAME:opacity=0.3,color=#rrggbb]… [--tool NAME]… [--section SPEC]` | Headless viewport render (CPU), 1280×800 by default. |
| `render SCRIPT\|DESIGN --out img.png [--samples N] [--transparent] …` | Path-traced render. It is slow; use it for presentation images, not for checks. |
| `exec COMMAND [json]` | Runs one command on an empty headless design. `--connect` has no effect here. |
| `commands` | The whole registry as JSON: id, label, `params` signature, `enabled`, `disabled_reason`. About 400 KB, so filter it with `sc_commands.py`. |
| `mcp [--headless] [--in F] [--connect 127.0.0.1:PORT [--token T]] [--allow-path DIR]… [--param-check off\|warn\|strict]` | MCP server over stdio. See below. |
| `mcp setup [--dry-run] [--client …] [--live]` | Writes a `solidcraft` entry into AI-client configs. It changes the user's config files, so run it only when asked. |
| `crashes [list\|show ID\|replay ID]`, `gpu`, `licences`, `bench-*`, `oracle`, `fuzz`, `recipe` | Diagnostics and benchmarks; not needed for normal work. |

`--view` takes `iso front back top bottom left right` or a view saved with `view.save`.
`--camera` takes `{target:[x,y,z], yaw, pitch, distance, fov?}` in mm and radians.
`--section` takes `z=27` (keeps the smaller side), `z=27,flip`, `XY`, `XZ` or `YZ`.
`--tool NAME` draws that body solid and everything else see-through, which is useful to
show a cutter inside the stock.

## `eval` JSON (abridged)

```json
{"body_count": 1,
 "bodies": [{"name": "Plate", "closed": true, "volume_mm3": 23420.14, "mass_g": 30.21,
             "density_g_cm3": 1.29, "material": "Default", "area_mm2": 7135.15,
             "bbox": {"min": [0,0,0], "max": [60,40,10]}, "center_of_mass": [30,20,5],
             "faces": 14, "edges": 32, "vertices": 24,
             "face_types": {"plane": 6, "cylinder": 8}, "kernel": {"faces": 18}}],
 "params": [{"name": "thickness", "expression": "10 mm", "value": 10.0, "unit": "mm", "error": null}],
 "sketches": [{"name": "Outline", "profiles": 5, "dof": 14, "status": "solved"}],
 "timeline": [{"id": 2, "name": "Extrude1", "type": "ExtrudeFeature", "error": null, "warning": null,
               "suppressed": false, "rolled_back": false}],
 "total": {"volume_mm3": 23420.14, "mass_g": 30.21, "open_bodies_skipped": 0}}
```

- Volume and mass are given only for closed bodies; `open_bodies_skipped` counts the rest.
- Compare `faces`, not `kernel.faces`.
- `params` lists **user** parameters only. Sketch dimensions and feature inputs (`d1`…)
  come from `parameters.list {filter: "all"}`, which `sc_params.py --all` runs.
- A STEP file opens as one `BaseFeature`, with no history or parameters.
- The default density is 1.29 g/cm³. Mass only means something after `material.assign`.

## Formats

| Direction | Formats |
|---|---|
| Export (`--out`, `file.export`, MCP `export`) | `.step/.stp`, `.stl` (binary), `stla` (ASCII STL), `.obj`, `.3mf`, `3mf-tagged`, `.urdf`, `.json`. **No IGES export.** STL/OBJ/3MF take `quality: standard\|fine\|finest`. |
| Open (`--in`, MCP `open`) | `.solidcraft`, `.step/.stp`, `.3mf`, `.stl`, `.obj`, `.glb/.gltf`. A mesh opens as a mesh body, so `eval` measures it but B-rep features can't use it. |
| Insert into the open design (`file.insert_step`, `file.insert_mesh`) | STEP, IGES, FreeCAD `.FCStd`, Rhino `.3dm`, meshes. |
| 2D | `sketch.export_dxf`, `sheet.export_dxf` (flat patterns), `file.export_view_dxf`. |

## MCP (what the scripts use)

`mcp --headless --param-check strict --allow-path DIR` gives a headless session in
which:
- **an unknown parameter key is an error** (`unknown key 'bodyname'; did you mean
  'body_name'?`). Plain `run` drops unknown keys silently;
- file access is limited to the `--allow-path` folders, the open design's folder and a
  temp folder. `--allow-any-path` lifts the limit; don't use it;
- tools include `batch` (all-or-nothing: on failure it reports `failed: {index, command,
  error}` and `nothing was run`), `execute`, `open`, `save`, `export`, `measure`,
  `inspect_design`, `set_parameter`, `screenshot`, `undo`/`redo`, `describe_command`,
  `list_commands`, `crash_reports` and `skill_reference`.

`skill_reference {skill, file}` returns SolidCraft's own agent docs:
- `solidcraft-modeling` (`SKILL.md`, `reference.md`): command shapes, sketch-plane axes,
  ids, a worked parametric plate;
- `solidcraft-editing`;
- `solidcraft-checking` (`SKILL.md`, `reference/porting.md`);
- `solidcraft-mechanisms` (joints, motion).

`sc_commands.py --doc NAME[/FILE]` prints them.
