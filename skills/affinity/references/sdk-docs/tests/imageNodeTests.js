'use strict';
const {app} = require('/application');
const {createTypedNode} = require('/node');

function testImageNode() {
    const doc = app.documents.current;
    if (doc) {
        // make sure your doc has a imagenode as its first node
        const imageNode = doc.layers.first;
        
        console.log("The extend type of the image node is:");
        console.log(imageNode.extendType);
        
        console.log("The upsampler type of the image node is:");
        console.log(imageNode.upsamplerType);
        
        console.log("The stock URL of the image node is:");
        console.log(imageNode.stockURL);
        
        console.log("The stock user profile URL of the image node is:");
        console.log(imageNode.stockUserProfileURL);
        
        console.log("The stock author of the image node is:");
        console.log(imageNode.stockAuthor);
        
        console.log("The last rendered timestamp of the image node is:");
        console.log(imageNode.lastRendered);
        
        console.log("The bitmap brush fill descriptor of the image node is:");
        console.log(imageNode.bitmapBrushFillDescriptor);
        
        console.log("Is the image node k only:");
        console.log(imageNode.isKOnly);
        
        console.log("The image resource interface of the image node is:")
        console.log(imageNode.imageResourceInterface)
        
        console.log("The raster interface of the image node is:")
        console.log(imageNode.rasterInterface)
    }
}

module.exports.testImageNode = testImageNode;
