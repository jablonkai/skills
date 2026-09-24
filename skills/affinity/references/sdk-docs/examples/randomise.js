'use strict';

// Randomises the position, rotation, scale and opacity of each selected object within the
// chosen ranges. Reshuffle picks a new random pattern. Previews live.

const { CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { Transform } = require('/geometry.js');
const { Selection } = require('/selections.js');
const { UnitType } = require('/units.js');

function isOk(result) {
    return (result?.value ?? result) == DialogResult.Ok.value;
}

function compound(cmds) {
    if (cmds.length == 0)
        return null;
    const builder = CompoundCommandBuilder.create();
    for (const cmd of cmds)
        builder.addCommand(cmd);
    return builder.createCommand();
}

function previewLoop(doc, dlg, build, onCommit) {
    const update = (preview) => {
        const cmd = build();
        if (cmd)
            doc.executeCommand(cmd, preview);
        else
            doc.clearPreviews();
        return cmd;
    };
    dlg.onControlValueChangedHandler = () => update(true);
    update(true);
    if (isOk(dlg.runModal())) {
        const cmd = update(false);
        if (cmd && onCommit)
            onCommit(cmd);
    }
    doc.clearPreviews();
}

function splitmix32(a) {
    return function() {
        a |= 0;
        a = a + 0x9e3779b9 | 0;
        let t = a ^ a >>> 16;
        t = Math.imul(t, 0x21f0aaad);
        t = t ^ t >>> 15;
        t = Math.imul(t, 0x735a2d97);
        return ((t = t ^ t >>> 15) >>> 0) / 4294967296;
    };
}

function aboutCentre(cx, cy, dx, dy, radians, scale) {
    return Transform.createTranslate(cx + dx, cy + dy)
        .multiply(Transform.createRotate(radians))
        .multiply(Transform.createScale(scale, scale))
        .multiply(Transform.createTranslate(-cx, -cy));
}

function createRandomiseCommand(doc, sources, opts) {
    const prng = splitmix32(opts.seed);
    const spread = (range) => (prng() * 2 - 1) * range;
    const cmds = [];
    for (const { node, centre } of sources) {
        const sel = Selection.create(doc, node);
        const dx = opts.position ? spread(opts.rangeX) : 0;
        const dy = opts.position ? spread(opts.rangeY) : 0;
        const rot = opts.rotation ? spread(opts.rangeRotation) * Math.PI / 180 : 0;
        const scale = opts.scale ? 1 + spread(opts.rangeScale) / 100 : 1;
        if (dx || dy || rot || scale != 1)
            cmds.push(DocumentCommand.createTransform(sel, aboutCentre(centre.x, centre.y, dx, dy, rot, Math.max(0.01, scale))));
        if (opts.opacity)
            cmds.push(DocumentCommand.createSetOpacity(sel, (opts.opacityMin + prng() * (opts.opacityMax - opts.opacityMin)) / 100));
    }
    return compound(cmds);
}

function enableBy(toggle, controls) {
    const update = () => controls.forEach(c => c.isEnabled = toggle.value);
    toggle.onValueChangedHandler = update;
    update();
}

function buildDialog(doc) {
    const pt = doc.dpi / 72;
    const dlg = Dialog.create("Randomise");
    const col = dlg.addColumn();

    const pos = col.addGroup("Position");
    dlg.position = pos.addSwitch("Enabled", true);
    dlg.rangeX = pos.addUnitValueEditor("Horizontal ±", UnitType.Pixel, doc.units, 20 * pt, 0);
    dlg.rangeY = pos.addUnitValueEditor("Vertical ±", UnitType.Pixel, doc.units, 20 * pt, 0);
    enableBy(dlg.position, [dlg.rangeX, dlg.rangeY]);

    const rot = col.addGroup("Rotation");
    dlg.rotation = rot.addSwitch("Enabled", true);
    dlg.rangeRotation = rot.addUnitValueEditor("Degrees ±", UnitType.Number, UnitType.Number, 15, 0, 180).setPrecision(1);
    enableBy(dlg.rotation, [dlg.rangeRotation]);

    const scale = col.addGroup("Scale");
    dlg.scale = scale.addSwitch("Enabled", false);
    dlg.rangeScale = scale.addUnitValueEditor("Percent ±", UnitType.Number, UnitType.Number, 20, 0, 99).setPrecision(0);
    enableBy(dlg.scale, [dlg.rangeScale]);

    const opacity = col.addGroup("Opacity");
    dlg.opacity = opacity.addSwitch("Enabled", false);
    dlg.opacityMin = opacity.addUnitValueEditor("Minimum %", UnitType.Number, UnitType.Number, 40, 0, 100).setPrecision(0);
    dlg.opacityMax = opacity.addUnitValueEditor("Maximum %", UnitType.Number, UnitType.Number, 100, 0, 100).setPrecision(0);
    enableBy(dlg.opacity, [dlg.opacityMin, dlg.opacityMax]);

    dlg.seed = 1;
    dlg.reshuffle = col.addGroup("").addButton("Reshuffle").setIsFullWidth();
    return dlg;
}

function readOptions(dlg) {
    return {
        seed: dlg.seed,
        position: dlg.position.value, rangeX: dlg.rangeX.value, rangeY: dlg.rangeY.value,
        rotation: dlg.rotation.value, rangeRotation: dlg.rangeRotation.value,
        scale: dlg.scale.value, rangeScale: dlg.rangeScale.value,
        opacity: dlg.opacity.value,
        opacityMin: Math.min(dlg.opacityMin.value, dlg.opacityMax.value),
        opacityMax: Math.max(dlg.opacityMin.value, dlg.opacityMax.value)
    };
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const nodes = doc.selection.nodes.toArray();
    if (nodes.length == 0) {
        alert("Please select one or more objects");
        return;
    }
    const sources = nodes.map(node => ({ node, centre: node.getSpreadBaseBox().centre }));
    const dlg = buildDialog(doc);
    const build = () => createRandomiseCommand(doc, sources, readOptions(dlg));
    dlg.reshuffle.onClickHandler = () => {
        dlg.seed++;
        const cmd = build();
        if (cmd)
            doc.executeCommand(cmd, true);
    };
    previewLoop(doc, dlg, build);
}

module.exports.main = main;