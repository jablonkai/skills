'use strict';

const { EnumerationResult, UnitType } = require('affinity:common');
const { DrawingScaleApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

class DrawingScale extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DrawingScale';
    }

    toString(useTightFormat, showUnits, indicateApproximations) {
        return DrawingScaleApi.getAsString(this.handle, useTightFormat, showUnits, indicateApproximations);
    }

    get leftValue() {
        return DrawingScaleApi.getLeftValue(this.handle);
    }

    get rightValue() {
        return DrawingScaleApi.getRightValue(this.handle);
    }

    static enumerateDefaults(units, callback) {
        const wrapped = (drawingScaleHandle) => { return callback(new DrawingScale(drawingScaleHandle)) ;}
        return DrawingScaleApi.enumerateDefaults(units, wrapped);
    }

    static getDefaults(units) {
        let res = [];
        function callback (drawingScale) {
            res.push(drawingScale);
            return EnumerationResult.Continue;
        }
        DrawingScale.enumerateDefaults(units, callback);
        return res;
    }

    static createFromIntegers(left, right, simplifyFaction) {
        return new DrawingScale(DrawingScaleApi.createFromIntegers(left, right, simplifyFaction));
    }

    static create(leftUnitValue, rightUnitValue) {
        return new DrawingScale(DrawingScaleApi.create(leftUnitValue, rightUnitValue));
    }

    static createFromString(str, simplifyFraction, simplifyDecimalPlaces, allowOneToOne) {
        return new DrawingScale(DrawingScaleApi.createFromString(str, simplifyFraction, simplifyDecimalPlaces, allowOneToOne));
    }

    static get identity() {
        return this.createFromIntegers(1, 1);
    }
}

module.exports.DrawingScale = DrawingScale;
module.exports.UnitType = UnitType;
