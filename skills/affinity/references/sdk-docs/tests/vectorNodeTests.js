'use strict';

const { app } = require('/application');
const { ShapeNodeDefinition, NodeChildType } = require('/nodes');
const { AddChildNodesCommandBuilder } = require('/commands');
const { FillDescriptor, FillType } = require('/fills');
const { BlendMode } = require('affinity:common');
const { LineStyleDescriptor, LineType } = require('/linestyle');
const { Colour, RGBA8 } = require('/colours');
const { ErrorCode } = require('affinity:common');
const { TestUtils } = require('/tests/testUtils');


function createTestFillDescriptor(r, g, b, a, blendMode = BlendMode.Normal) {
    const colour = RGBA8(r, g, b, a);
    return FillDescriptor.createSolid(colour, blendMode);
}

function createTestLineStyleDescriptor(weight = 5.0) {
    return LineStyleDescriptor.createDefault(weight);
}


function testBrushFillDescriptorCount() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    console.assert(shapeDef.brushFillDescriptorCount === 1, "Initial count should be 1");
    
    const fill1 = createTestFillDescriptor(255, 0, 0, 255);
    shapeDef.addBrushFillDescriptor(fill1);
    console.assert(shapeDef.brushFillDescriptorCount === 2, "Count should be 2 after adding");
    
    const fill2 = createTestFillDescriptor(0, 255, 0, 255);
    shapeDef.addBrushFillDescriptor(fill2);
    console.assert(shapeDef.brushFillDescriptorCount === 3, "Count should be 3 after adding another");
    
    console.log("testBrushFillDescriptorCount OK");
}


function testGetBrushFillDescriptor() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const fill1 = createTestFillDescriptor(255, 0, 0, 255, BlendMode.Normal);
    const fill2 = createTestFillDescriptor(0, 255, 0, 255, BlendMode.Multiply);
    
    shapeDef.addBrushFillDescriptor(fill1);
    shapeDef.addBrushFillDescriptor(fill2);
    
    const retrieved1 = shapeDef.getBrushFillDescriptor(1);
    console.assert(retrieved1.fill.fillType.value == FillType.Solid.value, "First fill should be solid");
    console.assert(retrieved1.blendMode.value === BlendMode.Normal.value, "First fill blend mode should be Normal");
    
    const retrieved2 = shapeDef.getBrushFillDescriptor(2);
    console.assert(retrieved2.fill.fillType.value == FillType.Solid.value, "Second fill should be solid");
    console.assert(retrieved2.blendMode.value === BlendMode.Multiply.value, "Second fill blend mode should be Multiply");
    
    console.log("testGetBrushFillDescriptor OK");
}


function testInsertBrushFillDescriptor() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const fillRed = createTestFillDescriptor(255, 0, 0, 255);
    const fillGreen = createTestFillDescriptor(0, 255, 0, 255);
    const fillBlue = createTestFillDescriptor(0, 0, 255, 255);
    
    shapeDef.addBrushFillDescriptor(fillRed);
    shapeDef.addBrushFillDescriptor(fillBlue);
    console.assert(shapeDef.brushFillDescriptorCount === 3);
    
    shapeDef.insertBrushFillDescriptor(1, fillGreen);
    console.assert(shapeDef.brushFillDescriptorCount === 4, "Count should be 3 after insert");
    
    const middle = shapeDef.getBrushFillDescriptor(1);
    console.assert(middle.fill.colour.rgba8.g === 255, "Middle fill should be green");
    
    console.log("testInsertBrushFillDescriptor OK");
}


function testSetBrushFillDescriptor() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const fillRed = createTestFillDescriptor(255, 0, 0, 255);
    const fillGreen = createTestFillDescriptor(0, 255, 0, 255);
    
    shapeDef.addBrushFillDescriptor(fillRed);
    console.assert(shapeDef.brushFillDescriptorCount === 2);
    
    const before = shapeDef.getBrushFillDescriptor(1);
    console.assert(before.fill.colour.rgba8.r === 255, "Should be red before");
    
    shapeDef.setBrushFillDescriptor(1, fillGreen);
    console.assert(shapeDef.brushFillDescriptorCount === 2, "Count should remain 2");
    
    const after = shapeDef.getBrushFillDescriptor(1);
    console.assert(after.fill.colour.rgba8.g === 255, "Should be green after");
    
    console.log("testSetBrushFillDescriptor OK");
}


