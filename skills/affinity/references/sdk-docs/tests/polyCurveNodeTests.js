'use strict';
const {app} = require('/application');
const {PolyCurveNodeDefinition} = require('/node');
const {dommodule} = require("affinity:dom");
const {DocumentCommand, AddChildNodesCommandBuilder} = require("/command");
const {Document, DocumentPromises} = require("/document.js");
const {PolyCurve, Curve, CurveBuilder, Rectangle} = require("/geometry.js");
const {Fill, FillDescriptor} = require("/fill");
const {BlendMode} = require("affinity:common");
const {LineStyleDescriptor, LineType} = require("/lineStyleDescriptor");
const {Colour, RGBA8} = require("/colour");
const {ErrorCode} = require('affinity:common');

const {TestUtils} = require('/tests/testUtils');


function testPolyCurveNodeDefault() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let polyCurveNodeDef = PolyCurveNodeDefinition.createDefault();
        
        let def = polyCurveNodeDef.asNodeDefinition();
        acnBuilder.addNode(def);
        
        let anCommand = acnBuilder.createCommand();
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        console.assert(newNode.isPolyCurveNode);
        
        const bfIface = newNode.brushFillInterface;
        console.assert(bfIface.allDescriptors.length === 1);
        console.assert(bfIface.fillDescriptor.fill.isNoFill);
        console.assert(bfIface.fillDescriptor.blendMode.value == BlendMode.Normal);
        
        const lsIFace = newNode.lineStyleInterface;
        console.assert(lsIFace.allDescriptors.length === 1);
        console.assert(lsIFace.fill.fill.isNoFill);
        console.assert(lsIFace.style.lineType.value == LineType.None);
        
        const xpIFace = newNode.transparencyInterface;
        console.assert(xpIFace.isTransparencyNone);
        
        doc.undo();
        doc.close();
        console.log("testPolyCurveNodeDefault OK");
    }
}

function testPolyCurveNodeCreate() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        // Generate a random number between 45 and 55 (inclusive)
        const min = 25;
        const max = 55;
        const randomNumber = Math.floor(Math.random() * (max - min + 1)) + min;
        
        let polyCurve = new PolyCurve();
        // Run a loop for the random number of times
        for (let i = 0; i < randomNumber; i++) {
            let x = Math.random() * (2000 - 100) + 100;
            let y = Math.random() * (2000 - 100) + 100;
            let w = Math.random() * (2000 - 100) + 100;
            let h = Math.random() * (2000 - 100) + 100;
            
            const rect = new Rectangle(x, y, w, h);
            
            let curve = Curve.createEllipse(rect);
            polyCurve.addCurve(curve);
        }
        const r = 255 * Math.random();
        const g = 255 * Math.random();
        const b = 255 * Math.random();
        const a = 150 + Math.random() * 100;
        
        const lineWeight = 10 + Math.random() * 40;
        
        const brushFill = FillDescriptor.createSolid(Colour.createRGBA8(new RGBA8(r, g, b, a)), BlendMode.Normal); // blendmode ColourBurn
        
        const lineFill = FillDescriptor.createSolid(Colour.createRGBA8(new RGBA8(g, b, a, r)), BlendMode.ColourBurn); // normal blend
        
        const transFill = FillDescriptor.createSolid(Colour.createRGBA8(new RGBA8(b, a, r, g)), BlendMode.Normal);
        
        const lineStyle = LineStyleDescriptor.createFromWeight(lineWeight);
        
        let pcNodeDef = PolyCurveNodeDefinition.create(polyCurve, brushFill, lineStyle, lineFill, transFill);
        
        acnBuilder.addPolyCurveNode(pcNodeDef);
        
        let anCommand = acnBuilder.createCommand();
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        console.assert(newNode.isPolyCurveNode);
        
        let cIface = newNode.curvesInterface;
        console.assert(cIface.polyCurve.curves.length == randomNumber);
        doc.undo();
        doc.close();
        console.log("testPolyCurveNodeCreate OK");
    }
}


