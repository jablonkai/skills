'use strict';

const { FillDescriptor } = require('/fills.js');
const { HandleObject } = require('/handleobject.js');
const { MarginsInterfaceApi } = require('affinity:dom');

class MarginsInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'MarginsInterface';
    }

    get margins() {
        return MarginsInterfaceApi.getMargins(this.handle);
    }

    get marginFill() {
        return new FillDescriptor(MarginsInterfaceApi.getMarginFill(this.handle));
    }

    get useMargins() {
        return MarginsInterfaceApi.getUseMargins(this.handle);
    }

    get hasMargins() {
        const margins = this.margins;
        return this.useMargins
            && !(margins.left === 0
                && margins.top === 0
                && margins.right === 0
                && margins.bottom === 0);
    }
}

module.exports.MarginsInterface = MarginsInterface;