function testRemoveBrushFillDescriptor() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const fillRed = createTestFillDescriptor(255, 0, 0, 255);
    const fillGreen = createTestFillDescriptor(0, 255, 0, 255);
    const fillBlue = createTestFillDescriptor(0, 0, 255, 255);
    
    shapeDef.addBrushFillDescriptor(fillRed);
    shapeDef.addBrushFillDescriptor(fillGreen);
    shapeDef.addBrushFillDescriptor(fillBlue);
    console.assert(shapeDef.brushFillDescriptorCount === 4);
    
    shapeDef.removeBrushFillDescriptor(2);
    console.assert(shapeDef.brushFillDescriptorCount === 3, "Count should be 3 after remove");
    
    const first = shapeDef.getBrushFillDescriptor(1);
    const second = shapeDef.getBrushFillDescriptor(2);
    console.assert(first.fill.colour.rgba8.r === 255, "First should still be red");
    console.assert(second.fill.colour.rgba8.b === 255, "Second should now be blue");
    
    console.log("testRemoveBrushFillDescriptor OK");
}


function testCurrentBrushFillIndex() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const fill1 = createTestFillDescriptor(255, 0, 0, 255);
    const fill2 = createTestFillDescriptor(0, 255, 0, 255);
    const fill3 = createTestFillDescriptor(0, 0, 255, 255);
    
    shapeDef.addBrushFillDescriptor(fill1);
    shapeDef.addBrushFillDescriptor(fill2);
    shapeDef.addBrushFillDescriptor(fill3);
    
    console.assert(shapeDef.currentBrushFillIndex === 0, "Initial current index should be 0");
    
    shapeDef.currentBrushFillIndex = 2;
    console.assert(shapeDef.currentBrushFillIndex === 2, "Current index should be 2");
    
    shapeDef.currentBrushFillIndex = 1;
    console.assert(shapeDef.currentBrushFillIndex === 1, "Current index should be 1");
    
    console.log("testCurrentBrushFillIndex OK");
}


function testLineStyleDescriptorCount() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    console.assert(shapeDef.lineDescriptorsCount === 1, "Initial count should be 1");
    
    const lineStyle1 = createTestLineStyleDescriptor(5.0);
    const lineFill1 = createTestFillDescriptor(255, 0, 0, 255);
    shapeDef.addLineDescriptors(lineFill1, lineStyle1);
    console.assert(shapeDef.lineDescriptorsCount === 2, "Count should be 2 after adding");
    
    const lineStyle2 = createTestLineStyleDescriptor(10.0);
    const lineFill2 = createTestFillDescriptor(0, 255, 0, 255);
    shapeDef.addLineDescriptors(lineFill2, lineStyle2);
    console.assert(shapeDef.lineDescriptorsCount === 3, "Count should be 3 after adding another");
    
    console.log("testLineStyleDescriptorCount OK");
}


function testGetLineDescriptors() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const lineStyle1 = createTestLineStyleDescriptor(5.0);
    const lineFill1 = createTestFillDescriptor(255, 0, 0, 255, BlendMode.Normal);
    
    const lineStyle2 = createTestLineStyleDescriptor(10.0);
    const lineFill2 = createTestFillDescriptor(0, 255, 0, 255, BlendMode.Multiply);
    
    shapeDef.addLineDescriptors(lineFill1, lineStyle1);
    shapeDef.addLineDescriptors(lineFill2, lineStyle2);
    
    const retrieved1 = shapeDef.getLineDescriptors(1);
    console.assert(retrieved1.lineStyle != null, "First lineStyle should exist");
    console.assert(retrieved1.fill != null, "First lineFill should exist");
    console.assert(retrieved1.fill.blendMode.value === BlendMode.Normal.value, "First lineFill blend mode should be Normal");
    
    const retrieved2 = shapeDef.getLineDescriptors(2);
    console.assert(retrieved2.lineStyle != null, "Second lineStyle should exist");
    console.assert(retrieved2.fill.blendMode.value === BlendMode.Multiply.value, "Second lineFill blend mode should be Multiply");
    
    console.log("testGetLineDescriptors OK");
}


