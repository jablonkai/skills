'use strict';
const {app} = require('/application');
const {ImageResourceInterface} = require('/imageResourceInterface');
const {ColourProfileSet} = require('/colour');
const {createTypedNode} = require('/node');

function testImageResourceInterface() {
    const doc = app.documents.current;
    if (doc) {
        // make sure your doc has a imagenode as its first node
        const imageNode = doc.layers.first;
        const imgResInterface = imageNode.imageResourceInterface;
        
        console.log("Getters of imageResourceInterface:");
        console.log(".imageFilePath:");
        console.log(imgResInterface.imageFilePath);
        
        console.log(".imageFileSize:");
        console.log(imgResInterface.imageFileSize);
        
        console.log(".modifiedTime:");
        console.log(imgResInterface.modifiedTime);
        
        console.log(".fileType:");
        console.log(imgResInterface.modifiedTime);
        
        console.log(".fileTypeName:");
        console.log(imgResInterface.modifiedTime);
        
        console.log(".page:");
        console.log(imgResInterface.modifiedTime);
        
        console.log(".artboard:");
        console.log(imgResInterface.modifiedTime);
        
        console.log(".isOnArtboard:");
        console.log(imgResInterface.modifiedTime);
        
        console.log(".originalDPI:");
        console.log(imgResInterface.originalDPI);
        
        console.log(".iccProfile:");
        console.log(imgResInterface.iccProfile);
        
        console.log(".placedSize:");
        console.log(imgResInterface.placedSize);
        
        console.log(".originalSize:");
        console.log(imgResInterface.originalSize);
        
        console.log(".imagePlacement:");
        console.log(imgResInterface.imagePlacement);
        
        console.log(".masterPage:");
        console.log(imgResInterface.masterPage);
        
        console.log(".resourceNode:");
        console.log(imgResInterface.resourceNode);
        
        console.log(".canEditOriginalImage:");
        console.log(imgResInterface.canEditOriginalImage);
        
        console.log("Functions of image resource interface:");
        console.log(".getColourFormat(allowRemote):");
        console.log(imgResInterface.getColourFormat(false));
        
        const colourProfileSet = ColourProfileSet.default;
        console.log(".getSmallThumbnail(format, colourProfileSet):");
        console.log(imgResInterface.getSmallThumbnail(0, colourProfileSet));
        
        console.log(".getLargeThumbnail(format, colourProfileSet):");
        console.log(imgResInterface.getLargeThumbnail(0, colourProfileSet));
        
        console.log(".createFileTypeName():");
        console.log(imgResInterface.createFileTypeName());
        
        console.log(".saveOriginalFile(filename):");
        console.log(imgResInterface.saveOriginalFile("definitelyanewname.png"));
    }
}

module.exports.testImageResourceInterface = testImageResourceInterface;
