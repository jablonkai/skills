---
name: solidcraft
description: 'Automate SolidCraft, the parametric solid-modeling CAD app, headless with solidcraft-cli: build parametric parts from sketch and feature scripts (extrude, holes, fillets, chamfers, shells, patterns, booleans) and save .solidcraft; change named parameters of an existing design and re-export; measure volume, bounding box and mass of designs and STEP/STL parts; export STEP, STL, 3MF and OBJ; render iso, orthographic and section snapshots, with every result read back by eval. Use when the user mentions SolidCraft, solidcraft-cli or a .solidcraft file, or wants a part modeled, resized or measured with SolidCraft: "model a mounting plate with four corner holes in SolidCraft", "set wall to 5 mm in this .solidcraft and re-export the STEP", "what is the volume and bounding box of this STEP in SolidCraft", "render an iso and a section view". Not for FreeCAD (freecad), BRL-CAD (brl-cad), 2D drawings or DXF (cadcraft, qcad), PCBs (kicad), or mesh and art modeling (blender).'
summary: "automate SolidCraft headless with solidcraft-cli — parametric parts from sketch and feature scripts (extrude, holes, fillets, patterns, booleans), named-parameter edits with re-evaluation, volume, bounding-box and mass read-back, STEP/STL/3MF export and import, iso and section snapshots, eval read-back verified"
category: cad
compatibility: "Built for SolidCraft 0.25.1 and its bundled solidcraft-cli 0.25.1 on macOS, Python 3.9+; pre-1.0, so command ids may change."
risk: medium
tags: [solidcraft, cad, parametric, solid-modeling, step, stl, 3mf, headless]
metadata:
  version: "1.0.2"
  author: "Tamás Jablonkai"
---

# SolidCraft via solidcraft-cli

SolidCraft is a parametric solid-modeling CAD app. A design (`.solidcraft`) holds user
parameters, sketches and a feature timeline (extrude, hole, fillet, pattern…) that
rebuild when a parameter changes. Every tool is a command in one registry (493 in
0.25.1). The same commands run from a script (`solidcraft-cli run`), from a headless MCP
session (`solidcraft-cli mcp`) and in the app. This skill drives them **headless**, with
no window open, and checks each result with `solidcraft-cli eval`, a measurement that
runs independently of the build. Verified against **SolidCraft 0.25.1** with the
**solidcraft-cli 0.25.1** inside the app on macOS. The software is pre-1.0, so if a
pinned id fails, look it up rather than guessing.

```sh
SC=/Applications/SolidCraft.app/Contents/MacOS/solidcraft-cli   # the app's own copy
$SC --version          # a solidcraft-cli on PATH may be older (0.22.1 was); prefer this one
```

## Pick the route

| Task | Route |
|---|---|
| New part from a feature script, saved and exported | `scripts/sc_run.py part.json --save P.solidcraft --out P.step --out P.stl --expect-volume V` |
| Add or change features on a copy of a design or STEP | `scripts/sc_run.py edit.json --in IN --save OUT.solidcraft [--out …]` |
| Change named parameters (wall, length…) and re-export | `scripts/sc_params.py IN --set wall="5 mm" --save OUT.solidcraft --out OUT.step` |
| What can be changed | `scripts/sc_params.py IN` (user parameters), or `--all` to include sketch and feature inputs |
| Size, volume, mass of a design, STEP, STL or 3MF; snapshots | `scripts/sc_inspect.py F [--snap-dir D --views iso top --section mid]` |
| Check an output against numbers, or an export against its design | `scripts/sc_verify.py part F --volume V --size X Y Z --same-as G` |
| Convert STEP ↔ STL/3MF/OBJ with no edits | `$SC run --in part.step --out part.3mf` |
| A design's history as a replayable script | `$SC script D.solidcraft --out D.json` |
| Find a command and its params | `scripts/sc_commands.py WORD…`, `--id ID` |
| How SolidCraft's own agent docs build things (plane axes, ids, worked part) | `scripts/sc_commands.py --doc solidcraft-modeling/reference.md` (also `solidcraft-editing`, `solidcraft-checking`, `solidcraft-mechanisms`) |

## Scripts

