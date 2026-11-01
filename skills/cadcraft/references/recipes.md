# Recipes

`S=<skill>/scripts`. Paths in a spec are relative to the spec file.

## Mounting plate

100×60 mm plate, R5 corners, 4× Ø6 holes 10 mm in, dimensions and a note on their own
layers.

```json
{"metric": true,
 "layers": [{"name": "GEOM", "color": "White"}, {"name": "DIM", "color": "Red"},
            {"name": "TEXT", "color": "Cyan"}],
 "draw": [
  {"layer": "GEOM", "cmd": "rectang", "params": {"p1": [0, 0], "p2": [100, 60], "fillet": 5}},
  {"layer": "GEOM", "cmd": "circle", "params": {"center": [10, 10], "diameter": 6}, "as": "h1"},
  {"layer": "GEOM", "cmd": "circle", "params": {"center": [90, 10], "diameter": 6}},
  {"layer": "GEOM", "cmd": "circle", "params": {"center": [90, 50], "diameter": 6}},
  {"layer": "GEOM", "cmd": "circle", "params": {"center": [10, 50], "diameter": 6}},
  {"layer": "DIM", "cmd": "dimlinear", "params": {"p1": [0, 0], "p2": [100, 0], "at": [50, -12]}},
  {"layer": "DIM", "cmd": "dimlinear", "params": {"p1": [100, 0], "p2": [100, 60], "at": [112, 30]}},
  {"layer": "DIM", "cmd": "dimlinear", "params": {"p1": [0, 10], "p2": [10, 10], "at": [5, -6]}},
  {"layer": "DIM", "cmd": "dimdiameter", "params": {"handle": "@h1", "at": [-8, 20]}},
  {"layer": "DIM", "cmd": "dimradius", "params": {"center": [95, 55], "point": [98.5355, 58.5355]}},
  {"layer": "TEXT", "cmd": "text", "params": {"at": [0, 70], "text": "MOUNTING PLATE  4x %%c6 THRU  R5", "height": 4}}
 ],
 "save": "plate.dxf",
 "exports": [{"path": "plate.pdf", "view": "extents"}, {"path": "plate.png", "view": "extents"}]}
```

```sh
python3 $S/cc_build.py plate.json
.venv-dxf/bin/python $S/cc_verify.py doc plate.dxf --layer GEOM DIM TEXT \
  --count Circle=4 Polyline=1 'Dimension>=4' --type-on Circle=GEOM Polyline=GEOM Dimension=DIM Text=TEXT \
  --units mm --circles 3=4 --size GEOM=100x60
python3 $S/cc_verify.py files . --ext png --px 2400x1600   # then view plate.png
```

The fillet radius is dimensioned by `{center, point}` because the R5 corners are bulge
arcs inside the polyline, not ARC entities.

## Batch conversion

```sh
python3 $S/cc_batch.py ~/drawings ~/drawings-out --to pdf,svg     # OUT outside IN
python3 $S/cc_verify.py files ~/drawings-out --ext pdf --count 5 --pdf-pages 1
python3 $S/cc_verify.py files ~/drawings-out --ext svg --count 5
# manifest.json in OUT holds every input's SHA-256 before/after; "inputs_changed": [] in the summary
```

For PNG add `png` to `--to` and choose framing (`--view extents` default). Drawings
with xrefs: check `cadcraft-cli run IN --cmd 'xref {}'` first — a `Not Found` xref
converts without error but without its geometry ([gotchas.md](gotchas.md)).

## Title block and layer move

Floorplan sample (no blocks): add an attributed title block, fill it, move A-ANNO's
objects (2 texts + 1 polyline) to a new layer, export a windowed PNG.

```sh
cadcraft-cli sample floorplan plan.dxf
cadcraft-cli info plan.dxf                       # extents ≈ [-0.45,-36.45]–[360.45,240]
python3 $S/cc_titleblock.py add plan.dxf plan-tb.dxf --at 240,-90 --size 120,45 \
  TITLE="Ground floor" DATE=2026-10-17 DRAWN_BY="T. J."
cadcraft-cli run plan-tb.dxf \
  --cmd 'layer.new {"name":"A-ANNO-NEW","color":"Magenta"}' \
  --cmd 'qselect {"layer":"A-ANNO"}' --cmd 'laymch {"layer":"A-ANNO-NEW"}' \
  --save plan-final.dxf --export plan-window.png --window=-10,-100,370,250
python3 $S/cc_verify.py doc plan-final.dxf --attr TITLE="Ground floor" DATE=2026-10-17 \
  --on-layer A-ANNO=0 A-ANNO-NEW=3 --layer A-ANNO-NEW
```

Fill later values with `cc_titleblock.py fill plan-final.dxf plan-rev.dxf DATE=2026-11-01`.
`qselect {"layer"}` returns the handles it selected — count them before moving.

## Text replace and purge

```sh
cadcraft-cli run in.dxf --cmd 'find {"find":"BEDROOM","replace":"BEDROOM 1","wholeWord":true}' \
  --cmd 'purge {"type":"all"}' --save out.dxf
```

`find` returns `{matches, total}`; total 0 means nothing changed — say so.

## Edit with handles (session)

```json
[{"open": "in.dxf"},
 {"query": {"type": "Circle", "layer": "GEOM", "limit": 500}},
 {"cmd": "properties.set", "params": {"handles": "$1.handles", "color": "Red"}},
 {"save": "out.dxf"},
 {"render": "out.png"}]
```

Steps count from 0: `$1.handles` is the handles of the entities step 1's query returned
(check its `count` equals `returned`). A one-step chain fits in `run` with `{last}`:

```sh
cadcraft-cli run --metric --cmd 'rectang {"p1":[0,0],"p2":[100,60]}' \
  --cmd 'dimlinear {"object":"{last}","at":[50,-10]}' --save part.dxf
```

```sh
python3 $S/cc_session.py steps.json --root "$PWD"
```
