# QCAD recipes

Each block is a complete script for `qcad-run.sh` (lib.js is preloaded).

## Contents
- [Walls with thickness and openings](#walls-with-thickness-and-openings)
- [Dimension chains](#dimension-chains)
- [Hatched section and centre lines](#hatched-section-and-centre-lines)
- [Blocks with many inserts (a bolt pattern)](#blocks-with-many-inserts)
- [Drawing from a CSV or JSON spec](#drawing-from-a-csv-or-json-spec)
- [Modify an existing DXF](#modify-an-existing-dxf)
- [Report what a drawing contains](#report-what-a-drawing-contains)

## Walls with thickness and openings

Model a wall as its two faces. An opening is a gap in both faces plus two
short "jamb" lines closing the wall ends — that is what a reader (and an
`ezdxf` check) sees as a door: two separate wall pieces with the opening
width between them.

```js
// wall(c, x1, y1, x2, y2, t, openings): axis-aligned wall centred on the
// segment, thickness t; openings = [[offsetFromStart, width], ...]
function wall(c, x1, y1, x2, y2, t, openings) {
    var horiz = y1 === y2, len = horiz ? Math.abs(x2 - x1) : Math.abs(y2 - y1);
    var dir = horiz ? (x2 > x1 ? 1 : -1) : (y2 > y1 ? 1 : -1), h = t / 2;
    var cuts = (openings || []).slice().sort(function (a, b) { return a[0] - b[0]; });
    var pieces = [], at = 0;
    cuts.forEach(function (o) { pieces.push([at, o[0]]); at = o[0] + o[1]; });
    pieces.push([at, len]);
    function P(s, side) {           // point at distance s along, offset to one face
        return horiz ? v(x1 + dir * s, y1 + side * h) : v(x1 + side * h, y1 + dir * s);
    }
    pieces.forEach(function (p) {
        if (p[1] - p[0] <= 0) return;
        addPolyline(c, [P(p[0], -1), P(p[1], -1), P(p[1], 1), P(p[0], 1)], true);
    });
}

var c = newDrawing();
addLayer(c, "WALLS", "white", "CONTINUOUS", RLineweight.Weight050);
var T = 300;                                         // 10 x 8 m outside, 300 mm walls
wall(c, 0, T / 2, 10000, T / 2, T);                  // south (centre lines inset by T/2)
wall(c, 0, 8000 - T / 2, 10000, 8000 - T / 2, T);    // north
wall(c, T / 2, T, T / 2, 8000 - T, T);               // west, between the long walls
wall(c, 10000 - T / 2, T, 10000 - T / 2, 8000 - T, T, [[2000, 1000]]);  // east, 1 m window
wall(c, 6000, T, 6000, 8000 - T, 150, [[1000, 900]]); // interior, 900 mm door
addLayer(c, "DIMENSIONS", "cyan");
setDimScale(c, 100);
addDimLinear(c, v(0, 0), v(10000, 0), v(0, -800), 0);
addDimLinear(c, v(10000, 0), v(10000, 8000), v(10800, 0), 90);
saveDrawing(c, ARGS[0] + "/walls.dxf");
exportPdf(c, ARGS[0] + "/walls.pdf", { paper: "A3" });
```

Each wall piece is one closed polyline, so pieces per wall = openings + 1,
and a door shows up as a gap of exactly its width between two pieces.
Door swings: `addArc(c, hinge, width, startDeg, endDeg)` plus a leaf line.

## Dimension chains

```js
function chain(c, xs, y, lineY) {    // horizontal chain through x positions at height y
    for (var i = 0; i + 1 < xs.length; i++) addDimLinear(c, v(xs[i], y), v(xs[i + 1], y), v(0, lineY), 0);
}
chain(c, [0, 2500, 6000, 10000], 0, -400);           // room widths
addDimLinear(c, v(0, 0), v(10000, 0), v(0, -900), 0); // overall, further out
```

Keep chains and overall dimensions on separate offset lines (about 4–5× the
paper text height times the dim scale apart) so the labels do not collide.

## Hatched section and centre lines

```js
var c = newDrawing();
addLayer(c, "OUTLINE", "white", "CONTINUOUS", RLineweight.Weight050);
var outer = [v(0, 0), v(80, 0), v(80, 40), v(0, 40)];
var hole = [v(30, 10), v(50, 10), v(50, 30), v(30, 30)];
addPolyline(c, outer, true); addPolyline(c, hole, true);
addLayer(c, "HATCH", "gray");
addHatch(c, [outer, hole], "ANSI31", 1);              // second loop = hole
addLayer(c, "CENTER", "red", "CENTER", RLineweight.Weight018);
addLine(c, v(40, -5), v(40, 45));
saveDrawing(c, ARGS[0] + "/section.dxf");
```

## Blocks with many inserts

```js
var c = newDrawing();
addLayer(c, "PART");
addCircle(c, v(0, 0), 60);
defineBlock(c, "BOLT_M8", v(0, 0), function (b) {
    addCircle(b, v(0, 0), 4.5); addLine(b, v(-6, 0), v(6, 0)); addLine(b, v(0, -6), v(0, 6));
});
for (var i = 0; i < 6; i++) {
    var a = RMath.deg2rad(i * 60);
    insertBlock(c, "BOLT_M8", v(45 * Math.cos(a), 45 * Math.sin(a)), 1, i * 60);
}
saveDrawing(c, ARGS[0] + "/flange.dxf");
```

One block definition, six INSERTs — `dxf-inspect.py` lists them under
`blocks.BOLT_M8.inserts`.

## Drawing from a CSV or JSON spec

```js
// rooms.csv: name,x,y,w,h  (mm)
var c = newDrawing();
addLayer(c, "ROOMS");
var rows = readTextFile(resolve(ARGS[0])).split("\n").filter(String);
rows.slice(1).forEach(function (l) {
    var f = l.split(","), x = +f[1], y = +f[2], w = +f[3], h = +f[4];
    setLayer(c, "ROOMS"); addRect(c, v(x, y), v(x + w, y + h));
    addText(c, v(x + w / 2, y + h / 2), f[0], { height: 200, hAlign: "center", vAlign: "middle" });
});
saveDrawing(c, ARGS[1]);
```

For JSON: `var spec = JSON.parse(readTextFile(resolve(ARGS[0])));`.

## Modify an existing DXF

```js
var c = openDrawing(ARGS[0]);
// move everything on layer OLD to NEW, delete construction lines, bump text height
addLayer(c, "NEW", "green");
var op = new RModifyObjectsOperation(), del = new RDeleteObjectsOperation();
entities(c).forEach(function (e) {
    if (e.getLayerName() === "OLD") { e.setLayerId(c.doc.getLayerId("NEW")); op.addObject(e, false); }
    else if (e.getLayerName() === "CONSTRUCTION") del.deleteObject(e);
    else if (isTextEntity(e)) { e.setTextHeight(e.getTextHeight() * 1.5); op.addObject(e, false); }
});
c.di.applyOperation(op); c.di.applyOperation(del);
saveDrawing(c, ARGS[1]);                               // a new file — keep the original
```

## Report what a drawing contains

From QCAD (no Python needed):

```js
var c = openDrawing(ARGS[0]), counts = {};
entities(c).forEach(function (e) {
    var k = e.getLayerName() + ":" + entityType(e); counts[k] = (counts[k] || 0) + 1;
});
print(JSON.stringify({ extents: extents(c), layers: c.doc.getLayerNames(), counts: counts }));
```

The independent check is still `dxf-inspect.py` — it reads the file the way
other CAD tools will.
