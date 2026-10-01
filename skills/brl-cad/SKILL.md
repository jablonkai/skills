---
name: brl-cad
description: 'Model CSG solids and analyse them with BRL-CAD from the CLI: write mged command scripts for primitives (rpp, rcc, sph, tor, trc, arb8 …), boolean regions and combinations, materials and colours; raytrace PNG views with rt; check overlaps, volume and mass with gqa; export STL/OBJ/STEP for printing or other CAD. Use for "model this part in BRL-CAD", "build a CSG model in a .g file", "write an mged script", "raytrace / render this .g from three views", "check this BRL-CAD model for overlaps" or "fix the gqa overlaps", "volume / mass of this region in aluminium", "export the .g to STL for 3D printing", "convert .g to OBJ or STEP". Not for sketch-and-pad parametric CAD or FreeCAD files (freecad), mesh/polygon modelling, sculpting or Blender renders (blender), OpenSCAD code, slicing STL for a printer, or 2D diagrams (drawio).'
summary: "model CSG solids headless with BRL-CAD — mged command scripts for primitives, boolean regions and materials, rt raytraced views, gqa overlap, volume and mass checks, STL/OBJ/STEP export"
category: cad
risk: low
tags:
    - brl-cad
    - cad
    - csg
    - mged
    - raytrace
    - stl
---

# BRL-CAD via headless scripts

BRL-CAD is driven by **short-lived CLI processes**. There is no GUI, server or bridge.

- Geometry is written as an **mged command script** (`.mged`, plain Tcl, one command
  per line) and built into a binary `.g` database.
- [scripts/brl.py](scripts/brl.py) wraps the tools: `mged`, `rt`, `gqa` and
  `g-stl`/`g-obj`/`g-step`.

**Use `brl.py`, not the raw tools.** BRL-CAD's own exit codes almost never signal
failure:

- `mged` exits 0 on unknown commands and missing objects.
- `gqa` exits 0 when it finds overlaps.
- `g-stl` exits 0 after writing an empty file.

`brl.py` reads each tool's log and turns it into an exit status (0 ok, 1 failed,
2 overlaps found, 3 setup error or timeout). It also reports which script line failed.

Verified against **BRL-CAD 7.44.0** (official arm64 DMG) on macOS 27. Run `brl.py` with
the system `python3`; it needs only the stdlib.

## Commands

```bash
BRL=<this skill>/scripts/brl.py
python3 $BRL find                                   # bin dir + version (installs: see gotchas.md)
python3 $BRL build part.mged -o part.g --fresh      # run script; errors listed by line
python3 $BRL tree part.g [obj]                      # title, units, tops, boolean tree
python3 $BRL render part.g obj -o renders/ [--views front,right,top,iso] [-s 512] [--prefix '']
python3 $BRL overlaps part.g obj [-g 1mm,0.25mm]    # exit 2 if any overlap
python3 $BRL mass part.g obj [--density file.density]   # volume, + weight per region
python3 $BRL export part.g obj -o part.stl [-b] [--merge] [--abs-tol 0.05]   # also .obj / .step
```

- `--json` on `build`, `render`, `overlaps`, `mass` and `export` gives machine-readable
  output.
- `--timeout S` goes **before** the subcommand. Default 600 s; on timeout the tool's whole
  process group is killed.
- Views:
  - `front`: X right, Z up
  - `right`: Y right, Z up
  - `top`: X right, Y up
  - `iso`: the MGED 35/25 view
  - also `back`, `left`, `bottom` and `iso2`
  - any `AZ/EL` pair such as `30/20`
  - Renders have a white background and are checked for not being blank.
  - Files are named `<prefix>_<view>.png`; `--prefix ''` gives plain `front.png`.
- `export` facts:
  - STL is always in **mm**.
  - It reports triangle count, size and **watertightness** (open or non-manifold edges).
  - STEP is written from a facetized copy, because g-step crashes on any CSG subtraction
    in 7.44. See [references/gotchas.md](references/gotchas.md).

## Workflow

1. **Write the `.mged` script.** Begin with `units mm` and `title …`, then:
   - one `in` per primitive
   - one `r` per solid part (region)
   - `mater` / `attr set … material_id` for colour and density
   - `g` to group everything into one top object

   Start from [assets/bracket.mged](assets/bracket.mged).
