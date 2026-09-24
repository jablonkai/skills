'use strict';

// Strokes Weight Up: increases the stroke weight of every selected object by 1pt.

const { CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Document } = require('/document.js');
const { LineStyle, LineStyleMask } = require('/linestyle.js');
const { Selection } = require('/selections.js');

const StepPoints = 1;

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const nodes = doc.selection.nodes.filter(n => n.isVectorNode || n.isTextNode).toArray();
    if (nodes.length == 0) {
        alert("Please select one or more objects with a stroke");
        return;
    }
    const step = StepPoints * doc.dpi / 72;
    const builder = CompoundCommandBuilder.create();
    for (const node of nodes) {
        const lineStyle = LineStyle.createDefault();
        lineStyle.weight = Math.max(0, node.lineWeight + step);
        builder.addCommand(DocumentCommand.createSetLineStyle(Selection.create(doc, node), lineStyle, { lineStyleMask: LineStyleMask.Weight }));
    }
    doc.executeCommand(builder.createCommand());
}

module.exports.main = main;