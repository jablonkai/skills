'use strict';
const {app} = require('/application');
const {ShapeNodeDefinition, PolyCurveNodeDefinition, ContainerNodeDefinition, ExposureAdjustmentRasterNodeDefinition, GaussianBlurFilterRasterNodeDefinition, createTypedNode, Node, NodeChildType} = require('/nodes');
const dommodule = require("affinity:dom");
const {DocumentCommand, AddChildNodesCommandBuilder, InsertionMode} = require("/commands");
const {Document, DocumentPromises} = require("/document.js");
const {Shape, ShapeType} = require("/shapes");
const {Fill, FillDescriptor} = require("/fills");
const {BlendMode} = require("affinity:common");
const {Rectangle} = require("/geometry");
const {LineStyleDescriptor, LineType} = require("/linestyle");
const {Colour, RGBA8} = require("/colours");
const {ErrorCode} = require('affinity:common');
const {RasterFormat} = require('/rasterobject');
const {RasterNodeDefinition, ImageNodeDefinition} = require('/nodes');

const {TestUtils} = require('/tests/testUtils');

function addChildNodeCollectiveFailPassTest() {
    let doc = TestUtils.getFile("/AddNodeDocSpreads.afdesign");
    
    if (doc) {
        // play with sel group node.
        const layernode = doc.layers.last;
        console.assert(layernode.isContainerNode);
        let shapeNodeDef = ShapeNodeDefinition.createDefault();
                
        { // Add node to layer's main will insert to it's main child.
            let acnBuilder = AddChildNodesCommandBuilder.create();
            acnBuilder.addNode(shapeNodeDef);
            
            acnBuilder.setInsertionTarget(layernode);
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
            let result = doc.executeCommand(anCommand);
        
            let snode = layernode.children.first;
            console.assert(snode.isShapeNode);
            doc.undo();
        }
        
        { // Add node to layer's enclosure should clip layer, no surprise.
            let acnBuilder = AddChildNodesCommandBuilder.create();
            acnBuilder.addNode(shapeNodeDef);
            acnBuilder.setInsertionTarget(layernode);
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Enclosure);
            let result = doc.executeCommand(anCommand);
            
            let snode = layernode.enclosures.first;
            console.assert(snode.isShapeNode);
            doc.undo();
        }
        
        const curSpread = doc.spreads.first; // first spread is the last spread node. ;-)
        { // Add node to any spread's main should add that as child
            let acnBuilder = AddChildNodesCommandBuilder.create();
            acnBuilder.addNode(shapeNodeDef);
            acnBuilder.setInsertionTarget(curSpread);
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
            let result = doc.executeCommand(anCommand);
            
            let snode = curSpread.children.first;
            console.assert(snode.isShapeNode);
            doc.undo();
        }
        
        const otherSpread = curSpread.nextSibling;
        { // Add node to any spread's main should add that as child
            let acnBuilder = AddChildNodesCommandBuilder.create();
            acnBuilder.addNode(shapeNodeDef);
            acnBuilder.setInsertionTarget(otherSpread);
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
            let result = doc.executeCommand(anCommand);
            
            let snode = otherSpread.children.first;
            console.assert(snode.isShapeNode);
            doc.undo();
        }
        
        { // Add node to spread's enclosure will fail.
            let acnBuilder = AddChildNodesCommandBuilder.create();
            acnBuilder.addNode(shapeNodeDef);
            acnBuilder.setInsertionTarget(otherSpread);
            try {
                let anCommand = acnBuilder.createCommand(false, NodeChildType.Enclosure);
                let result = doc.executeCommand(anCommand);
            } catch (err) {
                console.assert(err.errorCode.value == ErrorCode.INVALID_ARGS);
            }
        }
        
        { // Add image/raster node to different format doc will fail.
            let acnBuilder = AddChildNodesCommandBuilder.create();
            let rnd = RasterNodeDefinition.create(RasterFormat.CMYKA8);
            acnBuilder.addNode(rnd);
            try {
                let anCommand = acnBuilder.createCommand(false, NodeChildType.Enclosure);
                let result = doc.executeCommand(anCommand);
            } catch (err) {
                console.assert(err.errorCode.value == ErrorCode.ABORTED);
            }
        }
        
        // Add node to other nodes should be quite boring.
        const curvenode = layernode.previousSibling;
        {
            let acnBuilder = AddChildNodesCommandBuilder.create();
            acnBuilder.addNode(shapeNodeDef);
            acnBuilder.setInsertionTarget(curvenode);
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
            let result = doc.executeCommand(anCommand);
        }
        console.assert(curvenode.children.first.isShapeNode);
        doc.undo();
        
        {
            let acnBuilder = AddChildNodesCommandBuilder.create();
            acnBuilder.addNode(shapeNodeDef);
            acnBuilder.setInsertionTarget(curvenode);
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Enclosure);
            let result = doc.executeCommand(anCommand);
        }
        
        console.assert(curvenode.enclosures.first.isShapeNode);
        doc.undo();
        
        console.log("closing doc");
        //doc.close();
        console.log("addChildNodeCollectiveFailPassTest OK");
    }
}

