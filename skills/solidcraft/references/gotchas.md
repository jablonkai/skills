# Gotchas (SolidCraft 0.29.0)

## Silent failures

- **`parameters.change {name, expression}` with a misspelled name exits 0.** It creates a
  new parameter (`thikness = 6 mm`) and leaves the model as it was. Use the `changes`
  form, `parameters.change {"changes": {"thickness": "6 mm"}}`, which refuses an unknown
  name (`unknown parameter 'thikness'`) and applies all the changes or none.
  `sc_params.py` does this, then checks that no parameter was added.
- **Plain `run` ignores unknown parameter keys.** `solid.extrude {"bodyname": "X"}` gives
  a body called `Body1`. Run scripts through `sc_run.py` instead: its MCP session uses
  `--param-check strict`, which refuses the key and names the right one.
- **A cut, hole or fillet that misses can still report success.** Only a volume that
  matches your own calculation proves it worked. Work the expected volume out before
  building, then compare (`--expect-volume`).
- **Extrude takes every closed region by default.** A loop inside another becomes a hole,
  which is how the plate's Ø4 holes work, and a loop inside that hole is solid again. An
  unintended region changes the volume, not the exit code.

## Picks and geometry

- **Edges are picked by a point on the edge, and that point should be the midpoint.** A
  point where two edges meet is refused (`[0,0,5] is where 2 edges meet`). After a
  fillet, the old corner point no longer lies on any edge. A pick farther than 5 % of the
  body's size from every edge is refused, but on a large body that limit is wide, so a
  sloppy pick can snap to the wrong edge. Picks must be plain numbers, not expressions.
- **One pick takes the whole tangent chain.** A rounded rim needs one point, not eight.
- **The vertical corner edges of a box from (0,0,0) to (L,W,H)** are at `[0,0,H/2]`,
  `[L,0,H/2]`, `[L,W,H/2]` and `[0,W,H/2]`. On a part centred on the origin they are at
  `[±L/2, ±W/2, H/2]`.
- **Sketch plane axes:** on `XZ` the sketch y axis is world **−Z**. A feature at height
  z is drawn at sketch y = −z. See `sc_commands.py --doc solidcraft-modeling/reference.md`.
- **Fillet before shell**, except an edge of the face the shell removes: round that one
  after the shell.
- **A primitive cut against curved faces** (`solid.box`/`solid.cylinder` with
  `operation: cut`) can fail with `planar faces only`. Use a sketch profile and an
  extrude cut instead.
- **A plain number in a sketch doesn't follow parameters.** Drive positions with
  `sketch.dimension {value: "expr"}` or expression fields (`base: ["w/2-6", 0, 0]`).

## Files and runs

- **A failing feature makes `run` and `sc_run.py` exit 1 and write nothing.** Read the
  step number in the error, fix that one step and rerun the whole script. A `batch` is
  checked before its first step, so a key error means nothing ran.
- **`--save` must not be the input file.** Write `NAME-v2.solidcraft`. `file.save {}` in a
  session also overwrites the opened file.
- **`run --results` floods the terminal** with every step's reply. Use `--quiet` and then
  `eval --json-out`.
- **STEP has no history.** An imported STEP opens as one `BaseFeature`, with no
  parameters or features to edit. Changes go on top: cut, fillet, or `solid.offset_face`.
- **Mesh volumes differ by about 0.01–0.1 %** from the B-rep (tessellation). Compare an
  STL/3MF export with a tolerance of about 1 %, and a STEP export with 0.1 %.
- **Mass uses a density of 1.29 g/cm³** until `material.assign` sets a material. Report
  mass only together with its material.
- **The ground grid lies on Z 0.** A part below Z 0 is cut by it in snapshots; use
  `--no-grid`.
- **`exec` ignores `--connect`.** It always runs on an empty headless design.
- **The CLI on PATH may be older than the app** (0.22.1 against 0.25.0 once; both were
  0.29.0 at the last check). Commands it lacks, such as `solid.cone`, fail as unknown, and it refuses
  designs saved by the newer app (`format 41; reads up to 36`). Use the app's copy,
  which `sclib.cli()` picks.
