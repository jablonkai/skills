'use strict';

const { PixelReaderRGBA8Api, PixelReaderWriterRGBA8Api } = require('affinity:raster');
const { PixelReaderRGBA16Api, PixelReaderWriterRGBA16Api } = require('affinity:raster');
const { PixelReaderIA8Api, PixelReaderWriterIA8Api } = require('affinity:raster');
const { PixelReaderIA16Api, PixelReaderWriterIA16Api } = require('affinity:raster');
const { PixelReaderCMYKA8Api, PixelReaderWriterCMYKA8Api } = require('affinity:raster');
const { PixelReaderLABA16Api, PixelReaderWriterLABA16Api } = require('affinity:raster');
const { PixelReaderM8Api, PixelReaderWriterM8Api } = require('affinity:raster');
const { PixelReaderM16Api, PixelReaderWriterM16Api } = require('affinity:raster');
const { PixelReaderRGBAufApi, PixelReaderWriterRGBAufApi } = require('affinity:raster');
const { PixelReaderMfApi, PixelReaderWriterMfApi } = require('affinity:raster');
const { HandleObject } = require('./handleobject.js');

class PixelReaderRGBA8 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorRGBA8';
    }

    readPixel(x, y) {
        return PixelReaderRGBA8Api.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderRGBA8Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderRGBA8(PixelReaderRGBA8Api.create(bitmap.handle));
    }
}

class PixelReaderWriterRGBA8 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterRGBA8';
    }

    readPixel(x, y) {
        return PixelReaderWriterRGBA8Api.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterRGBA8Api.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterRGBA8Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterRGBA8(PixelReaderWriterRGBA8Api.create(bitmap.handle));
    }
}

class PixelReaderRGBA16 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorRGBA16';
    }

    readPixel(x, y) {
        return PixelReaderRGBA16Api.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderRGBA16Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderRGBA16(PixelReaderRGBA16Api.create(bitmap.handle));
    }
}

class PixelReaderWriterRGBA16 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterRGBA16';
    }

    readPixel(x, y) {
        return PixelReaderWriterRGBA16Api.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterRGBA16Api.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterRGBA16Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterRGBA16(PixelReaderWriterRGBA16Api.create(bitmap.handle));
    }
}

class PixelReaderIA8 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorIA8';
    }

    readPixel(x, y) {
        return PixelReaderIA8Api.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderIA8Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderIA8(PixelReaderIA8Api.create(bitmap.handle));
    }
}

class PixelReaderWriterIA8 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterIA8';
    }

    readPixel(x, y) {
        return PixelReaderWriterIA8Api.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterIA8Api.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterIA8Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterIA8(PixelReaderWriterIA8Api.create(bitmap.handle));
    }
}

class PixelReaderIA16 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorIA16';
    }

    readPixel(x, y) {
        return PixelReaderIA16Api.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderIA16Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderIA16(PixelReaderIA16Api.create(bitmap.handle));
    }
}

class PixelReaderWriterIA16 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterIA16';
    }

    readPixel(x, y) {
        return PixelReaderWriterIA16Api.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterIA16Api.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterIA16Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterIA16(PixelReaderWriterIA16Api.create(bitmap.handle));
    }
}

class PixelReaderCMYKA8 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorCMYKA8';
    }

    readPixel(x, y) {
        return PixelReaderCMYKA8Api.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderCMYKA8Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderCMYKA8(PixelReaderCMYKA8Api.create(bitmap.handle));
    }
}

class PixelReaderWriterCMYKA8 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterCMYKA8';
    }

    readPixel(x, y) {
        return PixelReaderWriterCMYKA8Api.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterCMYKA8Api.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterCMYKA8Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterCMYKA8(PixelReaderWriterCMYKA8Api.create(bitmap.handle));
    }
}

class PixelReaderLABA16 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorLABA16';
    }

    readPixel(x, y) {
        return PixelReaderLABA16Api.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderLABA16Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderLABA16(PixelReaderLABA16Api.create(bitmap.handle));
    }
}

