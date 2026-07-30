// -------------------------
// Makes a grid of artboards
// -------------------------

'use strict';

const { CompoundCommandBuilder, DocumentCommand } = require('/commands');
const { Dialog, DialogResult } = require('/dialog');
const { Document } = require('/document');
const { ShapeNodeDefinition } = require('/nodes');
const { Rectangle } = require('/geometry');
const { ShapeCornerType, ShapeRectangle } = require('/shapes');
const { UnitType } = require('/units');

function buildDialog(doc, docUnits, initialSize) {
    const dlg = Dialog.create("Add Artboards");
    const col = dlg.addColumn();
    const posGroup = col.addGroup("Initial Position");
    dlg.posX = posGroup.addUnitValueEditor("X", UnitType.Pixel, docUnits, 0, 0, 0).setNoMinValue().setNoMaxValue();
    dlg.posY = posGroup.addUnitValueEditor("Y", UnitType.Pixel, docUnits, 0, 0, 0).setNoMinValue().setNoMaxValue();

    const sizeGroup = col.addGroup("Artboard size");
    dlg.widthCtrl = sizeGroup.addUnitValueEditor("Width", UnitType.Pixel, docUnits, initialSize, 0, initialSize).setNoMaxValue();
    dlg.heightCtrl = sizeGroup.addUnitValueEditor("Height", UnitType.Pixel, docUnits, initialSize, 0, initialSize).setNoMaxValue();
    dlg.spaceWidthCtrl = sizeGroup.addUnitValueEditor("Spacing width", UnitType.Pixel, docUnits, 0, 0, 1).setNoMaxValue();
    dlg.spaceHeightCtrl = sizeGroup.addUnitValueEditor("Spacing height", UnitType.Pixel, docUnits, 0, 0, 1).setNoMaxValue();
    
    const countGroup = col.addGroup("Number of artboards");
    dlg.horzCountCtrl = countGroup.addUnitValueEditor("Horizontally", UnitType.Number, UnitType.Number, 1, 1, 1).setNoMaxValue().setPrecision(0);
    dlg.vertCountCtrl = countGroup.addUnitValueEditor("Vertically", UnitType.Number, UnitType.Number, 1, 1, 1).setNoMaxValue().setPrecision(0);

    dlg.createCommand = () => {
        const width = dlg.widthCtrl.value;
        const height = dlg.heightCtrl.value;
        const horzCount = dlg.horzCountCtrl.value;
        const vertCount = dlg.vertCountCtrl.value;

        if (width < 1 || height < 1 || horzCount < 1 || vertCount < 1)
            return null;

        const startx = dlg.posX.value;
        const starty = dlg.posY.value;
        const spaceWidth = dlg.spaceWidthCtrl.value;
        const spaceHeight = dlg.spaceHeightCtrl.value;
        const builder = CompoundCommandBuilder.create();
        for (let j = 0; j < vertCount; ++j) {
            for (let i = 0; i < horzCount; ++i) {
                const x = startx + i * (width + spaceWidth);
                const y = starty + j * (height + spaceHeight);
                const rect = new Rectangle(x, y, width, height);
                const def = ShapeNodeDefinition.createDefault();
                def.shape = ShapeRectangle.create();
                def.setBoundingRectangle(rect);
                const cmd = DocumentCommand.createAddArtboard(def);
                builder.addCommand(cmd);
            }
        }
        return builder.createCommand();
    };

    dlg.onControlValueChangedHandler = () => {
        const cmd = dlg.createCommand();
        if (cmd == null)
            doc.clearPreviews();
        else
            doc.executeCommand(cmd, true);
    };
    return dlg;
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
    const uvc = doc.unitValueConverter;
    const factor = uvc.getConversionFactor(units, UnitType.Pixel);
    
    const dlg = buildDialog(doc, units, factor * 100);
    function update(preview) {
        const cmd = dlg.createCommand();
        if (cmd == null)
            doc.clearPreviews();
        else
            doc.executeCommand(cmd, preview);
    }
    update(true);
    if (dlg.runModal() == DialogResult.Ok)
        update(false);
    else
        doc.clearPreviews();
}

module.exports.main = main;