function testPolyCurveNodeFailure() {
    //Empty curve not allowed as a poly curve node.
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let polyCurve = new PolyCurve();
        
        const r = 255 * Math.random();
        const g = 255 * Math.random();
        const b = 255 * Math.random();
        const a = 150 + Math.random() * 100;
        
        const lineWeight = 10 + Math.random() * 40;
        
        const brushFill = FillDescriptor.createSolid(Colour.createRGBA8(new RGBA8(r, g, b, a)), BlendMode.Normal); // blendmode ColourBurn
        
        const lineFill = FillDescriptor.createSolid(Colour.createRGBA8(new RGBA8(g, b, a, r)), BlendMode.ColourBurn); // normal blend
        
        const transFill = FillDescriptor.createSolid(Colour.createRGBA8(new RGBA8(b, a, r, g)), BlendMode.Normal);
        
        const lineStyle = LineStyleDescriptor.createFromWeight(lineWeight);
        
        let pcNodeDef = PolyCurveNodeDefinition.create(polyCurve, brushFill, lineStyle, lineFill, transFill);
        
        try {
            acnBuilder.addPolyCurveNode(pcNodeDef);
            console.assert(false, "Failed.");
        } catch(err) {
            if (err.errorCode.value != ErrorCode.INVALID_OP)
				console.log(err.stack);
        }
        doc.close();
        console.log("testPolyCurveNodeFailure OK");
    }
}


function testPolyCurveNode() {
    testPolyCurveNodeDefault();
    testPolyCurveNodeCreate();
    testPolyCurveNodeFailure();
}


function addPolyCurveDemo() {
    let doc = Document.current;
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let cBuilder = CurveBuilder.create();
        
        // Generate a random number between 45 and 55 (inclusive)
        const min = 45;
        const max = 55;
        const randomNumber = Math.floor(Math.random() * (max - min + 1)) + min;
        
        
        let beginx = Math.random() * (2000 - 100) + 100;
        let beginy = Math.random() * (2000 - 100) + 100;
        
        cBuilder.begin(beginx, beginy);
        // Run a loop for the random number of times
        for (let i = 0; i < randomNumber; i++) {
            let endx = Math.random() * (2000 - 100) + 100;
            let endy = Math.random() * (2000 - 100) + 100;
            
            cBuilder.lineTo(endx, endy);
            
            beginx = endx;
            beginy = endy;
        }
        let curve = cBuilder.createCurve();
            
        const r = 255 * Math.random();
        const g = 255 * Math.random();
        const b = 255 * Math.random();
        const a = 150 + Math.random() * 100;
        
        const lineWeight = 10 + Math.random() * 40;
        
        const bfColour = Colour.createRGBA8(new RGBA8(r, g, b, a));
        
        const brushFill = FillDescriptor.createSolid(bfColour, BlendMode.Normal); // blendmode ColourBurn
        
        const lineFill = FillDescriptor.createSolid(Colour.createRGBA8(new RGBA8(g, b, a, r)), BlendMode.ColourBurn); // normal blend
        
        const transFill = FillDescriptor.createSolid(Colour.createRGBA8(new RGBA8(b, a, r, g)), BlendMode.Normal);
        
        const lineStyle = LineStyleDescriptor.createFromWeight(lineWeight);
        
        let polyCurve = new PolyCurve();
        
        polyCurve.addCurve(curve);
        
        let pcNodeDef = PolyCurveNodeDefinition.create(polyCurve, brushFill, lineStyle, lineFill, transFill);
        
        let nodeDef = pcNodeDef.asNodeDefinition();
        
        acnBuilder.addNode(nodeDef);
        
        let anCommand = acnBuilder.createCommand();
        let result = doc.executeCommand(anCommand);
    }
}


module.exports.addPolyCurveDemo = addPolyCurveDemo;
module.exports.testPolyCurveNode = testPolyCurveNode;