class PixelReaderWriterLABA16 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterLABA16';
    }

    readPixel(x, y) {
        return PixelReaderWriterLABA16Api.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterLABA16Api.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterLABA16Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterLABA16(PixelReaderWriterLABA16Api.create(bitmap.handle));
    }
}

class PixelReaderM8 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorM8';
    }

    readPixel(x, y) {
        return PixelReaderM8Api.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderM8Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderM8(PixelReaderM8Api.create(bitmap.handle));
    }
}

class PixelReaderWriterM8 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterM8';
    }

    readPixel(x, y) {
        return PixelReaderWriterM8Api.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterM8Api.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterM8Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterM8(PixelReaderWriterM8Api.create(bitmap.handle));
    }
}

class PixelReaderM16 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorM16';
    }

    readPixel(x, y) {
        return PixelReaderM16Api.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderM16Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderM16(PixelReaderM16Api.create(bitmap.handle));
    }
}

class PixelReaderWriterM16 extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterM16';
    }

    readPixel(x, y) {
        return PixelReaderWriterM16Api.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterM16Api.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterM16Api.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterM16(PixelReaderWriterM16Api.create(bitmap.handle));
    }
}

class PixelReaderRGBAuf extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorRGBAuf';
    }

    readPixel(x, y) {
        return PixelReaderRGBAufApi.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderRGBAufApi.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderRGBAuf(PixelReaderRGBAufApi.create(bitmap.handle));
    }
}

class PixelReaderWriterRGBAuf extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterRGBAuf';
    }

    readPixel(x, y) {
        return PixelReaderWriterRGBAufApi.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterRGBAufApi.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterRGBAufApi.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterRGBAuf(PixelReaderWriterRGBAufApi.create(bitmap.handle));
    }
}

class PixelReaderMf extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelAccessorMf';
    }

    readPixel(x, y) {
        return PixelReaderMfApi.readPixel(this.handle, x, y);
    }

    dispose() {
        PixelReaderMfApi.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderMf(PixelReaderMfApi.create(bitmap.handle));
    }
}

class PixelReaderWriterMf extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelReaderWriterMf';
    }

    readPixel(x, y) {
        return PixelReaderWriterMfApi.readPixel(this.handle, x, y);
    }
    
    writePixel(x, y, rgba8) {
        return PixelReaderWriterMfApi.writePixel(this.handle, x, y, rgba8);
    }

    dispose() {
        PixelReaderWriterMfApi.dispose(this.handle);
    }

    static create(bitmap) {
        return new PixelReaderWriterMf(PixelReaderWriterMfApi.create(bitmap.handle));
    }
}


module.exports.PixelReaderRGBA8 = PixelReaderRGBA8;
module.exports.PixelReaderWriterRGBA8 = PixelReaderWriterRGBA8;
module.exports.PixelReaderRGBA16 = PixelReaderRGBA16;
module.exports.PixelReaderWriterRGBA16 = PixelReaderWriterRGBA16;
module.exports.PixelReaderIA8 = PixelReaderIA8;
module.exports.PixelReaderWriterIA8 = PixelReaderWriterIA8;
module.exports.PixelReaderIA16 = PixelReaderIA16;
module.exports.PixelReaderWriterIA16 = PixelReaderWriterIA16;
module.exports.PixelReaderCMYKA8 = PixelReaderCMYKA8;
module.exports.PixelReaderWriterCMYKA8 = PixelReaderWriterCMYKA8;
module.exports.PixelReaderLABA16 = PixelReaderLABA16;
module.exports.PixelReaderWriterLABA16 = PixelReaderWriterLABA16;
module.exports.PixelReaderM8 = PixelReaderM8;
module.exports.PixelReaderWriterM8 = PixelReaderWriterM8;
module.exports.PixelReaderM16 = PixelReaderM16;
module.exports.PixelReaderWriterM16 = PixelReaderWriterM16;
module.exports.PixelReaderRGBAuf = PixelReaderRGBAuf;
module.exports.PixelReaderWriterRGBAuf = PixelReaderWriterRGBAuf;
module.exports.PixelReaderMf = PixelReaderMf;
module.exports.PixelReaderWriterMf = PixelReaderWriterMf;
