# Rendering, analysis and export (BRL-CAD 7.44)

`brl.py` wraps all of these. Use the raw tools only for options it does not expose. The
binaries live in `/Applications/BRL-CAD_<ver>.app/Contents/Resources/brlcad/bin`
(`brl.py find`).

## rt — raytraced images

```bash
rt -s512 -W -a 35 -e 25 -o iso.png model.g obj1 obj2
```

| Option | Meaning |
|---|---|
| `-s N` / `-w W -n H` | square size / width and height in pixels |
| `-a AZ -e EL` | view azimuth/elevation in degrees (see the table below) |
| `-W` / `-C r/g/b` | white / custom background. The default is near-black `0/0/1`. |
| `-p FOV` | perspective with this field of view (default is orthographic) |
| `-A 0.6` | ambient light (0.4 default); raise it for darker shaded sides |
| `-R` | do not report overlaps |
| `-c "set ..."` | extra commands, e.g. `-c "set ambSlow=1"` |
| `-o file.png` | output; `.png` writes PNG, `.pix` raw |

- The view auto-frames the objects' bounding box, so the model fills the image.
- rt prints `OVERLAP1:`/`OVERLAP2:` blocks for every overlapping ray. `brl.py render`
  counts them and warns.
- `rt` exits 1 with `No primitives remaining` when no object name matched. This is the one
  tool whose exit code is honest.

View presets in `brl.py render --views`, measured on 7.44:

| Preset | az / el | Image shows |
|---|---|---|
| `front` | 270 / 0 | looking along +Y: X right, Z up |
| `back` | 90 / 0 | -X right, Z up |
| `right` | 0 / 0 | looking along -X: Y right, Z up |
| `left` | 180 / 0 | -Y right, Z up |
| `top` | 270 / 90 | X right, Y up |
| `bottom` | 270 / -90 | X right, -Y up |
| `iso` | 35 / 25 | MGED default view, from +X+Y above |
| `iso2` | 305 / 25 | from +X-Y above (front-right-top) |

Other renderers in the same bin directory:

- `rtedge`: edge/line drawing.
- `rthide`: hidden-line.
- `rtwizard`: composite.
- `rtxray`: X-ray density.
- `rtsil`: silhouette.
- `rtarea`: presented area.
- `rtweight`: weight via rays. Not needed, because gqa does weight.

## gqa — geometry quality analysis

```bash
gqa -Ao -g 1mm,0.25mm model.g asm          # overlaps
gqa -Av -g 1mm,0.25mm -u mm,"cu mm",grams model.g asm
gqa -Avw -f /abs/materials.density -g 1mm,0.25mm model.g asm
```

| `-A` letter | Analysis |
|---|---|
| `o` | overlaps: `/a.r /b.r count:N dist:Dmm @ (x y z)`; count = rays, dist = longest overlapping ray segment in any of the 3 directions (not the thickness: a 5 mm deep interference of a 20 mm block reads `dist:20mm`), @ = a point inside |
| `v` | volume per listed object, plus total |
| `w` | weight; needs densities (`-f file` or a table in the `.g`) |
| `e` | exposed air |
| `g` | gaps between regions |
| `a` / `b` | adjacent air / bounding box |

- **Always pass `-g upper,lower`.** gqa shoots a grid of rays from three directions and
  halves the spacing until the results converge or the lower limit is reached. With no
  `-g`, it refined a 100 mm part to 0.003 mm and took 13 s; a large model can take hours.
  - `brl.py` derives the grid from the largest bbox side L, rounded to 1-2-5:
    - `overlaps` uses `L/50, L/200`, scaled by 0.9871.
    - `mass` uses `L/50, L/1000`, unscaled.
- **Round grids report flush contact as overlap.**
  - The grid starts at the bbox minimum. With round spacing and round coordinates, some
    rays run exactly *in* a shared face.
  - Example: a pin standing on a plate at z=10 gave
    `pin.r plate.r count:10 dist:6mm @ (77 30 10)` at `-g 1mm,0.1mm`. That is a zero-volume
    false positive.
  - Hallmarks: a small `count`, and an `@` point lying on the contact plane.
  - Re-check with an off-round grid such as `-g 0.913mm,0.1141mm`. A real interference
    survives it.
  - Overlaps thinner than `lower` can be missed. Use a finer grid when parts are thin
    or close-fitting.
