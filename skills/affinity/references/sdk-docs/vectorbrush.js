'use strict';

const {
    CornerStrategy,
    VectorBrushApi,
    VectorBrushDynamicControllerType
} = require('affinity:brushes');

const { Spline } = require('./geometry.js');
const { HandleObject } = require('./handleobject.js');

class VectorBrush extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'VectorBrush';
    }

    static createDefault() {
        // Note: This would need to be implemented in the C++ API
        throw new Error('VectorBrush.createDefault() not yet implemented in C++ API');
    }

    clone() {
        return new VectorBrush(VectorBrushApi.clone(this.handle));
    }

    // Simplified size properties (direct access, no BrushDynamic objects)
    get brushWidth() {
        return VectorBrushApi.getBrushWidth(this.handle);
    }

    set brushWidth(newBrushWidth) {
        VectorBrushApi.setBrushWidth(this.handle, newBrushWidth);
    }

    get sizeVariance() {
        return VectorBrushApi.getSizeVariance(this.handle);
    }

    set sizeVariance(newSizeVariance) {
        VectorBrushApi.setSizeVariance(this.handle, newSizeVariance);
    }

    get sizeControllerType() {
        return VectorBrushApi.getSizeControllerType(this.handle);
    }

    set sizeControllerType(newSizeControllerType) {
        VectorBrushApi.setSizeControllerType(this.handle, newSizeControllerType);
    }

    #sizeSpline;
    get sizeSpline() {
        if (!this.#sizeSpline)
            this.#sizeSpline = new Spline(VectorBrushApi.getSizeSpline(this.handle));
        return this.#sizeSpline;
    }

    set sizeSpline(newSizeSpline) {
        VectorBrushApi.setSizeSpline(this.handle, newSizeSpline.handle);
        this.#sizeSpline = null; // Clear cache
    }

    // Opacity properties
    get opacityVariance() {
        return VectorBrushApi.getOpacityVariance(this.handle);
    }

    set opacityVariance(newOpacityVariance) {
        VectorBrushApi.setOpacityVariance(this.handle, newOpacityVariance);
    }

    // VectorBrush-specific properties
    get tailOffset() {
        return VectorBrushApi.getTailOffset(this.handle);
    }

    set tailOffset(newTailOffset) {
        VectorBrushApi.setTailOffset(this.handle, newTailOffset);
    }

    get headOffset() {
        return VectorBrushApi.getHeadOffset(this.handle);
    }

    set headOffset(newHeadOffset) {
        VectorBrushApi.setHeadOffset(this.handle, newHeadOffset);
    }

    get isRepeat() {
        return VectorBrushApi.isRepeat(this.handle);
    }

    set isRepeat(newIsRepeat) {
        VectorBrushApi.setIsRepeat(this.handle, newIsRepeat);
    }

    get cornerStrategy() {
        return VectorBrushApi.getCornerStrategy(this.handle);
    }

    set cornerStrategy(newCornerStrategy) {
        VectorBrushApi.setCornerStrategy(this.handle, newCornerStrategy);
    }
}

module.exports.VectorBrush = VectorBrush;
module.exports.VectorBrushDynamicControllerType = VectorBrushDynamicControllerType;
module.exports.CornerStrategy = CornerStrategy;
