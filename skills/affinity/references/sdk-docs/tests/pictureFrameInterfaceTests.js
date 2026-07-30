'use strict';
const {app} = require('/application');
const {PictureFrameInterface} = require('/pictureFrameInterface');
const {createTypedNode} = require('/node');

function testPictureFrameInterface() {
    const doc = app.documents.current;
    if (doc) {
        // make sure your doc has a shapenode as its first node
        const shapeNode = doc.layers.first
        const picFrame = shapeNode.pictureFrameInterface;

        console.log("Is picture frame interface enabled");
        console.log(picFrame.enabled);
        console.log("PictureFrameInterface's description");
        console.log(picFrame.description);
        console.log("Does the picture frame have contents");
        console.log(picFrame.hasFrameContents);
        console.log("Gets the node handle of the content");
        console.log(picFrame.frameContents);
        console.log("Gets the picture frame anchor of the iface");
        console.log(picFrame.pictureFrameAnchor);
        console.log("Is the pic frame clearing fill on populate");
        console.log(picFrame.clearFillOnPopulate);
        console.log("Gets the original content rectangle");
        console.log(picFrame.originalContentsRect);
        console.log("Gets the data merge field id");
        console.log(picFrame.dataMergeFieldId);
        
        //calculateAnchor and calculateConstraints requires the child node of picture frame.
        console.log("Calculates frame anchor with hint");
        console.log(picFrame.calculateAnchor(createTypedNode(picFrame.frameContents), 0));
        console.log("Calculates constraints");
        console.log(picFrame.calculateConstraints(createTypedNode(picFrame.frameContents), 0));
    }
}

module.exports.testPictureFrameInterface = testPictureFrameInterface;