- **gqa's own convergence test stops too early for volume.**
  - It stops once two grids agree within `-V` (default ≈ 0.1 % of the bbox volume).
    On an 80×80×8 plate that happened at 1 mm and read **4 % high**.
  - Pass a tiny `-V 1e-6 -W 1e-6` so it refines to the lower limit. `brl.py mass` does
    this.
  - **Measure one object per gqa run.** Listing a plate and a shaft together read the
    plate 1 % high. Alone it was exact. `brl.py mass` loops.
  - Measured with these settings, all under 1 s each:
    - plate 50 297 vs 50 295 mm³
    - bracket 60 191 vs 60 188 mm³
    - bushing 26 236 vs 26 239 mm³
    - 8-hole disk 110 814 vs 110 835 mm³
- `-t 0.01mm` ignores overlaps thinner than the tolerance. Use it only when you understand
  where those overlaps come from (e.g. tessellation noise in imported BoTs).
- **Volumes and weights are wrong while overlaps exist.** In a test, a 1000 mm³ region
  that overlapped another reported 499.7 mm³. Fix overlaps first.
- `-u length,volume,weight` sets the report units, e.g. `mm,cu cm,kg` or `in,cu in,lb`.
- Exit code is 0 whether or not overlaps were found. `brl.py overlaps` exits 2 when it
  finds them.

## Density files

```text
# id  g/cm3   name
1     7.85    Steel, mild
3     2.70    Aluminium 6061-T6
9     1.24    PLA
```

- Each region's `material_id` attribute selects a row. New regions default to
  `material_id 1`, so set it explicitly: `attr set part.r material_id 3`.
- `gqa -f /abs/path.density` (or `brl.py mass --density`) reads the file without touching
  the `.g`.
- To store the table inside the `.g`, run `mater -d import /abs/path.density`. A relative
  path silently imports nothing.
- `mater -d get --all` lists the stored table. Stored values are printed in g/mm³ (7.85 →
  0.00785).
- Samples: [assets/example.density](../assets/example.density), and
  `share/data/GQA_SAMPLE_DENSITIES` in the install.

## nirt — single ray queries

```bash
nirt -b -e "ae 0 0; xyz 20 30 5; s; q" model.g bracket < /dev/null   # ray along -X through y=30 z=5
```

This prints one line per region segment along the ray, with the entry point and the LOS
thickness. Use it to measure a wall, confirm a hole goes through (a gap between
segments), or locate an overlap reported by gqa. Quirks:

- nirt keeps reading commands from stdin after `-e`, so in a script it **hangs** unless
  you end with `; q` and redirect `< /dev/null`.
- In the bracket example the ray from +X gave segments `100→90`, `80→54`, `46→20` and
  `10→0`, so the holes and bore show up as gaps.
- **Rays at exactly `el 90` or `-90` miss everything in 7.44.** For vertical shots use
  `ae 0 89.99`, and check the result.
- Vertical shots at 89.99 report only the part of the ray above the `xyz` point. Put
  `xyz` below the object, i.e. at `zmin − 1`, to get the whole depth.

## Converters

| Tool | Notes |
|---|---|
| `g-stl -o f.stl db.g obj` | ASCII STL; `-b` binary; `-m DIR` writes one STL per region (`asm@a_r.stl`). Units are **mm**, always. |
| `g-obj -o f.obj db.g obj` | Wavefront OBJ, one group per region |
| `g-step -o f.stp db.g obj` | **Segfaults on any boolean subtraction in 7.44** and leaves a truncated file. Run it on a facetized BoT (`brl.py export … .step`) |
| `g-iges`, `g-dxf`, `g-vrml`, `g-x3d`, `g-ply`, `g-off` | other formats, same `-o out db.g obj` shape |
| `stl-g`, `obj-g`, `step-g`, `gcv` | import into a `.g`; imports are BoTs (meshes), not CSG |

**Tessellation tolerances** (`g-stl`/`g-obj`, and `brl.py export` flags):

- `-a` (`--abs-tol`) is the max distance in mm between the true surface and the facets.
  **Use this one.** The default turned a Ø60 cylinder into 59.49 mm across the flats,
  and `--abs-tol 0.05` gave 59.91 mm with 1 120 triangles in 0.3 s.
- `-r` (`--rel-tol`) is the same as a fraction of the object size. 0.001 took 3 s and
  gave 2 176 triangles.
- `-n` (`--norm-tol`) is the max angle in degrees between adjacent facet normals. **It
  hangs g-stl at some values in 7.44:** 5° and 15° spun at 100 % CPU until killed, while
  10° finished. Avoid it, or keep a `--timeout`.

**Export checks** done by `brl.py export`:

- STL: triangle count, bbox size, and watertightness (each edge shared by exactly two
  triangles). A single STL of several touching regions is still watertight per region.
  Regions that *overlap* give non-manifold edges.
- OBJ: vertex and face counts.
- STEP: header and `END-ISO-10303-21;` trailer (catches the g-step crash), face count.
