// QCAD skill helper library — loaded by qcad-run.sh before the user script.
// Runs inside QCAD's ECMAScript engine (headless, -no-gui). Units: drawing
// units (mm by default), angles in degrees unless a name ends in "Rad".
//
// Globals provided to the user script:
//   ARGS        extra command-line arguments, verbatim
//   CWD         the caller's working directory (QCAD itself runs elsewhere)
//   SKILL_DIR   directory of this file
//   resolve(p)  p made absolute against CWD — every file helper below calls it
//   v(x, y)     shorthand for new RVector(x, y)

include("scripts/library.js");
include("scripts/File/Print/Print.js");
include("scripts/File/BitmapExport/BitmapExportWorker.js");

function v(x, y) {
    return new RVector(x, y);
}

function resolve(p) {
    p = String(p);
    if (p.charAt(0) === "~") p = QDir.homePath() + p.substring(1);
    return new QFileInfo(p).isAbsolute() ? QDir.cleanPath(p) : QDir.cleanPath(CWD + "/" + p);
}

// --- documents --------------------------------------------------------------

// Each drawing is a "ctx" object: { doc, di, scene, view }. The scene and the
// off-screen view are needed for PDF/PNG export and for regenerating
// dimension blocks; they cost nothing for DXF-only work.
function _wrap(doc, di) {
    var scene = new RGraphicsSceneQt(di);
    var view = new RGraphicsViewImage();
    view.setScene(scene, false);
    return { doc: doc, di: di, scene: scene, view: view };
}

// New empty drawing. unit: RS.Millimeter (default), RS.Meter, RS.Inch, ...
function newDrawing(unit) {
    var doc = new RDocument(new RMemoryStorage(), createSpatialIndex());
    var di = new RDocumentInterface(doc);
    if (!isNull(unit)) {
        doc.setUnit(unit);
    }
    return _wrap(doc, di);
}

// Open an existing DXF (or DWG when the Pro DWG plugin is present).
// Throws when the file cannot be imported.
function openDrawing(path) {
    var doc = new RDocument(new RMemoryStorage(), createSpatialIndex());
    var di = new RDocumentInterface(doc);
    var ctx = _wrap(doc, di);
    path = resolve(path);
    var res = di.importFile(path);
    if (res !== RDocumentInterface.IoErrorNoError) {
        throw new Error("cannot import " + path + " (error " + res + ")");
    }
    return ctx;
}

// Save as DXF. version: "DXF 2013" (default), "DXF 2000", "DXF R12", or a
// DWG format such as "DWG 2013" (Pro only). Throws on failure.
function saveDrawing(ctx, path, version) {
    path = resolve(path);
    var ok = ctx.di.exportFile(path, isNull(version) ? "DXF 2013" : version);
    if (!ok) {
        throw new Error("cannot save " + path);
    }
    print("SAVED " + path);
}

// --- layers -----------------------------------------------------------------

// Add (or update) a layer and make it current. color: "red", "#00ff00", ...
// linetype: "CONTINUOUS", "DASHED", "CENTER", ... lineweight: RLineweight.Weight035 etc.
function addLayer(ctx, name, color, linetype, lineweight) {
    var doc = ctx.doc;
    var ltId = doc.getLinetypeId(isNull(linetype) ? "CONTINUOUS" : linetype);
    if (ltId === RObject.INVALID_ID) {
        ltId = doc.getLinetypeId("CONTINUOUS");
    }
    var layer = new RLayer(doc, name, false, false,
                           new RColor(isNull(color) ? "white" : color), ltId,
                           isNull(lineweight) ? RLineweight.Weight025 : lineweight);
    var op = new RModifyObjectsOperation();
    op.addObject(layer);
    ctx.di.applyOperation(op);
    ctx.di.setCurrentLayer(name);
    return layer;
}

function setLayer(ctx, name) {
    ctx.di.setCurrentLayer(name);
}

