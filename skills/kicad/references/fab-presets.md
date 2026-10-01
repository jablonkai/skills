# Fabrication presets

`kicad.py fab --preset jlcpcb|generic` produces:

| Output | jlcpcb | generic |
|--------|--------|---------|
| Gerber layers | F/B.Cu + inner, F/B.Mask, F/B.Silkscreen, F/B.Paste, Edge.Cuts | same |
| Gerber format | RS-274X, Protel extensions, **no X2, no netlist attrs, no job file** | X2 + netlist attrs + job file |
| Drill | Excellon, mm, decimal, absolute origin, separate PTH/NPTH, Gerber X2 maps | same |
| CPL | `Designator,Mid X,Mid Y,Layer,Rotation`, values `105.0000mm`, `Top/Bottom` | KiCad `Ref,Val,Package,PosX,PosY,Rot,Side` |
| BOM | `Comment,Designator,Footprint,LCSC Part #`, grouped by value+footprint+LCSC, refs comma-separated | `Reference,Value,Footprint,Qty[,LCSC]` |
| Zip | `<board>-gerbers.zip`: Gerbers + drill + maps only | same |

Required (exit 1 if missing): every copper layer, F/B.Mask, Edge.Cuts with outline
draws, at least one `.drl`, a non-empty CPL (unless `--no-cpl`).

## JLCPCB notes

- Upload the zip as the PCB, then the BOM and CPL in the assembly step.
- **LCSC field:** add an `LCSC` property (any name containing "LCSC" or "JLC" is
  auto-detected) to each symbol with the part number (e.g. `C17513`). Without it the
  BOM column is empty and `fab` reports a problem.
- **Rotation offsets:** JLCPCB's footprint origin/rotation convention differs from
  KiCad's for some packages (SOT-23, some diodes, QFN tapes). Their order preview shows
  each part. Fix wrong ones by editing the CPL `Rotation` column (+90/180/270), not the
  board. The skill doesn't guess these.
- **Through-hole parts** aren't in the CPL by default (`--include-tht` to add them).
  They stay in the BOM.
- Board outline: one closed shape on Edge.Cuts. Gaps produce an "outline not closed"
  rejection at the fab even though KiCad plots it.

## Other fabs

Use the `generic` preset and check the fab's current upload guide; layer set and
Excellon drill are universal, X2 attributes are widely accepted. Assembly BOM columns
differ per fab: build them with `kicad-cli sch export bom --fields … --labels …`
(see [cli-reference.md](cli-reference.md#exports-sch)), matching the fab's template.
