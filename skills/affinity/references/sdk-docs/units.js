'use strict';

const { UnitType, UnitValue, UnitValueConverterApi, UserUnitType } = require('affinity:common');
const { HandleObject } = require('./handleobject.js');

class UnitValueConverter extends HandleObject {
    constructor(handle) {
        super(handle)
    }

    get [Symbol.toStringTag]() {
        return 'UnitValueConverter';
    }

    static create(dpi, viewDpi = -1) {
        return new UnitValueConverter(UnitValueConverterApi.createWithViewDpi(dpi, viewDpi));
    }

    clone() {
        return new UnitValueConverter(UnitValueConverterApi.clone(this.handle));
    }

    get dpi() {
        return UnitValueConverterApi.getDpi(this.handle);
    }

    get viewDpi() {
        return UnitValueConverterApi.getViewDpi(this.handle);
    }

    getConversionFactor(from, to) {
        return UnitValueConverterApi.getConversionFactor(this.handle, from, to);
    }
}

module.exports.UnitType = UnitType;
module.exports.UnitValue = UnitValue;
module.exports.UnitValueConverter = UnitValueConverter;
module.exports.UserUnitType = UserUnitType;
