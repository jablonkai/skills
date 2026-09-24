'use strict';

// Makes a grid of artboards from a starting position, size, spacing and count, with a live preview.

const { CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { ShapeNodeDefinition } = require('/nodes.js');
const { Rectangle } = require('/geometry.js');
const { ShapeRectangle } = require('/shapes.js');
const { UnitType } = require('/units.js');

function isOk(result) {
    return (result?.value ?? result) == DialogResult.Ok.value;
}

function buildDialog(docUnits, initialSize) {
    const dlg = Dialog.create("Add Artboards");
    const col = dlg.addColumn();

    const posGroup = col.addGroup("Initial Position");
    dlg.posX = posGroup.addUnitValueEditor("X", UnitType.Pixel, docUnits, 0);
    dlg.posY = posGroup.addUnitValueEditor("Y", UnitType.Pixel, docUnits, 0);

    const sizeGroup = col.addGroup("Artboard size");
    dlg.width = sizeGroup.addUnitValueEditor("Width", UnitType.Pixel, docUnits, initialSize, 0);
    dlg.height = sizeGroup.addUnitValueEditor("Height", UnitType.Pixel, docUnits, initialSize, 0);
    dlg.spaceWidth = sizeGroup.addUnitValueEditor("Spacing width", UnitType.Pixel, docUnits, 0, 0);
    dlg.spaceHeight = sizeGroup.addUnitValueEditor("Spacing height", UnitType.Pixel, docUnits, 0, 0);

    const countGroup = col.addGroup("Number of artboards");
    dlg.horzCount = countGroup.addUnitValueEditor("Horizontally", UnitType.Number, UnitType.Number, 1, 1).setPrecision(0);
    dlg.vertCount = countGroup.addUnitValueEditor("Vertically", UnitType.Number, UnitType.Number, 1, 1).setPrecision(0);
    return dlg;
}

function readOptions(dlg) {
    return {
        x: dlg.posX.value,
        y: dlg.posY.value,
        width: dlg.width.value,
        height: dlg.height.value,
        spaceWidth: dlg.spaceWidth.value,
        spaceHeight: dlg.spaceHeight.value,
        horzCount: Math.round(dlg.horzCount.value),
        vertCount: Math.round(dlg.vertCount.value)
    };
}

function createGridCommand(opts) {
    if (opts.width < 1 || opts.height < 1 || opts.horzCount < 1 || opts.vertCount < 1)
        return null;
    const builder = CompoundCommandBuilder.create();
    for (let j = 0; j < opts.vertCount; ++j) {
        for (let i = 0; i < opts.horzCount; ++i) {
            const x = opts.x + i * (opts.width + opts.spaceWidth);
            const y = opts.y + j * (opts.height + opts.spaceHeight);
            const def = ShapeNodeDefinition.createDefault();
            def.shape = ShapeRectangle.create();
            def.setBoundingRectangle(new Rectangle(x, y, opts.width, opts.height));
            builder.addCommand(DocumentCommand.createAddArtboard(def));
        }
    }
    return builder.createCommand();
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    if (doc.isMultiPage) {
        alert("Artboards cannot be inserted into a multi-page document");
        return;
    }

    const units = doc.units;
    const initialSize = 100 * doc.unitValueConverter.getConversionFactor(units, UnitType.Pixel);
    const dlg = buildDialog(units, initialSize);

    const update = (preview) => {
        const cmd = createGridCommand(readOptions(dlg));
        if (cmd)
            doc.executeCommand(cmd, preview);
        else
            doc.clearPreviews();
        return cmd != null;
    };
    dlg.onControlValueChangedHandler = () => update(true);
    update(true);
    while (isOk(dlg.runModal())) {
        if (update(false))
            break;
        alert("Artboards need a size of at least one pixel and a count of at least one");
    }
    doc.clearPreviews();
}

module.exports.main = main;
