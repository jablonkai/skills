'use strict';

// Run from the Script Editor with:
// require('/examples/bulgedPolyline.js').main();

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

const EndpointMode = Object.freeze({
    Absolute: 0,
    Relative: 1,
});

const VersineTolerance = 1e-6;

function formatNumber(value) {
    return Number.isFinite(value) ? value.toFixed(3) : String(value);
}

function createCurve(sections) {
    const builder = CurveBuilder.create().beginXY(sections[0].start.x, sections[0].start.y);
    for (const section of sections)
        builder.bulgeToXY(section.end.x, section.end.y, section.bulge);
    return builder.createCurve();
}

function createNodeDefinition(sections) {
    const polyCurve = PolyCurve.create();
    polyCurve.addCurve(createCurve(sections));

    const noFill = FillDescriptor.createNone();
    const lineFill = FillDescriptor.createSolid(SVG11.blue, BlendMode.Normal);
    const definition = PolyCurveNodeDefinition.create(
        polyCurve,
        noFill,
        lineFill,
        LineStyleDescriptor.createDefault(3),
        noFill
    );
    definition.userDescription = "Bulged Polyline";
    return definition;
}

function currentStart(dlg, sections) {
    if (sections.length > 0)
        return sections[sections.length - 1].end;
    return {x: dlg.startX.value, y: dlg.startY.value};
}

function readCurrentSection(dlg, sections) {
    const start = currentStart(dlg, sections);
    const argument = {x: dlg.argumentX.value, y: dlg.argumentY.value};
    const endpointMode = dlg.endpointMode.selectedIndex;
    const end = endpointMode == EndpointMode.Relative
        ? {x: start.x + argument.x, y: start.y + argument.y}
        : argument;
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const chordLength = Math.hypot(dx, dy);
    const bulge = dlg.bulgeValue.value;

    return {
        start: {x: start.x, y: start.y},
        end,
        dx,
        dy,
        chordLength,
        bulge,
        versine: bulge * chordLength * 0.5,
    };
}

function describeCurrentSection(section, addedSectionCount) {
    const lines = [
        `Added sections: ${addedSectionCount}`,
        `Current section: ${addedSectionCount + 1}`,
        `Start: (${formatNumber(section.start.x)}, ${formatNumber(section.start.y)})`,
        `End: (${formatNumber(section.end.x)}, ${formatNumber(section.end.y)})`,
        `Chord: ${formatNumber(section.chordLength)} px`,
        `Bulge: ${formatNumber(section.bulge)}`,
    ];

    if (section.chordLength == 0) {
        lines.push("Coincident endpoints: appends a zero-length line.");
        return lines.join('\n');
    }

    if (Math.abs(section.versine) <= VersineTolerance) {
        lines.push("Tolerance-zero versine: appends a straight line.");
        return lines.join('\n');
    }

    const sweepRadians = 4 * Math.atan(section.bulge);
    const absVersine = Math.abs(section.versine);
    const radius = absVersine * 0.5 + section.chordLength * section.chordLength / (8 * absVersine);
    const direction = sweepRadians < 0 ? "clockwise" : "counterclockwise";
    const arcKind = Math.abs(sweepRadians) > Math.PI ? "major" :
        Math.abs(sweepRadians) == Math.PI ? "semicircle" : "minor";

    lines.push(
        `Signed sagitta: ${formatNumber(section.versine)} px`,
        `Sweep: ${formatNumber(Math.abs(sweepRadians) * 180 / Math.PI)}° ${direction} (${arcKind} arc)`,
        `Radius: ${formatNumber(radius)} px`
    );
    return lines.join('\n');
}

