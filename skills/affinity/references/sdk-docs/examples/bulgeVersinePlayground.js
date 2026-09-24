'use strict';

// Run from the Script Editor with:
// require('/examples/bulgeVersinePlayground.js').main();

const { app } = require('/application.js');
const { BlendMode } = require('affinity:common');
const { SVG11 } = require('/colours.js');
const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { FillDescriptor } = require('/fills.js');
const { CurveBuilder, PolyCurve } = require('/geometry.js');
const { LineStyleDescriptor } = require('/linestyle.js');
const { PolyCurveNodeDefinition } = require('/nodes.js');
const { UnitType } = require('/units.js');

const Operation = Object.freeze({
    Bulge: 0,
    Versine: 1,
});

const EndpointMode = Object.freeze({
    Absolute: 0,
    Relative: 1,
});

const VersineTolerance = 1e-6;

function formatNumber(value) {
    return Number.isFinite(value) ? value.toFixed(3) : String(value);
}

function addLine(polyCurve, start, end) {
    const curve = CurveBuilder.create()
        .beginXY(start.x, start.y)
        .lineToXY(end.x, end.y)
        .createCurve();
    polyCurve.addCurve(curve);
}

function createNodeDefinition(args) {
    const builder = CurveBuilder.create().beginXY(args.start.x, args.start.y);
    if (args.operation == Operation.Bulge) {
        if (args.endpointMode == EndpointMode.Relative)
            builder.bulgeRelativeXY(args.argument.x, args.argument.y, args.value);
        else
            builder.bulgeToXY(args.argument.x, args.argument.y, args.value);
    }
    else {
        if (args.endpointMode == EndpointMode.Relative)
            builder.versineRelativeXY(args.argument.x, args.argument.y, args.value);
        else
            builder.versineToXY(args.argument.x, args.argument.y, args.value);
    }

    const polyCurve = PolyCurve.create();
    polyCurve.addCurve(builder.createCurve());

    if (args.showGuides) {
        addLine(polyCurve, args.start, args.end);

        const markerSize = Math.max(4, Math.min(20, args.chordLength * 0.025));
        for (const point of [args.start, args.end]) {
            addLine(polyCurve,
                {x: point.x - markerSize, y: point.y},
                {x: point.x + markerSize, y: point.y});
            addLine(polyCurve,
                {x: point.x, y: point.y - markerSize},
                {x: point.x, y: point.y + markerSize});
        }
    }

    const noFill = FillDescriptor.createNone();
    const lineFill = FillDescriptor.createSolid(SVG11.blue, BlendMode.Normal);
    const definition = PolyCurveNodeDefinition.create(
        polyCurve,
        noFill,
        lineFill,
        LineStyleDescriptor.createDefault(3),
        noFill
    );
    definition.userDescription = "Bulge / Versine Playground";
    return definition;
}

function readArguments(dlg) {
    const start = {x: dlg.startX.value, y: dlg.startY.value};
    const argument = {x: dlg.argumentX.value, y: dlg.argumentY.value};
    const endpointMode = dlg.endpointMode.selectedIndex;
    const end = endpointMode == EndpointMode.Relative
        ? {x: start.x + argument.x, y: start.y + argument.y}
        : argument;
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const chordLength = Math.hypot(dx, dy);
    const operation = dlg.operation.selectedIndex;
    const value = operation == Operation.Bulge ? dlg.bulgeValue.value : dlg.versineValue.value;
    const versine = operation == Operation.Bulge ? value * chordLength * 0.5 : value;

    return {
        operation,
        endpointMode,
        start,
        argument,
        end,
        dx,
        dy,
        chordLength,
        value,
        versine,
        showGuides: dlg.showGuides.value,
    };
}

function describeArguments(args) {
    const lines = [
        `Resolved end: (${formatNumber(args.end.x)}, ${formatNumber(args.end.y)})`,
        `Chord: ${formatNumber(args.chordLength)} px`,
    ];

    if (args.chordLength == 0) {
        lines.push("Coincident endpoints: appends a zero-length line.");
        return {valid: true, text: lines.join('\n')};
    }

    if (Math.abs(args.versine) <= VersineTolerance) {
        lines.push("Tolerance-zero versine: appends a straight line.");
        return {valid: true, text: lines.join('\n')};
    }

    const absVersine = Math.abs(args.versine);
    const equivalentBulge = args.versine * 2 / args.chordLength;
    const sweepRadians = 4 * Math.atan(equivalentBulge);
    const radius = absVersine * 0.5 + args.chordLength * args.chordLength / (8 * absVersine);
    const direction = sweepRadians < 0 ? "clockwise" : "counterclockwise";
    const arcKind = Math.abs(sweepRadians) > Math.PI ? "major" :
        Math.abs(sweepRadians) == Math.PI ? "semicircle" : "minor";
    const centreDirection = args.versine < 0 ? -1 : 1;
    const centreDistance = centreDirection * (radius - absVersine);
    const centre = {
        x: (args.start.x + args.end.x) * 0.5 - args.dy / args.chordLength * centreDistance,
        y: (args.start.y + args.end.y) * 0.5 + args.dx / args.chordLength * centreDistance,
    };

    lines.push(
        `Signed sagitta: ${formatNumber(args.versine)} px`,
        `Equivalent bulge: ${formatNumber(equivalentBulge)}`,
        `Sweep: ${formatNumber(Math.abs(sweepRadians) * 180 / Math.PI)}° ${direction} (${arcKind} arc)`,
        `Radius: ${formatNumber(radius)} px`,
        `Centre: (${formatNumber(centre.x)}, ${formatNumber(centre.y)})`
    );
    return {valid: true, text: lines.join('\n')};
}