function testAddNodeDescription() {
    let doc = TestUtils.newA4Empty();
    
    // only one node should have full description.
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let shapeNodeDef = ShapeNodeDefinition.createDefault();
        let description = "my beautiful shape"
        shapeNodeDef.userDescription = description;
        acnBuilder.addNode(shapeNodeDef);
            
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let desc = anCommand.description;
        console.assert(!TestUtils.strEqual(desc, "Add"));
        
        let node = doc.layers.first;
        let descIface = node.descriptionInterface;
        console.assert(TestUtils.strEqual(descIface.userDescription, description));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let exp = ExposureAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(exp);
            
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let desc = anCommand.description;
        console.assert(!TestUtils.strEqual(desc, "Add"));
        
        doc.undo();
    }
    
    // more than one node will have Description of Add
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let shapeNodeDef = ShapeNodeDefinition.createDefault();
        let exp = ExposureAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(exp);
        acnBuilder.addNode(shapeNodeDef);
            
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let desc = anCommand.description;
        console.assert(TestUtils.strEqual(desc, "Add"));
        
        doc.undo();
    }
    
    doc.close();
    console.log("testAddNodeDescription OK");
}


function testAddMultipleNodes() {
    let doc = TestUtils.newA4Empty();
    
    let acnBuilder = AddChildNodesCommandBuilder.create();
    let sn = ShapeNodeDefinition.createDefault();
    let pcn = PolyCurveNodeDefinition.createDefault();
    let gbf = GaussianBlurFilterRasterNodeDefinition.createDefault();
    let ea = ExposureAdjustmentRasterNodeDefinition.createDefault();
    acnBuilder.addNode(sn);
    acnBuilder.addNode(pcn);
    acnBuilder.addNode(gbf);
    acnBuilder.addNode(pcn);
    acnBuilder.addNode(sn);
    acnBuilder.addNode(pcn);
    acnBuilder.addNode(sn);
    acnBuilder.addNode(ea);
    acnBuilder.addNode(pcn);
    acnBuilder.addNode(gbf);
    acnBuilder.addNode(sn);
        
    let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
    let result = doc.executeCommand(anCommand);
    
    let nodeiter = doc.layers.first;
    console.assert(nodeiter.isShapeNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isGaussianBlurFilterRasterNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isPolyCurveNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isExposureAdjustmentRasterNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isShapeNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isPolyCurveNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isShapeNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isPolyCurveNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isGaussianBlurFilterRasterNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isPolyCurveNode);
    nodeiter = nodeiter.previousSibling;
    console.assert(nodeiter.isShapeNode);
    
    doc.undo();
    
    doc.close();
    console.log("testAddMultipleNodes OK");
}


