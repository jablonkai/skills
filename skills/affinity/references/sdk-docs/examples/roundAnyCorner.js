'use strict';

// Rounds the corners of the selected curves with a given radius.
// Smooth points are left alone; the radius is clamped to half the shorter
// adjacent segment. Previews live.

const { CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { CurveBuilder, PolyCurve } = require('/geometry.js');
const { UnitType } = require('/units.js');

function isOk(result) {
    return (result?.value ?? result) == DialogResult.Ok.value;
}

function compound(cmds) {
    if (cmds.length == 0)
        return null;
    const builder = CompoundCommandBuilder.create();
    for (const cmd of cmds)
        builder.addCommand(cmd);
    return builder.createCommand();
}

// ---- Curve helpers --------------------------------------------------------------------------

function samePoint(a, b) {
    return Math.abs(a.x - b.x) < 1e-6 && Math.abs(a.y - b.y) < 1e-6;
}

function dist(a, b) {
    return Math.hypot(b.x - a.x, b.y - a.y);
}

// Anchors with left (incoming) and right (outgoing) handles; a retracted handle sits on its anchor.
function decompose(curve) {
    const bez = curve.beziers.toArray();
    if (bez.length == 0)
        return null;
    const closed = curve.isClosed;
    const wraps = closed && samePoint(bez[bez.length - 1].end, bez[0].start);
    const pts = bez.map(b => ({ anchor: { x: b.start.x, y: b.start.y }, left: null, right: { x: b.c1.x, y: b.c1.y } }));
    if (!wraps)
        pts.push({ anchor: { x: bez[bez.length - 1].end.x, y: bez[bez.length - 1].end.y }, left: null, right: null });
    for (let i = 0; i < bez.length; ++i)
        pts[(i + 1) % pts.length].left = { x: bez[i].c2.x, y: bez[i].c2.y };
    for (const p of pts) {
        p.left ??= { x: p.anchor.x, y: p.anchor.y };
        p.right ??= { x: p.anchor.x, y: p.anchor.y };
    }
    return { pts, closed };
}

function rebuild(pts, closed) {
    const b = CurveBuilder.create().beginXY(pts[0].anchor.x, pts[0].anchor.y);
    const segments = closed ? pts.length : pts.length - 1;
    for (let i = 0; i < segments; ++i) {
        const p = pts[i], q = pts[(i + 1) % pts.length];
        b.addBezierXY(p.right.x, p.right.y, q.left.x, q.left.y, q.anchor.x, q.anchor.y);
    }
    if (closed)
        b.close();
    return b.createCurve();
}

// Applies a per-curve transform to every curve of every source, from the pre-preview snapshots.
function createCurvesCommand(sources, transformCurve) {
    const cmds = [];
    for (const { node, original } of sources) {
        const poly = PolyCurve.create();
        for (const curve of original)
            poly.addCurve(transformCurve(curve) ?? curve.clone());
        if (poly.curveCount > 0)
            cmds.push(DocumentCommand.createSetCurves(node.curvesInterface, poly));
    }
    return compound(cmds);
}

function selectedCurveSources(doc) {
    return doc.selection.nodes.filter(n => n.isPolyCurveNode).toArray()
        .map(node => ({ node, original: node.polyCurve.clone() }));
}

function previewLoop(doc, dlg, build, onCommit) {
    const update = (preview) => {
        const cmd = build();
        if (cmd)
            doc.executeCommand(cmd, preview);
        else
            doc.clearPreviews();
        return cmd;
    };
    dlg.onControlValueChangedHandler = () => update(true);
    update(true);
    if (isOk(dlg.runModal())) {
        const cmd = update(false);
        if (cmd && onCommit)
            onCommit(cmd);
    }
    doc.clearPreviews();
}

function unit(v) {
    const len = Math.hypot(v.x, v.y);
    return len < 1e-9 ? null : { x: v.x / len, y: v.y / len };
}

// Direction the curve arrives at / leaves the anchor, falling back to the neighbouring anchor
// when the handle is retracted.
function tangents(prev, p, next) {
    const tin = unit({ x: p.anchor.x - p.left.x, y: p.anchor.y - p.left.y }) ?? unit({ x: p.anchor.x - prev.anchor.x, y: p.anchor.y - prev.anchor.y });
    const tout = unit({ x: p.right.x - p.anchor.x, y: p.right.y - p.anchor.y }) ?? unit({ x: next.anchor.x - p.anchor.x, y: next.anchor.y - p.anchor.y });
    return { tin, tout };
}

function roundCurve(curve, radius, minAngleRad) {
    const d = decompose(curve);
    if (!d || d.pts.length < 3)
        return null;
    const { pts, closed } = d;
    const n = pts.length;
    const out = [];
    for (let i = 0; i < n; ++i) {
        const p = pts[i];
        const isEnd = !closed && (i == 0 || i == n - 1);
        const prev = pts[(i + n - 1) % n], next = pts[(i + 1) % n];
        const { tin, tout } = isEnd ? { tin: null, tout: null } : tangents(prev, p, next);
        if (!tin || !tout) {
            out.push(p);
            continue;
        }
        const dot = Math.max(-1, Math.min(1, tin.x * tout.x + tin.y * tout.y));
        const turn = Math.acos(dot);                       // turning angle at the corner
        if (turn < minAngleRad || Math.PI - turn < 1e-3) { // straight-through or a spike
            out.push(p);
            continue;
        }
        const limit = 0.5 * Math.min(dist(prev.anchor, p.anchor), dist(p.anchor, next.anchor));
        const offset = Math.min(radius * Math.tan(turn / 2), limit);
        const r = offset / Math.tan(turn / 2);
        const h = (4 / 3) * Math.tan(turn / 4) * r;
        const pin = { x: p.anchor.x - tin.x * offset, y: p.anchor.y - tin.y * offset };
        const pout = { x: p.anchor.x + tout.x * offset, y: p.anchor.y + tout.y * offset };
        out.push({ anchor: pin, left: samePoint(p.left, p.anchor) ? pin : p.left, right: { x: pin.x + tin.x * h, y: pin.y + tin.y * h } });
        out.push({ anchor: pout, left: { x: pout.x - tout.x * h, y: pout.y - tout.y * h }, right: samePoint(p.right, p.anchor) ? pout : p.right });
    }
    return rebuild(out, closed);
}

function buildDialog(doc) {
    const pt = doc.dpi / 72;
    const dlg = Dialog.create("Round Any Corner");
    const grp = dlg.addColumn().addGroup("Corners");
    dlg.radius = grp.addUnitValueEditor("Radius", UnitType.Pixel, doc.units, 12 * pt, 0);
    dlg.minAngle = grp.addUnitValueEditor("Ignore corners shallower than (°)", UnitType.Number, UnitType.Number, 5, 0, 179).setPrecision(0);
    return dlg;
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const sources = selectedCurveSources(doc);
    if (sources.length == 0) {
        alert("Please select one or more curve objects (convert shapes or text to curves first)");
        return;
    }
    const dlg = buildDialog(doc);
    previewLoop(doc, dlg, () => createCurvesCommand(sources, curve => roundCurve(curve, dlg.radius.value, dlg.minAngle.value * Math.PI / 180)));
}

module.exports.main = main;