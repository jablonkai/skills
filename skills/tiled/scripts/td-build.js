// Build a Tiled map from a JSON spec with Tiled's own JS API, so the result is
// exactly what Tiled itself would save. Run through td-build.sh:
//
//   bash td-build.sh spec.json            writes the spec's "output" (.tmx / .tmj / .json)
//
// Paths inside the spec are relative to the spec file. The spec format is in
// references/spec.md; the short version:
//
//   { "output": "level.tmx", "width": 40, "height": 30, "tileWidth": 16, "tileHeight": 16,
//     "tilesets": [{ "name": "dungeon", "image": "tiles.png", "tsx": "dungeon.tsx" }],
//     "legend": { "#": "dungeon:1", ".": "dungeon:0", " ": null },
//     "layers": [
//       { "type": "tile", "name": "walls", "rows": ["####", "#..#", "####"] },
//       { "type": "object", "name": "objects", "objects": [
//           { "name": "spawn", "class": "spawn", "cell": [1, 1], "properties": { "hp": 10 } } ] } ] }
//
// Prints one line "TD_RESULT <json>" with the layer summary on success.

const specPath = FileInfo.cleanPath(FileInfo.fromNativeSeparators(tiled.scriptArguments[0] || ""));
if (!specPath || !File.exists(specPath)) throw new Error("usage: td-build.js SPEC.json (spec not found: " + specPath + ")");
const specDir = FileInfo.path(specPath);

function readText(path) {
  const f = new TextFile(path, TextFile.ReadOnly);
  const s = f.readAll();
  f.close();
  return s;
}

function abs(p) {
  if (!p) return p;
  return FileInfo.isAbsolutePath(p) ? FileInfo.cleanPath(p) : FileInfo.cleanPath(FileInfo.joinPaths(specDir, p));
}

const spec = JSON.parse(readText(specPath));
const errors = [];
const fail = (msg) => errors.push(msg);

// ---------------------------------------------------------------- properties

const FLOAT_MARK = "__TD_FLOAT__";
const objectsByName = {};   // name -> [MapObject]
const pendingRefs = [];     // [target object, property name, ref, where]

// JSON value -> Tiled property value. Plain values infer int/float/bool/string;
// {"type": T, "value": V} forces a type; {"type": "object", "ref": "name"|id} links an object.
function propValue(v, where, owner, name) {
  if (v === null || typeof v !== "object" || Array.isArray(v)) {
    if (typeof v === "number" && !Number.isInteger(v)) return v;           // float
    if (typeof v === "number") return Math.trunc(v);                       // int
    if (typeof v === "boolean" || typeof v === "string") return v;
    fail(where + ": unsupported property value " + JSON.stringify(v));
    return undefined;
  }
  const t = v.type;
  switch (t) {
    case "int": return Math.trunc(Number(v.value));
    case "float": {
      // The JS API stores a whole number as int and has no way to ask for float, so
      // whole floats are written as a marker string and patched after saving.
      const n = Number(v.value);
      return Number.isInteger(n) ? FLOAT_MARK + n : n;
    }
    case "bool": return v.value === true || v.value === "true";
    case "string": return String(v.value);
    case "color": return tiled.color(String(v.value));
    case "file": return tiled.filePath(abs(String(v.value)));
    case "object":
      if (owner) pendingRefs.push([owner, name, v.ref !== undefined ? v.ref : v.value, where]);
      return undefined;
    default:
      // A custom enum or class from the project (td-build.sh --project FILE).
      try {
        return tiled.propertyValue(t, v.value);
      } catch (e) {
        fail(where + ": custom property type '" + t + "' needs --project with that type (" + e + ")");
        return undefined;
      }
  }
}

function applyProps(owner, props, where) {
  for (const name in props || {}) {
    const val = propValue(props[name], where + " property '" + name + "'", owner, name);
    if (val !== undefined) owner.setProperty(name, val);
  }
}

// Turn FLOAT_MARK strings in a saved .tmx/.tsx/.tmj/.tsj into real float properties.
function patchFloats(path) {
  const text = readText(path);
  if (text.indexOf(FLOAT_MARK) < 0) return;
  const fixed = text
    .replace(/(?: type="string")? value="__TD_FLOAT__(-?[0-9.eE+-]+)"/g, ' type="float" value="$1"')
    .replace(/"type":\s*"string",(\s*)"value":\s*"__TD_FLOAT__(-?[0-9.eE+-]+)"/g, '"type":"float",$1"value":$2');
  const f = new TextFile(path, TextFile.WriteOnly);
  f.write(fixed);
  f.commit();
}

// ---------------------------------------------------------------- tilesets

