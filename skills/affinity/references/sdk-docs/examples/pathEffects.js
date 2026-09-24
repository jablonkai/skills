'use strict';

// Path effects for selected curve objects (convert shapes or text to curves first).
//
// Punk: pushes all control handles toward the centre of the object.
// Bloat: pushes all control handles away from the centre.
// PunkBloat / BloatPunk: one handle toward the centre, the other away.
// Twirl / AntiTwirl: the outgoing (or incoming) handle toward the centre, the other unchanged.
// Retract All: retracts all control handles.
// Make Rectangle / Make Ellipse: replaces the curves with the bounding rectangle or ellipse.

const { AddChildNodesCommandBuilder, CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { Curve, CurveBuilder, PolyCurve } = require('/geometry.js');
const { PolyCurveNodeDefinition } = require('/nodes.js');
const { UnitType } = require('/units.js');

const Effect = Object.freeze({
    Punk: 0, Bloat: 1, PunkBloat: 2, BloatPunk: 3, Twirl: 4, AntiTwirl: 5, RetractAll: 6, MakeRectangle: 7, MakeEllipse: 8
});
const EffectNames = ["Punk", "Bloat", "PunkBloat", "BloatPunk", "Twirl", "AntiTwirl", "Retract All", "Make Rectangle", "Make Ellipse"];

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

// Decomposes a curve into anchors with left (incoming) and right (outgoing) handles.
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

function applyEffect(pts, effect, centre, amount) {
    for (const p of pts) {
        const a = p.anchor;
        const dx = centre.x - a.x, dy = centre.y - a.y;
        const x = dx * amount, y = dy * amount;
        const toward = { x: centre.x - x, y: centre.y - y };
        const away = { x: a.x - x, y: a.y - y };
        const shifted = { x: a.x - (dx - x), y: a.y - (dy - y) };
        switch (effect) {
            case Effect.Punk: p.left = toward; p.right = toward; break;
            case Effect.Bloat: p.left = away; p.right = away; break;
            case Effect.PunkBloat: p.left = toward; p.right = shifted; break;
            case Effect.BloatPunk: p.left = shifted; p.right = toward; break;
            case Effect.Twirl: p.right = toward; break;
            case Effect.AntiTwirl: p.left = toward; break;
            case Effect.RetractAll: p.left = a; p.right = a; break;
        }
    }
}

function transformPolyCurve(polyCurve, effect, amount) {
    const bounds = polyCurve.boundingBox;
    const result = PolyCurve.create();
    if (effect == Effect.MakeRectangle) {
        result.addCurve(Curve.createRectangle(bounds));
        return result;
    }
    if (effect == Effect.MakeEllipse) {
        result.addCurve(Curve.createEllipse(bounds));
        return result;
    }
    const centre = bounds.centre;
    for (const curve of polyCurve.curves) {
        const d = decompose(curve);
        if (!d) {
            result.addCurve(curve.clone());
            continue;
        }
        applyEffect(d.pts, effect, centre, amount);
        result.addCurve(rebuild(d.pts, d.closed));
    }
    return result;
}

// A new curve object carrying the node's fills and stroke, so "apply to a copy" is one command.
function copyDefinition(node, poly) {
    const def = PolyCurveNodeDefinition.create(poly, node.brushFillDescriptor, node.penFillDescriptor,
        node.lineStyleDescriptor, node.transparencyFillDescriptor);
    def.transform = node.baseToSpreadTransform;
    def.userDescription = node.description;
    return def;
}

// Previews modify the nodes' curves, so always work from snapshots of the originals.
function createEffectCommand(sources, opts) {
    const cmds = [];
    const copies = AddChildNodesCommandBuilder.create();
    let copyCount = 0;
    for (const { node, original } of sources) {
        const poly = transformPolyCurve(original, opts.effect, opts.amount);
        if (poly.curveCount == 0)
            continue;
        if (opts.copyPath) {
            copies.addNode(copyDefinition(node, poly));
            ++copyCount;
        }
        else {
            cmds.push(DocumentCommand.createSetCurves(node.curvesInterface, poly));
        }
    }
    if (copyCount > 0)
        cmds.push(copies.createCommand(true));
    return compound(cmds);
}

function readOptions(dlg) {
    return {
        effect: dlg.effect.selectedIndex,
        amount: dlg.offset.value * 0.01,
        copyPath: dlg.copyPath.value
    };
}

function buildDialog() {
    const dlg = Dialog.create("Path Effects");
    const col = dlg.addColumn();
    const effect = col.addGroup("Effect");
    dlg.effect = effect.addRadioGroup("", EffectNames, Effect.Punk);
    const opts = col.addGroup("Options");
    dlg.offset = opts.addUnitValueEditor("Offset from centre %", UnitType.Number, UnitType.Number, 50, -1000, 1000).setPrecision(0);
    dlg.copyPath = opts.addSwitch("Apply to a copy", false);
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
    const dlg = buildDialog();
    const update = (preview) => {
        const cmd = createEffectCommand(sources, readOptions(dlg));
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