function testContainerNodeDefault() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let layerNodeDef = ContainerNodeDefinition.createDefault();
        acnBuilder.addContainerNode(layerNodeDef);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        const newNode = doc.layers.first;
        console.assert(newNode.isContainerNode);
        doc.undo();
        //doc.close();
        console.log("testContainerNodeDefault OK");
    }
}


function testShapeNodeDefault() {
    return;
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let shapeNodeDef = ShapeNodeDefinition.createDefault();
        acnBuilder.addShapeNode(shapeNodeDef);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        console.assert(newNode.isShapeNode);
        
        const bfIface = newNode.brushFillInterface;
        console.assert(bfIface.descriptors.length === 1);
        console.assert(bfIface.currentDescriptor.fill.isNoFill);
        console.assert(bfIface.currentDescriptor.blendMode.value == BlendMode.Normal);
        
        const lsIFace = newNode.lineStyleInterface;
        console.assert(lsIFace.allDescriptors.length === 1);
        console.assert(lsIFace.fill.fill.isNoFill);
        console.assert(lsIFace.style.lineType.value == LineType.None);
        
        const xpIFace = newNode.transparencyInterface;
        console.assert(xpIFace.isTransparencyNone);
        
        const shapeIFace = newNode.shapeInterface;
        console.assert(shapeIFace.type.value == ShapeType.Rectangle);
        
        doc.undo();
        doc.close();
        console.log("testShapeNodeDefault OK");
    }
}


function testRandom() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        // Generate a random number between 45 and 55 (inclusive)
        const min = 1;
        const max = 20;
        const testCounts = Math.floor(Math.random() * (max - min + 1)) + min;
        // Run a loop for the random number of times
        for (let i = 0; i < testCounts; i++) {
            const x = Math.random() * (2000 - 100) + 100;
            const y = Math.random() * (2000 - 100) + 100;

            const w = Math.random() * (150 - 100) + 100;
            const h = Math.random() * (150 - 100) + 100;
            
            const r = 255 * Math.random();
            const g = 255 * Math.random();
            const b = 255 * Math.random();
            const a = 150 + Math.random() * 100;
            
            const lineWeight = 10 + Math.random() * 40;
            
            const bfBlend = Math.floor(Math.random() * 30);
            const bfColour = RGBA8(r, g, b, a);
            const brushFill = FillDescriptor.createSolid(bfColour, bfBlend);
            
            const lfBlend = Math.floor(Math.random() * 30);
            const lfColour = RGBA8(g, b, a, r);
            const lineFill = FillDescriptor.createSolid(lfColour, lfBlend);
            const lineStyle = LineStyleDescriptor.createFromWeight(lineWeight);
            
            const transColour = RGBA8(b, a, r, g);
            const transFill = FillDescriptor.createSolid(transColour, BlendMode.Normal);
            
            const rect = new Rectangle(x, y, w, h);
            
            const s = Math.floor(Math.random() * 18);
            let shapeType = s;
            
            let shape = Shape.create(shapeType);
            
            let shapeDef = ShapeNodeDefinition.create(shape, rect, brushFill, lineFill, lineStyle, transFill);
            
            acnBuilder.addNode(shapeDef);
            
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
            let result = doc.executeCommand(anCommand);
            
            const newNode = doc.layers.first;
            
            console.assert(newNode.isShapeNode);
            
            const bfIface = newNode.brushFillInterface;
            console.assert(bfIface.allDescriptors.length === 1);
            console.assert(bfIface.fillDescriptor.fill.colour.rgba8.r === bfColour.rgba8.r);
            console.assert(bfIface.fillDescriptor.fill.isSolidFill);
            console.assert(bfIface.fillDescriptor.blendMode == bfBlend);
            
            const lsIFace = newNode.lineStyleInterface;
            console.assert(lsIFace.allDescriptors.length === 1);
            console.assert(lsIFace.fill.fill.isSolidFill);
            console.assert(lsIFace.fill.fill.colour.rgba8.r === lfColour.rgba8.r);
            console.assert(lsIFace.fill.blendMode == lfBlend);
            console.assert(lsIFace.style.lineType.value == LineType.Solid);
            
            const xpIFace = newNode.transparencyInterface;
            console.assert(!xpIFace.isTransparencyNone);
            
            const shapeIFace = newNode.shapeInterface;
            console.assert(shapeIFace.type == shapeType);
            console.assert(shapeIFace.boundingBox.x === rect.x);
            
            doc.undo();
        }
        doc.close();
        console.log("testRandom OK");
    }
}

