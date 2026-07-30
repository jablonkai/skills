'use strict';
const {Document, DocumentPromises} = require("/document.js");
const {RasterSelectionLogicalOperation} = require("/commands.js");
const {ErrorCode} = require('affinity:common');
const {RasterSelection} = require("/rasterselection.js");
const {TestUtils} = require("/tests/testUtils.js");
const {Curve, CurveNodeType} = require("/geometry.js");

function testRasterSelection() {
    const document = TestUtils.newA4Empty();
    let selectAll = document.rasterSelectAll();
    const rasterSelection = document.rasterSelection;
    console.assert(rasterSelection.isSelectAllOrNone);

    let deselect = document.rasterDeselect();
    const rasterSelection2 = document.rasterSelection;
    console.assert(rasterSelection2.isSelectNone);

    let reselect = document.rasterReselect();
    const rasterSelection3 = document.rasterSelection;
    console.assert(rasterSelection3.isSelectAllOrNone);

    let invert = document.rasterInvertSelection();
    const rasterSelection4 = document.rasterSelection;
    console.assert(rasterSelection4.isSelectNone);
}

function testCurveToRasterSelection() {
    let curve = Curve.create();
    const nodeTypes = [CurveNodeType.OnCurve, CurveNodeType.Cubic1, CurveNodeType.Cubic2];
    for (let i = 0; i < 25; i++) {
        curve.appendNode({
            position: {x: Math.random() * 3000 + 50, y: Math.random() * 3000 + 50}, 
            type: nodeTypes[i % 3]
        });
    }

    let doc = TestUtils.newA4Empty();
    doc.setRasterSelectionFromPolygon(curve.generatePolygon(0.1), RasterSelectionLogicalOperation.New, false, 10);

    doc.close();
}

module.exports.testRasterSelection = testRasterSelection;
module.exports.testCurveToRasterSelection = testCurveToRasterSelection;
