'use strict';
const {app} = require('/application');
const {Document, DocumentPromises, DocumentPreset} = require("/document");
const {PixelBuffer, RasterFormat} = require("/rasterObject");

class TestUtils {
    static getRandomRGBA8Bitmap(width, height) {
        let pixels = PixelBuffer.create(width, height, RasterFormat.RGBA8);
        let view = new Uint8Array(pixels.buffer);
        for (let i = 0; i < view.length; i++) {
            view[i] = Math.floor(Math.random() * 256);
        }
        return pixels.createCompatibleBitmap(true);
    }
    
    static getFile(filename) {
        let path = __dirname.concat(filename);
        console.log(path);
        return Document.load(path);
    }

    static floatEqual(a, b, epsilon = 1e-6) {
        return (Math.abs(a - b) < epsilon);
    }

    static strEqual(stra, strb) {
        return (stra.includes(strb) && strb.includes(stra));
    }
    
    static newA4Empty() {
        let a4p = DocumentPreset.all.filter(preset => preset.name.includes("A4"))[0];
        return Document.createFromPreset(a4p, false);
    }

}


module.exports.TestUtils = TestUtils;
