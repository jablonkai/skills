# Gotchas (BRL-CAD 7.44.0, macOS arm64)

Everything here was measured on this install. Where the manual differs, these
observations win.

## Install

- There is no Homebrew formula or cask. Use the official DMG from
  <https://github.com/BRL-CAD/brlcad/releases>, e.g.
  `BRL-CAD_7.44.0_macOS13.0_arm64.dmg` (arm64, macOS 13+, about 190 MB):

  ```bash
  gh release download -R BRL-CAD/brlcad -p '*arm64.dmg'
  hdiutil attach -nobrowse -readonly BRL-CAD_*.dmg
  ditto "/Volumes/BRL-CAD 7.44.0/BRL-CAD_7.44.0.app" /Applications/BRL-CAD_7.44.0.app
  hdiutil detach "/Volumes/BRL-CAD 7.44.0"
  ```

- The CLI tools are in `BRL-CAD_<ver>.app/Contents/Resources/brlcad/bin` (323 of them),
  which is **not on PATH**.
  - `brl.py find` locates the newest app bundle.
  - `BRLCAD_BIN=/path/to/bin` overrides it.
  - Linux `/usr/brlcad/…` installs are found too.
- The MGED and Archer **GUIs** need XQuartz. **None of the CLI tools do**, including
  `mged -c`, `rt -o`, `gqa` and the converters.
- Man pages: `man -M <app>/Contents/Resources/brlcad/share/man gqa`.

## Exit codes lie

| Tool | Exits 0 even when |
|---|---|
| `mged -c` | the command is unknown, an `in` failed, an object is missing, a region skipped members |
| `gqa` | overlaps were found, or the object does not exist |
| `g-stl` | the object does not exist ("0 triangles written", empty file) |
| `g-obj` | the object does not exist (writes a header-only OBJ) |

- `rt` (exit 1 on "No primitives remaining") and a missing `.g` file are the exceptions.
- `brl.py` decides success from the log and the output files instead. Don't script the raw
  tools with `&&` chains.

## mged script traps

1. **Multiple arguments are joined into one command.** `mged -c db.g "kill a" "r a u x"`
   runs `kill a r a u x`, which deletes `a`, `r`, `u` and `x`. A single command as
   arguments is safe. Put several commands in a script and run it with `brl.py build`.
2. **Piping a script to stdin is fragile.**
   - mged backslash-escapes `[`, so `[expr …]` and other Tcl substitution break.
   - An `in` with too few arguments **swallows the next line(s)** as its missing values.
   - `brl.py build` avoids both by `source`-ing a driver that `catch`es each command.
3. **`r`/`comb`/`g` append** to an existing combination. Re-running a script doubles every
   boolean term, and nothing errors. `build --fresh` (old `.g` → `.g.bak`) or `kill` first.
4. **Missing members are skipped, and the combination is still created.**
   `r x.r u a - typo` makes `x.r = a` and prints `skipping typo`. `build` reports it as
   an error.
5. **`in` won't overwrite**: you get `in: NAME already exists`. Run `kill NAME` first.
6. **`edcodes`, `red` and `ted` open `$EDITOR`** (nano) and block. Use `attr set`.
7. **`kill` drops everything about the object.** Recreating a region with `r` gives it a
   new region_id, the default material_id 1 and no shader. Reapply `mater` and
   `attr set`.
8. **A malformed primitive can segfault mged.** Seen once with a bad `pipe`. `build`
   reports the line it died on, and nothing after that line ran.
9. **Tcl comments**: `#` only starts a comment at the beginning of a command. Inline, use
   `;#`.

## Analysis traps

- **gqa without `-g`** keeps halving the grid down to µm. It took 13 s on a 100 mm part,
  and large models effectively never finish. `brl.py` always passes a grid.
