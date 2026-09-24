'use strict';

const { Collection } = require('/collection.js');
const { Dialog, DialogResult } = require('/dialog.js');
const { Document } = require('/document.js');
const { DocumentCommand, CompoundCommandBuilder } = require('/commands.js');
const { Selection } = require('/selections.js');
const { Transform } = require('/geometry.js');
const { UnitType } = require('/units.js');

const doc = Document.current;


function doOffsets(startPageIndex, endPageIndex, oddOffsets, evenOffsets) {
    let nodesOnPage = [];
    function addNodes(spread, parent) {
        for (const node of parent.children) {
            if (node.isContainerNode) {
                addNodes(spread, node);
            }
            else {
                const pageIndex = spread.firstPageIndex + spread.getPageIndexOfBox(node.getSpreadBaseBox());
                let nodesForPage = nodesOnPage[pageIndex];
                if (!nodesForPage)
                    nodesOnPage[pageIndex] = nodesForPage = [];
                nodesForPage.push(node);
            }
        }
    }
    
    for (const spread of doc.spreads) {
        if (spread.firstPageIndex > endPageIndex)
            break;
        if (spread.lastPageIndex < startPageIndex)
            continue;
        addNodes(spread, spread);
    }

    let cmds = [];
    for (let i = startPageIndex; i <= endPageIndex; ++i) {
        if (nodesOnPage[i]) {
            const isOdd = i % 2 != 0; // != 0 to convert from 0-based to 1-based
            const offsets = isOdd  ? evenOffsets : oddOffsets;
            if (!offsets)
                continue;
            const sel = Selection.create(doc, nodesOnPage[i], true);
            const xf = Transform.createTranslate(offsets.x, offsets.y);
            const cmd = DocumentCommand.createTransform(sel, xf);
            cmds.push(cmd);
        }
    }

    if (cmds.length == 0)
        return;
    if (cmds.length == 1)
        doc.executeCommand(cmds[0]);
    else {
        const builder = CompoundCommandBuilder.create();
        for (const cmd of cmds) {
            builder.addCommand(cmd);
        }
        doc.executeCommand(builder.createCommand());
    }
}


function enableBy(toggle, controls) {
    const update = () => controls.forEach(c => c.isEnabled = toggle.value);
    toggle.onValueChangedHandler = update;
    update();
}

function buildDialog() {
    const pages= Collection.range(1, doc.pageCount).toArray();
    const dlg = Dialog.create("Adjust Page Items");
    const col = dlg.addColumn();
    const pagesGroup = col.addGroup("Page Range");
    dlg.startPage = pagesGroup.addComboBox("Start page", pages);
    dlg.startPage.customSize = {width: 80, height: -1};
    dlg.endPage = pagesGroup.addComboBox("End page", pages);
    dlg.endPage.customSize = {width: 80, height: -1};
    dlg.endPage.selectedIndex = pages.length - 1;
    dlg.pages = pages;
    
    const evenGroup = col.addGroup("Even Pages");
    dlg.evenPages = evenGroup.addSwitch("Enabled", true);
    dlg.evenH = evenGroup.addUnitValueEditor("Horizontal", UnitType.Pixel, doc.units, 0);
    dlg.evenV = evenGroup.addUnitValueEditor("Vertical", UnitType.Pixel, doc.units, 0);
    enableBy(dlg.evenPages, [dlg.evenH, dlg.evenV]);

    const oddGroup = col.addGroup("Odd Pages");
    dlg.oddPages = oddGroup.addSwitch("Enabled", true);
    dlg.oddH = oddGroup.addUnitValueEditor("Horizontal", UnitType.Pixel, doc.units, 0);
    dlg.oddV = oddGroup.addUnitValueEditor("Vertical", UnitType.Pixel, doc.units, 0);
    enableBy(dlg.oddPages, [dlg.oddH, dlg.oddV]);
    
    return dlg;
}


function main() {
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    
    if (doc.hasArtboards) {
        alert("This script can only run on documents with pages");
        return;
    }

    const dlg = buildDialog();

    while (dlg.runModal() == DialogResult.Ok) {
        const startPage = dlg.pages[dlg.startPage.selectedIndex] - 1;
        const endPage = dlg.pages[dlg.endPage.selectedIndex] - 1;
        if (startPage > endPage) {
            alert("Start page must be less than or equal to end page");
        }
        else {
            const oddOffsets = dlg.oddPages.value ? {x:dlg.oddH.value, y: dlg.oddV.value} : null;
            const evenOffsets = dlg.evenPages.value ? {x:dlg.evenH.value, y: dlg.evenV.value} : null;
            doOffsets(startPage, endPage, oddOffsets, evenOffsets);
            break;
        }
    }
}

module.exports.main = main;
