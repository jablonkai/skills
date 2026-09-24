'use strict';
const {app} = require('/application.js');
const {TestUtils} = require('/tests/testUtils.js');
const {AddChildNodesCommandBuilder, NodeChildType} = require('/commands.js');
const {ContainerNodeDefinition} = require('/nodes.js');
const {Document} = require('/document.js');


function testContainerNode() {
    const document = TestUtils.newA4Empty();
    let acnBuilder = AddChildNodesCommandBuilder.create();
    let cnd = ContainerNodeDefinition.createDefault();
    acnBuilder.addNode(cnd);
    let cmd = acnBuilder.createCommand(false, NodeChildType.Main);
    document.executeCommand(cmd);

    const containerNode = document.layers.first;

    console.log("The layer colour of the container node is");
    console.log(containerNode.layerColour.rgba8);
    //document.close();
}

module.exports.testContainerNode = testContainerNode;
