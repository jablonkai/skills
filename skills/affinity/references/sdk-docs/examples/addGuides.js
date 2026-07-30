
'use strict';

const {Document} = require('/document');
const {Dialog, DialogResult} = require('/dialog');
const {UnitType} = require("/units");
const {unionRects} = require('/geometry');
const {DocumentCommand, CompoundCommandBuilder} = require('/commands');

function calculateOffsets(dlg) {
    const offsets = {
        left:0,
        top:0,
        right:0,
        bottom:0,
        hCentre:0,
        vCentre:0
    };
    if (dlg.enableOffsets.value) {
        const inflate = dlg.offsetMode.selectedIndex == 1;
        if (inflate) {
            offsets.left = -dlg.hOffset.value;
            offsets.top = -dlg.vOffset.value;
            offsets.right = dlg.hOffset.value;
            offsets.bottom = dlg.vOffset.value;
        }
        else {
            offsets.left = dlg.hOffset.value;
            offsets.top = dlg.vOffset.value;
            offsets.right = dlg.hOffset.value;
            offsets.bottom = dlg.vOffset.value;
            offsets.hCentre = dlg.hOffset.value;
            offsets.vCentre = dlg.vOffset.value;
        }
    }
    return offsets;
}

function addCommands(rc, dlg, offsets, cmds) {
    if (dlg.left.value) {
        cmds.push(DocumentCommand.createAddGuide(false, rc.x + offsets.left));
    }
    if (dlg.top.value) {
        cmds.push(DocumentCommand.createAddGuide(true, rc.y + offsets.top));
    }
    if (dlg.right.value) {
        cmds.push(DocumentCommand.createAddGuide(false, rc.x + rc.width + offsets.right));
    }
    if (dlg.bottom.value) {
        cmds.push(DocumentCommand.createAddGuide(true, rc.y + rc.height + offsets.bottom));
    }
    if (dlg.hCentre.value) {
        cmds.push(DocumentCommand.createAddGuide(false, rc.centre.x + offsets.hCentre));
    }
    if (dlg.vCentre.value) {
        cmds.push(DocumentCommand.createAddGuide(true, rc.centre.y + offsets.vCentre));
    }
}

function createGuides(doc, nodes, dlg, preview) {
    
    if (!dlg.anyGuidesSelected())
        return; // nothing to do
    
    const subCmds = [];
    const offsets = calculateOffsets(dlg);
    
    switch (dlg.guidesBounds.selectedIndex) {
        case 0: { // put guides around each object
            const builder = CompoundCommandBuilder.create();
            for (const node of nodes) {
                const rcNode = node.getSpreadBaseBox();
                addCommands(rcNode, dlg, offsets, subCmds);
            }
        }
        break;
        case 1: { // put guides around selection
            let rc = null;
            for (const node of nodes) {
                const rcNode = node.getSpreadBaseBox();
                if (rc == null)
                    rc = rcNode;
                else {
                    rc = unionRects(rc, rcNode);
                }
            }
            if (rc == null) {
                return;
            }
            addCommands(rc, dlg, offsets, subCmds);
        }
        break;
    }
    if (subCmds.length == 0)
        return;
    if (subCmds.length == 1)
        doc.executeCommand(subCmds[0], preview);
    else {
        const builder = CompoundCommandBuilder.create();
        for (const cmd of subCmds) {
            builder.addCommand(cmd);
        }
        doc.executeCommand(builder.createCommand(), preview);
    }
}

function buildDialog() {
    const dlg = Dialog.create("Add Guides");
    const column = dlg.addColumn();
    const grp1 = column.addGroup("Add Guides At");
    dlg.left = grp1.addSwitch("Left");
    dlg.top = grp1.addSwitch("Top");
    dlg.right = grp1.addSwitch("Right");
    dlg.bottom = grp1.addSwitch("Bottom");
    dlg.hCentre = grp1.addSwitch("Horizontal Centre");
    dlg.vCentre = grp1.addSwitch("Vertical Centre");
    dlg.guidesBounds = grp1.addButtonSet("Around", ["Each object", "Entire Selection"], 1);
    
    const grp2 = column.addGroup("Offsets");
    dlg.enableOffsets = grp2.addSwitch("Enabled");
    dlg.offsetMode = grp2.addButtonSet("Mode", ["Absolute", "Inflate"]);
    dlg.hOffset = grp2.addUnitValueEditor("Horizontal", UnitType.Pixel, UnitType.Millimetre, 0);
    dlg.vOffset = grp2.addUnitValueEditor("Vertical", UnitType.Pixel, UnitType.Millimetre, 0);
    dlg.offsetMode.isEnabled = false;
    dlg.hOffset.isEnabled = false;
    dlg.vOffset.isEnabled = false;
    dlg.enableOffsets.onValueChangedHandler = () => {
        const enabled = dlg.enableOffsets.value;
        dlg.offsetMode.isEnabled = enabled;
        dlg.hOffset.isEnabled = enabled;
        dlg.vOffset.isEnabled = enabled;
    };
    dlg.initialWidth = 300;
    dlg.anyGuidesSelected = () => {
        return dlg.top.value || dlg.left.value || dlg.bottom.value || dlg.right.value || dlg.hCentre.value || dlg.vCentre.value;
    }
    return dlg;
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
    }
    else {
        const selection = doc.selection;
        const nodes = selection.nodes;
        if (nodes.isEmpty) {
            alert("Please select some objects");
        }
        else {
            const dlg = buildDialog();
            function update() {
                if (dlg.anyGuidesSelected()) {
                    createGuides(doc, nodes, dlg, true);
                }
                else {
                    doc.clearPreviews();
                }
            }
            dlg.onControlValueChangedHandler = update;
            while (dlg.runModal() == DialogResult.Ok) {
                if (dlg.anyGuidesSelected()) {
                    createGuides(doc, nodes, dlg);
                    break;
                }
                else {
                    alert("Please select some guides to create");
                }
            }
            doc.clearPreviews();
        }
    }
}

module.exports.main = main;
