'use strict';

// Counts the selected objects and reports a breakdown by type, including nested children.

const { Document } = require('/document.js');

function classify(node) {
    if (node.isImageNode)
        return "Images";
    if (node.isEmbeddedDocumentNode)
        return "Placed documents";
    if (node.isVectorNode && node.pictureFrameEnabled)
        return "Picture frames";
    if (node.isShapeNode)
        return "Shapes";
    if (node.isPolyCurveNode)
        return "Curves";
    if (node.isTextNode)
        return "Text";
    if (node.isGroupNode)
        return "Groups";
    if (node.isContainerNode)
        return "Layers";
    return "Other";
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const nodes = doc.selection.nodes.toArray();
    if (nodes.length == 0) {
        alert("Nothing is selected");
        return;
    }

    const counts = new Map();
    const tally = node => counts.set(classify(node), (counts.get(classify(node)) ?? 0) + 1);
    let nested = 0;
    for (const node of nodes) {
        tally(node);
        for (const child of node.children.all) {
            tally(child);
            ++nested;
        }
    }

    const lines = [`${nodes.length} selected object${nodes.length == 1 ? "" : "s"}`];
    if (nested > 0)
        lines.push(`${nested} nested object${nested == 1 ? "" : "s"} inside them`);
    lines.push("");
    for (const [type, count] of [...counts].sort((a, b) => b[1] - a[1]))
        lines.push(`${type}: ${count}`);
    alert(lines.join("\n"));
}

module.exports.main = main;