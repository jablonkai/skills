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


function testCurveCorner() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let cBuilder = CurveBuilder.create();
        cBuilder.beginXY(100, 200);//point0
        cBuilder.lineToXY(200, 500);//point1
        cBuilder.lineToXY(400, 300);//point1->cusp
        cBuilder.addBezierXY(600, 100, 700, 100, 700, 300);//point2 smooth
        cBuilder.addBezierXY(700, 500, 800, 500, 900, 400);//point3 smooth
        cBuilder.addBezierXY(900, 1000, 1250, 1250, 750, 660);//point4 cusp
        //end at point5
        
        cBuilder.setCorner(1, {type: CurveCornerType.Round, radius: 50.0}, false);
        // force conversion of point2
        
        cBuilder.setCorner(2, {type: CurveCornerType.CutOut, radius: 100.0}, true);
        
        
        let curve = cBuilder.createCurve();
        
        let polyCurve = new PolyCurve();
        polyCurve.addCurve(curve);
        
        const noFill = FillDescriptor.createNone();
        const lineFill = FillDescriptor.createSolid(SVG11.red, BlendMode.Normal);
        const lineStyle = LineStyleDescriptor.createDefault(10);
        
        let pcNodeDef = PolyCurveNodeDefinition.create(polyCurve, noFill, lineStyle, lineFill, noFill);
        
        let acnBuilder = AddChildNodesCommandBuilder.create();
        acnBuilder.addNode(pcNodeDef);
        let anCommand = acnBuilder.createCommand();
        let result = doc.executeCommand(anCommand);
        let pcNode = doc.layers.first;
        
        let theCurve = pcNode.polyCurve.curves.first;
        console.log(theCurve);
        
        let corner1 = theCurve.getCorner(1);
        console.assert(corner1.type.value == CurveCornerType.Round);
        let corner2 = theCurve.getCorner(2);
        console.assert(corner2.type.value == CurveCornerType.CutOut);
        
        doc.undo();
        
        theCurve.setCorner(3, {type: CurveCornerType.Straight, radius: 25.0}, true);
        theCurve.setCorner(4, {type: CurveCornerType.Inverse, radius: 75.0}, false);
        
        let pc2 = new PolyCurve();
        pc2.addCurve(theCurve);
        
        const fill2 = FillDescriptor.createSolid(SVG11.tan, BlendMode.Normal);
        const ls2 = LineStyleDescriptor.createDefault(100);
        
        let pcnDef2 = PolyCurveNodeDefinition.create(pc2, noFill, ls2, fill2, noFill);
        acnBuilder.clearNodes();
        acnBuilder.addNode(pcnDef2);
        let cmd = acnBuilder.createCommand();
        result = doc.executeCommand(cmd);
        
        let pcNode2 = doc.layers.first;
        let newCurve = pcNode2.polyCurve.curves.first;
        console.log(newCurve);
        
        let corner3 = theCurve.getCorner(3);
        console.assert(corner3.type.value == CurveCornerType.Straight);
        let corner4 = theCurve.getCorner(4);
        console.assert(corner4.type.value == CurveCornerType.Inverse);
        doc.undo();
        
        console.log("testCurveCorner OK");
        //doc.close();
    }
}

function testCutCurve() {
    let doc = TestUtils.newA4Empty();

    if (doc) {
        let curve = Curve.createLine({x: 0, y: 250}, {x: 800, y: 250});
        console.assert(curve.length == 800);
        let curves = curve.cut(true, 0.8);
        console.log(curves.curveA, curves.curveB);
        console.log(curves.curveA.length, curves.curveB.length);
        console.assert(639.9 <= curves.curveA.length && curves.curveA.length <= 640.1);
        console.assert(159.9 <= curves.curveB.length && curves.curveB.length <= 160.1);
        let cmd = DocumentCommand.createAddCurve(curves.curveA);
        doc.executeCommand(cmd, false);

        let selection = doc.selection;
        console.log(selection);

        let cutCurve = Curve.createLine({x: 320, y: 150}, {x: 320, y: 350});
        cmd = DocumentCommand.createKnifeCut(cutCurve, selection);
        doc.executeCommand(cmd, false);

        selection = doc.selection
        console.log(selection);

        let item = selection.at(0);
        console.log(item);
        const nodeHandle = dommodule.SelectionItemApi.getNode(item.handle);
        console.log(nodeHandle);
        let node = new Node(nodeHandle);
        console.log(node);

        cmd = DocumentCommand.createScissorCut(node, 0, 0, true, 0.5);
        console.log(cmd);
        doc.executeCommand(cmd, false);

        selection = doc.selection
        console.log(selection.length);

        item = selection.at(0);
        console.log(item);
        node = item.node;
        console.log(node);
        let curvesInf = node.curvesInterface;
        console.log(curvesInf);
        const count = curvesInf.getSubSelectionCount(0);
        console.log(count);

        let subSelection = curvesInf.getSubSelection(0, 0);
        selection = Selection.create(doc);
        console.log(selection);
        let added = selection.add(node);
        console.log(added);
        added = selection.addSubSelectionForNode(node, subSelection);
        console.log(added);

        cmd = DocumentCommand.createSetSelection(selection);
        doc.executeCommand(cmd, false);

        cmd = DocumentCommand.createSplitCurve(selection, 0.5);
        doc.executeCommand(cmd, false);

        console.log("testCutCurve OK");
    }
}

function runTests() {
    testCurveCorner();
    testCutCurve();
}

module.exports.runTests = runTests
