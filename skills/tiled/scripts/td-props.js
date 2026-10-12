// Bulk-edit custom properties on the objects of a Tiled map with Tiled's JS API.
// Run through td-props.sh:
//
//   bash td-props.sh MAP.tmx RULES.json [--out OTHER.tmx] [--dry-run]
//
// RULES.json:
//   { "map":   { "set": { "difficulty": 2 } },                      optional, map properties
//     "rules": [
//       { "where": { "class": "enemy" },                    "set": { "hp": 10, "aggressive": true } },
//       { "where": { "class": "enemy", "name": "orc_*" },   "set": { "hp": 25 } },
//       { "where": { "class": "chest", "props": { "tier": "rare" } }, "set": { "loot": "gem" } },
//       { "where": { "name": "door_a" }, "set": { "target": { "type": "object", "ref": "door_b" } } },
//       { "where": { "layer": "markers" }, "unset": ["debug"] } ] }
//
// Rules run in order, so a later rule overrides an earlier one. "where" keys are
// ANDed: class, name (glob with *), layer (name or group/name), id (number or
// list), shape, props (existing values, compared as strings). A rule that matches
// nothing is an error unless it has "optional": true. Values follow the same
// typing as td-build.js: plain JSON infers int/float/bool/string; {"type", "value"}
// forces int, float, bool, string, color, file or a project enum/class type.
//
// Prints "TD_RESULT <json>" with every change; writes nothing with --dry-run.

// Arguments are key=value: Tiled's own option parser rejects "-" and drops "".
const args = {};
for (const a of tiled.scriptArguments) { const i = a.indexOf("="); if (i > 0) args[a.slice(0, i)] = a.slice(i + 1); }
const mapPath = args.map, rulesPath = args.rules;
if (!mapPath || !rulesPath) throw new Error("usage: td-props.js map=MAP rules=RULES.json [out=OUT] [dry=1]");
const outPath = args.out || mapPath;
const dryRun = args.dry === "1";

function readText(path) {
  const f = new TextFile(path, TextFile.ReadOnly);
  const s = f.readAll();
  f.close();
  return s;
}

const FLOAT_MARK = "__TD_FLOAT__";
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

const fmtOf = (p) => (/\.(tmj|json)$/.test(p) ? "json" : /\.tmx$/.test(p) ? "tmx" : null);
if (!fmtOf(mapPath)) throw new Error("map must be .tmx, .tmj or .json: " + mapPath);
if (!fmtOf(outPath)) throw new Error("output must be .tmx, .tmj or .json: " + outPath);
const map = tiled.mapFormat(fmtOf(mapPath)).read(mapPath);
const spec = JSON.parse(readText(rulesPath));
const errors = [];

// Every object with its layer path.
const objects = [];
(function walk(layers, prefix) {
  for (const l of layers) {
    if (l.isObjectLayer) for (const o of l.objects) objects.push({ o: o, layer: prefix + l.name });
    else if (l.isGroupLayer) walk(l.layers, prefix + l.name + "/");
  }
})(map.layers, "");

const SHAPE = {};
SHAPE[MapObject.Rectangle] = "rectangle"; SHAPE[MapObject.Ellipse] = "ellipse"; SHAPE[MapObject.Point] = "point";
SHAPE[MapObject.Polygon] = "polygon"; SHAPE[MapObject.Polyline] = "polyline"; SHAPE[MapObject.Text] = "text";

function glob(pattern, s) {
  const re = new RegExp("^" + String(pattern).replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*") + "$");
  return re.test(s);
}

function show(v) {
  if (v && typeof v === "object" && v.id !== undefined && v.name !== undefined) return "object " + v.id + " (" + v.name + ")";
  if (v && typeof v === "object" && v.typeName) return v.typeName + " " + JSON.stringify(v.value);
  return typeof v === "string" && v.indexOf(FLOAT_MARK) === 0 ? Number(v.slice(FLOAT_MARK.length)) : v;
}

function matches(e, w) {
  const o = e.o;
  if (w.class !== undefined && !glob(w.class, o.className)) return false;
  if (w.name !== undefined && !glob(w.name, o.name)) return false;
  if (w.layer !== undefined && !glob(w.layer, e.layer)) return false;
  if (w.id !== undefined && (Array.isArray(w.id) ? w.id.indexOf(o.id) < 0 : w.id !== o.id)) return false;
  if (w.shape !== undefined && SHAPE[o.shape] !== w.shape) return false;
  for (const k in w.props || {}) {
    const v = o.property(k);
    if (v === undefined || String(show(v)) !== String(w.props[k])) return false;
  }
  return true;
}

function findObject(ref, where) {
  const hits = objects.filter((e) => (typeof ref === "number" ? e.o.id === ref : e.o.name === ref));
  if (hits.length !== 1) {
    errors.push(where + ": " + (hits.length ? hits.length + " objects match '" + ref + "'" : "no object '" + ref + "'"));
    return null;
  }
  return hits[0].o;
}

function value(v, where) {
  if (v === null || typeof v !== "object" || Array.isArray(v)) {
    if (typeof v === "number") return v;          // whole numbers become int, others float
    if (typeof v === "boolean" || typeof v === "string") return v;
    errors.push(where + ": unsupported value " + JSON.stringify(v));
    return undefined;
  }
  switch (v.type) {
    case "int": return Math.trunc(Number(v.value));
    case "float": { const n = Number(v.value); return Number.isInteger(n) ? FLOAT_MARK + n : n; }
    case "bool": return v.value === true || v.value === "true";
    case "string": return String(v.value);
    case "color": return tiled.color(String(v.value));
    case "file": return tiled.filePath(String(v.value));
    case "object": return findObject(v.ref !== undefined ? v.ref : v.value, where) || undefined;
    default:
      try { return tiled.propertyValue(v.type, v.value); }
      catch (e) { errors.push(where + ": custom type '" + v.type + "' needs --project (" + e + ")"); return undefined; }
  }
}

const changes = [];
const report = [];

function apply(owner, label, set, unset, where) {
  for (const k in set || {}) {
    const nv = value(set[k], where + " '" + k + "'");
    if (nv === undefined) continue;
    const old = owner.property(k);
    owner.setProperty(k, nv);
    changes.push({ target: label, property: k, old: old === undefined ? null : show(old), new: show(nv) });
  }
  for (const k of unset || []) {
    if (owner.property(k) === undefined) continue;
    changes.push({ target: label, property: k, old: show(owner.property(k)), new: null });
    owner.removeProperty(k);
  }
}

if (spec.map) apply(map, "map", spec.map.set, spec.map.unset, "map");
(spec.rules || []).forEach((r, i) => {
  const where = "rule " + (i + 1);
  const hits = objects.filter((e) => matches(e, r.where || {}));
  report.push({ rule: i + 1, where: r.where || {}, matched: hits.length });
  if (!hits.length && !r.optional) errors.push(where + ": matched no object (" + JSON.stringify(r.where || {}) + "); add \"optional\": true if that is expected");
  for (const e of hits) apply(e.o, "object " + e.o.id + " (" + e.o.name + ") in " + e.layer, r.set, r.unset, where);
});

if (errors.length) throw new Error(errors.length + " error(s):\n  " + errors.join("\n  "));

if (!dryRun) {
  const err = tiled.mapFormat(fmtOf(outPath)).write(map, outPath);
  if (err) throw new Error("writing " + outPath + ": " + err);
  patchFloats(outPath);
}
tiled.log("TD_RESULT " + JSON.stringify({ map: mapPath, output: dryRun ? null : outPath, objects: objects.length, rules: report, changes: changes }));