// --- entities ---------------------------------------------------------------
// Every add* function draws on the current layer and current block, and
// returns the added entity.

function addEntity(ctx, entity) {
    var op = new RAddObjectsOperation();
    op.addObject(entity);
    ctx.di.applyOperation(op);
    return entity;
}

function addLine(ctx, p1, p2) {
    return addEntity(ctx, new RLineEntity(ctx.doc, new RLineData(p1, p2)));
}

function addCircle(ctx, center, radius) {
    return addEntity(ctx, new RCircleEntity(ctx.doc, new RCircleData(center, radius)));
}

// Counter-clockwise arc from startDeg to endDeg.
function addArc(ctx, center, radius, startDeg, endDeg) {
    return addEntity(ctx, new RArcEntity(ctx.doc,
        new RArcData(center, radius, RMath.deg2rad(startDeg), RMath.deg2rad(endDeg), false)));
}

// points: array of RVector. closed: true for a closed outline.
function addPolyline(ctx, points, closed) {
    var pl = new RPolyline();
    for (var i = 0; i < points.length; i++) {
        pl.appendVertex(points[i]);
    }
    pl.setClosed(closed === true);
    return addEntity(ctx, new RPolylineEntity(ctx.doc, new RPolylineData(pl)));
}

// Axis-aligned rectangle from corner p1 to the opposite corner p2, as a closed polyline.
function addRect(ctx, p1, p2) {
    return addPolyline(ctx, [p1, v(p2.x, p1.y), p2, v(p1.x, p2.y)], true);
}

// Single-line or multi-line text. opts: { height, angleDeg, hAlign, vAlign, font }
// hAlign: "left" | "center" | "right"; vAlign: "top" | "middle" | "base" | "bottom".
function addText(ctx, pos, text, opts) {
    opts = opts || {};
    var h = { left: RS.HAlignLeft, center: RS.HAlignCenter, right: RS.HAlignRight };
    var va = { top: RS.VAlignTop, middle: RS.VAlignMiddle, base: RS.VAlignBase, bottom: RS.VAlignBottom };
    var data = new RTextData(pos, pos,
        isNull(opts.height) ? 2.5 : opts.height, 0.0,
        va[opts.vAlign || "base"], h[opts.hAlign || "left"],
        RS.LeftToRight, RS.Exact, 1.0, text,
        opts.font || "Standard", false, false,
        RMath.deg2rad(opts.angleDeg || 0), false);
    return addEntity(ctx, new RTextEntity(ctx.doc, data));
}

// Dimension text, arrows and gaps default to 2.5 drawing units — invisible on
// a building plan drawn in mm. Scale them for the plot scale: a 1:100 plan
// wants factor 100 (2.5 mm text on paper = 250 mm in the model). Applies to
// dimensions added afterwards. (Setting the DIM* document variables headless
// does not reach the dimension style — the per-entity DIMSCALE does.)
function setDimScale(ctx, factor) {
    ctx.dimScale = factor;
}

function _addDim(ctx, entity) {
    if (!isNull(ctx.dimScale)) {
        entity.setDimscale(ctx.dimScale);
    }
    return addEntity(ctx, entity);
}

// Aligned dimension between p1 and p2; the dimension line passes through linePos.
function addDimAligned(ctx, p1, p2, linePos) {
    var data = new RDimAlignedData();
    data.setExtensionPoint1(p1);
    data.setExtensionPoint2(p2);
    data.setDefinitionPoint(linePos);
    return _addDim(ctx, new RDimAlignedEntity(ctx.doc, data));
}

