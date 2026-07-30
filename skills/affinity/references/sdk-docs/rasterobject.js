'use strict';

const { RasterExtendType, RasterFormat, RasterIntent, RasterObjectApi, RasterObjectType, RasterResamplerType } = require('affinity:raster');
const { HandleObject } = require('./handleobject.js');

function createTypedRasterObject(handle) {
    if (handle == null)
        return null;
    const rasterObjectType = RasterObjectApi.getType(handle);
    switch (rasterObjectType.value) {
        case RasterObjectType.Bitmap.value:
            return new Bitmap(handle);
        case RasterObjectType.Buffer.value:
            return new PixelBuffer(handle);
        case RasterObjectType.RenderingEngine.value:
            return new NodeRenderingEngine(handle);
        default:
            return new RasterObject(handle);
    }
}

class RasterObject extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'RasterObject';
    }

    get width() {
        return RasterObjectApi.getWidth(this.handle);
    }

    get height() {
        return RasterObjectApi.getHeight(this.handle);
    }

    get format() {
        return RasterObjectApi.getFormat(this.handle);
    }

    get pixelSize() {
        return RasterObjectApi.getPixelSize(this.handle);
    }
    
    get type() {
        return RasterObjectApi.getType(this.handle);
    }

    createCompatibleBitmap(copyContents) {
        return new Bitmap(RasterObjectApi.createCompatibleBitmap(this.handle, copyContents));
    }

    createCompatibleBuffer(copyContents) {
        return new PixelBuffer(RasterObjectApi.createCompatibleBuffer(this.handle, copyContents));
    }

    copyTo(dest, destRect, srcX, srcY) {
        return RasterObjectApi.copyTo(this.handle, dest.handle, destRect, srcX, srcY);
    }
	
	clone() {
		return new RasterObject(RasterObjectApi.clone(this.handle));
	}
	
	cloneEmpty() {
		return new RasterObject(RasterObjectApi.cloneEmpty(this.handle));
	}
}

class Bitmap extends RasterObject {
    
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Bitmap';
    }

    static create(width, height, format) {
        return new Bitmap(RasterObjectApi.createBitmap(width, height, format));
    }

    static loadFromFile(path, format = RasterFormat.RGBA8) {
        return new Bitmap(RasterObjectApi.loadBitmapFromFile(path, format));
    }

    static loadFromFileAsync(path, format, callback) {
        if (typeof callback === 'function') {
            function wrappedCallback(errorCode, rasterObjectHandle) {
                let rasterObject = rasterObjectHandle ? new Bitmap(rasterObjectHandle) : null;
                return callback(errorCode, rasterObject);
            }
            return RasterObjectApi.loadBitmapFromFileAsync(path, format, wrappedCallback);
        }
        return RasterObjectApi.loadBitmapFromFileAsync(path, format, callback);
    }
}

class PixelBuffer extends RasterObject {
    
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelBuffer';
    }

    static create(width, height, format) {
        return new PixelBuffer(RasterObjectApi.createPixelBuffer(width, height, format));
    }

    get buffer() {
        return RasterObjectApi.getArrayBuffer(this.handle);
    }
}

class NodeRenderingEngine extends RasterObject {

	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'NodeRenderingEngine';
	}

	static createDefault(node, format) {
		return new NodeRenderingEngine(RasterObjectApi.createDefaultNodeRenderingEngine(node.handle, format));
	}

	static create(node, format, options) {
		return new NodeRenderingEngine(RasterObjectApi.createNodeRenderingEngine(node.handle, format, options));
	}
}

module.exports.createTypedRasterObject = createTypedRasterObject;
module.exports.RasterObject = RasterObject;
module.exports.Bitmap = Bitmap;
module.exports.PixelBuffer = PixelBuffer;
module.exports.NodeRenderingEngine = NodeRenderingEngine;
module.exports.RasterExtendType = RasterExtendType;
module.exports.RasterFormat = RasterFormat;
module.exports.RasterIntent = RasterIntent;
module.exports.RasterObjectType = RasterObjectType;
module.exports.RasterResamplerType = RasterResamplerType;
