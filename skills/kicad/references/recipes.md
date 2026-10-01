# Recipes

`K` is the skill's `scripts/` directory; `PY=~/.venvs/kicad/bin/python`.

## 1. "Run DRC and tell me what's wrong"

```bash
python3 $K/kicad.py drc board.kicad_pcb --refill-zones --top 3
```

Explain from the summary, errors first:

> 6 errors. **Clearance (2):** the +3V3 track at (61.2, 40.5) passes 0.08 mm from
> U2 pad 4 [GND]; the rule is 0.15 mm. Reroute it around the pad.
> **Courtyard overlap (1)** + **solder-mask bridge (2)**: C8 was dropped onto C7,
> one misplacement causing both. Move C8 clear of C7.
> **Unconnected (1):** net SDA between U2 pad 6 and J3 pad 2 has no track.
> Warnings: silkscreen clipped by mask on C7/C8 (goes away with the move).

Group by root cause, give coordinates and the refs or nets involved, and say how to fix it.
For a schematic: `python3 $K/kicad.py erc board.kicad_sch`. `pin_not_connected`
on intentionally open pins is fixed with a no-connect flag, not a wire.

## 2. JLCPCB order package

```bash
python3 $K/kicad.py drc board.kicad_pcb || echo "fix DRC first"
python3 $K/kicad.py fab board.kicad_pcb -o fab/ --preset jlcpcb --zip --step
unzip -l fab/board-gerbers.zip
```

Upload `board-gerbers.zip` → PCB; `board-BOM.csv` + `board-CPL.csv` → assembly.
If `fab` prints `PROBLEM: no LCSC field`, add an `LCSC` property to the symbols (Symbol
Fields Table in Eeschema) and re-run.

## 3. LEDs in a circle (running KiCad)

```bash
$PY $K/kicad_ipc.py list --glob 'D*'          # check refs, current positions
$PY $K/kicad_ipc.py place-circle D1-D8 --center 125,125 --radius 20 \
    --start-angle 90 --direction cw --facing tangent --dry-run
$PY $K/kicad_ipc.py place-circle D1-D8 --center 125,125 --radius 20 \
    --start-angle 90 --direction cw --facing tangent --save
```

- D1 at 12 o'clock, clockwise like a clock face: `--start-angle 90 --direction cw`.
- Board centre: `--center board` (the Edge.Cuts bounding-box centre; `status` prints it).
- Then `python3 $K/kicad.py drc board.kicad_pcb`. Large footprints on a small radius
  overlap courtyards. Increase `--radius` until DRC is clean.
- The resistors can follow on an inner circle with the same angles:
  `place-circle R1-R8 --radius 14 …`.

## 4. Footprints in a grid / row

No subcommand; a short kipy script:

```python
from kipy import KiCad
from kipy.geometry import Vector2
board = KiCad().get_board()
fps = {f.reference_field.text.value: f for f in board.get_footprints()}
c = board.begin_commit()
for i, ref in enumerate(f"R{n}" for n in range(1, 9)):
    fps[ref].position = Vector2.from_xy_mm(105 + (i % 4) * 5, 135 + (i // 4) * 4)
board.update_items([fps[f"R{n}"] for n in range(1, 9)])
board.push_commit(c, "Grid R1-R8")
```

## 5. Board picture for a README

```bash
python3 $K/kicad.py render board.kicad_pcb -o docs/top.png --quality high
python3 $K/kicad.py render board.kicad_pcb -o docs/iso.png --rotate -45,0,45 --quality high
```

## 6. Title block before release

```bash
$PY $K/kicad_ipc.py set-title --revision C --date 2026-10-01 --comment 1="Released for fab" --save
```

Without a running KiCad, edit the `(title_block …)` in the `.kicad_pcb` text: it has no
geometry, so text editing is safe there.
