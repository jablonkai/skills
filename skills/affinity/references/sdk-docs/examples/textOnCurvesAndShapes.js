'use strict';

// Creates one of each curve/shape-backed text node type on a new A4
// landscape document. Each node's text is just its type name (with spaces)
// laid against an actual curve or shape, with a small amount of formatting
// applied via StoryBuilder so the result is visibly styled.
//
// Layout (A4 landscape, roughly):
//   top-left      CurvePathTextNode  — text along a wavy bezier
//   top-right     PolyCurveTextNode  — text inside a rectangular polycurve container
//   bottom-left   ShapePathTextNode  — text along a heart outline
//   bottom-right  ShapeTextNode      — text inside a star

const { Document, DocumentPreset } = require('/document');
const { AddChildNodesCommandBuilder } = require('/commands');
const { StoryBuilder } = require('/storybuilder');
const { StoryDelta } = require('/storydelta');
const { GlyphAttDoubleType } = require('/glyphatts');
const { ParagraphAlignXType } = require('/paragraphatts');
const { FontWeight } = require('/fonts');
const { CurveBuilder, PolyCurve, Transform } = require('/geometry');
const { Shape, ShapeType } = require('/shapes');
const {
    CurvePathTextNodeDefinition,
    PolyCurveTextNodeDefinition,
    ShapePathTextNodeDefinition,
    ShapeTextNodeDefinition,
} = require('/nodes');

function newA4Landscape() {
    const a4 = DocumentPreset.all.filter(p => p.name.includes("A4"))[0];
    return Document.createFromPreset(a4, true);
}

function addNode(doc, def) {
    const builder = AddChildNodesCommandBuilder.create();
    builder.addNode(def);
    doc.executeCommand(builder.createCommand());
}

// A StoryBuilder seeded with frame-text defaults, body height, and a glyph
// fill colour applied as a delta so subsequent text picks it up.
function newBuilder(doc, heightPt) {
    const pxPerPt = doc.dpi / 72;
    const sb = StoryBuilder.create();
    sb.setToFrameTextDefaultStyle(doc.dpi, doc.rasterFormat);
    sb.applyGlyphDelta(StoryDelta.createGlyphDouble(GlyphAttDoubleType.Height, heightPt * pxPerPt));
    return sb;
}

// Builds: bold word, then italic word, then plain word — separated by spaces.
// e.g. parts = ["Curve", "Path", "Text", "Node"] →
//   "Curve" bold, " Path" italic, " Text Node" plain.
function addStyledWords(sb, parts) {
    sb.applyGlyphDelta(StoryDelta.createWeight(FontWeight.Bold));
    sb.addText(parts[0]);
    sb.applyGlyphDelta(StoryDelta.createWeight(FontWeight.Normal));

    sb.applyGlyphDelta(StoryDelta.createItalic(true));
    sb.addText(" " + parts[1]);
    sb.applyGlyphDelta(StoryDelta.createItalic(false));

    sb.addText(" " + parts.slice(2).join(" "));
}

// ── CurvePathTextNode: text flows along a wavy bezier curve ──────────────
function makeCurvePathNode(doc, originX, originY) {
    const curve = new CurveBuilder()
        .beginXY(0, 0)
        .addBezierXY(80, -120, 240, 120, 320, 0)
        .addBezierXY(400, -120, 560, 120, 640, 0)
        .createCurve();
    const polyCurve = PolyCurve.create();
    polyCurve.addCurve(curve);
    polyCurve.transform(Transform.createTranslate(originX, originY));

    const sb = newBuilder(doc, 28);
    addStyledWords(sb, ["Curve", "Path", "Text", "Node"]);
    return CurvePathTextNodeDefinition.createFromStoryBuilder(polyCurve, sb);
}

// ── PolyCurveTextNode: text flows inside an irregular blob ───────────────
// Mixes line segments with bezier sides so it's visibly not a frame
// rectangle: jagged top, curved right side, slanted bottom, bulging left.
function makePolyCurveNode(doc, x, y, w, h) {
    const blob = new CurveBuilder()
        .beginXY(x, y + h * 0.15)
        .lineToXY(x + w * 0.25, y)
        .lineToXY(x + w * 0.55, y + h * 0.10)
        .lineToXY(x + w * 0.85, y)
        .addBezierXY(x + w * 1.05, y + h * 0.35,
                     x + w * 0.95, y + h * 0.70,
                     x + w * 0.80, y + h)
        .lineToXY(x + w * 0.20, y + h * 0.85)
        .addBezierXY(x - w * 0.05, y + h * 0.75,
                     x - w * 0.05, y + h * 0.35,
                     x, y + h * 0.15)
        .close()
        .createCurve();
    const polyCurve = PolyCurve.create();
    polyCurve.addCurve(blob);

    const sb = newBuilder(doc, 22);
    sb.applyParagraphDelta(StoryDelta.createAlignX(ParagraphAlignXType.Centre));
    addStyledWords(sb, ["Poly", "Curve", "Text", "Node"]);
    return PolyCurveTextNodeDefinition.createFromStoryBuilder(polyCurve, sb);
}

// ── ShapePathTextNode: text flows along the outline of a heart shape ─────
function makeShapePathNode(doc, x, y, size) {
    const heart = Shape.create(ShapeType.Heart);
    const bounds = { x: x, y: y, width: size, height: size };

    const sb = newBuilder(doc, 22);
    addStyledWords(sb, ["Shape", "Path", "Text", "Node"]);
    return ShapePathTextNodeDefinition.createFromStoryBuilder(heart, bounds, sb);
}

// ── ShapeTextNode: text flows inside a star shape ────────────────────────
function makeShapeNode(doc, x, y, size) {
    const star = Shape.create(ShapeType.Star);
    const bounds = { x: x, y: y, width: size, height: size };

    const sb = newBuilder(doc, 18);
    sb.applyParagraphDelta(StoryDelta.createAlignX(ParagraphAlignXType.Centre));
    addStyledWords(sb, ["Shape", "Text", "Node"]);
    return ShapeTextNodeDefinition.createFromStoryBuilder(star, bounds, sb);
}

function main() {
    const doc = newA4Landscape();
    const w = doc.widthPixels;
    const h = doc.heightPixels;
    const margin = 40;

    // Top-left: curve path
    addNode(doc, makeCurvePathNode(doc, margin, h / 4));

    // Top-right: polycurve rectangle
    addNode(doc, makePolyCurveNode(doc, w / 2 + margin, margin, w / 2 - 2 * margin, h / 2 - 2 * margin));

    // Bottom-left: heart outline
    const shapeSize = Math.min(w / 2 - 2 * margin, h / 2 - 2 * margin);
    addNode(doc, makeShapePathNode(doc, margin, h / 2 + margin, shapeSize));

    // Bottom-right: star
    addNode(doc, makeShapeNode(doc, w / 2 + margin, h / 2 + margin, shapeSize));
}

module.exports.main = main;
