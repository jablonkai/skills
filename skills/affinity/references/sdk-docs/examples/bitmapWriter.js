// Demonstrates writing bitmap using 2 methods.
// Passing true-ish to main() will use a PixelReaderWriterRGBA8 to write the pixels directly into the bitmap.
// Otherwise the data will be written into a PixelBuffer which is then copied to the bitmap.

'use strict';

const { app } = require('/application');
const { Dialog, DialogResult } = require('/dialog');
const { Document } = require('/document');
const { ImageNodeDefinition } = require('/nodes');
const { Bitmap, PixelBuffer, RasterFormat } = require('/rasterobject');
const { PixelReaderWriterRGBA8 } = require('/pixelaccessor');
const { UnitType } = require('/units');

function main(usePixelWriter) {
    const doc = Document.current;
    if (!doc) {
        app.alert("This example requires an open document");
        return;
    }

    const WIDTH = Math.ceil(doc.widthPixels);
    const HEIGHT = Math.ceil(doc.heightPixels);

    // Creates a Bitmap and updates its pixels using a PixelReaderWriter.
    // Useful for when a few, sparse pixels need updating.
    function createBitmapUsingPixelWriter(blue) {
        const bitmap = Bitmap.create(WIDTH, HEIGHT, RasterFormat.RGBA8);
        const w = PixelReaderWriterRGBA8.create(bitmap);
        try {
            const pixelData = { b:blue, alpha:255 };
            for(let y = 0; y < HEIGHT; ++y) {
                for(let x = 0; x < WIDTH; ++x) {
                    pixelData.r = 255*y/HEIGHT;
                    pixelData.g = 255*x/WIDTH;
                    w.writePixel(x, y, pixelData);
                }
            }
        }
        finally {
            w.dispose();
        }
        return bitmap;
    }

    // Creates a PixelBuffer, writes the pixel data to it and then copies
    // the data to a bitmap, which is then returned.
    // In general particularly for large blocks of contiguous pixels,
    // this is much faster than using a PixelReaderWriter to write the pixel data.
    function createBitmapUsingPixelBuffer(blue) {
        const buffer = PixelBuffer.create(WIDTH, HEIGHT, RasterFormat.RGBA8);
        const arr = new Uint8Array(buffer.buffer)
        let i = 0;
        for(let y = 0; y < HEIGHT; ++y) {
            for(let x = 0; x < WIDTH; ++x) {
                arr[i++] = 255*y/HEIGHT;
                arr[i++] = 255*x/WIDTH;
                arr[i++] = blue;
                arr[i++] = 255;
            }
        }
        return buffer.createCompatibleBitmap(true);
    }

    function buildDialog() {
        const dlg = Dialog.create("Bitmap Rainbow Fun");
        const col = dlg.addColumn();
        const group = col.addGroup();
        dlg.blue = group.addUnitValueEditor("Blue", UnitType.Number, UnitType.Number, 128, 0, 255)
            .setShowPopupSlider(true)
            .setPrecision(0);
        return dlg;
    }

    const dlg = buildDialog();
    const nodeDef = ImageNodeDefinition.create(RasterFormat.RGB8);
    nodeDef.userDescription = "JavaScript made this";

    function update(preview) {
        const blue = dlg.blue.value;
        nodeDef.bitmap = usePixelWriter ? createBitmapUsingPixelWriter(blue) : createBitmapUsingPixelBuffer(blue);
        doc.addNode(nodeDef, null, undefined, preview);
    }
    
    update(true);
    dlg.onControlValueChangedHandler = () => update(true);
    if (dlg.runModal() == DialogResult.Ok) {
        update(false);
    }
    else
        doc.clearPreviews();
}

module.exports.main = main;
