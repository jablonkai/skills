'use strict';

const { TestUtils } = require('/tests/testUtils');
const { Document } = require('/document');
const { Selection } = require('/selections');
const { DocumentCommand } = require('/commands');
const { ShapeNodeDefinition, NodeChildType } = require('/nodes');
const { AddChildNodesCommandBuilder } = require('/commands');
const { Spline, SplineProfile } = require('/geometry');
const { BlendMode, AntialiasingMode } = require('/blendmodeinterface');

function testBlendModeInterface() {
    let doc = TestUtils.newA4Empty();
    
    let shapeDef = ShapeNodeDefinition.createDefault();
    
    let acnBuilder = AddChildNodesCommandBuilder.create();
    acnBuilder.addNode(shapeDef);
    let addCommand = acnBuilder.createCommand(false, NodeChildType.Main);
    doc.executeCommand(addCommand);
    
    let shapeNode = doc.layers.first;
    console.assert(shapeNode.isShapeNode, "Should be a ShapeNode");
    
    let blendModeIface = shapeNode.blendModeInterface;
    console.assert(blendModeIface.isBlendModeInterface, "Should have BlendModeInterface");
    
    let initialBlendMode = blendModeIface.blendMode;
    console.assert(initialBlendMode !== undefined, "Should have blend mode");
    
    let antialiasingMode = blendModeIface.antialiasingMode;
    console.assert(antialiasingMode !== undefined, "Should have antialiasing mode");
    
    let blendOptions = blendModeIface.blendOptions;
    console.assert(blendOptions.isBlendOptions, "Should have BlendOptions");
    
    let selection = Selection.create(doc, shapeNode);
    
    let setGammaCmd = DocumentCommand.createSetBlendGamma(selection, 2.4);
    doc.executeCommand(setGammaCmd);
    
    blendOptions = shapeNode.blendOptions;
    let newGamma = blendOptions.gamma;
    console.assert(TestUtils.floatEqual(newGamma, 2.4), "Gamma should be 2.4");
    
    let masterSpline = Spline.createFromProfile(SplineProfile.Linear);
    let p1 = {x: 0.3, y: 0.5};
    let p2 = {x: 0.7, y: 0.9};
    masterSpline.insertPoint(p1);
    masterSpline.insertPoint(p2);
    
    blendOptions.masterSourceLayerRanges = masterSpline;
    
    let readBackSpline = blendOptions.masterSourceLayerRanges;
    console.assert(readBackSpline.pointCount === 4, "Master source spline should have 4 points");
    console.assert(TestUtils.floatEqual(readBackSpline.getPoint(1).y, 0.5), "Point 1 y should be 0.5");
    
    let channelSpline = Spline.createFromProfile(SplineProfile.Linear);
    let p3 = {x: 0.2, y: 0.3};
    let p4 = {x: 0.8, y: 0.7};
    channelSpline.insertPoint(p3);
    channelSpline.insertPoint(p4);
    
    blendOptions.setChannelSourceLayerRanges(0, channelSpline);
    let readChannelSpline = blendOptions.getChannelSourceLayerRanges(0);
    console.assert(readChannelSpline.pointCount === 4, "Channel 0 source spline should have 4 points");
    console.assert(TestUtils.floatEqual(readChannelSpline.getPoint(1).y, 0.3), "Channel point 1 y should be 0.3");
    
    blendOptions.masterUnderlyingCompositionRanges = masterSpline;
    let underlyingSpline = blendOptions.masterUnderlyingCompositionRanges;
    console.assert(underlyingSpline.pointCount === 4, "Master underlying spline should have 4 points");
    
    blendOptions.setChannelUnderlyingCompositionRanges(1, channelSpline);
    let readUnderlyingChannel = blendOptions.getChannelUnderlyingCompositionRanges(1);
    console.assert(readUnderlyingChannel.pointCount === 4, "Channel 1 underlying spline should have 4 points");
    
    let setRangesCmd = DocumentCommand.createSetBlendRanges(selection, blendOptions);
    doc.executeCommand(setRangesCmd);
    
    let blendOptionsAfterCmd = shapeNode.blendOptions;
    let verifySpline = blendOptionsAfterCmd.getChannelSourceLayerRanges(0);
    console.assert(verifySpline.pointCount === 4, "Channel 0 should persist after command");
    
    let nodeBack = blendModeIface.node;
    console.assert(nodeBack.isSameNode(shapeNode), "GetNode should return same node");
    
    
    doc.close();
    console.log("testBlendModeInterface OK");
}

module.exports.testBlendModeInterface = testBlendModeInterface;
