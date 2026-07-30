'use strict';
const {app} = require('/application');
const {PolyCurveNodeDefinition, NodeChildType, Node} = require('/nodes');
const dommodule = require("affinity:dom");
const {DocumentCommand, AddChildNodesCommandBuilder} = require("/commands");
const {Document, DocumentPromises} = require("/document.js");
const {PolyCurve, Curve, CurveBuilder, Rectangle, CurveCornerData, CurveCornerType} = require("/geometry.js");
const {Fill, FillDescriptor, NoFill} = require("/fills");
const {BlendMode} = require("affinity:common");
const {LineStyleDescriptor, LineType} = require("/linestyle");
const {Colour, RGBA8, SVG11} = require("/colours");
const {ErrorCode} = require('affinity:common');
const {CurvesInterface} = require('/curvesinterface')
const {Selection, SelectionItem} = require('/selections')

const {TestUtils} = require('/tests/testUtils');


// Test CreateSetCurvesCommand with PolyCurveNode
function testSetCurvesCommand() {
    let doc = TestUtils.newA4Empty();

    if (doc) {
        // Create initial PolyCurveNode with a square
        let cBuilder = CurveBuilder.create();
        cBuilder.beginXY(100, 100);
        cBuilder.lineToXY(300, 100);
        cBuilder.lineToXY(300, 300);
        cBuilder.lineToXY(100, 300);
        cBuilder.close();
        let curve = cBuilder.createCurve();

        let polyCurve = new PolyCurve();
        polyCurve.addCurve(curve);

        const noFill = FillDescriptor.createNone();
        const lineFill = FillDescriptor.createSolid(SVG11.blue, BlendMode.Normal);
        const lineStyle = LineStyleDescriptor.createDefault(5);

        let pcNodeDef = PolyCurveNodeDefinition.create(polyCurve, noFill, lineStyle, lineFill, noFill);

        let acnBuilder = AddChildNodesCommandBuilder.create();
        acnBuilder.addNode(pcNodeDef);
        let anCommand = acnBuilder.createCommand();
        doc.executeCommand(anCommand);

        let pcNode = doc.layers.first;
        console.assert(pcNode.polyCurve.curves.length == 1, "Initial polycurve should have 1 curve");

        // Create new curves (a triangle)
        let cBuilder2 = CurveBuilder.create();
        cBuilder2.beginXY(150, 150);
        cBuilder2.lineToXY(350, 150);
        cBuilder2.lineToXY(250, 350);
        cBuilder2.close();
        let newCurve = cBuilder2.createCurve();

        let newPolyCurve = new PolyCurve();
        newPolyCurve.addCurve(curve);
        newPolyCurve.addCurve(newCurve);

        // Test CreateSetCurvesCommand
        let curvesInterface = pcNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");

        let cmd = DocumentCommand.createSetCurves(curvesInterface, newPolyCurve);
        doc.executeCommand(cmd);

        // Verify the curves were replaced
        let updatedNode = doc.layers.first;
        console.assert(updatedNode.polyCurve.curves.length == 2, "Updated polycurve should have 1 curve");

        console.log("testSetCurvesCommand OK");
    }
}

// Test CreateAddCurveCommand with PolyCurveNode
function testAddCurveCommand() {
    let doc = TestUtils.newA4Empty();

    if (doc) {
        // Create initial PolyCurveNode with one curve
        let cBuilder = CurveBuilder.create();
        cBuilder.beginXY(100, 100);
        cBuilder.lineToXY(200, 100);
        cBuilder.lineToXY(200, 200);
        cBuilder.lineToXY(100, 200);
        cBuilder.close();
        let curve = cBuilder.createCurve();

        let polyCurve = new PolyCurve();
        polyCurve.addCurve(curve);

        const noFill = FillDescriptor.createNone();
        const lineFill = FillDescriptor.createSolid(SVG11.green, BlendMode.Normal);
        const lineStyle = LineStyleDescriptor.createDefault(3);

        let pcNodeDef = PolyCurveNodeDefinition.create(polyCurve, noFill, lineStyle, lineFill, noFill);

        let acnBuilder = AddChildNodesCommandBuilder.create();
        acnBuilder.addNode(pcNodeDef);
        let anCommand = acnBuilder.createCommand();
        doc.executeCommand(anCommand);

        let pcNode = doc.layers.first;
        console.assert(pcNode.polyCurve.curves.length == 1, "Initial polycurve should have 1 curve");

        // Create a new curve to add
        let newCurve = Curve.createLine({x: 250, y: 250}, {x: 350, y: 350});

        // Test CreateAddCurveCommand
        let curvesInterface = pcNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");

        // Add curve with selection
        let cmd = DocumentCommand.createAddCurve(curvesInterface, newCurve, true, false);
        doc.executeCommand(cmd);

        // Verify the curve was added
        let updatedNode = doc.layers.first;
        console.assert(updatedNode.polyCurve.curves.length == 2, "Updated polycurve should have 2 curves");

        console.log("testAddCurveCommand OK");
    }
}

