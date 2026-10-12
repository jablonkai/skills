# Formats

Authoritative specs: TMX at <https://doc.mapeditor.org/en/stable/reference/tmx-map-format/>,
JSON at <https://doc.mapeditor.org/en/stable/reference/json-map-format/>. This page
covers what matters when generating, checking or converting files.

## Contents
- [Files](#files)
- [GIDs and flip flags](#gids-and-flip-flags)
- [Layer data encodings](#layer-data-encodings)
- [Objects](#objects)
- [Properties](#properties)
- [Projects and custom types](#projects-and-custom-types)
- [Exporters](#exporters)

## Files

| Ext | What | Notes |
|---|---|---|
| `.tmx` | map, XML | Tiled's native format |
| `.tmj` | map, JSON | same model; `.json` also works |
| `.tsx` / `.tsj` | tileset, XML / JSON | referenced by maps via `source` |
| `.tx` | object template | objects reference it with `template="…"` |
| `.tiled-project` | project | folders, custom property types, `extensionsPath` (GUI only) |
| `.world` | world | JSON placing several maps; not exported by the CLI |

Paths inside files (tileset `source`, image `source`, templates) are relative to the
file that contains them. Moving a map without its tilesets breaks those references;
`td-verify.py` reports which ones.

Exports work the same way: a `.tmj` or `.lua` written to another folder references
the source `.tsx` through `../../…`. For anything that gets deployed, export with
`--embed-tilesets` and copy the tileset images next to the output (embedded tilesets
still reference their image file). td-export warns when the output climbs out of its
folder.

## GIDs and flip flags

- Each tileset in a map gets a `firstgid`. A cell's GID is `firstgid + local id`, and
  0 means empty.
- The top four bits are flags:
  - `0x80000000` horizontal
  - `0x40000000` vertical
  - `0x20000000` anti-diagonal
  - `0x10000000` hexagonal 120° rotation
- Mask them off (`gid & 0x0FFFFFFF`) before looking up the tile.
- The owning tileset is the one with the largest `firstgid` ≤ GID.
- Firstgids are assigned in tileset order when a map is saved. Never hardcode GIDs
  across maps; refer to local ids, as the spec's `tileset:id` does.

## Layer data encodings

| `<data>` attributes | Content |
|---|---|
| `encoding="csv"` | comma-separated GIDs, row by row |
| `encoding="base64"` | little-endian uint32 GIDs |
| `encoding="base64" compression="zlib"` | Tiled's default |
| `compression="gzip"` / `"zstd"` | zstd needs the `zstandard` package; td-verify skips checking it |
| no encoding | one `<tile gid="…"/>` per cell (deprecated, huge) |

- Infinite maps (`infinite="1"`) store `<chunk x y width height>` blocks, usually
  16×16, instead of one block.
- Most engine loaders, and Godot's exporter, expect fixed-size maps. Build fixed
  maps unless asked otherwise.
- In JSON, `data` is a GID array for CSV, or a base64 string with `encoding` and
  `compression`.

## Objects

- `x`,`y` are pixels from the map's top-left. For tile objects (`gid` set), that is
  the object's **bottom-left** corner.
- `rotation` is in degrees, clockwise, around `x`,`y`.
- Point objects carry `<point/>`, ellipses `<ellipse/>`, polygons and polylines
  `points="x,y x,y …"` relative to `x`,`y`, and text objects `<text>`.
- The object's class is written as `type` in both `.tmx` and `.tmj` at the 1.10
  format level, which is what Tiled 1.12 writes by default; other elements use
  `class`. Readers should accept both names.
- `nextobjectid` must be greater than every object id. Tiled keeps it right; a
  hand-edited file that breaks it gets duplicate ids on the next GUI edit.
  td-verify checks it.

## Properties

```xml
<properties>
 <property name="hp" type="int" value="10"/>
 <property name="name" value="Bob"/>                       <!-- string: type omitted -->
 <property name="desc">multi
line</property>                                            <!-- long strings as text -->
 <property name="tint" type="color" value="#ffff8800"/>   <!-- #AARRGGBB -->
 <property name="target" type="object" value="12"/>        <!-- object id, 0 = none -->
 <property name="loot" type="class" propertytype="Loot">   <!-- custom class -->
  <properties><property name="gold" type="int" value="5"/></properties>
 </property>
 <property name="dir" propertytype="Dir" value="south"/>   <!-- custom enum -->
</properties>
```

Types: `string`, `int`, `float`, `bool`, `color`, `file`, `object`, `class`. JSON
uses `{"name", "type", "value"}` (plus `propertytype`), in the `properties` array of
the owner.

## Projects and custom types

A `.tiled-project` is JSON. Its `propertyTypes` define classes (with `members`) and
enums (with `values`, `storageType` string or int). To use them headless, pass
`--project file.tiled-project` (td-build, td-props, `tiled.sh --project … eval`).

Engines that don't read projects see only the values that were set explicitly.
`td-export.sh --resolve-types` bakes the class defaults into the exported file.

## Exporters

`bash tiled.sh --formats` lists what this Tiled has. In 1.12.2:
- **map formats:** csv, gmx, js, json, lua, tmx, tscn, yy
- **tileset formats:** json, lua, tsx

| Format | Output | Quirks |
|---|---|---|
| `json` | `.tmj` | Full fidelity. External tilesets stay as `source` references unless `--embed-tilesets` is passed. Layer data keeps the map's encoding (zlib by default), which Phaser can't read; `td-export --standalone` writes plain arrays. |
| `lua` | `.lua` | Tables for LÖVE/STI. External tilesets stay `filename` references unless `--embed-tilesets` is passed. |
| `csv` | one `.csv` per tile layer | Named `<base>_<layer>.csv` when there are several tile layers. Objects are dropped. |
| `js` | `.js` | JSON wrapped in a `(function(map){…})` loader call for `<script>` use |
| `tscn` | Godot 4 scene | Needs `project.godot` above the output and the art inside it. Objects are exported only with `resPath`, placed at their centre. Tile layers become a `TileMap` node. Image layers are dropped. |
| `gmx`, `yy` | GameMaker 1.4 / 2.x rooms | Object/instance mapping uses custom properties; see Tiled's docs |
| `tmx` | `.tmx` | Useful to convert `.tmj` → `.tmx`, or with `--embed-tilesets`/`--detach-templates` |

Godot exporter options are custom properties:
- **Map:** `tilesetResPath` writes the TileSet to a separate `.tres`. Every map that
  shares it must use the same tilesets.
- **Layer:** `noExport` (bool), `zIndex` (int), `ySortEnabled` (bool), `tilesetOnly`
  (bool, exports only the layer's tilesets).
- **Object:** `resPath` (string, `res://….tscn`).
- **Tile:** custom properties become TileSet custom data layers, and collision shapes
  become physics layer polygons.
- **Tileset:** `exportAlternates` is only for Godot 4.0/4.1.
- **Not supported:** image-collection tilesets and image layers.
