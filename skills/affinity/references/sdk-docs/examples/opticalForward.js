'use strict';

// Optical Forward: moves the selection forward in the z-order past the nearest sibling whose
// bounds overlap it, so every step produces a visible change. Ordinary "Forward One"
// steps past siblings that may not touch the selection at all.

const { DocumentCommand, NodeMoveType } = require('/commands.js');
const { Document } = require('/document.js');
const { rectsIntersect, unionRects } = require('/geometry.js');

const Forward = true;

function opticalMove(doc, forward) {
    const nodes = doc.selection.nodes.toArray();
    if (nodes.length == 0) {
        alert("Please select one or more objects");
        return;
    }
    const parent = nodes[0].parent;
    if (!parent || nodes.some(n => !n.parent || !n.parent.isSameNode(parent))) {
        alert("The selected objects must share the same parent");
        return;
    }

    // Children run back to front; the selection's siblings and its extent.
    const siblings = parent.children.toArray();
    const isSelected = siblings.map(s => nodes.some(n => n.isSameNode(s)));
    const bounds = nodes.map(n => n.getSpreadVisibleBox()).reduce((a, b) => unionRects(a, b));

    // Nearest sibling beyond the selection, in the direction of travel, that overlaps it.
    const indices = isSelected.flatMap((sel, i) => sel ? [i] : []);
    const start = forward ? Math.max(...indices) + 1 : Math.min(...indices) - 1;
    const step = forward ? 1 : -1;
    let target = null;
    for (let i = start; i >= 0 && i < siblings.length; i += step) {
        if (!isSelected[i] && rectsIntersect(bounds, siblings[i].getSpreadVisibleBox())) {
            target = siblings[i];
            break;
        }
    }
    if (!target)
        return;
    doc.executeCommand(DocumentCommand.createMoveNodes(doc.selection, target, forward ? NodeMoveType.After : NodeMoveType.Before));
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    opticalMove(doc, Forward);
}

module.exports.main = main;