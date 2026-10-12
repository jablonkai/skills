# td-build spec and td-props rules

## Contents
- [Map spec (td-build.sh)](#map-spec-td-buildsh)
- [Tilesets](#tilesets)
- [Tile references and the legend](#tile-references-and-the-legend)
- [Layers](#layers)
- [Objects](#objects)
- [Property values](#property-values)
- [Rules file (td-props.sh)](#rules-file-td-propssh)

## Map spec (td-build.sh)

All paths are relative to the spec file. `output` decides the format: `.tmx` (XML),
`.tmj` or `.json` (JSON). For other formats, build a `.tmx` first and run
`td-export.sh`.

```json
{
  "output": "maps/level1.tmx",
  "width": 40, "height": 30,
  "tileWidth": 16, "tileHeight": 16,
  "orientation": "orthogonal",
  "properties": { "music": "cave.ogg", "level": 1 },
  "tilesets": [ { "name": "dungeon", "image": "art/dungeon.png", "tsx": "art/dungeon.tsx" } ],
  "legend": { "#": "dungeon:1", ".": "dungeon:0", " ": null },
  "layers": [
    { "type": "tile", "name": "floor", "fill": "dungeon:0" },
    { "type": "tile", "name": "walls", "rows": ["####", "#  #", "####"] },
    { "type": "object", "name": "objects", "objects": [ { "name": "spawn", "class": "spawn", "cell": [1, 1] } ] }
  ]
}
```

| Key | Required | Meaning |
|---|---|---|
| `output` | yes | file to write; directories are created |
| `width`, `height` | yes | map size in tiles |
| `tileWidth`, `tileHeight` | yes | grid cell size in px |
| `orientation` | no | `orthogonal` (default), `isometric`, `staggered`, `hexagonal` |
| `hexSideLength`, `staggerAxis` (`x`/`y`), `staggerIndex` (`odd`/`even`) | no | staggered/hex maps |
| `backgroundColor` | no | `#rrggbb` |
| `class` | no | the map's class (custom type name) |
| `layerDataFormat` | no | `zlib` (Tiled's default), `base64`, `gzip`, `csv`, `xml` — `csv` keeps diffs readable |
| `properties` | no | map properties, see [Property values](#property-values) |
| `tilesets` | no | list, in firstgid order |
| `legend` | no | character → tile, shared by all tile layers |
| `layers` | no | bottom to top |

## Tilesets

```json
{ "name": "dungeon", "image": "art/dungeon.png", "tsx": "art/dungeon.tsx",
  "tileWidth": 16, "tileHeight": 16, "spacing": 0, "margin": 0,
  "generate": { "colors": ["#6b5b45", "#3a3a48", "#8a5a20"], "columns": 8, "border": true },
  "tiles": { "1": { "class": "wall", "properties": { "solid": true } } },
  "properties": { "author": "me" },
  "overwrite": false }
```

- `image` is a sprite sheet. Tile ids count left to right, top to bottom, from 0.
  `tileWidth`/`tileHeight` default to the map's.
- `tsx` set: the tileset is written as an external `.tsx` (`.tsj` for JSON) and the
  map references it.
  - If that file already exists, it is **reused as is** and `image`/`generate` are
    ignored, so several maps can share one tileset. Set `"overwrite": true` to
    rebuild it.
  - `tsx` alone, with no `image`, uses an existing tileset.
- `tsx` absent: the tileset is embedded in the map.
- `generate` writes placeholder art to `image` first: one flat colour per tile, in
  `columns` per row (default: all in one row), with a 1 px dark border unless
  `"border": false`. Use it when the user has no art yet, and say that it is
  placeholder art.
- `tiles` sets a class and properties per tile id. Tile properties become Godot
  custom data layers in a `.tscn` export.

## Tile references and the legend

A tile reference is one of:
- `"tileset:id"`, for example `"dungeon:1"`;
- a bare number `1`, meaning that id in the first tileset;
- `null`, for an empty cell.

Append `|` and flip flags to flip a tile: `h` horizontal, `v` vertical, `d`
anti-diagonal. `"dungeon:2|h"`, or `"dungeon:2|hd"` for a 90° rotation.

`legend` maps one character to one tile reference. A layer's own `legend` is merged
over the map's. Every character in `rows` must be in the merged legend; a missing one
is an error, not a blank cell.

## Layers

Every layer takes `name`, and optionally `class`, `opacity` (0–1),
`visible: false`, `locked: true`, `offset: [x, y]` (px) and `properties`.

| `type` | Extra keys |
|---|---|
| `tile` | `fill` (one tile reference for every cell), then `rows` (exactly `height` strings of exactly `width` characters), then `cells` (`[[x, y, ref], …]`, where `ref` null clears). These apply in that order, so `cells` override `rows`, which override `fill`. |
| `object` | `objects` (below), `color` (`#rrggbb`) |
| `image` | `image` (path), `repeatX`, `repeatY` |
| `group` | `layers` (nested list, same format) |

Rows are characters, not bytes, so non-ASCII legend characters work. Keep to ASCII
when someone else will edit the spec.

## Objects

```json
{ "name": "spawn", "class": "spawn", "cell": [3, 4], "properties": { "hp": 10 } }
{ "name": "zone",  "x": 32, "y": 48, "width": 64, "height": 32, "shape": "ellipse" }
{ "name": "path",  "x": 0, "y": 0, "shape": "polyline", "points": [[0, 0], [64, 0], [64, 32]] }
{ "name": "chest", "tile": "dungeon:3", "cell": [5, 2] }
{ "name": "sign",  "text": "Beware", "x": 0, "y": 0, "width": 96, "height": 16 }
```

- `cell: [cx, cy]` puts the object's top-left corner at that cell and makes it one
  tile in size. Explicit `x`, `y`, `width`, `height` (px) override it.
- `shape`: `rectangle` (default), `ellipse`, `point`, `polygon`, `polyline` or
  `text`. `points` are relative to `x`,`y`.
- `tile` makes a **tile object**. Tiled anchors tile objects at their bottom-left,
  so with `cell` the y is set to the cell's bottom edge for you. With explicit `x`,`y`,
  give the bottom-left corner.
- `rotation` is in degrees, clockwise. `visible: false` hides the object.
- Ids are assigned in order, starting at 1. Object names don't have to be unique,
  but an object-reference `ref` by name does need a unique name.

## Property values

The same rules apply in `td-build` specs and `td-props` rules.

| JSON | Tiled type |
|---|---|
| `10` | int |
| `2.5` | float |
| `true` | bool |
| `"text"` | string |
| `{"type": "int", "value": "10"}` | int (forced) |
| `{"type": "float", "value": 2}` | float. Whole floats are written as `type="float"` by a post-save patch. |
| `{"type": "bool", "value": "true"}` | bool |
| `{"type": "string", "value": 10}` | string `"10"` |
| `{"type": "color", "value": "#ff8800"}` | color (`#aarrggbb` in the file) |
| `{"type": "file", "value": "sfx/door.wav"}` | file. The path is relative to the spec in td-build, and to the cwd in td-props. |
| `{"type": "object", "ref": "door_b"}` | object reference, by unique name or by numeric id |
| `{"type": "Loot", "value": {"gold": 5}}` | custom class or enum from a Tiled project. This needs `--project file.tiled-project` with that type defined. |

A plain whole number is always int. Write `{"type": "float", "value": 3}` when the
engine expects a float.

## Rules file (td-props.sh)

```json
{
  "map":   { "set": { "difficulty": 2 }, "unset": ["draft"] },
  "rules": [
    { "where": { "class": "enemy" },                              "set": { "hp": 10, "aggressive": true } },
    { "where": { "class": "enemy", "name": "orc_*" },             "set": { "hp": 25 } },
    { "where": { "class": "chest" },                              "set": { "loot": "gold" } },
    { "where": { "class": "chest", "props": { "tier": "rare" } }, "set": { "loot": "gem" } },
    { "where": { "name": "door_a" }, "set": { "target": { "type": "object", "ref": "door_b" } } },
    { "where": { "layer": "debug*" }, "unset": ["note"], "optional": true }
  ]
}
```

- Rules run top to bottom, and a later `set` overwrites an earlier one. So write the
  general case first and the exceptions after it.
- `where` keys are ANDed. An empty `where` matches every object.
  - `class` and `name` are globs where `*` matches anything; matching is case
    sensitive.
  - `layer` is a glob on the layer path, with groups as `group/layer`.
  - `id` is a number or a list of numbers.
  - `shape` is one of the shape names above.
  - `props` is `{name: value}`, compared as strings against the current values.
- `set` replaces both the value and the type. An existing `"hp": "10"` string becomes
  int with `"hp": 10`.
- `unset` removes properties, if present.
- A rule that matches nothing is an error, because it usually means a typo in a class
  or name. Add `"optional": true` when an empty match is fine.
- `--dry-run` prints every change as `target: property old -> new` and writes
  nothing. Without it, the map is rewritten in place, or to `--out` (which may switch
  format, e.g. `.tmx` → `.tmj`).

td-props edits objects and map properties only. For layer, tile or tileset
properties, write a `tiled.sh eval` script; the pattern is in
[scripting-api.md](scripting-api.md).
