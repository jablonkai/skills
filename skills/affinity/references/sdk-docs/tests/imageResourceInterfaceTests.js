'use strict';
const {app} = require('/application.js');
const {ImageResourceInterface} = require('/imageresourceinterface.js');
const {ColourProfileSet} = require('/colour.js');
const {createTypedNode} = require('/node.js');

function testImageResourceInterface() {
    const doc = app.documents.current;
    if (doc) {
        // make sure your doc has a imagenode as its first node
        const imageNode = doc.layers.first;
        const imgResInterface = imageNode.imageResourceInterface;
        
        console.log("Getters of imageResourceInterface:");
        console.log(".imageFilePath:");
        console.log(imgResInterface.imageFilePath);
        
        console.log(".getImageFileSize(asBigInt):");
        console.log(imgResInterface.getImageFileSize(false));
        console.log(imgResInterface.getImageFileSize(true));
        
        console.log(".getModifiedTime(asBigInt):");
        console.log(imgResInterface.getModifiedTime(false));
        console.log(imgResInterface.getModifiedTime(true));
        
        console.log(".fileType:");
        console.log(imgResInterface.fileType);
        
        console.log(".fileTypeName:");
        console.log(imgResInterface.fileTypeName);
        
        console.log(".page:");
        console.log(imgResInterface.page);
        
        console.log(".artboard:");
        console.log(imgResInterface.artboard);
        
        console.log(".isOnArtboard:");
        console.log(imgResInterface.isOnArtboard);
        
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
