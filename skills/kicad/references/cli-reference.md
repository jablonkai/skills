# kicad-cli 10 reference (subset used by this skill)

Binary: `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`. Run any subcommand
with `--help` for the full list. All flags below were checked with `--help` on 10.0.6.

Top level: `fp`, `jobset`, `pcb`, `sch`, `sym`, `version`.

## Checks

```bash
kicad-cli pcb drc  --format json --units mm --severity-all [--refill-zones [--save-board]] \
                   [--schematic-parity] [--exit-code-violations] -o drc.json board.kicad_pcb
kicad-cli sch erc  --format json --units mm --severity-all [--exit-code-violations] \
                   -o erc.json board.kicad_sch
```

- Severities: `--severity-error`, `--severity-warning`, `--severity-exclusions`, `--severity-all`.
- DRC JSON (`schemas.kicad.org/drc.v1.json`): `violations[]`, `unconnected_items[]`,
  `schematic_parity[]`, each `{type, severity, description, items[{description, pos{x,y}, uuid}]}`;
  plus `ignored_checks`, `kicad_version`, `coordinate_units`.
- ERC JSON: `sheets[{path, uuid_path, violations[]}]`, same violation shape (positions
  scaled 1/100, see gotchas).

## Exports (pcb)

```bash
kicad-cli pcb export gerbers -o out/ -l F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts \
          [--no-x2] [--no-netlist] [--check-zones] [--no-protel-ext] [--board-plot-params] board.kicad_pcb
kicad-cli pcb export drill -o out/ --format excellon --excellon-units mm --excellon-zeros-format decimal \
          --drill-origin absolute [--excellon-separate-th] [--generate-map --map-format gerberx2] board.kicad_pcb
kicad-cli pcb export pos  -o pos.csv --format csv --units mm --side both [--smd-only] [--exclude-dnp] board.kicad_pcb
kicad-cli pcb export step -f -o board.step [--subst-models] [--board-only] [--no-dnp] board.kicad_pcb
kicad-cli pcb export svg|pdf|dxf -l F.Cu,Edge.Cuts -o out board.kicad_pcb
kicad-cli pcb render -o top.png --side top|bottom|left|right|front|back -w 1600 -h 900 \
          [--quality basic|high] [--rotate -45,0,45] [--background transparent|opaque] board.kicad_pcb
```

Other `pcb export` targets: `3dpdf brep gencad glb ipc2581 ipcd356 odb ply ps stats stl stpz u3d vrml xao`.
`--board-plot-params` reuses the plot settings saved in the board (the GUI's Plot dialog).

- Protel extensions are the default (`.gtl .gbl .gts .gbs .gto .gbo .gtp .gbp .gm1`, inner `.g1…`).
- Inner copper layer names: `In1.Cu`, `In2.Cu`, …
- `pos` CSV columns: `Ref,Val,Package,PosX,PosY,Rot,Side`.

## Exports (sch)

```bash
kicad-cli sch export bom -o bom.csv --fields 'Value,Reference,${FOOTPRINT_NAME},LCSC' \
          --labels 'Comment,Designator,Footprint,LCSC Part #' --group-by 'Value,${FOOTPRINT_NAME},LCSC' \
          --ref-range-delimiter '' [--exclude-dnp] board.kicad_sch
kicad-cli sch export netlist -o net.xml --format kicadxml board.kicad_sch
kicad-cli sch export pdf|svg -o out board.kicad_sch
```

- Generated BOM fields: `${QUANTITY}`, `${ITEM_NUMBER}`, `${DNP}`, `${FOOTPRINT_NAME}`
  (footprint without the library prefix), `${FOOTPRINT_LIBRARY}`.
- `--fields` and `--labels` are comma-separated and paired by position.

## Jobsets

`kicad-cli jobset run -f fab.kicad_jobset project.kicad_pro` runs an output job list
saved from the KiCad project manager (10.0). Useful when the user already maintains one.
Otherwise `kicad.py fab` is simpler.
