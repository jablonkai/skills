'use strict';

const { CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { CurveBuilder, PolyCurve } = require('/geometry.js');
const { UnitType } = require('/units.js');

const CornerType = Object.freeze({ Rounded: 0, InverseRounded: 1, Bevel: 2, Inset: 3, Fancy: 4 });
const CornerNames = ["Rounded", "Inverse Rounded", "Bevel", "Inset", "Fancy"];
const Patterns = [
    "all points", "first point", "last point", "second point", "third point", "fourth point",
    "first two", "second and third", "last two", "first and last", "odd points", "even points"
];

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

function samePoint(a, b) {
    return Math.abs(a.x - b.x) < 1e-6 && Math.abs(a.y - b.y) < 1e-6;
}

function decompose(curve) {
    const bez = curve.beziers.toArray();
    if (bez.length == 0)
        return null;
    const closed = curve.isClosed;
    const wraps = closed && samePoint(bez[bez.length - 1].end, bez[0].start);
    const pts = bez.map(b => ({ anchor: b.start, left: null, right: b.c1 }));
    if (!wraps)
        pts.push({ anchor: bez[bez.length - 1].end, left: null, right: null });
    for (let i = 0; i < bez.length; ++i)
        pts[(i + 1) % pts.length].left = bez[i].c2;
    for (const p of pts) {
        p.left ??= p.anchor;
        p.right ??= p.anchor;
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

function pointQualifies(index, count, closed, pattern) {
    if (!closed && (index == 0 || index == count - 1))
        return false;
    switch (pattern) {
        case "all points": return true;
        case "first point": return index == 0;
        case "last point": return index == count - 1;
        case "second point": return index == 1;
        case "third point": return index == 2;
        case "fourth point": return index == 3;
        case "first two": return index <= 1;
        case "second and third": return index == 1 || index == 2;
        case "last two": return index >= count - 2;
        case "first and last": return index == 0 || index == count - 1;
        case "even points": return index % 2 != 0;
        case "odd points": return index % 2 == 0;
    }
    return false;
}

// Point at `offset` along the line from `from` toward `to`.
function towards(from, to, offset) {
    const len = Math.hypot(to.x - from.x, to.y - from.y);
    if (len == 0)
        return { x: from.x, y: from.y };
    return { x: from.x + (to.x - from.x) / len * offset, y: from.y + (to.y - from.y) / len * offset };
}

function retracted(p) {
    return { anchor: p, left: p, right: p };
}

function cornerPoints(corner, next, prev, cornerType, offset) {
    const p1 = towards(corner, next, offset);   // on the outgoing edge
    const p2 = towards(corner, prev, offset);   // on the incoming edge
    const z = { x: p2.x + p1.x - corner.x, y: p2.y + p1.y - corner.y };
    switch (cornerType) {
        case CornerType.Rounded:
            return [{ anchor: p2, left: p2, right: corner }, retracted(p1)];
        case CornerType.InverseRounded:
            return [{ anchor: p2, left: p2, right: z }, retracted(p1)];
        case CornerType.Bevel:
            return [retracted(p2), retracted(p1)];
        case CornerType.Inset:
            return [retracted(p2), retracted(z), retracted(p1)];
        case CornerType.Fancy: {
            const third = 1 / 3, twoThirds = 2 / 3;
            const t1 = { x: (corner.x - p2.x) * twoThirds, y: (corner.y - p2.y) * twoThirds };
            const t2 = { x: (corner.x - p1.x) * twoThirds, y: (corner.y - p1.y) * twoThirds };
            const d = { x: z.x + third * (p1.x - z.x), y: z.y + third * (p1.y - z.y) };
            const e = { x: z.x + third * (p2.x - z.x), y: z.y + third * (p2.y - z.y) };
            const f = { x: d.x + twoThirds * (corner.x - t1.x - d.x), y: d.y + twoThirds * (corner.y - t1.y - d.y) };
            const g = { x: e.x + twoThirds * (corner.x - t2.x - e.x), y: e.y + twoThirds * (corner.y - t2.y - e.y) };
            const h = { x: z.x + t1.x + t2.x, y: z.y + t1.y + t2.y };
            return [p2, e, g, h, f, d, p1].map(retracted);
        }
    }
    return [{ anchor: corner, left: corner, right: corner }];
}

function transformCurve(curve, opts) {
    const d = decompose(curve);
    if (!d)
        return curve.clone();
    const { pts, closed } = d;
    const count = pts.length;
    const out = [];
    for (let i = 0; i < count; ++i) {
        if (!pointQualifies(i, count, closed, opts.pattern)) {
            out.push(pts[i]);
            continue;
        }
        const next = pts[(i + 1) % count].anchor;
        const prev = pts[(i + count - 1) % count].anchor;
        out.push(...cornerPoints(pts[i].anchor, next, prev, opts.cornerType, opts.offset));
    }
    return rebuild(out, closed);
}

// Previews modify the nodes' curves, so always work from snapshots of the originals.
function createCornerCommand(sources, opts) {
    const cmds = [];
    for (const { node, original } of sources) {
        const poly = PolyCurve.create();
        for (const curve of original.curves)
            poly.addCurve(transformCurve(curve, opts));
        if (poly.curveCount > 0)
            cmds.push(DocumentCommand.createSetCurves(node.curvesInterface, poly));
    }
    return compound(cmds);
}

function readOptions(dlg) {
    return {
        cornerType: dlg.cornerType.selectedIndex,
        offset: dlg.offset.value,
        pattern: Patterns[dlg.pattern.selectedIndex]
    };
}

function buildDialog(doc) {
    const pt = doc.dpi / 72;
    const dlg = Dialog.create("Corner Effects");
    const col = dlg.addColumn();
    const type = col.addGroup("Corner Type");
    dlg.cornerType = type.addRadioGroup("", CornerNames, CornerType.Rounded);
    const opts = col.addGroup("Options");
    dlg.offset = opts.addUnitValueEditor("Offset", UnitType.Pixel, doc.units, 12 * pt, 0).setNoMaxValue();
    dlg.pattern = opts.addComboBox("Pattern", Patterns, 0);
    return dlg;
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const nodes = doc.selection.nodes.filter(n => n.isPolyCurveNode).toArray();
    if (nodes.length == 0) {
        alert("Please select one or more curve objects (convert shapes or text to curves first)");
        return;
    }
    const sources = nodes.map(node => ({ node, original: node.polyCurve.clone() }));
    const dlg = buildDialog(doc);
    const update = (preview) => {
        const cmd = createCornerCommand(sources, readOptions(dlg));
        if (cmd)
            doc.executeCommand(cmd, preview);
        else
            doc.clearPreviews();
    };
    dlg.onControlValueChangedHandler = () => update(true);
    update(true);
    if (isOk(dlg.runModal()))
        update(false);
    doc.clearPreviews();
}

module.exports.main = main;