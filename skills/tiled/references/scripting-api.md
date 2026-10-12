# Tiled JS API: the headless subset

Everything here was run through `tiled.sh eval` (`Tiled --evaluate`) on Tiled 1.12.2.
The full API reference is at <https://www.mapeditor.org/docs/scripting/>, and the
TypeScript definitions are in the `@mapeditor/tiled-api` npm package. Anything that
needs the editor (`tiled.open`, `tiled.activeAsset`, actions, menus, tools, dialogs)
doesn't work headless.

## Contents
- [Running scripts](#running-scripts)
- [Read, modify, write](#read-modify-write)
- [Maps and layers](#maps-and-layers)
- [Tiles and cells](#tiles-and-cells)
- [Objects](#objects)
- [Tilesets](#tilesets)
- [Properties](#properties)
- [Files and images](#files-and-images)
- [Does not work headless](#does-not-work-headless)

## Running scripts

```bash
bash "$B/tiled.sh" eval my.js map=/abs/in.tmx out=/abs/out.tmx
bash "$B/tiled.sh" --project game.tiled-project eval my.js …   # custom property types available
```

- `tiled.scriptArguments` is the array of trailing arguments. Use `key=value`
  strings: Tiled's own option parser rejects `-` and swallows empty strings.
- Pass absolute paths. Relative paths resolve against the cwd, which is fine if you
  `cd` first.
- `tiled.log(msg)` prints a line. Report results as your own marker lines (`RESULT
  …`), because Tiled's own messages are localized.
- Fail with `throw new Error(...)`. `tiled.sh eval` turns any uncaught exception into
  exit 1. `tiled.error()` only prints.
- Plain scripts only: ES module `import` can't be used inside `tiled.sh eval`.

```js
const args = {};
for (const a of tiled.scriptArguments) { const i = a.indexOf("="); if (i > 0) args[a.slice(0, i)] = a.slice(i + 1); }
```

## Read, modify, write

```js
const map = tiled.mapFormat("tmx").read(args.map);        // "json" for .tmj
// … modify …
const err = tiled.mapFormat("tmx").write(map, args.out);  // undefined on success, a string on failure
if (err) throw new Error(err);
```

- Reading a map keeps external tilesets and templates external on write.
- Tiled normalizes the file on write: attribute order, an empty embedded `<grid>`
  dropped, `version` bumped when a newer feature is used. The data stays the same.
  Don't promise a byte-identical diff.
- Maps loaded this way are "detached": `map.resize()` throws ("not supported for
  detached maps"). To resize, build a new `TileMap` and copy the cells (loop over
  `cellAt` / `setTile` with an offset).

## Maps and layers

```js
const map = new TileMap();
map.setSize(40, 30);  map.setTileSize(16, 16);
map.orientation = TileMap.Orthogonal;           // Isometric, Staggered, Hexagonal
map.layerDataFormat = TileMap.CSV;              // Base64Zlib (default), Base64, Base64Gzip, XML
map.backgroundColor = "#202030";
map.className = "Level";

const layer = new TileLayer("walls");           // gets the map's size when added
map.addLayer(layer);                            // on top
map.insertLayerAt(0, new TileLayer("bg"));      // at the bottom (give width/height first)
map.removeLayerAt(i);
map.layerCount; map.layerAt(i); map.layers;     // top-level only; recurse into GroupLayer.layers

layer.name = "solid"; layer.opacity = 0.5; layer.visible = false; layer.offset = Qt.point(4, 2);
layer.isTileLayer; layer.isObjectLayer; layer.isGroupLayer; layer.isImageLayer;

const group = new GroupLayer("decor"); group.addLayer(new TileLayer("props")); map.addLayer(group);
const img = new ImageLayer("sky"); img.imageFileName = "/abs/sky.png"; img.repeatX = true;
```

Find a layer by name (recursive):

```js
function findLayer(layers, name) {
  for (const l of layers) {
    if (l.name === name) return l;
    if (l.isGroupLayer) { const r = findLayer(l.layers, name); if (r) return r; }
  }
  return null;
}
```

## Tiles and cells

```js
const edit = layer.edit();                       // batch edits, then apply once
edit.setTile(x, y, tileset.tile(3));             // place tile id 3
edit.setTile(x, y, tileset.tile(3), Tile.FlippedHorizontally | Tile.FlippedAntiDiagonally);
edit.setTile(x, y, null);                        // clear
edit.apply();                                    // without apply() nothing changes

layer.cellAt(x, y).tileId;   // local id in its tileset, -1 when empty
layer.tileAt(x, y);          // Tile or null; .id, .tileset, .className, .property()
layer.flagsAt(x, y);         // FlippedHorizontally=1, FlippedVertically=2, FlippedAntiDiagonally=4
layer.region().rects;        // painted area as rectangles
```

Rotation through flags: 90° clockwise = `AntiDiagonally | Horizontally`, 180° =
`Horizontally | Vertically`, 270° = `AntiDiagonally | Vertically`.

Replace one tile with another everywhere, keeping flips:

```js
const e = layer.edit();
for (let y = 0; y < layer.height; y++)
  for (let x = 0; x < layer.width; x++)
    if (layer.cellAt(x, y).tileId === 1) e.setTile(x, y, ts.tile(5), layer.flagsAt(x, y));
e.apply();
```

## Objects

```js
const og = new ObjectGroup("objects"); map.addLayer(og);
const o = new MapObject("spawn");
o.className = "spawn"; o.x = 32; o.y = 48; o.width = 16; o.height = 16;
o.shape = MapObject.Point;            // Rectangle, Ellipse, Polygon, Polyline, Text
o.polygon = [Qt.point(0, 0), Qt.point(32, 0), Qt.point(16, 24)];
o.tile = ts.tile(3);                  // tile object, anchored bottom-left
o.rotation = 90; o.visible = false;
og.addObject(o);                      // the id is assigned here (o.id)
og.objects;                           // in drawing order, not id order
og.removeObject(o); og.objectCount;
```

- In `.tmx` files written at the 1.10 format level, an object's class is stored as
  `type="…"`. On other elements it is `class="…"`.
- Removing objects while iterating `og.objects` is safe, because the getter returns
  a copy.

## Tilesets

```js
const ts = new Tileset("dungeon");
ts.tileWidth = 16; ts.tileHeight = 16;
ts.image = "/abs/dungeon.png";             // slices the sheet; ts.tileCount follows (either order works)
ts.tile(1).className = "wall";
ts.tile(1).setProperty("solid", true);
const coll = new ObjectGroup(); const r = new MapObject(); r.width = 16; r.height = 16; coll.addObject(r);
ts.tile(1).objectGroup = coll;             // collision shape (Godot export: physics polygon)
map.addTileset(ts);                        // embedded unless ts came from a file reference

const err = tiled.tilesetFormat("tsx").write(ts, "/abs/dungeon.tsx");
```

**External tilesets.** A `Tileset` from `new Tileset()` or
`tiled.tilesetFormat("tsx").read()` has an empty `fileName`, so it is embedded in any
map. To reference a `.tsx`, read it through a map:

```js
function loadExternalTileset(tsxPath) {          // what td-build.js does
  const stub = FileInfo.joinPaths(FileInfo.path(tsxPath), ".stub-" + Date.now() + ".tmx");
  const f = new TextFile(stub, TextFile.WriteOnly);
  f.write('<?xml version="1.0" encoding="UTF-8"?>\n<map version="1.10" orientation="orthogonal" renderorder="right-down" width="1" height="1" tilewidth="1" tileheight="1" infinite="0" nextlayerid="2" nextobjectid="1">\n <tileset firstgid="1" source="' + FileInfo.fileName(tsxPath) + '"/>\n <layer id="1" name="x" width="1" height="1"><data encoding="csv">0</data></layer>\n</map>\n');
  f.commit();
  try { return tiled.mapFormat("tmx").read(stub).tilesets[0]; } finally { File.remove(stub); }
}
```

The map then writes `<tileset source="…"/>` with a path relative to the map.

## Properties

```js
obj.setProperty("hp", 10);                         // int (any whole number)
obj.setProperty("speed", 2.5);                     // float
obj.setProperty("alive", true);                    // bool
obj.setProperty("name", "Bob");                    // string
obj.setProperty("tint", tiled.color("#ff8800"));   // color
obj.setProperty("sfx", tiled.filePath("/abs/door.wav"));  // file
obj.setProperty("target", otherMapObject);         // object reference (type="object")
obj.setProperty("loot", tiled.propertyValue("Loot", { gold: 5 }));  // project class/enum (needs --project)
obj.property("hp"); obj.properties(); obj.removeProperty("hp");
```

- **Whole-number floats can't be written.** `2.0` is stored as `type="int"`, and
  `tiled.propertyValue("float", …)` throws. Work around it by storing a marker string
  and patching the saved file, as td-build/td-props do:

  ```js
  obj.setProperty("speed", "__TD_FLOAT__2");
  // after write():
  const t = new TextFile(path, TextFile.ReadOnly); let s = t.readAll(); t.close();
  s = s.replace(/(?: type="string")? value="__TD_FLOAT__(-?[0-9.eE+-]+)"/g, ' type="float" value="$1"')          // tmx/tsx
       .replace(/"type":\s*"string",(\s*)"value":\s*"__TD_FLOAT__(-?[0-9.eE+-]+)"/g, '"type":"float",$1"value":$2'); // tmj/tsj
  const w = new TextFile(path, TextFile.WriteOnly); w.write(s); w.commit();
  ```
- `setProperty` with a different type replaces the old type.
- `tiled.filePath()` stores the path as given. Tiled makes it relative to the map
  only when the GUI saves, so pass the path you want to appear in the file.
- Custom types come from the project file's `propertyTypes`. `tiled.propertyValue`
  throws when the type is unknown.

## Files and images

```js
File.exists(p); File.makePath(dir); File.remove(p); File.copy(a, b);
FileInfo.path(p); FileInfo.fileName(p); FileInfo.baseName(p); FileInfo.joinPaths(a, b);
FileInfo.isAbsolutePath(p); FileInfo.cleanPath(p);

const t = new TextFile(p, TextFile.ReadOnly); const s = t.readAll(); t.close();
const w = new TextFile(p, TextFile.WriteOnly); w.write(s); w.commit();   // commit, not close

const img = new Image(64, 16, Image.Format_ARGB32);
img.fill(0xff000000); img.setPixel(x, y, 0xffaa6633);   // 0xAARRGGBB
img.save("/abs/tiles.png");                             // true on success
```

## Does not work headless

| Call | Result |
|---|---|
| `tiled.open(path)` | throws "editor not available" (localized). Use `mapFormat(…).read`. |
| `tiled.activeAsset`, `tiled.openAssets` | nothing is open |
| `map.resize()` on a read map | throws: detached maps |
| `tiled.mapFormatForFile(p)` | returns a format without a usable name; pick by extension |
| `cell.tileset` | undefined; use `layer.tileAt(x, y).tileset` |
| `tiled.registerAction`, menus, tools | register, but nothing can trigger them |