function testInsertLineDescriptors() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const lineStyleRed = createTestLineStyleDescriptor(5.0);
    const lineFillRed = createTestFillDescriptor(255, 0, 0, 255);
    
    const lineStyleGreen = createTestLineStyleDescriptor(10.0);
    const lineFillGreen = createTestFillDescriptor(0, 255, 0, 255);
    
    const lineStyleBlue = createTestLineStyleDescriptor(15.0);
    const lineFillBlue = createTestFillDescriptor(0, 0, 255, 255);
    
    shapeDef.addLineDescriptors(lineFillRed, lineStyleRed);
    shapeDef.addLineDescriptors(lineFillBlue, lineStyleBlue);
    console.assert(shapeDef.lineDescriptorsCount === 3);
    
    shapeDef.insertLineDescriptors(1, lineFillGreen, lineStyleGreen);
    console.assert(shapeDef.lineDescriptorsCount === 4, "Count should be 4 after insert");
    
    const middle = shapeDef.getLineDescriptors(1);
    console.assert(middle.fill.fill.colour.rgba8.g === 255, "Middle lineFill should be green");
    
    console.log("testInsertLineDescriptors OK");
}


function testSetLineDescriptors() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const lineStyleRed = createTestLineStyleDescriptor(5.0);
    const lineFillRed = createTestFillDescriptor(255, 0, 0, 255);
    
    const lineStyleGreen = createTestLineStyleDescriptor(10.0);
    const lineFillGreen = createTestFillDescriptor(0, 255, 0, 255);
    
    shapeDef.addLineDescriptors(lineFillRed, lineStyleRed);
    console.assert(shapeDef.lineDescriptorsCount === 2);
    
    const before = shapeDef.getLineDescriptors(1);
    console.assert(before.fill.fill.colour.rgba8.r === 255, "Should be red before");
    
    shapeDef.setLineDescriptors(1, lineFillGreen, lineStyleGreen);
    console.assert(shapeDef.lineDescriptorsCount === 2, "Count should remain 1");
    
    const after = shapeDef.getLineDescriptors(1);
    console.assert(after.fill.fill.colour.rgba8.g === 255, "Should be green after");
    
    console.log("testSetLineDescriptors OK");
}


function testRemoveLineDescriptors() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const lineStyleRed = createTestLineStyleDescriptor(5.0);
    const lineFillRed = createTestFillDescriptor(255, 0, 0, 255);
    
    const lineStyleGreen = createTestLineStyleDescriptor(10.0);
    const lineFillGreen = createTestFillDescriptor(0, 255, 0, 255);
    
    const lineStyleBlue = createTestLineStyleDescriptor(15.0);
    const lineFillBlue = createTestFillDescriptor(0, 0, 255, 255);
    
    shapeDef.addLineDescriptors(lineFillRed, lineStyleRed);
    shapeDef.addLineDescriptors(lineFillGreen, lineStyleGreen);
    shapeDef.addLineDescriptors(lineFillBlue, lineStyleBlue);
    console.assert(shapeDef.lineDescriptorsCount === 4);
    
    shapeDef.removeLineDescriptors(2);
    console.assert(shapeDef.lineDescriptorsCount === 3, "Count should be 3 after remove");
    
    const first = shapeDef.getLineDescriptors(1);
    const second = shapeDef.getLineDescriptors(2);
    console.assert(first.fill.fill.colour.rgba8.r === 255, "First should still be red");
    console.assert(second.fill.fill.colour.rgba8.b === 255, "Second should now be blue");
    
    console.log("testRemoveLineDescriptors OK");
}


