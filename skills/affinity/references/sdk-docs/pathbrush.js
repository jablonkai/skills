'use strict';

const {
    CornerStrategy,
    PathBrushApi,
    PathBrushDynamicControllerType
} = require('affinity:brushes');

const { Spline } = require('/geometry.js');
const { HandleObject } = require('/handleobject.js');

class PathBrush extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PathBrush';
    }

    static createDefault() {
        // Note: This would need to be implemented in the C++ API
        throw new Error('PathBrush.createDefault() not yet implemented in C++ API');
    }

    clone() {
        return new PathBrush(PathBrushApi.clone(this.handle));
    }

    // Simplified size properties (direct access, no BrushDynamic objects)
    get brushWidth() {
        return PathBrushApi.getBrushWidth(this.handle);
    }

    set brushWidth(newBrushWidth) {
        PathBrushApi.setBrushWidth(this.handle, newBrushWidth);
    }

    get sizeVariance() {
        return PathBrushApi.getSizeVariance(this.handle);
    }

    set sizeVariance(newSizeVariance) {
        PathBrushApi.setSizeVariance(this.handle, newSizeVariance);
    }

    get sizeControllerType() {
        return PathBrushApi.getSizeControllerType(this.handle);
    }

    set sizeControllerType(newSizeControllerType) {
        PathBrushApi.setSizeControllerType(this.handle, newSizeControllerType);
    }

    #sizeSpline;
    get sizeSpline() {
        if (!this.#sizeSpline)
            this.#sizeSpline = new Spline(PathBrushApi.getSizeSpline(this.handle));
        return this.#sizeSpline;
    }

    set sizeSpline(newSizeSpline) {
        PathBrushApi.setSizeSpline(this.handle, newSizeSpline.handle);
        this.#sizeSpline = null; // Clear cache
    }

    // Opacity properties
    get opacityVariance() {
        return PathBrushApi.getOpacityVariance(this.handle);
    }

    set opacityVariance(newOpacityVariance) {
        PathBrushApi.setOpacityVariance(this.handle, newOpacityVariance);
    }

    // Path brush-specific properties
    get tailOffset() {
        return PathBrushApi.getTailOffset(this.handle);
    }

    set tailOffset(newTailOffset) {
        PathBrushApi.setTailOffset(this.handle, newTailOffset);
    }

    get headOffset() {
        return PathBrushApi.getHeadOffset(this.handle);
    }

    set headOffset(newHeadOffset) {
        PathBrushApi.setHeadOffset(this.handle, newHeadOffset);
    }

    get isRepeat() {
        return PathBrushApi.isRepeat(this.handle);
    }

    set isRepeat(newIsRepeat) {
        PathBrushApi.setIsRepeat(this.handle, newIsRepeat);
    }

    get cornerStrategy() {
        return PathBrushApi.getCornerStrategy(this.handle);
    }

    set cornerStrategy(newCornerStrategy) {
        PathBrushApi.setCornerStrategy(this.handle, newCornerStrategy);
    }
}

module.exports.PathBrush = PathBrush;
module.exports.PathBrushDynamicControllerType = PathBrushDynamicControllerType;
module.exports.CornerStrategy = CornerStrategy;
