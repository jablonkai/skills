'use strict';

const { UnitCategory, UnitType, UnitValue, UnitValueApi, UnitValueConverterApi, UserUnitType } = require('affinity:common');
const { HandleObject } = require('/handleobject.js');

// Add object-oriented helpers to the UnitValue prototype that delegate to UnitValueApi
Object.assign(UnitValue.prototype, {
    assign: function(source) { UnitValueApi.assign(this, source); return this; },
    makeZero: function() { UnitValueApi.makeZero(this); return this; },
    makeInfinity: function() { UnitValueApi.makeInfinity(this); return this; },
    getValueAsDegrees: function() { return UnitValueApi.getValueAsDegrees(this); },
    getValueAsRadians: function() { return UnitValueApi.getValueAsRadians(this); },
    getValueAsNumber: function() { return UnitValueApi.getValueAsNumber(this); },
    getValueAsPixels: function(converter) { return UnitValueApi.getValueAsPixels(this, converter); },
    getValueAsUnitType: function(converter, unitType) { return UnitValueApi.getValueAsUnitType(this, converter, unitType); },
    getValueAsUnitTypePower: function(converter, unitTypePower) { return UnitValueApi.getValueAsUnitTypePower(this, converter, unitTypePower); },
});

Object.defineProperties(UnitValue.prototype, {
    isFinite: { get() { return UnitValueApi.isFinite(this); } },
});

// Static helpers on UnitValue that delegate to UnitValueApi
UnitValue.getTypeCategory = function(unitType) { return UnitValueApi.getTypeCategory(unitType); };

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

module.exports.UnitCategory = UnitCategory;
module.exports.UnitType = UnitType;
module.exports.UnitValue = UnitValue;
module.exports.UnitValueConverter = UnitValueConverter;
module.exports.UserUnitType = UserUnitType;