// Horizontal (angleDeg 0) or vertical (angleDeg 90) linear dimension.
function addDimLinear(ctx, p1, p2, linePos, angleDeg) {
    var data = new RDimRotatedData();
    // rotation first: setDefinitionPoint projects the point using the
    // rotation already set, so the reverse order snaps a vertical dimension
    // line onto the measured edge
    data.setRotation(RMath.deg2rad(angleDeg || 0));
    data.setExtensionPoint1(p1);
    data.setExtensionPoint2(p2);
    data.setDefinitionPoint(linePos);
    return _addDim(ctx, new RDimRotatedEntity(ctx.doc, data));
}

// Hatch inside one or more closed boundary loops (arrays of RVector).
// pattern: "SOLID" for a solid fill, else a pattern name such as "ANSI31".
function addHatch(ctx, loops, pattern, scale, angleDeg) {
    var data = new RHatchData();
    var solid = isNull(pattern) || pattern.toUpperCase() === "SOLID";
    data.setSolid(solid);
    data.setPatternName(solid ? "SOLID" : pattern);
    data.setScale(isNull(scale) ? 1.0 : scale);
    data.setAngle(RMath.deg2rad(angleDeg || 0));
    for (var l = 0; l < loops.length; l++) {
        var pts = loops[l];
        data.newLoop();
        for (var i = 0; i < pts.length; i++) {
            data.addBoundary(new RLine(pts[i], pts[(i + 1) % pts.length]));
        }
    }
    return addEntity(ctx, new RHatchEntity(ctx.doc, data));
}

// --- blocks -----------------------------------------------------------------

// Define a block: draw(ctx) adds its entities (relative to basePoint).
// Redefining an existing name replaces nothing — pick a fresh name instead.
function defineBlock(ctx, name, basePoint, draw) {
    var block = new RBlock(ctx.doc, name, isNull(basePoint) ? v(0, 0) : basePoint);
    var op = new RAddObjectOperation(block);
    ctx.di.applyOperation(op);
    ctx.di.setCurrentBlock(name);
    try {
        draw(ctx);
    } finally {
        ctx.di.setCurrentBlock(RBlock.modelSpaceName);
    }
    return ctx.doc.getBlockId(name);
}

function insertBlock(ctx, name, pos, scale, angleDeg) {
    var id = ctx.doc.getBlockId(name);
    if (id === RObject.INVALID_ID) {
        throw new Error("no such block: " + name);
    }
    var s = isNull(scale) ? 1 : scale;
    return addEntity(ctx, new RBlockReferenceEntity(ctx.doc,
        new RBlockReferenceData(id, pos, v(s, s), RMath.deg2rad(angleDeg || 0))));
}

// --- queries ----------------------------------------------------------------

// Bounding box of everything visible in model space, as {minX, minY, maxX, maxY, w, h}.
function extents(ctx) {
    var b = ctx.doc.getBoundingBox(true, true);
    var c1 = b.getMinimum(), c2 = b.getMaximum();
    return { minX: c1.x, minY: c1.y, maxX: c2.x, maxY: c2.y, w: c2.x - c1.x, h: c2.y - c1.y };
}

// DXF-style type name of an entity: "LINE", "ARC", "CIRCLE", "POLYLINE",
// "TEXT", "INSERT", "HATCH", "DIMENSION", ... ("OTHER" when unknown).
function entityType(e) {
    var t = [["LINE", isLineEntity], ["ARC", isArcEntity], ["CIRCLE", isCircleEntity],
             ["ELLIPSE", isEllipseEntity], ["POLYLINE", isPolylineEntity], ["SPLINE", isSplineEntity],
             ["TEXT", isTextEntity], ["INSERT", isBlockReferenceEntity], ["HATCH", isHatchEntity],
             ["DIMENSION", isDimensionEntity], ["POINT", isPointEntity]];
    for (var i = 0; i < t.length; i++) {
        if (t[i][1](e)) return t[i][0];
    }
    return "OTHER";
}