function buildDialog(doc) {
    const dlg = Dialog.create("Bulge / Versine Playground");
    const column = dlg.addColumn();

    const chordLength = Math.min(doc.widthPixels * 0.5, 600);
    const startX = doc.widthPixels * 0.5 - chordLength * 0.5;
    const endX = startX + chordLength;
    const y = doc.heightPixels * 0.5;
    const quarterCircleBulge = Math.tan(Math.PI / 8);

    const modeGroup = column.addGroup("CurveBuilder call");
    dlg.operation = modeGroup.addButtonSet("Parameter", ["Bulge", "Versine"], Operation.Bulge);

    const startGroup = column.addGroup("Start point");
    dlg.startX = startGroup.addUnitValueEditor("X", UnitType.Pixel, doc.units, startX).setPrecision(2);
    dlg.startY = startGroup.addUnitValueEditor("Y", UnitType.Pixel, doc.units, y).setPrecision(2);

    const argumentGroup = column.addGroup("End point");
    dlg.endpointMode = argumentGroup.addButtonSet(
        "Endpoint",
        ["To (x, y)", "Relative (dx, dy)"],
        EndpointMode.Absolute
    );
    dlg.argumentX = argumentGroup.addUnitValueEditor("X / dx", UnitType.Pixel, doc.units, endX).setPrecision(2);
    dlg.argumentY = argumentGroup.addUnitValueEditor("Y / dy", UnitType.Pixel, doc.units, y).setPrecision(2);

    const parameterGroup = column.addGroup("Arc parameter");
    dlg.bulgeValue = parameterGroup
        .addUnitValueEditor("Bulge", UnitType.Number, UnitType.Number, quarterCircleBulge, -4, 4)
        .setShowPopupSlider(true)
        .setPrecision(4);
    dlg.versineValue = parameterGroup
        .addUnitValueEditor("Versine", UnitType.Pixel, doc.units, quarterCircleBulge * chordLength * 0.5,
            -Math.max(doc.widthPixels, doc.heightPixels), Math.max(doc.widthPixels, doc.heightPixels))
        .setShowPopupSlider(true)
        .setPrecision(2)
        .setIsVisible(false);
    dlg.showGuides = parameterGroup.addSwitch("Show chord and endpoints", true);

    const resultGroup = column.addGroup("Computed geometry");
    dlg.readout = resultGroup.addStaticText(null, "").setIsFullWidth();
    resultGroup.addStaticText(null, "OK adds the displayed construction. Cancel removes the preview.").setIsFullWidth();

    dlg.initialWidth = 480;
    return dlg;
}

function main() {
    const doc = Document.current;
    if (!doc) {
        app.alert("Open a document before running the Bulge / Versine Playground.");
        return;
    }

    const dlg = buildDialog(doc);
    let updating = false;
    let previousOperation = dlg.operation.selectedIndex;
    let previousEndpointMode = dlg.endpointMode.selectedIndex;

    function preserveCurveAcrossModeChanges() {
        const endpointMode = dlg.endpointMode.selectedIndex;
        if (endpointMode != previousEndpointMode) {
            if (endpointMode == EndpointMode.Relative) {
                dlg.argumentX.value -= dlg.startX.value;
                dlg.argumentY.value -= dlg.startY.value;
            }
            else {
                dlg.argumentX.value += dlg.startX.value;
                dlg.argumentY.value += dlg.startY.value;
            }
            previousEndpointMode = endpointMode;
        }

        const operation = dlg.operation.selectedIndex;
        if (operation != previousOperation) {
            const chordLength = readArguments(dlg).chordLength;
            if (operation == Operation.Versine)
                dlg.versineValue.value = dlg.bulgeValue.value * chordLength * 0.5;
            else
                dlg.bulgeValue.value = chordLength == 0 ? 0 : dlg.versineValue.value * 2 / chordLength;
            previousOperation = operation;
        }
    }

    function update(preview) {
        if (updating)
            return false;
        updating = true;
        try {
            preserveCurveAcrossModeChanges();
            const isBulge = dlg.operation.selectedIndex == Operation.Bulge;
            dlg.bulgeValue.isVisible = isBulge;
            dlg.versineValue.isVisible = !isBulge;

            const args = readArguments(dlg);
            const description = describeArguments(args);
            dlg.readout.text = description.text;
            if (!description.valid) {
                doc.clearPreviews();
                return false;
            }

            doc.addNode(createNodeDefinition(args), null, undefined, preview);
            return true;
        }
        catch (error) {
            dlg.readout.text = `CurveBuilder rejected these arguments:\n${String(error)}`;
            doc.clearPreviews();
            return false;
        }
        finally {
            updating = false;
        }
    }

    dlg.onControlValueChangedHandler = () => update(true);
    update(true);

    while (dlg.runModal() == DialogResult.Ok) {
        if (update(false))
            return;
        app.alert("Choose arguments that CurveBuilder accepts before adding the curve.");
    }
    doc.clearPreviews();
}

module.exports.main = main;