function testCurrentLineDescriptorsIndex() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const lineStyle1 = createTestLineStyleDescriptor(5.0);
    const lineFill1 = createTestFillDescriptor(255, 0, 0, 255);
    
    const lineStyle2 = createTestLineStyleDescriptor(10.0);
    const lineFill2 = createTestFillDescriptor(0, 255, 0, 255);
    
    const lineStyle3 = createTestLineStyleDescriptor(15.0);
    const lineFill3 = createTestFillDescriptor(0, 0, 255, 255);
    
    shapeDef.addLineDescriptors(lineStyle1, lineFill1);
    shapeDef.addLineDescriptors(lineStyle2, lineFill2);
    shapeDef.addLineDescriptors(lineStyle3, lineFill3);
    
    console.assert(shapeDef.currentLineDescriptorsIndex === 0, "Initial current index should be 0");
    
    shapeDef.currentLineDescriptorsIndex = 2;
    console.assert(shapeDef.currentLineDescriptorsIndex === 2, "Current index should be 2");
    
    shapeDef.currentLineDescriptorsIndex = 1;
    console.assert(shapeDef.currentLineDescriptorsIndex === 1, "Current index should be 1");
    
    console.log("testCurrentLineDescriptorsIndex OK");
}


function testVectorNodeDefinitionIntegration() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let shapeDef = ShapeNodeDefinition.createDefault();
        
        const brushFill1 = createTestFillDescriptor(255, 0, 0, 255, BlendMode.Normal);
        const brushFill2 = createTestFillDescriptor(0, 255, 0, 255, BlendMode.Multiply);
        
        shapeDef.addBrushFillDescriptor(brushFill1);
        shapeDef.addBrushFillDescriptor(brushFill2);
        
        const lineStyle1 = createTestLineStyleDescriptor(5.0);
        const lineFill1 = createTestFillDescriptor(0, 0, 255, 255);
        
        const lineStyle2 = createTestLineStyleDescriptor(10.0);
        const lineFill2 = createTestFillDescriptor(255, 255, 0, 255);
        
        shapeDef.addLineDescriptors(lineStyle1, lineFill1);
        shapeDef.addLineDescriptors(lineStyle2, lineFill2);
        
        console.assert(shapeDef.brushFillDescriptorCount === 3, "Should have 3 brush fills");
        console.assert(shapeDef.lineDescriptorsCount === 3, "Should have 3 line styles");
        
        shapeDef.currentBrushFillIndex = 2;
        console.assert(shapeDef.currentBrushFillIndex === 2, "Current brush fill index should be 2");
        
        shapeDef.currentLineDescriptorsIndex = 2;
        console.assert(shapeDef.currentLineDescriptorsIndex === 2, "Current line style index should be 2");
        
        acnBuilder.addShapeNode(shapeDef);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        console.assert(newNode.isShapeNode, "Should be a shape node");
        
        const bfIface = newNode.brushFillInterface;
        console.assert(bfIface.allDescriptors.length === 3, "Node should have 3 brush fills");
        console.assert(bfIface.currentIndex === 2, "Current brush fill index should be 2");
        
        const currentBrushFill = bfIface.getCurrentDescriptor();
        console.assert(currentBrushFill.fill.colour.rgba8.g === 255, "Current brush fill should be green");
        console.assert(currentBrushFill.blendMode.value === BlendMode.Multiply.value, "Current brush fill blend mode should be Multiply");
        
        const lsIface = newNode.lineStyleInterface;
        console.assert(lsIface.descriptorCount === 3, "Node should have 3 line styles");
        console.assert(lsIface.currentIndex === 2, "Current line style index should be 2");
        
        const currentLineFill = lsIface.getCurrentFillDescriptor();
        console.assert(currentLineFill.fill.colour.rgba8.r === 255 && currentLineFill.fill.colour.rgba8.g === 255, "Current line fill should be yellow");
        
        doc.undo();
        doc.close();
        console.log("testVectorNodeDefinitionIntegration OK");
    }
}