function testShapeNodeFailure() {
    //Should fail because no 0 width&height rect allowed.
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        const x = Math.random() * (2000 - 100) + 100;
        const y = Math.random() * (2000 - 100) + 100;
        
        const w = 0.0;
        const h = 0.0;
        
        const r = 255 * Math.random();
        const g = 255 * Math.random();
        const b = 255 * Math.random();
        const a = 150 + Math.random() * 100;
        
        const lineWeight = 10 + Math.random() * 40;
        
        const bfBlend = Math.floor(Math.random() * 30);
        const bfColour = Colour.createRGBA8(new RGBA8(r, g, b, a));
        const brushFill = FillDescriptor.createSolid(bfColour, bfBlend);
        
        const lfBlend = Math.floor(Math.random() * 30);
        const lfColour = Colour.createRGBA8(new RGBA8(g, b, a, r));
        const lineFill = FillDescriptor.createSolid(lfColour, lfBlend);
        const lineStyle = LineStyleDescriptor.createFromWeight(lineWeight);
        
        const transColour = Colour.createRGBA8(new RGBA8(b, a, r, g))
        const transFill = FillDescriptor.createSolid(transColour, BlendMode.Normal);
        
        const rect = new Rectangle(x, y, w, h);
        
        const s = Math.floor(Math.random() * 18);
        let shapeType = s;
        
        let shape = Shape.create(shapeType);
        
        let shapeDef = ShapeNodeDefinition.create(shape, rect, brushFill, lineFill, lineStyle, transFill);
        
        let nodeDef = shapeDef.asNodeDefinition();
        
        try {
            acnBuilder.addNode(nodeDef);
            console.assert(false, "Failed");
        } catch (err) {
            if (err.errorCode.value != ErrorCode.INVALID_OP)
				console.log(err.stack);
        }
        doc.close();
        console.log("testShapeNodeFailure OK");
    }
}



function testShapeNodeAddBrushAndLineStyle() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        const r = 255 * Math.random();
        const g = 255 * Math.random();
        const b = 255 * Math.random();
        const a = 150 + Math.random() * 100;
        
        
        const bfBlend = Math.floor(Math.random() * 30);
        const bfColour = Colour.createRGBA8(new RGBA8(r, g, b, a));
        const brushFill = FillDescriptor.createSolid(bfColour, bfBlend);
        
        
        const lineWeight = 10 + Math.random() * 40;
        
        const lfBlend = Math.floor(Math.random() * 30);
        const lfColour = Colour.createRGBA8(new RGBA8(g, b, a, r));
        const lineFill = FillDescriptor.createSolid(lfColour, lfBlend);
        const lineStyle = LineStyleDescriptor.createFromWeight(lineWeight);
        
        
        let shapeDef = ShapeNodeDefinition.createDefault();
        shapeDef.addBrushFillDescriptor(brushFill);
        shapeDef.addLineDescriptors(lineFill, lineStyle);
        
        acnBuilder.addShapeNode(shapeDef);
        
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isShapeNode);
        
        const bfIface = newNode.brushFillInterface;
        console.assert(bfIface.allDescriptors.length === 2);
        
        const lsIFace = newNode.lineStyleInterface;
        console.assert(lsIFace.allDescriptors.length === 2);
    
        doc.undo();
        doc.close();
        console.log("testShapeNodeAddBrushAndLineStyle OK");
    }
}


