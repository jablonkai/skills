'use strict';
const {Document} = require('/document');
const {DocumentCommand, AddChildNodesCommandBuilder, NodeChildType} = require('/commands');
const {ShapeNodeDefinition} = require('/nodes');
const {TagInterface, PredefinedTagKey} = require('/tagInterface');
const {TestUtils} = require("/tests/testUtils");

function testTagInterface() {
    let doc = TestUtils.newA4Empty();
    
    let acnBuilder = AddChildNodesCommandBuilder.create();
    let def = ShapeNodeDefinition.createDefault();
    acnBuilder.addNode(def);
    let cmd = acnBuilder.createCommand(true, NodeChildType.Main);
    let result = doc.executeCommand(cmd);
    
    let scrTag = "Test";
    let setTagCmd = DocumentCommand.createSetTagValueForPredefinedKey(null, PredefinedTagKey.ScriptLabel, scrTag);
    result = doc.executeCommand(setTagCmd);
    
    const shNode = doc.layers.first;
    let iface = shNode.tagInterface;
    console.assert(iface.hasPredefinedKey(PredefinedTagKey.ScriptLabel));
    let res = iface.getValueForPredefinedKey(PredefinedTagKey.ScriptLabel);
    console.assert(TestUtils.strEqual(scrTag, res));
    console.log("testTagInterface Ok");
    
    // waiting for close to be fixed.
    //doc.close();
}

module.exports.testTagInterface = testTagInterface;