// Entities in model space, optionally filtered by layer name.
function entities(ctx, layerName) {
    var ids = ctx.doc.queryAllEntities(false, true);
    var out = [];
    for (var i = 0; i < ids.length; i++) {
        var e = ctx.doc.queryEntity(ids[i]);
        if (isNull(e) || e.getBlockId() !== ctx.doc.getModelSpaceBlockId()) {
            continue;
        }
        if (!isNull(layerName) && e.getLayerName() !== layerName) {
            continue;
        }
        out.push(e);
    }
    return out;
}

// --- export -----------------------------------------------------------------

// PDF via QCAD's own print engine (Community edition, no trial stamp).
// opts: { paper: "A4" | "A3" | ... | "420x297" (mm), landscape: bool|undefined (auto),
//         monochrome: bool (default true: black lines on white) }
function exportPdf(ctx, path, opts) {
    path = resolve(path);
    opts = opts || {};
    var doc = ctx.doc, di = ctx.di;
    doc.setVariable("UnitSettings/PaperUnit", RS.Millimeter);
    var paper = opts.paper || "A4";
    var m = /^(\d+\.?\d*)x(\d+\.?\d*)$/.exec(paper);
    if (m) {
        doc.setVariable("PageSettings/PaperWidth", parseFloat(m[1]));
        doc.setVariable("PageSettings/PaperHeight", parseFloat(m[2]));
    } else {
        var ps = Print.getPaperSizeFromSizeName(paper);
        if (!ps.isValid()) {
            throw new Error("unknown paper size " + paper);
        }
        doc.setVariable("PageSettings/PaperWidth", ps.width());
        doc.setVariable("PageSettings/PaperHeight", ps.height());
    }
    ctx.view.setColorMode(opts.monochrome === false ? RGraphicsView.FullColor : RGraphicsView.BlackWhite);
    if (opts.landscape === true || opts.landscape === false) {
        Print.setPageOrientationEnum(di, opts.landscape ? RS.Landscape : RS.Portrait);
        Print.autoFitDrawing(di, false);
    } else {
        Print.autoFitDrawing(di, true);
    }
    di.regenerateScenes();
    var p = new Print(undefined, doc, ctx.view);
    if (!p.print(path)) {
        throw new Error("PDF export failed: " + path);
    }
    print("PDF " + path);
}

// PNG/JPG (format from the extension). opts: { width (px, default 1600), height,
// margin (px, default 20), background: "white" (default) | "black" }
function exportImage(ctx, path, opts) {
    path = resolve(path);
    opts = opts || {};
    var props = [];
    props["width"] = opts.width || 1600;
    props["height"] = opts.height || Math.round(props["width"] * 0.75);
    props["margin"] = isNull(opts.margin) ? 20 : opts.margin;
    props["backgroundColor"] = new RColor(opts.background || "white");
    props["antialiasing"] = true;
    props["monochrome"] = (opts.background || "white") === "white";
    props["zoomAll"] = true;
    props["regen"] = true;
    var res = exportBitmap(ctx.doc, ctx.scene, path, props, ctx.view);
    if (res[0] !== true) {
        throw new Error("image export failed: " + path + " " + res[1]);
    }
    print("IMAGE " + path);
}

// Files matching extensions (e.g. ["dxf"]) under dir, recursively, sorted.
function listFiles(dir, exts, recursive) {
    var out = [];
    var d = new QDir(resolve(dir));
    var infos = d.entryInfoList(makeQDirFilters(QDir.Files, QDir.Dirs, QDir.NoDotAndDotDot),
                                makeQDirSortFlags(QDir.Name));
    for (var i = 0; i < infos.length; i++) {
        var fi = infos[i];
        if (fi.isDir()) {
            if (recursive !== false) {
                out = out.concat(listFiles(fi.absoluteFilePath(), exts, true));
            }
        } else if (exts.indexOf(fi.suffix().toLowerCase()) !== -1) {
            out.push(fi.absoluteFilePath());
        }
    }
    return out;
}

function mkdirs(dir) {
    new QDir().mkpath(resolve(dir));
}
