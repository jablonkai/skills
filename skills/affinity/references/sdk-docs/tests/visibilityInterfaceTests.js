'use strict';
const {Document} = require('/document');
const {DocumentCommand, AddChildNodesCommandBuilder, NodeChildType} = require('/commands');
const {ShapeNodeDefinition} = require('/nodes');
const {VisibilityInterface, VisibilityTestOptionsApi, TextVisibilityOptionsApi} = require('/visibilityInterface');
const {TestUtils} = require("/tests/testUtils");

function testVisibilityInterface() {
    let doc = TestUtils.newA4Empty();
    
    let acnBuilder = AddChildNodesCommandBuilder.create();
    let def = ShapeNodeDefinition.createDefault();
    acnBuilder.addNode(def);
    let cmd = acnBuilder.createCommand(true, NodeChildType.Main);
    let result = doc.executeCommand(cmd);

    let node = doc.layers.first;
    let testOptions = VisibilityTestOptionsApi.create();
    console.log(node.globalOpacity);
    let res = node.testVisibility(testOptions);
    console.assert(res);
    
    console.log("testVisibilityInterface Ok");
    
    // waiting for close to be fixed.
    //doc.close();
}

module.exports.testVisibilityInterface = testVisibilityInterface;
