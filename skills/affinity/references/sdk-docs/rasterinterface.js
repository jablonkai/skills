'use strict';

const { RasterInterfaceApi } = require('affinity:dom');
const { RasterFormat } = require('affinity:raster');
const { HandleObject } = require('./handleobject.js');
const { Bitmap, PixelBuffer } = require('./rasterobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

// monkey patches:
require('/geometry.js');

class RasterInterface extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'RasterInterface';
    }

    get width() {
        return RasterInterfaceApi.getWidth(this.handle);
    }

    get height() {
        return RasterInterfaceApi.getHeight(this.handle);
    }

    get format() {
        return RasterInterfaceApi.getFormat(this.handle);
    }

    get pixelSize() {
        return RasterInterfaceApi.getPixelSize(this.handle);
    }

    createCompatibleBitmap(copyContents) {
        return new Bitmap(RasterInterfaceApi.createCompatibleBitmap(this.handle, copyContents));
    }

    createCompatibleBuffer(copyContents) {
        return new PixelBuffer(RasterInterfaceApi.createCompatibleBuffer(this.handle, copyContents));
    }

    copyTo(dest, destRect, srcX, srcY) {
        return RasterInterfaceApi.copyTo(this.handle, dest.handle, destRect, srcX, srcY);
    }
    
    get node() {
        return NodesModule.createTypedNode(RasterInterfaceApi.getNode(this.handle));
    }
}

module.exports.RasterFormat = RasterFormat;
module.exports.RasterInterface = RasterInterface;