- **gqa volume stops refining too early** with its default `-V` tolerance: 4 % high on a
  plain plate. Listing several objects in one run also biased one by 1 %. `brl.py mass`
  passes `-V 1e-6 -W 1e-6` and runs one object per process. Error is now ≤ 0.02 % on
  test parts.
- **Flush contact can show up as an overlap** on a round gqa grid, because rays lie in the
  shared face. `brl.py overlaps` uses an off-round grid to avoid this. If you pass `-g`
  yourself, avoid round values, and treat a low-count overlap whose `@` point is on a
  contact plane as suspect. Details in analysis.md.
- **gqa `dist:` is not the overlap depth.** It is the longest overlapping ray segment.
  A 5 mm deep interference of a 20 mm block reads `dist:20mm`.
- **Overlaps make volume and weight meaningless.** In a test, a 1000 mm³ box overlapping
  another reported 499.7 mm³. Fix overlaps first. `mass` warns when gqa mentions them.
- **Weight needs densities.**
  - Without them gqa prints "Could not find any density information".
  - `gqa -f FILE` reads a density file; `brl.py mass --density FILE` uses it.
  - `-d` is a debug flag, not density.
  - A region's `material_id` (default 1) picks the row.
- **`mater -d import` needs an absolute path.** A relative one silently imports nothing.
- **`bb` ignores cuts.** It reports primitive bounds, so a half-space trim or a
  subtraction does not shrink it. For the true extent, use the exported STL bbox.
- **nirt** rays at exactly `el ±90` miss everything. Use `89.99`.

## Export traps

- **`g-step` segfaults on any boolean subtraction** (rc 139) and leaves a truncated file
  that looks plausible. Unions alone work.
  - `brep REGION brep` followed by g-step does not crash, but it produced **wrong
    geometry**: FreeCAD read no solid and 39 840 instead of 60 188 mm³.
  - `brl.py export … .step` therefore facetizes into a scratch copy of the `.g` and
    exports the BoT. FreeCAD read that as 1 valid solid, 60 186 mm³, exact bbox.
  - The STEP is faceted (planar triangles), not exact NURBS. Say so when you deliver it.
    `--csg-step` forces the direct route for union-only models.
- **`g-stl -n` (normal tolerance) can hang** at some values (5°, 15°). Use `-a`/`--abs-tol`.
- **Default tessellation is coarse.** A Ø60 cylinder came out 59.49 mm across the flats.
  For printing, use `--abs-tol 0.05`.
- STL is always mm, whatever `units` the database uses.
- **Touching regions export as separate shells** with internal faces where they meet.
  For a printable single body, use `export --merge`, which runs `facetize` into one BoT
  in a scratch copy, with `tol abs` defaulting to 0.05 mm.
- One STL of several regions that **overlap** has non-manifold edges. Fix the overlaps,
  or export `--per-region`.

## rt

- The default background is near-black (0/0/1). `brl.py render` passes `-W` (white),
  and `--bg r/g/b` changes it.
- rt auto-frames the bounding box of the listed objects, so a tiny part fills the image
  just like a large one. State the size in words when reporting.
- A completely blank image (object not in view, or wrong object) is caught by the
  coverage check (< 0.5 % non-background pixels).

## Security posture

- **No bridge.** Nothing listens on a socket or port, so there is no cross-origin or
  token surface (repo issues #17, #32).
- Scripts run through `build` execute **arbitrary Tcl inside mged** with the user's
  rights, including `exec` and file I/O. Only build scripts you wrote or have read. Treat
  a `.mged` from elsewhere like a shell script.
- `brl.py` writes only:
  - the `.g` you name
  - `.g.bak` (with `--fresh`)
  - the render or export paths you name
  - temporary Tcl/`.g` files in the system temp dir, which it deletes afterwards
- **Stop path** (#35): every BRL-CAD process runs in its own process group with
  `--timeout` (default 600 s). On timeout or Ctrl-C the whole group is killed, so no
  stray `rt`/`gqa`/`g-stl` keeps spinning.
