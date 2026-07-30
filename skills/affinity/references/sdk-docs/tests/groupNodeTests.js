'use strict';
const {app} = require('/application');
const {createTypedNode} = require('/node');

function testGroupNode() {
    const doc = app.documents.current;
    if (doc) {
        // make sure your doc has a groupnode as its first node
        const groupNode = doc.layers.first;

        console.log("the (group) node is :");
        console.log(groupNode.toString());
        console.log("the node's parent is:");
        console.log(groupNode.parent);
        console.log("the group node's children are:");
        for (const child of groupNode.children) {
            console.log(child)
        }
    }
}

module.exports.testGroupNode = testGroupNode;