function testAddNodeFail() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let shapeNodeDef = ShapeNodeDefinition.createDefault();
        acnBuilder.addShapeNode(shapeNodeDef);
        let dNode = doc.rootNode;
        
        try {
            acnBuilder.setInsertionTarget(dNode);
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
            let result = doc.executeCommand(anCommand);
            console.assert(false, "Failed");
        } catch (err) {
            console.assert(err.errorCode.value == ErrorCode.INVALID_ARGS);
        }
        
        acnBuilder = AddChildNodesCommandBuilder.create();
        
        acnBuilder.addShapeNode(shapeNodeDef);
        let sNode = doc.spreads.current;
        
        try {
            acnBuilder.setInsertionTarget(sNode);
            let anCommand = acnBuilder.createCommand(false, NodeChildType.Enclosure);
            let result = doc.executeCommand(anCommand);
            //nothing happens at the moment, but the assert shouldn't get reached as the command would fail. To be fixed.
            //console.assert(false, "Failed");
        } catch (err) {
            console.assert(err.errorCode.value == ErrorCode.INVALID_ARGS);
        }
        
        doc.close();
        console.log("testAddNodeFail OK");
    }
}


function testAddNodes() {
    //testAddNodeDescription();
    addChildNodeCollectiveFailPassTest();
    testContainerNodeDefault();
    testShapeNodeDefault();
    testShapeNodeFailure();
    testRandom();
    testShapeNodeAddBrushAndLineStyle();
    testAddNodeFail();
}

function addNodesDemo() {
    let doc = Document.current;
    console.assert(doc != null);
    
    let acnBuilder = AddChildNodesCommandBuilder.create();
    
    // Generate a random number between 45 and 55 (inclusive)
    const min = 45;
    const max = 55;
    const randomNumber = Math.floor(Math.random() * (max - min + 1)) + min;
    // Run a loop for the random number of times
    for (let i = 0; i < randomNumber; i++) {
        const x = Math.random() * (2000 - 100) + 100;
        const y = Math.random() * (2000 - 100) + 100;

        const w = Math.random() * (150 - 100) + 100;
        const h = Math.random() * (150 - 100) + 100;
        
        const r = 255 * Math.random();
        const g = 255 * Math.random();
        const b = 255 * Math.random();
        const a = 150 + Math.random() * 100;
        
        const lineWeight = 10 + Math.random() * 40;
        
        const bfColour = RGBA8(r, g, b, a);
        
        const brushFill = FillDescriptor.createSolid(bfColour, BlendMode.Normal); // blendmode ColourBurn
        
        const lineFill = FillDescriptor.createSolid(RGBA8(g, b, a, r), BlendMode.ColourBurn); // normal blend
        
        const transFill = FillDescriptor.createSolid(RGBA8(b, a, r, g), BlendMode.Normal);
        
        const lineStyle = LineStyleDescriptor.createDefault(lineWeight);
        
        const rect = new Rectangle(x, y, w, h);
        
        const s = Math.floor(Math.random() * 4);
        
        let shape;
        switch (s) {
            case 0:
                shape = Shape.create(ShapeType.Cat);
                break;
            case 1:
                shape = Shape.create(ShapeType.Cat2);
                break;
            case 2:
                shape = Shape.create(ShapeType.Cat3);
                break;
            case 3:
                shape = Shape.create(ShapeType.Cat4);
                break;
            default:
                shape = Shape.create(ShapeType.Donut);
        }
        
        let shapeDef = ShapeNodeDefinition.create(shape, rect, brushFill, lineFill, lineStyle, transFill);
        
        acnBuilder.addNode(shapeDef);
        
    }
    
    let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
    console.log("ece");
    let result = doc.executeCommand(anCommand);
    console.log("done");
}


module.exports.testAddNodes = testAddNodes;
module.exports.addNodesDemo = addNodesDemo;
module.exports.testAddNodeDescription = testAddNodeDescription;
module.exports.testAddMultipleNodes = testAddMultipleNodes;
