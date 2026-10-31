# Recipes (checked against SolidCraft 0.28.0)

In the commands below, `S=<skill>/scripts`. Every recipe states its expected volume,
worked out by hand before building. `sc_run.py --expect-volume` turns that number into
a check.

## 1. Parametric plate with corner holes and edge fillets

A 60×40×10 plate with four Ø4 holes 6 mm in from each edge and r3 rounds on the four
vertical corners.

```json
{"commands":[
 {"command":"parameters.add","params":{"name":"thickness","expression":"10 mm"}},
 {"command":"sketch.create","params":{"plane":"XY","name":"Outline"}},
 {"command":"sketch.rectangle.two_point","params":{"p0":[0,0],"p1":[60,40]}},
 {"command":"sketch.circle.center","params":{"center":[6,6],"diameter":4}},
 {"command":"sketch.circle.center","params":{"center":[54,6],"diameter":4}},
 {"command":"sketch.circle.center","params":{"center":[54,34],"diameter":4}},
 {"command":"sketch.circle.center","params":{"center":[6,34],"diameter":4}},
 {"command":"sketch.finish","params":{}},
 {"command":"solid.extrude","params":{"distance":"thickness","body_name":"Plate","name":"Plate"}},
 {"command":"solid.fillet","params":{"edges":[[0,0,5],[60,0,5],[60,40,5],[0,40,5]],"radius":3,"name":"Corners"}}
]}
```

- The circles inside the rectangle become holes, because extrude takes every region.
- Each fillet pick is the midpoint of a vertical edge (z = thickness/2).
- Expected volume: 60·40·10 − 4·π·2²·10 − 4·(3² − π·3²/4)·10 = **23420.1 mm³**, with 8 cylindrical faces (4 holes and 4 rounds).

```sh
python3 $S/sc_run.py plate.json --save plate.solidcraft --out plate.step --out plate.stl \
  --expect-volume 23420.1 --expect-size 60 40 10 --expect-bodies 1
python3 $S/sc_inspect.py plate.solidcraft --snap-dir shots --views iso top
```

For a fully constrained sketch whose holes follow `L`, `W` and `inset`, use the vendor's
worked example: `sc_commands.py --doc solidcraft-modeling/reference.md`, section
*Worked example*. It uses `sketch.draw.dimensioned` together with a hole sketch and a
pattern.

## 2. L-bracket driven by `wall` and `hole_d`, then a parameter edit

```json
{"commands":[
 {"command":"parameters.add","params":{"name":"wall","expression":"3 mm"}},
 {"command":"parameters.add","params":{"name":"hole_d","expression":"5 mm"}},
 {"command":"solid.box","params":{"length":50,"width":30,"height":"wall","corner":[0,0,0],"body_name":"Bracket","name":"Base"}},
 {"command":"solid.box","params":{"length":50,"width":"wall","height":40,"corner":[0,0,0],"operation":"join","targets":["Bracket"],"name":"Upright"}},
 {"command":"solid.cylinder","params":{"diameter":"hole_d","height":"wall + 2","base":[15,"wall + (30 - wall)/2",-1],"operation":"cut","targets":["Bracket"],"name":"Hole1"}},
 {"command":"solid.cylinder","params":{"diameter":"hole_d","height":"wall + 2","base":[35,"wall + (30 - wall)/2",-1],"operation":"cut","targets":["Bracket"],"name":"Hole2"}}
]}
```

- Expected volume: V(w, d) = 50·30·w + 50·w·(40 − w) − 2·π·(d/2)²·w.
  - V(3, 5) = **9932.2 mm³**;
  - V(5, 5) = **16053.7 mm³**.
- The holes' `base` and `height` are expressions, so they stay centred on the base and
  through it when `wall` changes.

```sh
python3 $S/sc_run.py bracket.json --save bracket.solidcraft --expect-volume 9932.2
python3 $S/sc_params.py bracket.solidcraft                     # what can be changed
python3 $S/sc_params.py bracket.solidcraft --set wall="5 mm" \
  --save bracket-wall5.solidcraft --out bracket-wall5.step --expect-volume 16053.7
```

**Several values at once:** use `--set a=1 b=2`, which rebuilds once and applies all of
them or none.

**When the value isn't a user parameter:** run `--all` to list the sketch dimensions
and feature inputs (`d1` for `Extrude1 › Distance`). Change those the same way.

**Previewing without saving:**
`solidcraft-cli eval change.json --in bracket.solidcraft`.

## 3. Inspect a STEP part: size, volume, iso and section views

```sh
python3 $S/sc_inspect.py part.step --snap-dir shots --views iso --section mid
# or a given height / plane:
python3 $S/sc_inspect.py part.step --snap-dir shots --section z=12.5 --section XZ
```

- The report gives the body count, volume, mass (at the default density), the overall
  bbox and the bodies.
- Each section render is compared against a plain render from the same view.
- Look at the PNGs (Read them) before describing them.
- A STEP opens without history. To change it, add features on top:
  `sc_run.py edit.json --in part.step --save part-edit.solidcraft`.

## 4. Flange with a bolt circle (circular pattern) and a chamfer

```json
{"commands":[
 {"command":"parameters.add","params":{"name":"T","expression":"8 mm"}},
 {"command":"parameters.add","params":{"name":"bcd","expression":"60 mm"}},
 {"command":"parameters.add","params":{"name":"n","expression":"6","unit":""}},
 {"command":"sketch.create","params":{"plane":"XY","name":"FlangeSketch"}},
 {"command":"sketch.circle.center","params":{"center":[0,0],"diameter":80}},
 {"command":"sketch.circle.center","params":{"center":[0,0],"diameter":30}},
 {"command":"sketch.finish","params":{}},
 {"command":"solid.extrude","params":{"distance":"T","body_name":"Flange","name":"Disc"}},
 {"command":"solid.cylinder","params":{"diameter":6.6,"height":"T + 2","base":["bcd/2",0,-1],"operation":"cut","targets":["Flange"],"name":"BoltHole"}},
 {"command":"solid.pattern.circular","params":{"features":["BoltHole"],"axis":"Z","count":"n","name":"BoltHoles"}},
 {"command":"solid.chamfer","params":{"edges":[[40,0,8]],"distance":1,"name":"RimChamfer"}}
]}
```

- Expected volume: π(40² − 15²)·8 − 6·π·3.3²·8 − ½·1²·2π·(40 − ⅓) = **32790.7 mm³**.
- One pick on the circular top edge chamfers the whole rim.
- A full circular pattern keeps the centre of mass on the axis. Check the bolt-circle
  radius with a top-view snapshot.

## 5. Print-ready mesh from a design or a STEP

```sh
solidcraft-cli run --in part.step --out part.3mf --out part.stl      # no script: convert only
python3 $S/sc_verify.py part part.3mf --same-as part.step --same-tol 1 --closed
```

- For a finer mesh, export through a script step:
  `{"command":"file.export","params":{"path":"part.stl","quality":"fine"}}`.
- `file.send_to_slicer` and `file.slicers` hand the part to an installed slicer. Run
  them only when the user asks, because they open another app.

## 6. A design's history as a script (to reuse or diff)

```sh
solidcraft-cli script bracket.solidcraft --out bracket.history.json
```

The output replays with `sc_run.py` or `solidcraft-cli run`. Edit the JSON to make a
variant, for example a new length, then rebuild it to a new path.
