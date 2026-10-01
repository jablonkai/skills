---
name: kicad
description: 'Automate KiCad 10 PCB and schematic work: run DRC/ERC with kicad-cli and summarise the violations, build a manufacturer-ready fabrication package (Gerbers, Excellon drill, pick-and-place/CPL, BOM, STEP, zipped, with a JLCPCB preset), render the board to PNG, and script footprint placement and board edits in a running PCB editor through the KiCad IPC API (kicad-python / kipy). Use for "run DRC on this board", "why does ERC fail", "summarise the DRC errors", "export Gerbers for JLCPCB / PCBWay", "make the fab zip", "generate the BOM and CPL / centroid file", "place these LEDs in a circle", "move or rotate footprints by script", "set the title block", or anything mentioning .kicad_pcb, .kicad_sch, kicad-cli or pcbnew scripting. Not for mechanical CAD, enclosures, STEP modelling or turning existing Gerbers into printable 3D parts (freecad, brl-cad), photoreal renders of a board in a 3D scene (blender), block or wiring diagrams (drawio), circuit simulation (SPICE), or flashing firmware to a board.'
summary: "automate KiCad 10 — DRC/ERC with JSON violation summaries, JLCPCB-ready fabrication zips (Gerbers, drill, CPL, BOM, STEP), board renders, and scripted footprint placement in a running PCB editor via the IPC API"
category: electronics
risk: medium
tags:
    - kicad
    - pcb
    - electronics
    - gerber
    - drc
    - jlcpcb
---

# KiCad automation

KiCad 10 has three automation surfaces. Pick by task:

| Task | Surface | Tool |
|------|---------|------|
| DRC / ERC, summaries | `kicad-cli` (headless) | `scripts/kicad.py drc` / `erc` |
| Gerbers, drill, CPL, BOM, STEP, zip | `kicad-cli` (headless) | `scripts/kicad.py fab` |
| Board picture | `kicad-cli pcb render` | `scripts/kicad.py render` |
| Move/rotate/arrange footprints, title block | IPC API in a **running** PCB editor | `scripts/kicad_ipc.py` |
| Edits with no GUI available | legacy SWIG `pcbnew` (deprecated, gone in KiCad 11) | [references/ipc-api.md](references/ipc-api.md#swig-fallback) |

Read `.kicad_pcb`/`.kicad_sch` text (S-expressions) to inspect or verify. Don't
hand-edit it for placement. In the file, pad and field offsets are relative to the
footprint, but their **angles are absolute**, so changing a footprint's rotation in
`(at X Y ROT)` leaves every pad at the old angle.

Verified against **KiCad 10.0.6** on macOS. `kicad-cli` lives in
`/Applications/KiCad/KiCad.app/Contents/MacOS/` and is not on `PATH`. The helpers
find it (or use `$KICAD_APP`).

## Why the helpers instead of raw kicad-cli

Raw `kicad-cli` has measured traps (details in [references/gotchas.md](references/gotchas.md)):

- **Output follows the KiCad UI language**, JSON report descriptions included
  ("Szigetelési távolság megsértése…" on a Hungarian Mac). `kicad.py` runs every call
  against a throwaway English copy of the user's config, so reports are readable and
  stable. The user's settings are never touched.
- **Exit codes disagree:** `pcb drc --exit-code-violations` gives 5, `sch erc` gives 0
  with 50 violations. `kicad.py` reads the JSON and exits 2 when errors exist.
- **ERC JSON positions are 1/100 of the stated unit** in 10.0.6. `kicad.py erc`
  detects and corrects this.
- **`pcb export gerbers` without `-l` plots every layer** (User.*, Fab, Margin…), and an
  invalid layer name is only a warning (exit 0). `fab` passes an explicit layer list
  derived from the board's copper count.
- **`sch export bom` writes ranges** (`D1-D8`); fab houses want `D1,D2,…`.

## Commands

```bash
K=~/path/to/skills/kicad/scripts      # wherever the skill is installed
python3 $K/kicad.py find                       # version, paths, API switch, kipy

python3 $K/kicad.py drc board.kicad_pcb        # writes board-drc.json, grouped summary
python3 $K/kicad.py drc board.kicad_pcb --refill-zones --parity --top 5
python3 $K/kicad.py erc board.kicad_sch        # writes board-erc.json

python3 $K/kicad.py fab board.kicad_pcb -o fab/ --preset jlcpcb --zip --step
python3 $K/kicad.py render board.kicad_pcb -o top.png [--side bottom] [--rotate -45,0,45]
```

Exit status everywhere: **0** ok · **1** failed · **2** violations found · **3** setup
error or timeout. `--json` gives machine-readable output; `--timeout N` (default 600 s)
kills a hung call's process group.

### DRC / ERC

The summary groups violations by severity and type, with a count and the first
`--top` examples (items, refs and mm positions). **Unconnected items** and **schematic
parity** come from separate JSON arrays and are listed separately, so don't add them into
the violation count.

When explaining DRC results to a user:

1. Lead with errors, by count, before warnings.
2. Name the parts or nets involved and the measured vs required value (e.g. "VCC
   track 0.05 mm from D5 pad 1 [GND], rule 0.2 mm").
3. Say which errors are one root cause. A misplaced footprint can cause a courtyard
   overlap, mask bridges and silk warnings at once.
4. Suggest the fix, not just the rule name.

Run `--refill-zones` when the board has copper pours: stale fills cause false
clearance/unconnected results. Without `--save-board` the file is not modified.

### Fabrication package

`fab` writes `gerbers/` (copper incl. inner layers, mask, paste, silkscreen, Edge.Cuts,
plus `*-PTH.drl`/`*-NPTH.drl` and drill maps), a CPL, a BOM from the matching
`.kicad_sch`, an optional STEP, and with `--zip` a zip of `gerbers/` only (what fab
upload forms expect; BOM/CPL are uploaded separately).

- `--preset jlcpcb`: no X2/netlist attributes, no job file. CPL is
  `Designator,Mid X,Mid Y,Layer,Rotation`. BOM is `Comment,Designator,Footprint,LCSC Part #`,
  grouped, with the LCSC field auto-detected (`--lcsc-field` to name it).
- `--preset generic` (default): KiCad's own column names, X2 Gerbers.
- The CPL holds SMD parts only, without DNP parts (`--include-tht` to add through-hole).
- Exit 1 with a `PROBLEM:` line for anything a fab would reject: missing required
  layer, empty outline, empty CPL, no LCSC field on a JLCPCB BOM.

Run `drc --parity` first when a schematic exists. A clean plain DRC only means the
copper that's there is legal. Parity also catches a board that was never updated from
its schematic or never routed. `fab` prints `WARNING:` lines for boards with pads but
no tracks/zones, or no nets at all. The files still export, but **tell the user**
before they order, because those boards come back as isolated pads.
Per-part rotation offsets for JLCPCB assembly are not corrected; see
[references/fab-presets.md](references/fab-presets.md).

## Live edits through the IPC API

Setup, once per machine (details in [references/ipc-api.md](references/ipc-api.md)):

1. `python3 -m venv ~/.venvs/kicad && ~/.venvs/kicad/bin/pip install kicad-python`
2. **The user** switches on KiCad › Preferences › Plugins › *Enable KiCad API*. It is off
   by default. Don't flip it by editing their config; ask.
3. Open the board in the PCB editor. If the KiCad project manager is running, board calls
   can fail with "no handler": the project manager owns the socket. Open the board
   *from* that project window, or use the standalone PCB Editor with KiCad closed.

```bash
PY=~/.venvs/kicad/bin/python
$PY $K/kicad_ipc.py status
$PY $K/kicad_ipc.py list --glob 'D*'
$PY $K/kicad_ipc.py place-circle D1-D8 --center board --radius 20 \
    --start-angle 90 --direction cw --facing tangent --save
$PY $K/kicad_ipc.py move J1 145 125 --rot 90 --save
$PY $K/kicad_ipc.py set-title --title "LED ring" --revision B --save
```

- Coordinates are **mm as shown in the editor: X right, Y down**. Angles are degrees
  **counter-clockwise as seen from the top**, like KiCad's Rotation field.
- `status` prints the Edge.Cuts outline and its centre. `--center board` uses that centre.
- `place-circle`: `--start-angle 0` puts the first part right of the centre, `90` above
  it. `radial` points each footprint's +X outward; `tangent` aligns it with the circle;
  `--rotation-offset` corrects footprints whose "natural" direction isn't +X.
- Each footprint command is **one commit**: one Cmd+Z in KiCad undoes it all (verified).
  `set-title` edits are not on KiCad's undo stack. `--dry-run`
  prints the computed positions and changes nothing. Without `--save` the edit lives only
  in the open editor.
- For anything the helper doesn't cover, write a short kipy script following
  [references/ipc-api.md](references/ipc-api.md): positions are `Vector2` in **nm**,
  wrap edits in `begin_commit()`/`push_commit()`, then `update_items()`.

## Verify

- DRC/ERC: re-run `drc` after a fix; the summary is the oracle.
- Placement: run `drc` afterwards (new positions often collide with existing parts),
  then `kicad_ipc.py list --json` or read `(footprint … (at X Y ROT))` from the
  saved `.kicad_pcb`; `render` gives a picture.
- Fab: open the zip and check the layer list; `render` and
  `kicad-cli pcb export svg` for visual checks.

## References

- [references/cli-reference.md](references/cli-reference.md): the kicad-cli 10 subcommands and flags used here
- [references/ipc-api.md](references/ipc-api.md): kipy calls, units, commits, socket and SWIG fallback
- [references/fab-presets.md](references/fab-presets.md): JLCPCB / generic layer, drill and column specs
- [references/recipes.md](references/recipes.md): worked tasks end to end
- [references/gotchas.md](references/gotchas.md): measured traps and the security posture