2. **`build --fresh`.** `--fresh` matters when re-running a script: `r`, `comb` and `g` on
   an existing name *append* members rather than replacing them, so a second run would
   duplicate every boolean term. `--fresh` moves the old `.g` aside to `.g.bak`.
   - To edit an existing `.g` in place, write a script that `kill`s the region before
     re-creating it. `build` warns when a line would append.
3. **`tree`** to confirm the boolean structure is what you meant.
4. **`overlaps`** on the top object. Two regions claiming the same space is a modelling
   error in BRL-CAD: it makes volumes, masses and exports wrong. Fix every overlap before
   step 5.
5. **`mass`** and/or **`render`**. Look at the PNGs: render coverage proves something was
   drawn, but only your eyes prove it is the *right* thing (holes through, boss on top).
6. **`export`**, if asked.
   - For printing, use `--merge --abs-tol 0.05`. `--merge` unions all regions into
     **one shell**; without it, regions that touch export as separate shells with
     internal faces. The default tessellation is coarse: a Ø60 cylinder came out 59.5 mm.
   - Require `watertight` in the output.
7. **Report** the `.mged` and `.g` paths, the region list, overlap status, volume or mass
   with the grid used, and the output files.

## Modelling essentials

```tcl
units mm
in plate.rpp rpp 0 100 0 60 0 10          ;# box: xmin xmax ymin ymax zmin zmax
in hole.rcc  rcc 50 30 -1  0 0 12  5      ;# cylinder: base V, height vector H, radius
r  plate.r u plate.rpp - hole.rcc         ;# region = one solid part
mater plate.r plastic 200 40 40 0         ;# shader R G B inherit
attr set plate.r material_id 3            ;# row in the density table
g  model plate.r                          ;# assembly / top-level group
```

- **Booleans:**
  - `u` (union), `-` (subtract) and `+` (intersect) bind left to right inside each `u`
    term.
  - So `u A - B u C - D` is `(A−B) ∪ (C−D)`.
  - Start every region with `u`.
- **Cutters must poke through.** Extend holes 1 mm past both faces (`z` from −1 to
  `t+1`). Coincident faces give raytrace speckle and broken meshes.
- **Regions are the solid parts.** Each region has one material and is never nested
  inside another region. Groups (`g`) and combinations (`comb`) assemble regions. Every
  region must occupy its own space: where a pin goes through a plate, subtract the pin
  from the plate.
- **Names:** use the suffixes `.s`/`.rpp`/`.rcc` for primitives, `.r` for regions, and no
  suffix for groups. Names must be unique in the `.g`.
- **Tcl loops work** in scripts run through `build`, for example a bolt circle:

```tcl
for {set i 0} {$i < 6} {incr i} {
  set a [expr {$i*60*acos(-1)/180}]
  in bolt$i.rcc rcc [expr {50+30*cos($a)}] [expr {50+30*sin($a)}] -1 0 0 12 3
}
```

Every primitive and its argument order, plus the editing commands (`kill`, `mv`, `cp`,
`l`, `tops`, `attr`, `edcodes`, `mirror`, `xpush`): see
[references/mged-commands.md](references/mged-commands.md).

## Fixing overlaps

`overlaps` names each pair (`/asm/b.r x /asm/a.r`), the longest overlapping ray segment,
and a point inside the overlap. Then decide which region owns the shared space:

- **Subtract the overlapping solid from the region that should lose it:** `kill b.r`,
  then `r b.r u b.rpp - a.rpp`. Use this when one part genuinely sits in a pocket of the
  other.
- **Move or resize the primitive** when the overlap is a dimension mistake. Use `kill`
  then `in` with the corrected args.
- Never delete a region just to silence the report.

Re-run `overlaps` until it prints `No overlaps`, then re-check `mass`. A fix should change
the total volume by roughly the overlap volume, not by a whole part.

## References

- [references/mged-commands.md](references/mged-commands.md): primitives with argument
  order, booleans, the region/comb/group rules, material and attribute commands, and the
  inspection/edit commands.
- [references/analysis.md](references/analysis.md): `rt` options and views, `gqa`
  analyses and grid choice, density files, `nirt` ray queries, and the export
  tolerances.
- [references/recipes.md](references/recipes.md): a mechanical part, an assembly,
  patterns, the overlap fix, mass with materials, export for printing, and editing an
  existing `.g`.
- [references/gotchas.md](references/gotchas.md): exit codes, argument joining, append on
  `r`, the g-step crash, the gqa grid, density paths, install, and the security posture.