function testBrushFillCRUDWorkflow() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const fillRed = createTestFillDescriptor(255, 0, 0, 255);
    const fillGreen = createTestFillDescriptor(0, 255, 0, 255);
    const fillBlue = createTestFillDescriptor(0, 0, 255, 255);
    const fillYellow = createTestFillDescriptor(255, 255, 0, 255);
    
    shapeDef.addBrushFillDescriptor(fillRed);
    shapeDef.addBrushFillDescriptor(fillGreen);
    shapeDef.addBrushFillDescriptor(fillBlue);
    console.assert(shapeDef.brushFillDescriptorCount === 4, "Should have 4 fills");
    
    shapeDef.setBrushFillDescriptor(1, fillYellow);
    const modified = shapeDef.getBrushFillDescriptor(1);
    console.assert(modified.fill.colour.rgba8.r === 255 && modified.fill.colour.rgba8.g === 255, "Middle should be yellow");
    
    shapeDef.removeBrushFillDescriptor(0);
    console.assert(shapeDef.brushFillDescriptorCount === 3, "Should have 3 fills after remove");
    
    shapeDef.currentBrushFillIndex = 1;
    console.assert(shapeDef.currentBrushFillIndex === 1, "Current index should be 1");
    
    console.log("testBrushFillCRUDWorkflow OK");
}


function testLineStyleCRUDWorkflow() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const ls1 = createTestLineStyleDescriptor(5.0);
    const lf1 = createTestFillDescriptor(255, 0, 0, 255);
    
    const ls2 = createTestLineStyleDescriptor(10.0);
    const lf2 = createTestFillDescriptor(0, 255, 0, 255);
    
    const ls3 = createTestLineStyleDescriptor(15.0);
    const lf3 = createTestFillDescriptor(0, 0, 255, 255);
    
    const ls4 = createTestLineStyleDescriptor(20.0);
    const lf4 = createTestFillDescriptor(255, 255, 0, 255);
    
    shapeDef.addLineStyleDescriptor(ls1, lf1);
    shapeDef.addLineStyleDescriptor(ls2, lf2);
    shapeDef.addLineStyleDescriptor(ls3, lf3);
    console.assert(shapeDef.lineStyleDescriptorCount === 4, "Should have 4 line styles");
    
    shapeDef.setLineStyleDescriptor(1, ls4, lf4);
    const modified = shapeDef.getLineStyleDescriptor(1);
    console.assert(modified.fill.fill.colour.rgba8.r === 255 && modified.fill.fill.colour.rgba8.g === 255, "Middle should be yellow");
    
    shapeDef.removeLineStyleDescriptor(0);
    console.assert(shapeDef.lineStyleDescriptorCount === 3, "Should have 3 line styles after remove");
    
    shapeDef.currentLineStyleIndex = 1;
    console.assert(shapeDef.currentLineStyleIndex === 1, "Current index should be 1");
    
    console.log("testLineStyleCRUDWorkflow OK");
}


function testAddBrushFillDescriptorWithNull() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    const initialCount = shapeDef.brushFillDescriptorCount;
    
    shapeDef.addBrushFillDescriptor(null);
    console.assert(shapeDef.brushFillDescriptorCount === initialCount + 1, "Count should increase after adding null");
    
    const retrieved = shapeDef.getBrushFillDescriptor(initialCount);
    console.assert(retrieved.fill.fillType.value === FillType.None.value, "Null fill should result in FillType.None");
    
    console.log("testAddBrushFillDescriptorWithNull OK");
}