// A Tileset read on its own (tilesetFormat.read) has no fileName, so a map would
// embed it. Reading it through a one-tile stub map keeps it external.
function loadExternalTileset(tsxPath) {
  const stub = FileInfo.joinPaths(FileInfo.path(tsxPath), ".td-stub-" + Date.now() + ".tmx");
  const f = new TextFile(stub, TextFile.WriteOnly);
  f.write('<?xml version="1.0" encoding="UTF-8"?>\n<map version="1.10" orientation="orthogonal" renderorder="right-down" width="1" height="1" tilewidth="1" tileheight="1" infinite="0" nextlayerid="2" nextobjectid="1">\n <tileset firstgid="1" source="' + FileInfo.fileName(tsxPath) + '"/>\n <layer id="1" name="x" width="1" height="1"><data encoding="csv">0</data></layer>\n</map>\n');
  f.commit();
  try {
    const m = tiled.mapFormat("tmx").read(stub);
    return m.tilesets[0];
  } finally {
    File.remove(stub);
  }
}

function hexColor(s) {
  const h = String(s).replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  return (0xff000000 | parseInt(full.slice(-6), 16)) >>> 0;
}

// Placeholder art: one flat colour per tile, with a dark 1 px border so tiles read as a grid.
function generateImage(path, gen, tw, th) {
  const colors = gen.colors || [];
  const cols = gen.columns || colors.length;
  const rows = Math.ceil(colors.length / cols);
  const img = new Image(cols * tw, rows * th, Image.Format_ARGB32);
  img.fill(0x00000000);
  colors.forEach((c, i) => {
    const ox = (i % cols) * tw, oy = Math.floor(i / cols) * th;
    for (let y = 0; y < th; y++)
      for (let x = 0; x < tw; x++) {
        const edge = gen.border !== false && (x === 0 || y === 0 || x === tw - 1 || y === th - 1);
        img.setPixel(ox + x, oy + y, edge ? 0xff101010 : hexColor(c));
      }
  });
  File.makePath(FileInfo.path(path));
  if (!img.save(path)) throw new Error("cannot write generated tileset image " + path);
}

function buildTileset(t, i) {
  const where = "tileset " + (t.name || i);
  const tw = t.tileWidth || spec.tileWidth, th = t.tileHeight || spec.tileHeight;
  const tsx = abs(t.tsx);
  if (tsx && File.exists(tsx) && !t.overwrite) {
    if (t.image || t.generate) tiled.log("note: " + where + ": reusing existing " + t.tsx + " (set overwrite:true to rebuild it)");
    return loadExternalTileset(tsx);
  }
  const image = abs(t.image);
  if (t.generate) generateImage(image, t.generate, tw, th);
  if (!image) throw new Error(where + ": needs image (or tsx pointing at an existing tileset)");
  if (!File.exists(image)) throw new Error(where + ": image not found: " + image);
  const ts = new Tileset(t.name || FileInfo.baseName(image));
  ts.tileWidth = tw;
  ts.tileHeight = th;
  if (t.spacing) ts.tileSpacing = t.spacing;
  if (t.margin) ts.margin = t.margin;
  ts.image = image;
  if (ts.tileCount === 0) throw new Error(where + ": image " + image + " holds no " + tw + "x" + th + " tiles");
  for (const id in t.tiles || {}) {
    const tile = ts.tile(Number(id));
    if (!tile) { fail(where + ": tile " + id + " does not exist (tileset has " + ts.tileCount + ")"); continue; }
    const d = t.tiles[id];
    if (d.class) tile.className = d.class;
    applyProps(tile, d.properties, where + " tile " + id);
  }
  applyProps(ts, t.properties, where);
  if (!tsx) return ts;                       // embedded in the map
  File.makePath(FileInfo.path(tsx));
  const err = tiled.tilesetFormat(tsx.endsWith(".tsj") || tsx.endsWith(".json") ? "json" : "tsx").write(ts, tsx);
  if (err) throw new Error(where + ": " + err);
  patchFloats(tsx);
  return loadExternalTileset(tsx);
}

// ---------------------------------------------------------------- map

const W = spec.width, H = spec.height;
if (!W || !H || !spec.tileWidth || !spec.tileHeight) throw new Error("spec needs width, height, tileWidth, tileHeight");
const output = abs(spec.output);
if (!output) throw new Error("spec needs output");

