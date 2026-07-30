'use strict';

const { FileType, ImagePlacement, ImageResourceInterfaceApi } = require('affinity:dom');
const { RasterFormat } = require('affinity:raster');
const { HandleObject} = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class ImageResourceInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ImageResourceInterface';
    }
    
    get imageFilePath() {
        return ImageResourceInterfaceApi.getImageFilePath(this.handle);
    }
    
    get imageFileSize() {
        return ImageResourceInterfaceApi.getImageFileSize(this.handle);
    }
    
    get modifiedTime() {
        return ImageResourceInterfaceApi.getModifiedTime(this.handle);
    }
    
    get fileType() {
        return ImageResourceInterfaceApi.getFileType(this.handle);
    }
    
    get fileTypeName() {
        return ImageResourceInterfaceApi.getFileTypeName(this.handle);
    }
    
    get page() {
        return ImageResourceInterfaceApi.getPage(this.handle);
    }
    
    get artboard() {
        return ImageResourceInterfaceApi.getArtboard(this.handle);
    }
    
    get isOnArtboard() {
        return ImageResourceInterfaceApi.isOnArtboard(this.handle);
    }
    
    get originalDPI() {
        return ImageResourceInterfaceApi.getOriginalDPI(this.handle);
    }
    
    get iccProfile() {
        return ImageResourceInterfaceApi.getICCProfile(this.handle);
    }
    
    get placedSize() {
        return ImageResourceInterfaceApi.getPlacedSize(this.handle);
    }
    
    get originalSize() {
        return ImageResourceInterfaceApi.getOriginalSize(this.handle);
    }
    
    getColourFormat(allowRemote) {
        return ImageResourceInterfaceApi.getColourFormat(this.handle, allowRemote);
    }
    
    get imagePlacement() {
        return ImageResourceInterfaceApi.getImagePlacement(this.handle);
    }
    
    get masterPage() {
        return ImageResourceInterfaceApi.getMasterPage(this.handle);
    }
    
    getSmallThumbnail(format, colourProfileSet) {
        return ImageResourceInterfaceApi.getSmallThumbnail(this.handle, format, colourProfileSet.handle);
    }
    
    getLargeThumbnail(format, colourProfileSet) {
        return ImageResourceInterfaceApi.getLargeThumbnail(this.handle, format, colourProfileSet.handle);
    }
    
    get resourceNode() {
        return NodesModule.createTypedNode(ImageResourceInterfaceApi.getResourceNode(this.handle));
    }
    
    get canEditOriginalImage() {
        return ImageResourceInterfaceApi.canEditOriginalImage(this.handle);
    }
    
    
    createFileTypeName() {
        return ImageResourceInterfaceApi.createFileTypeName(this.handle);
    }
    
    saveOriginalFile(filename) {
        return ImageResourceInterfaceApi.saveOriginalFile(this.handle, filename);
    }

    get node() {
        return NodesModule.createTypedNode(ImageResourceInterfaceApi.getNode(this.handle));
    }
}

module.exports.FileType = FileType;
module.exports.ImagePlacement = ImagePlacement;
module.exports.ImageResourceInterface = ImageResourceInterface;
module.exports.RasterFormat = RasterFormat;
