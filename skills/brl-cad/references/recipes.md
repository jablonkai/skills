# Recipes

All snippets are `.mged` scripts for `brl.py build`, and were run on BRL-CAD 7.44.0.
`BRL` is `<skill>/scripts/brl.py`.

## 1. Mechanical part → three views

```tcl
units mm
title Flanged bushing
in flange.rcc rcc 0 0 0   0 0 6   30
in body.rcc   rcc 0 0 6   0 0 24  16
in bore.rcc   rcc 0 0 -1  0 0 32  10
in chamf.trc  trc 0 0 29  0 0 1.01 10 11      ;# 1 mm 45° chamfer at the bore mouth
for {set i 0} {$i < 4} {incr i} {
  set a [expr {$i*90*acos(-1)/180}]
  in bolt$i.rcc rcc [expr {23*cos($a)}] [expr {23*sin($a)}] -1 0 0 8 2.75
}
r bushing.r u flange.rcc - bore.rcc - bolt0.rcc - bolt1.rcc - bolt2.rcc - bolt3.rcc \
            u body.rcc - bore.rcc - chamf.trc
mater bushing.r plastic 180 180 190 0
attr set bushing.r material_id 3
g bushing bushing.r
```

```bash
python3 $BRL build bushing.mged -o bushing.g --fresh
python3 $BRL overlaps bushing.g bushing
python3 $BRL render bushing.g bushing -o renders --views front,top,iso
```

- A trailing `\` continues a command onto the next line, as it does in Tcl.
- Write each subtraction once per `u` term that the cutter crosses. A cutter only removes
  material from the term it follows.

## 2. Assembly of several parts

One region per physical part, grouped. Parts that touch must not overlap. Where a shaft
passes through a plate, the plate needs a hole.

```tcl
units mm
in plate.rpp rpp -40 40 -40 40 0 8
in shaft.rcc rcc 0 0 -20 0 0 60 6
in hole.rcc  rcc 0 0 -1 0 0 10 6               ;# same radius as the shaft = press fit
r plate.r u plate.rpp - hole.rcc
r shaft.r u shaft.rcc
mater plate.r plastic 120 120 130 0
mater shaft.r plastic 220 180 40 0
attr set plate.r material_id 3
attr set shaft.r material_id 1
g assembly plate.r shaft.r
```

`overlaps` should print `No overlaps`. If the hole were smaller than the shaft, gqa would
report `/assembly/plate.r x /assembly/shaft.r` with the interference depth.

## 3. Find and fix an overlap

```bash
python3 $BRL overlaps model.g model          # exit 2:
#   /model/bolt.r  x  /model/bracket.r  rays:220  longest overlap along a ray:10mm  first at (5 0 1)
python3 $BRL tree model.g bolt.r bracket.r   # see what each region is made of
```

Decide who owns the shared space, then edit with a small script against the existing
`.g`. Don't use `--fresh` here: that would start from an empty database.

```tcl
# bracket gets a clearance hole where the bolt passes
in bolt_clear.rcc rcc 5 5 -1 0 0 12 3.2
kill bracket.r
r bracket.r u bracket.rpp - bolt_clear.rcc
mater bracket.r plastic 200 40 40 0          ;# kill dropped colour and material: set them again
attr set bracket.r material_id 3
```

```bash
python3 $BRL build fix.mged -o model.g      # warns if a line would append
python3 $BRL overlaps model.g model          # -> No overlaps
python3 $BRL mass model.g model              # volume changed by about the overlap only
```

- `kill` + `r` keeps the region's name. The group that referenced `bracket.r` picks up
  the new one automatically, because combinations reference by name.
- The other fix is to move a part: `kill part.rpp`, then `in part.rpp rpp …` with
  corrected coordinates.

## 4. Mass with materials

```bash
python3 $BRL mass model.g plate.r shaft.r --density <skill>/assets/example.density
# Recipe 2 measured: plate.r 50297 cu mm / 135.802 g (analytic 50295), shaft.r 6772.24 cu mm / 53.16 g
python3 $BRL mass model.g model -u "mm,cu cm,kg" --density materials.density
```

- List several objects to get per-part numbers and a total. `brl.py` runs gqa once per
  object, because objects sharing one gqa run were measured 1% off.
- Every region must have a `material_id` that exists in the file, otherwise gqa stops with
  a density error.

## 5. Export for 3D printing

```bash
python3 $BRL overlaps part.g part                       # must be clean first
python3 $BRL export part.g part -o part.stl -b --merge --abs-tol 0.05
# widget.stl (36084 bytes, 720 triangles, binary, size 59.906 x 59.906 x 44.000 mm, watertight, merged into one shell)
python3 $BRL export asm.g asm -o stl_parts --per-region  # one STL per region
python3 $BRL export part.g part -o part.step             # facetized STEP, see gotchas
```

- Check that the size matches the design (STL is mm). Most slicers assume mm.
  - The default tessellation made the Ø60 flange 59.49 mm across the flats.
  - `--abs-tol 0.05` (max 0.05 mm chord error) gave 59.91 mm.
- `--merge` evaluates the union of every region (`facetize`) into one closed shell,
  using a scratch copy, so your `.g` is not touched. Without it, a base, post and cap
  that touch export as three shells with internal faces, which slicers can mishandle.
- `watertight` is required for printing. "NOT watertight" usually means:
  - coincident faces from a cutter that ended flush, or
  - two regions overlapping inside one STL.
  Fix the model rather than the mesh.

## 6. Editing an existing `.g` you didn't write

```bash
python3 $BRL tree model.g                 # tops, units
python3 $BRL tree model.g some_assembly   # its boolean tree
mged -c model.g "l some.r"                # one object (a single command is safe as args)
```

- Then write a small edit script and run `build` without `--fresh`.
- Keep a copy (`cp model.g model.orig.g`). `.g` files have no undo.

## 7. Patterns (bolt circles, arrays)

```tcl
set n 8; set r 40; set d 6
for {set i 0} {$i < $n} {incr i} {
  set a [expr {2*acos(-1)*$i/$n}]
  in h$i.rcc rcc [expr {$r*cos($a)}] [expr {$r*sin($a)}] -1  0 0 12  [expr {$d/2.0}]
}
# subtract them all: build the operator list in Tcl
set terms {u disk.rcc}
for {set i 0} {$i < $n} {incr i} { lappend terms - h$i.rcc }
eval r disk.r $terms
```

`clone -n 4 -t 25 0 0 obj` also makes linear arrays. Its copies are named `obj100`,
`obj200`, and so on.
