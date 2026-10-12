# Recipes

Each recipe was run end to end on Tiled 1.12.2 / Godot 4.7.2. `B` is this skill's
`scripts/` directory.

## Contents
- [Procedural dungeon (rooms and corridors)](#procedural-dungeon-rooms-and-corridors)
- [Map from a hand-drawn layout](#map-from-a-hand-drawn-layout)
- [Hand a Tiled level to Godot 4](#hand-a-tiled-level-to-godot-4)
- [Typed properties across a map](#typed-properties-across-a-map)
- [Custom export format](#custom-export-format)
- [Web / LÖVE exports](#web--löve-exports)

## Procedural dungeon (rooms and corridors)

Generate the ASCII rows in Python, write a spec, build. Adapt sizes, legend and
object rules to the request. The fixed seed keeps the map reproducible.

```python
#!/usr/bin/env python3
"""Rooms-and-corridors dungeon -> td-build spec. Adapt sizes, legend and objects."""
import json, random

W, H, ROOMS, SEED = 40, 30, 6, 7
rnd = random.Random(SEED)              # fixed seed: same map on every run
grid = [["#"] * W for _ in range(H)]   # start solid, carve floor

rooms = []                              # (x, y, w, h), interior cells only
for _ in range(500):
    if len(rooms) == ROOMS:
        break
    w, h = rnd.randint(4, 9), rnd.randint(4, 7)
    x, y = rnd.randint(1, W - w - 1), rnd.randint(1, H - h - 1)
    # keep one wall cell between rooms so they stay separate rooms
    if any(x - 1 <= rx + rw and rx - 1 <= x + w and y - 1 <= ry + rh and ry - 1 <= y + h
           for rx, ry, rw, rh in rooms):
        continue
    rooms.append((x, y, w, h))
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            grid[yy][xx] = "."
assert len(rooms) == ROOMS, "not enough space: shrink rooms or the count"

rooms.sort(key=lambda r: (r[0], r[1]))  # left to right, so 'first' and 'last' are far apart
centre = lambda r: (r[0] + r[2] // 2, r[1] + r[3] // 2)
for a, b in zip(rooms, rooms[1:]):      # L-shaped corridor between consecutive rooms
    (x1, y1), (x2, y2) = centre(a), centre(b)
    for x in range(min(x1, x2), max(x1, x2) + 1):
        grid[y1][x] = "."
    for y in range(min(y1, y2), max(y1, y2) + 1):
        grid[y][x2] = "."

rows = ["".join(r) for r in grid]
cell_in = lambda r, dx, dy: [r[0] + dx, r[1] + dy]
objects = [{"name": "spawn", "class": "spawn", "cell": cell_in(rooms[0], 1, 1)}]
for i, r in enumerate(rnd.sample(rooms[1:-1], 3)):   # 3 chests in 3 different rooms
    objects.append({"name": f"chest_{i + 1}", "class": "chest", "cell": cell_in(r, r[2] - 2, 1)})
objects.append({"name": "exit", "class": "exit", "cell": cell_in(rooms[-1], rooms[-1][2] - 2, rooms[-1][3] - 2)})

spec = {
    "output": "dungeon.tmx", "width": W, "height": H, "tileWidth": 16, "tileHeight": 16,
    "layerDataFormat": "csv",
    "tilesets": [{"name": "dungeon", "image": "dungeon_tiles.png", "tsx": "dungeon.tsx"}],
    "legend": {"#": "dungeon:1", ".": None},
    "layers": [
        {"type": "tile", "name": "floor", "fill": "dungeon:0"},
        {"type": "tile", "name": "walls", "rows": rows},
        {"type": "object", "name": "objects", "objects": objects},
    ],
}
json.dump(spec, open("dungeon.spec.json", "w"), indent=1)
print("\n".join(rows))
```

```bash
python3 gen_dungeon.py && bash "$B/td-build.sh" dungeon.spec.json
python3 "$B/td-verify.py" dungeon.tmx --ascii --layer walls
```

Notes:
- The walls layer is solid everywhere except the carved cells. That keeps the
  border closed and makes "walkable" simply "no wall".
- If the floor should only exist under rooms, give the floor layer `rows` too, with
  `.` → floor and `#` → `null`.
- Check the requirements on the grid before building (or let the generator assert
  them): every walkable cell reachable from the spawn (a BFS over `.`), the room
  count, objects on walkable cells, and the chests in distinct rooms. A user asking
  for "at least 5 rooms, all connected" will check exactly that.
- Doors in doorways: put a `door` tile or object where a corridor crosses a room
  edge. Those are the cells where a corridor `.` touches a room's outer ring.

## Map from a hand-drawn layout

When the user gives the layout as text (or describes it precisely), the rows go
straight into the spec:

```json
{ "output": "arena.tmx", "width": 12, "height": 6, "tileWidth": 32, "tileHeight": 32,
  "tilesets": [ { "name": "t", "image": "tiles.png", "generate": { "colors": ["#3c8c3c", "#555555", "#3060c0"] } } ],
  "legend": { ".": "t:0", "#": "t:1", "~": "t:2" },
  "layers": [ { "type": "tile", "name": "ground", "rows": [
      "############",
      "#....~~....#",
      "#....~~....#",
      "#..........#",
      "#..........#",
      "############" ] } ] }
```

Count the characters: a row that is one short is an error naming the row.

## Hand a Tiled level to Godot 4

Given `level-src/level1.tmx` with `tiles/forest.tsx` → `forest.png`, and a Godot
project `game/` with `res://enemy.tscn`:

```bash
# 1. The exporter needs the art inside the Godot project: copy the map with its tileset.
mkdir -p game/tiled && cp -R level-src/level1.tmx level-src/tiles game/tiled/
# 2. Objects are only exported with a resPath; give the enemies one.
cat > respath.json <<'EOF'
{ "rules": [ { "where": { "layer": "enemies" }, "set": { "resPath": "res://enemy.tscn" } } ] }
EOF
bash "$B/td-props.sh" game/tiled/level1.tmx respath.json
# 3. Export into the project and prove it loads.
bash "$B/td-export.sh" game/tiled/level1.tmx game/levels/level1.tscn
bash "$B/td-godot-check.sh" game res://levels/level1.tscn --map game/tiled/level1.tmx   # must print PASS
```

- Keep the copy under `game/tiled/` as the level's source of truth from now on, and
  re-export after each edit. Tell the user which copy that is.
- Instances land at the object's centre (a 16×16 object at 80,80 gives an instance
  at 88,88). Give `enemy.tscn` a centred sprite.
- One `.tres` for several levels: set the map property `tilesetResPath` to
  `res://tiles/forest.tres` on every level that shares those tilesets.
- Collision: draw collision shapes on tiles in Tiled's tileset editor (tile
  `objectgroup`). The exporter turns them into TileSet physics polygons.

## Typed properties across a map

```json
{ "rules": [
  { "where": { "class": "enemy" },                              "set": { "hp": 10, "aggressive": true } },
  { "where": { "class": "enemy", "name": "orc_*" },             "set": { "hp": 25 } },
  { "where": { "class": "chest" },                              "set": { "loot": "gold" } },
  { "where": { "class": "chest", "props": { "tier": "rare" } }, "set": { "loot": "gem" } },
  { "where": { "name": "door_a" }, "set": { "target": { "type": "object", "ref": "door_b" } } },
  { "where": { "name": "door_b" }, "set": { "target": { "type": "object", "ref": "door_a" } } }
] }
```

```bash
bash "$B/td-props.sh" rooms.tmx rules.json --dry-run    # check matched counts and values
bash "$B/td-props.sh" rooms.tmx rules.json
```

`set` replaces both value and type, so a legacy `hp="10"` string becomes an int.
Properties that no rule touches are kept.

## Custom export format

Write the extension from `assets/map-format-template.js`, then:

```bash
bash "$B/td-extension.sh" try roguelike.js dungeon.tmx out.rl.txt   # no install, shows JS errors
diff out.rl.txt expected.txt                                         # when there is a reference
bash "$B/td-extension.sh" install roguelike.js                      # only when the user wants it in Tiled
bash "$B/td-export.sh" dungeon.tmx out.rl.txt --format roguelike     # the CLI path, through the installed copy
```

Extension pitfalls:
- `extension` is the part after the **last** dot. A format for `*.rl.txt` uses
  `extension: "txt"` and the output name supplies the rest.
- `layer.objects` is in drawing order, not id order. Sort when the output needs ids.
- `cellAt(x, y).tileId` is the **local** id in that cell's tileset, and `-1` when
  empty. `layer.tileAt(x, y).tileset` tells you which tileset (`cell.tileset` is
  undefined).
- Object x/y are pixels. For tile coordinates use `Math.floor(o.x / map.tileWidth)`.
  Tile objects are anchored bottom-left, so use `(o.y - 1)` for their cell.
- Without `file.commit()` the file is never written.

## Web / LÖVE exports

```bash
bash "$B/td-export.sh" level.tmx dist/web/level.tmj --standalone   # Phaser: embedded tilesets, images in dist/web/images
bash "$B/td-export.sh" level.tmx dist/love/level.lua --standalone  # LÖVE with STI, same treatment
bash "$B/td-export.sh" tiles.tsx web/tiles.tsj                      # tileset on its own
```

Phaser's `load.tilemapTiledJSON` can't follow external tileset references.
`--standalone` embeds them, copies the images next to the export and rewrites the
paths. It also stores JSON tile data as plain arrays: Phaser warns "Layer
compression is unsupported" and skips any zlib/gzip layer, which is Tiled's default.
STI's Lua loader can decompress zlib through `love.data`. Each output folder then works when copied anywhere on its own. Check that with
`grep -n '\.\./' dist/web/level.tmj`, which should find nothing.
