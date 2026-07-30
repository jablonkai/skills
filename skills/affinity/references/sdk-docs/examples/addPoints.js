'use strict';

const { Document } = require('/document');
const { DocumentCommand, CompoundCommandBuilder } = require('/commands');
const { CurveBuilder, PolyCurve } = require('/geometry');

const doc = Document.current;

function createNewCurve(curve) {
    const builder = CurveBuilder.create();
    const firstPoint = curve.beziers.first?.start;
    if (!firstPoint)
        return;
    builder.begin(firstPoint);
    for (const bez of curve.beziers) {
        const t = bez.getParamAtLength(bez.length * 0.5);
        const curves = bez.split(t);
        builder.addBezierXY(curves.left.c1.x, curves.left.c1.y, curves.left.c2.x, curves.left.c2.y, curves.left.end.x, curves.left.end.y);
        builder.addBezierXY(curves.right.c1.x, curves.right.c1.y, curves.right.c2.x, curves.right.c2.y, curves.right.end.x, curves.right.end.y);
    }
    return builder.createCurve();
}

function createNewPolyCurve(polyCurve) {
    const newPolyCurve = PolyCurve.create();
    for (const curve of polyCurve) {
        const newCurve = createNewCurve(curve);
        if (newCurve) {
            newPolyCurve.addCurve(newCurve);
        }
    }
    return newPolyCurve;
}

function addPoints(polyCurveNodes) {
    const cmds = [];
    for (const polyCurveNode of polyCurveNodes) {
        const newPoly = createNewPolyCurve(polyCurveNode.polyCurve);
        if (newPoly.curveCount > 0) {
            cmds.push(DocumentCommand.createSetPolyCurveNodeCurves(polyCurveNode, newPoly));
        }
    }

    if (cmds.length == 0)
        return;
    if (cmds.length == 1)
        doc.executeCommand(cmds[0]);
    else {
        const builder = CompoundCommandBuilder.create();
        for (const cmd of cmds) {
            builder.addCommand(cmd);
        }
        doc.executeCommand(builder.createCommand());
    }
}

function main() {
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const nodes = doc.selection.nodes.filter(node => node.isPolyCurveNode);
    if (nodes.isEmpty) {
        alert("Select some curves");
        return;
    }
    addPoints(nodes);
}

module.exports.main = main;