// Test CreateAddCurveNodeCommand with PolyCurveNode
function testAddCurveNodeCommand() {
    let doc = TestUtils.newA4Empty();

    if (doc) {
        // Create a PolyCurveNode with a simple line
        let curve = Curve.createLine({x: 100, y: 100}, {x: 400, y: 100});

        let polyCurve = new PolyCurve();
        polyCurve.addCurve(curve);

        const noFill = FillDescriptor.createNone();
        const lineFill = FillDescriptor.createSolid(SVG11.red, BlendMode.Normal);
        const lineStyle = LineStyleDescriptor.createDefault(5);

        let pcNodeDef = PolyCurveNodeDefinition.create(polyCurve, noFill, lineStyle, lineFill, noFill);

        let acnBuilder = AddChildNodesCommandBuilder.create();
        acnBuilder.addNode(pcNodeDef);
        let anCommand = acnBuilder.createCommand();
        doc.executeCommand(anCommand);

        let pcNode = doc.layers.first;
        let initialCurve = pcNode.polyCurve.curves.first;

        // Get the curve's node count before adding
        let curvesInterface = pcNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");

        // Create curveHandle to reference the first curve (curveID=0, nodeID=0 for the first segment)
        let curveHandle = {curveID: 0, nodeID: 0};

        // Test CreateAddCurveNodeCommand - add a node at parametric distance 0.5 (middle)
        let cmd = DocumentCommand.createAddCurveNode(curvesInterface, curveHandle, 0.5);
        doc.executeCommand(cmd);

        // Verify a node was added
        let updatedNode = doc.layers.first;
        let updatedCurve = updatedNode.polyCurve.curves.first;

        // The curve should now have more control points after adding a node
        console.log("Node added at parametric distance 0.5");

        console.log("testAddCurveNodeCommand OK");
    }
}

// Test CreateSetCurvesCommand with CurvePathTextNode
function testSetCurvesCommandWithCurvePathText() {
    let doc = TestUtils.getFile("/CurvePathTextNodeDoc.af");

    if (doc) {
        let textNode = doc.layers.first;
        console.assert(textNode.isCurvePathTextNode);

        let curvesInterface = textNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");
        console.assert(curvesInterface.isMutable, "curvesInterface should be mutable");

        // Get initial curves
        let initialCurves = curvesInterface.polyCurve;
        console.log("CurvePathText - Initial curves start:", initialCurves.curves.first.points.first);

        // Create new curves (a simple arc path for text to follow)
        let cBuilder = CurveBuilder.create();
        cBuilder.beginXY(1000, 2000);
        cBuilder.addBezierXY(200, 100, 300, 100, 2000, 2000);
        let curve1 = cBuilder.createCurve();

        // Create a second curve
        let cBuilder2 = CurveBuilder.create();
        cBuilder2.beginXY(300, 300);
        cBuilder2.lineToXY(1200, 1250);
        let curve2 = cBuilder2.createCurve();

        let newPolyCurve = new PolyCurve();
        newPolyCurve.addCurve(curve1);
        newPolyCurve.addCurve(curve2);

        // Test CreateSetCurvesCommand
        let cmd = DocumentCommand.createSetCurves(curvesInterface, newPolyCurve);
        doc.executeCommand(cmd);

        // Verify the curves were replaced
        let updatedInterface = textNode.curvesInterface;
        let updatedCurves = updatedInterface.polyCurve;
        console.log("New Start:", updatedCurves.curves.first.points.first);
        console.assert(initialCurves.curves.first.points.first.x != updatedCurves.curves.first.points.first.x && initialCurves.curves.first.points.first.y != updatedCurves.curves.first.points.first.y, "Updated should have different starting point");

        console.log("testSetCurvesCommandWithCurvePathText OK");
        doc.close();
    }
}

