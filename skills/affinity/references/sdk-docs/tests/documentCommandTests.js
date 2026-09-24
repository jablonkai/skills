'use strict';

const {ErrorCode} = require('affinity:common');
const {Document} = require('/document.js');
const {DocumentPreset, NewDocumentOptions, DocumentPresetType} = require('/document.js');
const {DocumentCommand, AddChildNodesCommandBuilder} = require('/commands.js')
const {TestUtils} = require('/tests/testUtils.js');
const {ShapeNodeDefinition, NodeChildType, ImageNodeDefinition} = require('/nodes.js');
const {Selection} = require('/selections.js');
const {PixelBuffer, RasterFormat} = require('/rasterobject.js');

function testRasteriseObjects() {
    let doc = TestUtils.getA4Empty();
    let builder = AddChildNodesCommandBuilder.create();
    let snd = ShapeNodeDefinition.createDefault();
    builder.addNode(snd);
    let cmd = builder.createCommand(false, NodeChildType.Main);
    let result = doc.executeCommand(cmd);
    
    let node = doc.layers.first;
    console.assert(node.isVectorNode);
    
    let sel = Selection.create(doc, node);
    
    let rasteriseCmd = DocumentCommand.createRasteriseObjects(sel, false, false);
    doc.executeCommand(rasteriseCmd);
    
    let test = doc.layers.first;
    console.assert(test.isRasterNode);
    console.log("testRasteriseObjects OK");
    doc.close();
}

function testConvertToCurves() {
    let doc = TestUtils.getA4Empty();
    let builder = AddChildNodesCommandBuilder.create();
    let rnd = ImageNodeDefinition.create(RasterFormat.RGBA8);
   
    rnd.bitmap = TestUtils.getRandomRGBA8Bitmap(200, 200);
    builder.addNode(rnd);
    let cmd = builder.createCommand(false, NodeChildType.Main);
    let result = doc.executeCommand(cmd);
    
    let node = doc.layers.first;
    console.assert(node.isImageNode);
    
    let sel = Selection.create(doc, node);
    
    let toCurve = DocumentCommand.createConvertToCurves(sel);
    doc.executeCommand(toCurve);
    
    let test = doc.layers.first;
    console.assert(test.isVectorNode);
    console.log("testConvertToCurves OK");
    doc.close();
}

function runTests() {
    testRasteriseObjects();
    testConvertToCurves();
}

module.exports.runTests = runTests;
module.exports.testRasteriseObjects = testRasteriseObjects;
module.exports.testConvertToCurves = testConvertToCurves;
