'use strict';

// Swaps the positions of two selected objects, keeping their centres.

const { CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Document } = require('/document.js');
const { Transform } = require('/geometry.js');
const { Selection } = require('/selections.js');

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const nodes = doc.selection.nodes.toArray();
    if (nodes.length != 2) {
        alert("Please select exactly two objects");
        return;
    }
    const [a, b] = nodes.map(n => ({ node: n, c: n.getSpreadBaseBox().centre }));
    const builder = CompoundCommandBuilder.create()
        .addCommand(DocumentCommand.createTransform(Selection.create(doc, a.node), Transform.createTranslate(b.c.x - a.c.x, b.c.y - a.c.y)))
        .addCommand(DocumentCommand.createTransform(Selection.create(doc, b.node), Transform.createTranslate(a.c.x - b.c.x, a.c.y - b.c.y)));
    doc.executeCommand(builder.createCommand());
}

module.exports.main = main;