const map = new TileMap();
map.setSize(W, H);
map.setTileSize(spec.tileWidth, spec.tileHeight);
const ORIENT = { orthogonal: TileMap.Orthogonal, isometric: TileMap.Isometric, staggered: TileMap.Staggered, hexagonal: TileMap.Hexagonal };
if (spec.orientation) {
  if (!(spec.orientation in ORIENT)) throw new Error("unknown orientation " + spec.orientation);
  map.orientation = ORIENT[spec.orientation];
}
if (spec.hexSideLength) map.hexSideLength = spec.hexSideLength;
if (spec.staggerAxis) map.staggerAxis = spec.staggerAxis === "x" ? TileMap.StaggerX : TileMap.StaggerY;
if (spec.staggerIndex) map.staggerIndex = spec.staggerIndex === "even" ? TileMap.StaggerEven : TileMap.StaggerOdd;
if (spec.backgroundColor) map.backgroundColor = spec.backgroundColor;
if (spec.class) map.className = spec.class;
const DATA = { csv: TileMap.CSV, base64: TileMap.Base64, zlib: TileMap.Base64Zlib, gzip: TileMap.Base64Gzip, xml: TileMap.XML };
if (spec.layerDataFormat) map.layerDataFormat = DATA[spec.layerDataFormat];
applyProps(map, spec.properties, "map");

const tilesets = {};
const tilesetList = [];
(spec.tilesets || []).forEach((t, i) => {
  const ts = buildTileset(t, i);
  map.addTileset(ts);
  tilesets[t.name || ts.name] = ts;
  tilesetList.push(ts);
});

const FLIP = { h: Tile.FlippedHorizontally, v: Tile.FlippedVertically, d: Tile.FlippedAntiDiagonally };

// "dungeon:3", "dungeon:3|hv", 3 (first tileset) or null (empty) -> {tile, flags}
function resolveTile(ref, where) {
  if (ref === null || ref === undefined || ref === "") return null;
  let s = String(ref), flags = 0;
  if (s.indexOf("|") >= 0) {
    const parts = s.split("|");
    s = parts[0];
    for (const c of parts[1]) {
      if (!FLIP[c]) { fail(where + ": unknown flip flag '" + c + "' (use h, v, d)"); continue; }
      flags |= FLIP[c];
    }
  }
  let ts = tilesetList[0], id = s;
  const colon = s.lastIndexOf(":");
  if (colon >= 0) {
    ts = tilesets[s.slice(0, colon)];
    id = s.slice(colon + 1);
    if (!ts) { fail(where + ": no tileset named '" + s.slice(0, colon) + "'"); return null; }
  }
  const tile = ts ? ts.tile(Number(id)) : null;
  if (!tile) { fail(where + ": tile '" + ref + "' does not exist"); return null; }
  return { tile: tile, flags: flags };
}

function buildTileLayer(L, where) {
  const layer = new TileLayer(L.name);
  const legend = Object.assign({}, spec.legend || {}, L.legend || {});
  const edit = layer.edit();
  if (L.fill !== undefined) {
    const t = resolveTile(L.fill, where + " fill");
    if (t) for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) edit.setTile(x, y, t.tile, t.flags);
  }
  if (L.rows) {
    if (L.rows.length !== H) fail(where + ": " + L.rows.length + " rows, map height is " + H);
    L.rows.forEach((row, y) => {
      if (y >= H) return;
      const chars = Array.from(row);
      if (chars.length !== W) fail(where + " row " + y + ": " + chars.length + " characters, map width is " + W);
      chars.forEach((c, x) => {
        if (x >= W) return;
        if (!(c in legend)) { fail(where + " row " + y + " col " + x + ": character '" + c + "' is not in the legend"); return; }
        if (legend[c] === null) return;
        const t = resolveTile(legend[c], where + " '" + c + "'");
        if (t) edit.setTile(x, y, t.tile, t.flags);
      });
    });
  }
  for (const c of L.cells || []) {           // [x, y, "tileset:id"] or [x, y, null] to clear
    const t = resolveTile(c[2], where + " cell " + c[0] + "," + c[1]);
    if (t) edit.setTile(c[0], c[1], t.tile, t.flags);
    else if (c[2] === null) edit.setTile(c[0], c[1], null);
  }
  edit.apply();
  return layer;
}

const SHAPES = { rectangle: MapObject.Rectangle, ellipse: MapObject.Ellipse, point: MapObject.Point, polygon: MapObject.Polygon, polyline: MapObject.Polyline, text: MapObject.Text };

