const {Dialog, DialogResult} = require('/dialog.js');
const {Document} = require('/document.js');
const {RasterFormat} = require('/rasterobject.js');

const Formats = [
    ["RGB/8", RasterFormat.RGBA8],
    ["RGB/16", RasterFormat.RGBA16],
    ["RGB/32 (HDR)", RasterFormat.RGBAUF],
    ["Grey/8", RasterFormat.IA8],
    ["Grey/16", RasterFormat.IA16],
    ["CMYK/8", RasterFormat.CMYKA8],
    ["LAB/16", RasterFormat.LABA16]
];

function buildDialog() {
    const dlg = Dialog.create("Set Document Format");
    const grp = dlg.addColumn().addGroup();
    const combo = grp.addComboBox("New Format:", Formats.map(f => f[0]));
    dlg.getFormat = () => {
        return Formats[combo.selectedIndex][1];
    };
    
    return dlg;
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const dlg = buildDialog();
    if (dlg.runModal().equals(DialogResult.Ok)) {
        doc.format = dlg.getFormat();
    }
}

module.exports.main = main;
