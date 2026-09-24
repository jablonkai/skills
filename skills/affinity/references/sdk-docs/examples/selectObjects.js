'use strict';

const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { Selection } = require('/selections.js');
const { ShapeType } = require('/shapes.js');

function isOk(result) {
    return (result?.value ?? result) == DialogResult.Ok.value;
}

function matches(node, opts) {
    if (node.isImageNode)
        return opts.images;
    if (node.isEmbeddedDocumentNode)
        return opts.placedDocuments;
    if (node.isVectorNode && node.pictureFrameEnabled)
        return opts.pictureFrames;
    if (node.isShapeNode) {
        const type = node.shapeType.value;
        if (type == ShapeType.Rectangle.value)
            return opts.rectangles;
        if (type == ShapeType.Ellipse.value)
            return opts.ellipses;
        return opts.otherShapes;
    }
    if (node.isPolyCurveNode)
        return opts.curves;
    if (node.isFrameTextNode)
        return opts.textFrames;
    if (node.isTextNode)
        return opts.otherText;
    if (node.isGroupNode)
        return opts.groups;
    return false;
}

function selectObjects(doc, opts) {
    const candidates = opts.currentSpreadOnly ? doc.currentSpread.children.all : doc.rootNode.children.all;
    const nodes = [];
    for (const node of candidates) {
        if (matches(node, opts))
            nodes.push(node);
    }
    if (nodes.length == 0) {
        alert(opts.currentSpreadOnly ? "No matching objects on the current spread" : "No matching objects in the document");
        return;
    }
    doc.selection = Selection.create(doc, nodes, true);
}

function buildDialog() {
    const dlg = Dialog.create("Select Objects");
    const col = dlg.addColumn();
    const grp = col.addGroup("Select");
    dlg.rectangles = grp.addSwitch("Rectangles", true);
    dlg.ellipses = grp.addSwitch("Ellipses", true);
    dlg.otherShapes = grp.addSwitch("Other shapes", true);
    dlg.curves = grp.addSwitch("Curves", true);
    dlg.textFrames = grp.addSwitch("Text frames", true);
    dlg.otherText = grp.addSwitch("Other text", true);
    dlg.groupsSwitch = grp.addSwitch("Groups", true);
    dlg.pictureFrames = grp.addSwitch("Picture frames", true);
    dlg.images = grp.addSwitch("Images", true);
    dlg.placedDocuments = grp.addSwitch("Placed documents", true);

    const switches = [
        dlg.rectangles, dlg.ellipses, dlg.otherShapes, dlg.curves, dlg.textFrames,
        dlg.otherText, dlg.groupsSwitch, dlg.pictureFrames, dlg.images, dlg.placedDocuments
    ];
    const row = col.addGroup("").addColumnStack();
    const addButton = (label, setValue) => {
        const button = row.addColumn().addGroup().addButton(label).setIsFullWidth();
        button.onClickHandler = () => switches.forEach(sw => sw.value = setValue(sw.value));
    };
    addButton("All", () => true);
    addButton("None", () => false);
    addButton("Invert", v => !v);

    const scope = col.addGroup("Scope");
    dlg.currentSpreadOnly = scope.addSwitch("Current spread only", true);
    return dlg;
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const dlg = buildDialog();
    if (!isOk(dlg.runModal()))
        return;
    selectObjects(doc, {
        rectangles: dlg.rectangles.value,
        ellipses: dlg.ellipses.value,
        otherShapes: dlg.otherShapes.value,
        curves: dlg.curves.value,
        textFrames: dlg.textFrames.value,
        otherText: dlg.otherText.value,
        groups: dlg.groupsSwitch.value,
        pictureFrames: dlg.pictureFrames.value,
        images: dlg.images.value,
        placedDocuments: dlg.placedDocuments.value,
        currentSpreadOnly: dlg.currentSpreadOnly.value
    });
}

module.exports.main = main;