'use strict';

const { MarginsInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

class MarginsInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'MarginsInterface';
    }

    get useMargins() {
        return MarginsInterfaceApi.getUseMargins(this.handle);
    }

    get hasMargins() {
        return MarginsInterfaceApi.hasMargins(this.handle);
    }
}

module.exports.MarginsInterface = MarginsInterface;
