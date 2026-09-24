'use strict';

const { BlendMode } = require('affinity:common');
const { SVG11 } = require('/colours.js');
const { AddChildNodesCommandBuilder, CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { FillDescriptor } = require('/fills.js');
const { Curve, PolyCurve, Rectangle, unionRects } = require('/geometry.js');
const { LineStyleDescriptor } = require('/linestyle.js');
const { ContainerNodeDefinition, PolyCurveNodeDefinition } = require('/nodes.js');
const { UnitType } = require('/units.js');

function isOk(result) {
    return (result?.value ?? result) == DialogResult.Ok.value;
}

class MarkBuilder {
    constructor(weight) {
        this.noFill = FillDescriptor.createNone();
        this.lineFill = FillDescriptor.createSolid(SVG11.black, BlendMode.Normal);
        this.lineStyle = LineStyleDescriptor.createDefault(weight);
        this.defs = [];
    }

    add(curve, name) {
        const poly = PolyCurve.create();
        poly.addCurve(curve);
        const def = PolyCurveNodeDefinition.create(poly, this.noFill, this.lineFill, this.lineStyle, this.noFill);
        def.userDescription = name;
        this.defs.push(def);
    }

    line(x1, y1, x2, y2) {
        this.add(Curve.createLineXY(x1, y1, x2, y2), "Crop mark");
    }

    circle(cx, cy, r) {
        this.add(Curve.createEllipse(new Rectangle(cx - r, cy - r, 2 * r, 2 * r)), "Registration mark");
    }
}

function addCropMarks(mb, rc, length, offset) {
    const x1 = rc.x, y1 = rc.y, x2 = rc.x + rc.width, y2 = rc.y + rc.height;
    mb.line(x1 - offset, y1, x1 - offset - length, y1);
    mb.line(x1, y1 - offset, x1, y1 - offset - length);
    mb.line(x1 - offset, y2, x1 - offset - length, y2);
    mb.line(x1, y2 + offset, x1, y2 + offset + length);
    mb.line(x2 + offset, y1, x2 + offset + length, y1);
    mb.line(x2, y1 - offset, x2, y1 - offset - length);
    mb.line(x2 + offset, y2, x2 + offset + length, y2);
    mb.line(x2, y2 + offset, x2, y2 + offset + length);
}

function addRegMarks(mb, rc, offset, inner, outer) {
    const x1 = rc.x, y1 = rc.y, x2 = rc.x + rc.width, y2 = rc.y + rc.height;
    const cx = rc.x + rc.width / 2, cy = rc.y + rc.height / 2;
    const d = offset + outer;
    const target = (tx, ty) => {
        mb.circle(tx, ty, inner);
        mb.line(tx, ty - outer, tx, ty + outer);
        mb.line(tx - outer, ty, tx + outer, ty);
    };
    target(cx, y1 - d);
    target(cx, y2 + d);
    target(x1 - d, cy);
    target(x2 + d, cy);
}

function createMarksCommand(nodes, originalSelection, opts) {
    if (!opts.cropMarks && !opts.regMarks)
        return null;
    const rects = nodes.map(n => n.getSpreadVisibleBox());
    const targets = opts.eachObject ? rects : [rects.reduce((a, b) => unionRects(a, b))];
    const mb = new MarkBuilder(opts.weight);
    for (const rc of targets) {
        if (opts.cropMarks)
            addCropMarks(mb, rc, opts.cropLength, opts.cropOffset);
        if (opts.regMarks)
            addRegMarks(mb, rc, opts.regOffset, opts.regInner, opts.regOuter);
    }
    // Add the layer and select it, add the marks with no insertion target so they go into
    // the current selection (the layer), then optionally restore the original selection.
    const layerBuilder = AddChildNodesCommandBuilder.create();
    layerBuilder.addNode(ContainerNodeDefinition.create("Printers Marks"));
    const marksBuilder = AddChildNodesCommandBuilder.create();
    for (const def of mb.defs)
        marksBuilder.addNode(def);
    const compound = CompoundCommandBuilder.create()
        .addCommand(layerBuilder.createCommand(true))
        .addCommand(marksBuilder.createCommand(false));
    if (opts.keepSelection)
        compound.addCommand(DocumentCommand.createSetSelection(originalSelection));
    return compound.createCommand();
}

function enableBy(toggle, controls) {
    const update = () => controls.forEach(c => c.isEnabled = toggle.value);
    toggle.onValueChangedHandler = update;
    update();
}

function buildDialog(doc) {
    const pt = doc.dpi / 72;
    const dlg = Dialog.create("Crop Marks");
    const col = dlg.addColumn();

    const crop = col.addGroup("Crop Marks");
    dlg.cropMarks = crop.addSwitch("Enabled", true);
    dlg.cropLength = crop.addUnitValueEditor("Length", UnitType.Pixel, doc.units, 6 * pt, 0).setNoMaxValue();
    dlg.cropOffset = crop.addUnitValueEditor("Offset", UnitType.Pixel, doc.units, 3 * pt, 0).setNoMaxValue();
    enableBy(dlg.cropMarks, [dlg.cropLength, dlg.cropOffset]);

    const reg = col.addGroup("Registration Marks");
    dlg.regMarks = reg.addSwitch("Enabled", true);
    dlg.regInner = reg.addUnitValueEditor("Inside radius", UnitType.Pixel, doc.units, 2 * pt, 0).setNoMaxValue();
    dlg.regOuter = reg.addUnitValueEditor("Outside radius", UnitType.Pixel, doc.units, 4 * pt, 0).setNoMaxValue();
    dlg.regOffset = reg.addUnitValueEditor("Offset", UnitType.Pixel, doc.units, 3 * pt, 0).setNoMaxValue();
    enableBy(dlg.regMarks, [dlg.regInner, dlg.regOuter, dlg.regOffset]);

    const opts = col.addGroup("Options");
    dlg.weight = opts.addUnitValueEditor("Stroke weight", UnitType.Pixel, UnitType.Point, 1 * pt, 0).setNoMaxValue().setPrecision(2);
    dlg.around = opts.addButtonSet("Draw marks around", ["Each object", "Entire selection"], 0);
    dlg.keepSelection = opts.addSwitch("Keep current selection", true);
    dlg.initialWidth = 420;
    return dlg;
}

function readOptions(dlg) {
    return {
        cropMarks: dlg.cropMarks.value,
        cropLength: dlg.cropLength.value,
        cropOffset: dlg.cropOffset.value,
        regMarks: dlg.regMarks.value,
        regInner: dlg.regInner.value,
        regOuter: dlg.regOuter.value,
        regOffset: dlg.regOffset.value,
        weight: dlg.weight.value,
        eachObject: dlg.around.selectedIndex == 0,
        keepSelection: dlg.keepSelection.value
    };
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const originalSelection = doc.selection;
    const nodes = originalSelection.nodes.toArray();
    if (nodes.length == 0) {
        alert("Please select one or more objects");
        return;
    }
    const dlg = buildDialog(doc);
    const update = (preview) => {
        const cmd = createMarksCommand(nodes, originalSelection, readOptions(dlg));
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
        alert("No printers marks were selected");
    }
    doc.clearPreviews();
}

module.exports.main = main;