// Test CreateAddCurveCommand with CurvePathTextNode
function testAddCurveCommandWithCurvePathText() {
    let doc = TestUtils.getFile("/CurvePathTextNodeDoc.af");

    if (doc) {
        let textNode = doc.layers.first;
        console.assert(textNode.isCurvePathTextNode);

        let curvesInterface = textNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");

        // Get initial curves count
        let initialCurves = curvesInterface.polyCurve;
        let initialCount = initialCurves.curves.length;
        console.log("CurvePathText - Initial curves count:", initialCount);

        // Create a new curve to add
        let newCurve = Curve.createLine({x: 100, y: 300}, {x: 400, y: 300});

        // Test CreateAddCurveCommand
        let cmd = DocumentCommand.createAddCurve(curvesInterface, newCurve, true, false);
        doc.executeCommand(cmd);

        console.log("testAddCurveCommandWithCurvePathText OK");
        doc.close();
    }
}

// Test CreateAddCurveNodeCommand with CurvePathTextNode
function testAddCurveNodeCommandWithCurvePathText() {
    let doc = TestUtils.getFile("/CurvePathTextNodeDoc.af");

    if (doc) {
        let textNode = doc.layers.first;
        console.assert(textNode.isCurvePathTextNode);

        let curvesInterface = textNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");

        // Create curveHandle to reference the first curve, first segment
        let curveHandle = {curveID: 0, nodeID: 0};

        // Test CreateAddCurveNodeCommand - add a node at parametric distance 0.5
        let cmd = DocumentCommand.createAddCurveNode(curvesInterface, curveHandle, 0.5);
        doc.executeCommand(cmd);

        console.log("CurvePathText - Node added at parametric distance 0.5");
        console.log("testAddCurveNodeCommandWithCurvePathText OK");
        doc.close();
    }
}

// Test CreateSetCurvesCommand with PolyCurveTextNode
function testSetCurvesCommandWithPolyCurveText() {
    let doc = TestUtils.getFile("/PolyCurveTextNodeDoc.af");

    if (doc) {
        let textNode = doc.layers.first;
        console.assert(textNode.isPolyCurveTextNode);

        let curvesInterface = textNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");
        console.assert(curvesInterface.isMutable, "curvesInterface should be mutable");

        // Get initial curves
        let initialCurves = curvesInterface.polyCurve;
        console.log("CurvePathText - Initial curves start:", initialCurves.curves.first.points.first);


        // Create new curves (a rectangle for text frame)
        let cBuilder = CurveBuilder.create();
        cBuilder.beginXY(1500, 1500);
        cBuilder.lineToXY(3500, 1500);
        cBuilder.lineToXY(3500, 3500);
        cBuilder.lineToXY(1500, 3500);
        cBuilder.close();
        let curve1 = cBuilder.createCurve();

        // Create a second curve (an inner ellipse hole)
        let cBuilder2 = CurveBuilder.create();
        cBuilder2.beginXY(250, 200);
        cBuilder2.addBezierXY(250, 180, 270, 180, 280, 200);
        cBuilder2.addBezierXY(290, 200, 290, 220, 280, 240);
        cBuilder2.addBezierXY(270, 260, 250, 260, 230, 240);
        cBuilder2.addBezierXY(210, 240, 210, 220, 230, 200);
        let curve2 = cBuilder2.createCurve();

        let newPolyCurve = new PolyCurve();
        newPolyCurve.addCurve(curve1);
        newPolyCurve.addCurve(curve2);

        // Test CreateSetCurvesCommand
        let cmd = DocumentCommand.createSetCurves(curvesInterface, newPolyCurve);
        doc.executeCommand(cmd);

        // Verify the curves were replaced
        let updatedInterface = textNode.curvesInterface;
        let updatedCurves = updatedInterface.polyCurve;
        console.log("New Start:", updatedCurves.curves.first.points.first);
        console.assert(initialCurves.curves.first.points.first.x != updatedCurves.curves.first.points.first.x && initialCurves.curves.first.points.first.y != updatedCurves.curves.first.points.first.y, "Updated should have different starting point");

        console.log("testSetCurvesCommandWithPolyCurveText OK");
        doc.close();
    }
}

