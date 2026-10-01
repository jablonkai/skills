# mged command cheat sheet (BRL-CAD 7.44)

Every argument order below was checked with `l <name>` on 7.44.0. Lengths are in the
database's `units` (set `units mm` first). Vectors are three numbers. Run scripts through
`brl.py build`, which reports errors by line. Full manual:
`man -M <brlcad>/share/man mged` or `man -M <brlcad>/share/man in`.

## Primitives — `in NAME TYPE args…`

| Type | Args | Shape |
|---|---|---|
| `rpp` | xmin xmax ymin ymax zmin zmax | axis-aligned box |
| `box` | V  Hvec  Wvec  Dvec | box from a corner and 3 edge vectors (stored as ARB8) |
| `arb8` | 8 points (bottom face 1-4, then top 5-8) | general hexahedron, convex |
| `arb7` / `arb6` / `arb5` / `arb4` | 7 / 6 / 5 / 4 points | wedge-like solids (arb6 = triangular prism, arb5 = pyramid, arb4 = tetrahedron) |
| `rcc` | V  Hvec  r | right circular cylinder: base centre, axis vector (length = height), radius |
| `trc` | V  Hvec  r_base r_top | truncated cone; r_top 0 for a cone |
| `rec` | V  Hvec  Avec  Bvec | elliptical cylinder; A, B semi-axes ⟂ H |
| `tgc` | V  Hvec  Avec  Bvec  c d | general cone: base ellipse A,B; top semi-axes c, d (scalars) |
| `sph` | V  r | sphere |
| `ell` | V  Avec Bvec Cvec | ellipsoid from 3 ⟂ semi-axis vectors |
| `ell1` | V  Avec  r | ellipsoid of revolution about A |
| `tor` | V  Nvec  r1 r2 | torus: N normal, r1 centre-ring radius, r2 tube radius |
| `eto` | V  Nvec  r  Cvec  d | elliptical torus |
| `half` | Nvec  d | half-space: everything *behind* the plane N·x = d (N points outward) |
| `rpc` | V  Hvec  Bvec  r | right parabolic cylinder |
| `rhc` | V  Hvec  Bvec  r  c | right hyperbolic cylinder |
| `epa` | V  Hvec  Avec  r2 | elliptical paraboloid |
| `ehy` | V  Hvec  Avec  r2  c | elliptical hyperboloid |
| `hyp` | V  Hvec  Avec  b  neck_ratio | hyperboloid of one sheet |
| `part` | V  Hvec  r_v  r_h | particle: sphere-capped cone (rounded rod/pin) |
| `pipe` | N  then N × (x y z  **ID  OD**  bend_r) | swept tube; inner diameter first, `bend_r` ≥ OD/2; ID 0 for a solid rod |

- `half` is unbounded. Only use it inside an intersection (`+`) or a subtraction (`-`),
  never as the first `u` term of a region.
- Arb point order: go round the bottom face, then the top face in the same order. Faces
  must be planar and the solid convex, or rt shows holes.
- `pipe` input mistakes are errors, but a malformed pipe once segfaulted mged in testing.
  `build` names the line it died on.
- `in` refuses an existing name ("already exists"). Use `kill name` first, or a new name.

## Regions, combinations, groups

```tcl
r   part.r  u base.rpp - hole.rcc + clip.half   ;# region: one solid part, one material
comb asm.c  u part.r u other.r                  ;# combination (not a region)
g   model   asm.c bolts                          ;# group = union of members
```

- **Operators:**
  - `u` is union, `-` is subtract, `+` is intersect.
  - Precedence: `-` and `+` bind to the nearest preceding `u`, and the `u` terms are
    unioned. So `u A - B + C u D` = `((A−B)∩C) ∪ D`.
- **Region rules** (BRL-CAD's data model, which gqa, rt and the exporters all rely on):
  - Leaf geometry lives only in regions.
  - A region may not contain another region.
  - Regions must not overlap.
  - Each region carries one `material_id`, `region_id` and shader.
- **Appending:** `r`, `comb` and `g` *add* to an existing combination. Re-running a
  script duplicates terms, and `build` warns about it. Kill first, or `build --fresh`.
- A missing member is **skipped**: `r` prints `skipping X` and `g` prints
  `skip member X`, yet the object is still created. `build` reports both as errors.
- Region ids are auto-assigned (1000, 1001, …). Change them with
  `attr set R region_id N`.

## Materials, colour, attributes

```tcl
mater part.r plastic 200 40 40 0          ;# shader R G B inherit(0|1)
mater part.r "plastic {sp .7 di .3}" 0 120 255 0
attr set part.r material_id 3             ;# density table row (see analysis.md)
attr set part.r region_id 2001 los 100
attr show part.r
attr set model description "Rev B bracket"
```

- Shaders:
  - `plastic`: the default.
  - `mirror`
  - `glass`
  - `light`: an emitter.
  - `checker`
  - `cloud`
  - `stack`
  - `bump`
  - `texture`: needs image files.
- **Don't use `edcodes` or `red` in scripts.** With arguments, they open `$EDITOR` (nano)
  and block until the timeout. Use `attr set` instead.
- Density table inside the `.g`: `mater -d import /ABS/path/file.density`. A relative
  path silently fails. Not needed for `brl.py mass`, which passes the file to gqa.

## Inspect

| Command | Prints |
|---|---|
| `tops` / `tops -n` | top-level objects (not referenced by anything) |
| `ls` / `ls -c` / `ls -r` / `ls -s` | all / combinations / regions / primitives |
| `l NAME` | full parameters of a primitive, or the members of a comb |
| `tree NAME` | indented boolean tree (`brl.py tree`) |
| `bb -q NAME` | bounding-box lengths and volume; uses primitive bounds, so it ignores cuts (a `half` or subtraction does not shrink it) |
| `title` / `units` | database title, editing units |
| `search . -type region` | find-like queries (`-name '*.r'`, `-attr material_id=3`) |

## Edit

| Command | Effect |
|---|---|
| `kill A B` | delete objects (references to them dangle → `killrefs`) |
| `killtree C` | delete a combination and everything below it that nothing else uses |
| `killrefs A` | remove A from every combination that references it |
| `mv OLD NEW` | rename (`mvall` also renames references) |
| `cp SRC DST` | copy one object |
| `mirror SRC DST x\|y\|z` | mirrored copy across the plane through the origin |
| `clone -n 4 -t 25 0 0 SRC` | 4 translated copies, each 25 mm further, named `SRC100`, `SRC200`, … (deep-copies the tree) |
| `rm COMB MEMBER` | remove a member from a combination |
| `xpush COMB` | push matrices down to the leaves (before export or edit) |
| `facetize OUT.bot OBJ` | evaluate the CSG to a triangle mesh (BoT) |

Moving or rotating a primitive by editing it numerically is easiest by `kill` and then
`in` with new coordinates. For a whole assembly, put members in a combination and use
`arced`, `oed`, or `clone -t`/`-r`.
