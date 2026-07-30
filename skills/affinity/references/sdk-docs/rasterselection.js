'use strict';

const { RasterSelectionApi } = require('affinity:dom');
const { HandleObject } = require("./handleobject.js");

class RasterSelection extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RasterSelection';
    }

    get isCurrentPixelSelection() {
        return RasterSelectionApi.isCurrentPixelSelection(this.handle);
    }

    get isSelectAllOrNone() {
        return RasterSelectionApi.isSelectAllOrNone(this.handle);
    }   

    get isSelectNone() {
        return RasterSelectionApi.isSelectNone(this.handle);
    }
}

module.exports.RasterSelection = RasterSelection;