function buildObjectLayer(L, where) {
  const group = new ObjectGroup(L.name);
  if (L.color) group.color = L.color;
  (L.objects || []).forEach((o, i) => {
    const ow = where + " object " + (o.name || i);
    const mo = new MapObject(o.name || "");
    if (o.class) mo.className = o.class;
    if (o.cell) {                            // top-left of a cell, one tile in size
      mo.x = o.cell[0] * spec.tileWidth;
      mo.y = o.cell[1] * spec.tileHeight;
      mo.width = spec.tileWidth;
      mo.height = spec.tileHeight;
    }
    if (o.x !== undefined) mo.x = o.x;
    if (o.y !== undefined) mo.y = o.y;
    if (o.width !== undefined) mo.width = o.width;
    if (o.height !== undefined) mo.height = o.height;
    if (o.shape) {
      if (!(o.shape in SHAPES)) fail(ow + ": unknown shape " + o.shape);
      else mo.shape = SHAPES[o.shape];
      if (o.shape === "point") { mo.width = 0; mo.height = 0; }
    }
    if (o.points) mo.polygon = o.points.map((p) => Qt.point(p[0], p[1]));
    if (o.text !== undefined) { mo.shape = MapObject.Text; mo.text = o.text; }
    if (o.tile) {                            // tile objects are anchored bottom-left
      const t = resolveTile(o.tile, ow);
      if (t) {
        mo.tile = t.tile;
        mo.tileFlippedHorizontally = !!(t.flags & Tile.FlippedHorizontally);
        mo.tileFlippedVertically = !!(t.flags & Tile.FlippedVertically);
        if (o.cell) mo.y = (o.cell[1] + 1) * spec.tileHeight;
      }
    }
    if (o.rotation) mo.rotation = o.rotation;
    if (o.visible === false) mo.visible = false;
    group.addObject(mo);
    applyProps(mo, o.properties, ow);
    if (mo.name) (objectsByName[mo.name] = objectsByName[mo.name] || []).push(mo);
  });
  return group;
}

function buildLayer(L, prefix) {
  const where = "layer '" + prefix + L.name + "'";
  let layer;
  if (L.type === "tile") layer = buildTileLayer(L, where);
  else if (L.type === "object") layer = buildObjectLayer(L, where);
  else if (L.type === "image") {
    layer = new ImageLayer(L.name);
    layer.imageFileName = abs(L.image);
    if (L.repeatX) layer.repeatX = true;
    if (L.repeatY) layer.repeatY = true;
  } else if (L.type === "group") {
    layer = new GroupLayer(L.name);
    (L.layers || []).forEach((c) => layer.addLayer(buildLayer(c, prefix + L.name + "/")));
  } else throw new Error(where + ": unknown layer type " + L.type + " (tile, object, image, group)");
  if (L.class) layer.className = L.class;
  if (L.opacity !== undefined) layer.opacity = L.opacity;
  if (L.visible === false) layer.visible = false;
  if (L.locked) layer.locked = true;
  if (L.offset) layer.offset = Qt.point(L.offset[0], L.offset[1]);
  applyProps(layer, L.properties, where);
  return layer;
}

(spec.layers || []).forEach((L) => map.addLayer(buildLayer(L, "")));

// Object references are resolved last, so they may point forwards or across layers.
for (const [owner, name, ref, where] of pendingRefs) {
  let target = null;
  if (typeof ref === "number") {
    for (const list of Object.values(objectsByName)) for (const o of list) if (o.id === ref) target = o;
  } else {
    const hits = objectsByName[ref] || [];
    if (hits.length > 1) fail(where + ": object name '" + ref + "' is not unique (" + hits.length + " objects)");
    target = hits[0];
  }
  if (!target) fail(where + ": no object '" + ref + "' to reference");
  else owner.setProperty(name, target);
}

if (errors.length) throw new Error(errors.length + " spec error(s):\n  " + errors.join("\n  "));

File.makePath(FileInfo.path(output));
const fmt = /\.(tmj|json)$/.test(output) ? "json" : /\.tmx$/.test(output) ? "tmx" : null;
if (!fmt) throw new Error("output must end in .tmx, .tmj or .json — use td-export.sh for other formats");
const err = tiled.mapFormat(fmt).write(map, output);
if (err) throw new Error("writing " + output + ": " + err);
patchFloats(output);

const summary = { output: output, width: W, height: H, tilesets: tilesetList.map((t) => t.fileName || ("embedded:" + t.name)), layers: [] };
(function walk(layers, prefix) {
  for (const l of layers) {
    if (l.isTileLayer) {
      let n = 0;
      for (let y = 0; y < l.height; y++) for (let x = 0; x < l.width; x++) if (l.cellAt(x, y).tileId >= 0) n++;
      summary.layers.push({ name: prefix + l.name, type: "tile", tiles: n });
    } else if (l.isObjectLayer) summary.layers.push({ name: prefix + l.name, type: "object", objects: l.objectCount });
    else if (l.isGroupLayer) walk(l.layers, prefix + l.name + "/");
    else summary.layers.push({ name: prefix + l.name, type: "image" });
  }
})(map.layers, "");
tiled.log("TD_RESULT " + JSON.stringify(summary));