function testInsertBrushFillDescriptorWithNull() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const fillRed = createTestFillDescriptor(255, 0, 0, 255);
    shapeDef.addBrushFillDescriptor(fillRed);
    const countBefore = shapeDef.brushFillDescriptorCount;
    
    shapeDef.insertBrushFillDescriptor(1, null);
    console.assert(shapeDef.brushFillDescriptorCount === countBefore + 1, "Count should increase after inserting null");
    
    const inserted = shapeDef.getBrushFillDescriptor(1);
    console.assert(inserted.fill.fillType.value === FillType.None.value, "Inserted null fill should result in FillType.None");
    
    console.log("testInsertBrushFillDescriptorWithNull OK");
}


function testSetBrushFillDescriptorWithNull() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const fillRed = createTestFillDescriptor(255, 0, 0, 255);
    shapeDef.addBrushFillDescriptor(fillRed);
    
    const before = shapeDef.getBrushFillDescriptor(1);
    console.assert(before.fill.fillType.value === FillType.Solid.value, "Should be solid before");
    
    shapeDef.setBrushFillDescriptor(1, null);
    
    const after = shapeDef.getBrushFillDescriptor(1);
    console.assert(after.fill.fillType.value === FillType.None.value, "After setting to null, should be FillType.None");
    
    console.log("testSetBrushFillDescriptorWithNull OK");
}


function testAddLineStyleDescriptorWithNullLineStyle() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    const initialCount = shapeDef.lineStyleDescriptorCount;
    
    const lineFill = createTestFillDescriptor(255, 0, 0, 255);
    shapeDef.addLineStyleDescriptor(null, lineFill);
    console.assert(shapeDef.lineStyleDescriptorCount === initialCount + 1, "Count should increase after adding with null lineStyle");
    
    const retrieved = shapeDef.getLineStyleDescriptor(initialCount);
    console.assert(retrieved.lineStyle != null, "LineStyle should exist (defaulted)");
    console.assert(retrieved.fill.fill.fillType.value === FillType.Solid.value, "LineFill should be solid");
    
    console.log("testAddLineStyleDescriptorWithNullLineStyle OK");
}


function testAddLineStyleDescriptorWithNullLineFill() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    const initialCount = shapeDef.lineStyleDescriptorCount;
    
    const lineStyle = createTestLineStyleDescriptor(5.0);
    shapeDef.addLineStyleDescriptor(lineStyle, null);
    console.assert(shapeDef.lineStyleDescriptorCount === initialCount + 1, "Count should increase after adding with null lineFill");
    
    const retrieved = shapeDef.getLineStyleDescriptor(initialCount);
    console.assert(retrieved.lineStyle != null, "LineStyle should exist");
    console.assert(retrieved.fill.fill.fillType.value === FillType.None.value, "Null lineFill should result in FillType.None");
    
    console.log("testAddLineStyleDescriptorWithNullLineFill OK");
}


function testAddLineStyleDescriptorWithBothNull() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    const initialCount = shapeDef.lineStyleDescriptorCount;
    
    shapeDef.addLineStyleDescriptor(null, null);
    console.assert(shapeDef.lineStyleDescriptorCount === initialCount + 1, "Count should increase after adding with both null");
    
    const retrieved = shapeDef.getLineStyleDescriptor(initialCount);
    console.assert(retrieved.lineStyle != null, "LineStyle should exist (defaulted)");
    console.assert(retrieved.fill.fill.fillType.value === FillType.None.value, "LineFill should be FillType.None");
    
    console.log("testAddLineStyleDescriptorWithBothNull OK");
}


function testInsertLineStyleDescriptorWithNulls() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const ls = createTestLineStyleDescriptor(5.0);
    const lf = createTestFillDescriptor(255, 0, 0, 255);
    shapeDef.addLineStyleDescriptor(ls, lf);
    const countBefore = shapeDef.lineStyleDescriptorCount;
    
    shapeDef.insertLineStyleDescriptor(1, null, null);
    console.assert(shapeDef.lineStyleDescriptorCount === countBefore + 1, "Count should increase after inserting nulls");
    
    const inserted = shapeDef.getLineStyleDescriptor(1);
    console.assert(inserted.lineStyle.lineStyle.type.value === LineType.None.value, "Inserted lineStyle should be LineType.None");
    console.assert(inserted.fill.fill.fillType.value === FillType.None.value, "Inserted lineFill should be FillType.None");
    
    console.log("testInsertLineStyleDescriptorWithNulls OK");
}


