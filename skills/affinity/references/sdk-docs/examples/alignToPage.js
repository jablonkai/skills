'use strict';

const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document');
const { GroupTransformAnchor, GroupTransformData, GroupTransformOrder, GroupTransformType } = require('/commands');

const doc = Document.current;

function createGroupTransformData(alignment, considerMargins) {
    const res = new GroupTransformData();    
    res.type = alignment;
    res.anchor = considerMargins ? GroupTransformAnchor.PageMargins : GroupTransformAnchor.Page;
    return res;
}

function doPageAlign(alignX, alignY, considerMargins) {
    const xData = createGroupTransformData(alignX, considerMargins);
    const yData = createGroupTransformData(alignY, considerMargins);
    doc.applyGroupTransform(xData, yData);
}

function buildDialog() {
    const dlg = Dialog.create("Align To Page");
    const grp = dlg.addColumn().addGroup("");
    dlg.y = grp.addComboBox("Vertical", ["Top", "Centre", "Bottom", "None"]);
    dlg.x = grp.addComboBox("Horizontal", ["Left", "Centre", "Right", "None"]);
    dlg.margins = grp.addSwitch("Consider margins");
    return dlg;
}

function main() {
    if (!doc) {
        alert("This script requires an open document");
        return;
    }

    const dlg = buildDialog();
    if (dlg.runModal() == DialogResult.Ok.value) {
        let getAlignType = (value) => {
            switch (value) {
                case 0: return GroupTransformType.Min;
                case 1: return GroupTransformType.Mid;
                case 2: return GroupTransformType.Max;
                default:  return GroupTransformType.None;
            }
        };
        
        const alignX = getAlignType(dlg.x.selectedIndex);
        const alignY = getAlignType(dlg.y.selectedIndex);
        if (alignX.value == GroupTransformType.None && alignY.value == GroupTransformType.None) {
            return;
        }
        doPageAlign(alignX, alignY, dlg.margins.value);
    }
}

module.exports.main = main;