function buildDialog(doc) {
    const dlg = Dialog.create("Create Bulged Polyline");
    const column = dlg.addColumn();

    const sectionLength = Math.min(doc.widthPixels * 0.25, 300);
    const startX = doc.widthPixels * 0.5 - sectionLength;
    const startY = doc.heightPixels * 0.5;

    const startGroup = column.addGroup("Start point");
    dlg.startX = startGroup
        .addUnitValueEditor("X", UnitType.Pixel, doc.units, startX)
        .setNoMinValue()
        .setNoMaxValue()
        .setPrecision(2);
    dlg.startY = startGroup
        .addUnitValueEditor("Y", UnitType.Pixel, doc.units, startY)
        .setNoMinValue()
        .setNoMaxValue()
        .setPrecision(2);

    const endGroup = column.addGroup("End point");
    dlg.endpointMode = endGroup.addButtonSet(
        "Endpoint",
        ["To (x, y)", "Relative (dx, dy)"],
        EndpointMode.Absolute
    );
    dlg.argumentX = endGroup
        .addUnitValueEditor("X / dx", UnitType.Pixel, doc.units, startX + sectionLength)
        .setNoMinValue()
        .setNoMaxValue()
        .setPrecision(2);
    dlg.argumentY = endGroup
        .addUnitValueEditor("Y / dy", UnitType.Pixel, doc.units, startY)
        .setNoMinValue()
        .setNoMaxValue()
        .setPrecision(2);

    const sectionGroup = column.addGroup("Section");
    dlg.bulgeValue = sectionGroup
        .addUnitValueEditor("Bulge", UnitType.Number, UnitType.Number, 0, -4, 4)
        .setNoMinValue()
        .setNoMaxValue()
        .setShowPopupSlider(true)
        .setPrecision(4);
    dlg.addSection = sectionGroup.addButton("Add section").setIsFullWidth();
    sectionGroup.addStaticText(
        null,
        "Add section keeps the current section and starts another. OK keeps the current section and creates the polyline."
    ).setIsFullWidth();

    const resultGroup = column.addGroup("Current geometry");
    dlg.readout = resultGroup.addStaticText(null, "").setIsFullWidth();

    dlg.initialWidth = 480;
    return dlg;
}

function main() {
    const doc = Document.current;
    if (!doc) {
        app.alert("Open a document before running Create Bulged Polyline.");
        return;
    }

    const dlg = buildDialog(doc);
    const sections = [];
    let updating = false;
    let previousEndpointMode = dlg.endpointMode.selectedIndex;

    function preserveEndpointAcrossModeChange() {
        const endpointMode = dlg.endpointMode.selectedIndex;
        if (endpointMode == previousEndpointMode)
            return;

        const start = currentStart(dlg, sections);
        if (endpointMode == EndpointMode.Relative) {
            dlg.argumentX.value -= start.x;
            dlg.argumentY.value -= start.y;
        }
        else {
            dlg.argumentX.value += start.x;
            dlg.argumentY.value += start.y;
        }
        previousEndpointMode = endpointMode;
    }

    function update(preview) {
        if (updating)
            return false;
        updating = true;
        try {
            preserveEndpointAcrossModeChange();
            const currentSection = readCurrentSection(dlg, sections);
            dlg.readout.text = describeCurrentSection(currentSection, sections.length);
            doc.addNode(createNodeDefinition(sections.concat(currentSection)), null, undefined, preview);
            return true;
        }
        catch (error) {
            dlg.readout.text = `CurveBuilder rejected this section:\n${String(error)}`;
            doc.clearPreviews();
            return false;
        }
        finally {
            updating = false;
        }
    }

    function addSection() {
        if (updating)
            return;
        updating = true;
        try {
            preserveEndpointAcrossModeChange();
            const section = readCurrentSection(dlg, sections);
            createCurve(sections.concat(section));
            sections.push(section);

            dlg.startX.value = section.end.x;
            dlg.startY.value = section.end.y;
            dlg.startX.isEnabled = false;
            dlg.startY.isEnabled = false;

            if (dlg.endpointMode.selectedIndex == EndpointMode.Absolute) {
                dlg.argumentX.value = section.end.x + section.dx;
                dlg.argumentY.value = section.end.y + section.dy;
            }
            dlg.bulgeValue.value = 0;
        }
        catch (error) {
            app.alert(`Cannot add this section:\n${String(error)}`);
        }
        finally {
            updating = false;
        }
        update(true);
    }

    for (const control of [
        dlg.startX,
        dlg.startY,
        dlg.endpointMode,
        dlg.argumentX,
        dlg.argumentY,
        dlg.bulgeValue,
    ]) {
        control.onValueChangedHandler = () => update(true);
    }
    dlg.addSection.onClickHandler = addSection;

    update(true);
    while (dlg.runModal() == DialogResult.Ok) {
        if (update(false))
            return;
        app.alert("Choose a section that CurveBuilder accepts before creating the polyline.");
    }
    doc.clearPreviews();
}

module.exports.main = main;