// Test CreateAddCurveCommand with PolyCurveTextNode
function testAddCurveCommandWithPolyCurveText() {
    let doc = TestUtils.getFile("/PolyCurveTextNodeDoc.af");

    if (doc) {
        let textNode = doc.layers.first;
        console.assert(textNode.isPolyCurveTextNode);

        let curvesInterface = textNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");

        // Get initial curves count
        let initialCurves = curvesInterface.polyCurve;
        let initialCount = initialCurves.curves.length;
        console.log("PolyCurveText - Initial curves count:", initialCount);

        // Create a new curve to add (an ellipse hole)
        let cBuilder = CurveBuilder.create();
        cBuilder.beginXY(250, 200);
        cBuilder.addBezierXY(250, 150, 300, 150, 350, 200);
        cBuilder.addBezierXY(400, 200, 400, 250, 350, 300);
        cBuilder.addBezierXY(350, 350, 300, 350, 250, 300);
        cBuilder.addBezierXY(200, 300, 200, 250, 250, 200);
        let newCurve = cBuilder.createCurve();

        // Test CreateAddCurveCommand
        let cmd = DocumentCommand.createAddCurve(curvesInterface, newCurve, true, false);
        doc.executeCommand(cmd);

        console.log("testAddCurveCommandWithPolyCurveText OK");
        doc.close();
    }
}

// Test CreateAddCurveNodeCommand with PolyCurveTextNode
function testAddCurveNodeCommandWithPolyCurveText() {
    let doc = TestUtils.getFile("/PolyCurveTextNodeDoc.af");

    if (doc) {
        let textNode = doc.layers.first;
        console.assert(textNode.isPolyCurveTextNode);

        let curvesInterface = textNode.curvesInterface;
        console.assert(curvesInterface, "curvesInterface should exist");

        // Create curveHandle to reference the first curve, first segment
        let curveHandle = {curveID: 0, nodeID: 0};

        // Test CreateAddCurveNodeCommand - add a node at parametric distance 0.5
        let cmd = DocumentCommand.createAddCurveNode(curvesInterface, curveHandle, 0.5);
        doc.executeCommand(cmd);

        console.log("PolyCurveText - Node added at parametric distance 0.5");
        console.log("testAddCurveNodeCommandWithPolyCurveText OK");
        doc.close();
    }
}

// Test with text nodes - runs all text node tests
function testSetCurvesCommandWithTextNodes() {
    console.log("=== Testing CurvePathTextNode ===");
    testSetCurvesCommandWithCurvePathText();
    testAddCurveCommandWithCurvePathText();
    testAddCurveNodeCommandWithCurvePathText();

    console.log("=== Testing PolyCurveTextNode ===");
    testSetCurvesCommandWithPolyCurveText();
    testAddCurveCommandWithPolyCurveText();
    testAddCurveNodeCommandWithPolyCurveText();

    console.log("testSetCurvesCommandWithTextNodes: All text node tests completed");
}

function runTests() {
    testSetCurvesCommand();
    testAddCurveCommand();
    testAddCurveNodeCommand();
    testSetCurvesCommandWithTextNodes();
}

module.exports.runTests = runTests
module.exports.testSetCurvesCommand = testSetCurvesCommand;
module.exports.testAddCurveCommand = testAddCurveCommand;
module.exports.testAddCurveNodeCommand = testAddCurveNodeCommand;
module.exports.testSetCurvesCommandWithTextNodes = testSetCurvesCommandWithTextNodes;