Set `S=<this skill>/scripts` and call each as `python3 $S/<script>`. They need Python
3.9+ and the standard library only, and each has a full `--help`. They find the CLI
(`SOLIDCRAFT_CLI`, then the app's copy, then PATH), never write to their input, refuse
to overwrite outputs without `--overwrite`, print JSON and exit 1 on any failed check.

- **`sc_run.py SCRIPT [--in F] [--save F.solidcraft] [--out F]… [--expect-volume V] [--tol PCT] [--expect-size X Y Z] [--expect-bodies N]`**
  - SCRIPT is `{"commands":[{"command":ID,"params":{…}}]}`, from a file or inline.
  - The steps run as one all-or-nothing MCP batch with **strict parameter checks**. A
    misspelled key or a failing feature stops the run before anything is applied, and
    the error names the step.
  - After saving and exporting, every output is measured again with `eval`. Each
    export is compared with the design: 0.1 % for STEP, 1 % for meshes.
- **`sc_params.py IN [--all] [--set NAME=EXPR …] --save OUT [--out F]… [--expect-volume V]`**
  - With no `--set` it lists parameters.
  - With `--set` it first refuses unknown names, then applies all values at once.
  - Then it checks each saved expression, that no parameter was added, and that no
    feature has an error. It reports the volume before and after.
- **`sc_inspect.py F [--snap-dir D] [--views iso top …] [--section mid|z=N|XZ…] [--json-out J]`**
  - It reports the body count, volume, mass, overall bbox and bodies.
  - Snapshots are named `NAME-VIEW.png` and `NAME-section-SPEC.png`. Each is checked to
    be non-blank, and each section to differ from a plain render.
- **`sc_verify.py`** has three modes:
  - `part F --bodies N --volume V --size X Y Z --param wall="5 mm" --params-exact wall hole_d --no-errors --closed --face-type cylinder=8 --same-as G`;
  - `png F --width W --not-blank --differs G.png`;
  - `hash PATH… --save m.json` / `--compare m.json`.
- **`sc_commands.py WORD…`**, also `--prefix solid.`, `--id solid.hole` or `--doc NAME[/FILE]`: filtered registry lookup and SolidCraft's bundled docs.

## Workflow

1. **Work the part out as numbers first.** List the parameters, where each feature
   sits, the world point of every edge or face pick (an edge's midpoint), and the
   **expected volume and bounding box**, calculated by hand. A cut or fillet that
   misses can still report success, so only a measured volume that matches your number
   proves the feature worked.
2. **Inspect what exists.** Run `sc_inspect.py F` and `sc_params.py F --all` before
   editing. Look up any command you haven't used this session with `sc_commands.py`.
   The vendor's `solidcraft-modeling/reference.md` has the exact shapes for sketches,
   holes, patterns and mirrors.
3. **Never touch the originals.** Write to a new path (`NAME-v2.solidcraft`). The scripts
   refuse to save over their input.
4. **Build in one script** and run it through `sc_run.py` with `--expect-volume` and
   `--expect-size`. If a step fails, fix that step and rerun the whole script; nothing
   was written.
5. **Read back.** The scripts measure every saved design and export again. For anything
   else, use `sc_verify.py part`.
6. **Look at it.** Run `sc_inspect.py OUT --snap-dir D --views iso top`, plus `--section`
   for inside features, then Read the PNGs. A hole in the wrong corner keeps the volume
   right; only the picture shows it.
7. **Report** the outputs, the measured numbers next to the expected ones, and anything
   you could not check.

## The traps that cost the most (details in [gotchas.md](references/gotchas.md))

- **`parameters.change {name}` with a misspelled name silently adds a new parameter**,
  and the model doesn't change. Use `sc_params.py`, or the `{"changes": {name: expr}}`
  form, which refuses unknown names.
- **Plain `solidcraft-cli run` drops unknown keys** (`bodyname` gives `Body1`). Run
  scripts through `sc_run.py`, which uses `--param-check strict`.
- **Edges are picked by a point on them.** A corner where two edges meet is refused,
  and after a fillet the old corner point is gone. Use edge midpoints, as plain numbers.
- **Extrude takes every closed region:** circles inside a rectangle become holes, and a
  stray loop changes the volume.
- **Positions written as plain numbers don't follow parameters.** Use expressions such
  as `"wall + (30 - wall)/2"` or sketch dimensions with expression values.
- **STEP has no history.** It opens as one base feature, so edits go on top.
- **Mass uses 1.29 g/cm³** until a material is assigned.
- **The CLI on PATH can be older than the app**, which then reports commands it lacks
  as unknown. Use the app's copy.

## The running app (optional)

To change the design the user has open in SolidCraft, rather than a file, use the app's
token-authenticated control channel through `solidcraft-cli mcp --connect
127.0.0.1:PORT` (see [security.md](references/security.md)). Ask before `open` or
`new_design`, because both discard the app's unsaved work. Headless work on files is
the default.

## References

- [references/cli.md](references/cli.md): subcommands, script format, `eval` JSON, formats, MCP tools.
- [references/commands.md](references/commands.md): command ids by task, pinned to 0.25.1.
- [references/recipes.md](references/recipes.md): the plate, the bracket and its parameter edit, STEP inspection, a flange with a bolt circle, mesh export, history scripts.
- [references/gotchas.md](references/gotchas.md): silent failures and surprises.
- [references/security.md](references/security.md): file access, the app's control channel, config the app writes.