function testSetLineStyleDescriptorWithNulls() {
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    const ls = createTestLineStyleDescriptor(5.0);
    const lf = createTestFillDescriptor(255, 0, 0, 255);
    shapeDef.addLineStyleDescriptor(ls, lf);
    
    const before = shapeDef.getLineStyleDescriptor(1);
    console.assert(before.fill.fill.fillType.value === FillType.Solid.value, "Should be solid before");
    
    shapeDef.setLineStyleDescriptor(1, null, null);
    
    const after = shapeDef.getLineStyleDescriptor(1);
    console.assert(after.lineStyle.lineStyle.type.value === LineType.None.value, "LineStyle should be LineType.None");
    console.assert(after.fill.fill.fillType.value === FillType.None.value, "After setting to null, lineFill should be FillType.None");
    
    console.log("testSetLineStyleDescriptorWithNulls OK");
}


function testNullDescriptorsIntegration() {
    let doc = TestUtils.newA4Empty();
    
    if (doc) {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let shapeDef = ShapeNodeDefinition.createDefault();
        
        shapeDef.addBrushFillDescriptor(null);
        shapeDef.addLineStyleDescriptor(null, null);
        
        console.assert(shapeDef.brushFillDescriptorCount === 2, "Should have 2 brush fills");
        console.assert(shapeDef.lineStyleDescriptorCount === 2, "Should have 2 line styles");
        
        shapeDef.currentBrushFillIndex = 1;
        shapeDef.currentLineStyleIndex = 1;
        
        acnBuilder.addShapeNode(shapeDef);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        console.assert(newNode.isShapeNode, "Should be a shape node");
        
        const bfIface = newNode.brushFillInterface;
        console.assert(bfIface.allDescriptors.length === 2, "Node should have 2 brush fills");
        const currentBrushFill = bfIface.getCurrentDescriptor();
        console.assert(currentBrushFill.fill.fillType.value === FillType.None.value, "Current brush fill should be None");
        
        const lsIface = newNode.lineStyleInterface;
        console.assert(lsIface.descriptorCount === 2, "Node should have 2 line styles");
        const currentLineFill = lsIface.getCurrentFillDescriptor();
        console.assert(currentLineFill.fill.fillType.value === FillType.None.value, "Current line fill should be None");
        
        doc.undo();
        doc.close();
        console.log("testNullDescriptorsIntegration OK");
    }
}


function testVectorNodeDefinition() {
    testBrushFillDescriptorCount();
    testGetBrushFillDescriptor();
    testInsertBrushFillDescriptor();
    testSetBrushFillDescriptor();
    testRemoveBrushFillDescriptor();
    testCurrentBrushFillIndex();
    
    testLineStyleDescriptorCount();
    testGetLineStyleDescriptor();
    testInsertLineStyleDescriptor();
    testSetLineStyleDescriptor();
    testRemoveLineStyleDescriptor();
    testCurrentLineStyleIndex();
    
    testVectorNodeDefinitionIntegration();
    testBrushFillCRUDWorkflow();
    testLineStyleCRUDWorkflow();
    
    testAddBrushFillDescriptorWithNull();
    testInsertBrushFillDescriptorWithNull();
    testSetBrushFillDescriptorWithNull();
    testAddLineStyleDescriptorWithNullLineStyle();
    testAddLineStyleDescriptorWithNullLineFill();
    testAddLineStyleDescriptorWithBothNull();
    testInsertLineStyleDescriptorWithNulls();
    testSetLineStyleDescriptorWithNulls();
    testNullDescriptorsIntegration();
    
    console.log("=== All VectorNodeDefinition Tests Passed ===");
}


module.exports.testVectorNodeDefinition = testVectorNodeDefinition;
