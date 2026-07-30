'use strict';

const {
    BrushDynamicApi,
    BrushDynamicControllerType,
    RasterBrushApi,
    RasterBrushTextureMode
} = require('affinity:brushes');
const { BlendMode } = require('affinity:common');
const { Spline } = require('./geometry.js');
const { HandleObject } = require('./handleobject.js');
const { RasterObject } = require('./rasterobject.js');

class BrushDynamic extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BrushDynamic';
    }

    clone() {
        return new BrushDynamic(BrushDynamicApi.clone(this.handle));
    }

    get value() {
        return BrushDynamicApi.getValue(this.handle);
    }

    set value(newValue) {
        BrushDynamicApi.setValue(this.handle, newValue);
    }

    get variance() {
        return BrushDynamicApi.getVariance(this.handle);
    }

    set variance(newVariance) {
        BrushDynamicApi.setVariance(this.handle, newVariance);
    }

    get controllerType() {
        return BrushDynamicApi.getControllerType(this.handle);
    }

    set controllerType(newControllerType) {
        BrushDynamicApi.setControllerType(this.handle, newControllerType);
    }

    get dynamicMax() {
        return BrushDynamicApi.getDynamicMax(this.handle);
    }

    get dynamicMin() {
        return BrushDynamicApi.getDynamicMin(this.handle);
    }

    #spline;
    get spline() {
        if (!this.#spline)
            this.#spline = new Spline(BrushDynamicApi.getSpline(this.handle));
        return this.#spline;
    }

    set spline(newSpline) {
        BrushDynamicApi.setSpline(this.handle, newSpline.handle);
        this.#spline = null; 
    }
}


class RasterBrush extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RasterBrush';
    }

    static createDefault() {
        // Note: This would need to be implemented in the C++ API
        // For now, this is a placeholder
        throw new Error('RasterBrush.createDefault() not yet implemented in C++ API');
    }

    clone() {
        return new RasterBrush(RasterBrushApi.clone(this.handle));
    }

    #size;
    get size() {
        if (!this.#size)
            this.#size = new BrushDynamic(RasterBrushApi.getSize(this.handle));
        return this.#size;
    }

    set size(newSize) {
        RasterBrushApi.setSize(this.handle, newSize.handle);
        this.#size = null; 
    }

    #accumulation;
    get accumulation() {
        if (!this.#accumulation)
            this.#accumulation = new BrushDynamic(RasterBrushApi.getAccumulation(this.handle));
        return this.#accumulation;
    }

    set accumulation(newAccumulation) {
        RasterBrushApi.setAccumulation(this.handle, newAccumulation.handle);
        this.#accumulation = null; 
    }

    #flow;
    get flow() {
        if (!this.#flow)
            this.#flow = new BrushDynamic(RasterBrushApi.getFlow(this.handle));
        return this.#flow;
    }

    set flow(newFlow) {
        RasterBrushApi.setFlow(this.handle, newFlow.handle);
        this.#flow = null; 
    }

    #angle;
    get angle() {
        if (!this.#angle)
            this.#angle = new BrushDynamic(RasterBrushApi.getAngle(this.handle));
        return this.#angle;
    }

    set angle(newAngle) {
        RasterBrushApi.setAngle(this.handle, newAngle.handle);
        this.#angle = null; 
    }

    #scatterX;
    get scatterX() {
        if (!this.#scatterX)
            this.#scatterX = new BrushDynamic(RasterBrushApi.getScatterX(this.handle));
        return this.#scatterX;
    }

    set scatterX(newScatterX) {
        RasterBrushApi.setScatterX(this.handle, newScatterX.handle);
        this.#scatterX = null; 
    }

    #scatterY;
    get scatterY() {
        if (!this.#scatterY)
            this.#scatterY = new BrushDynamic(RasterBrushApi.getScatterY(this.handle));
        return this.#scatterY;
    }

    set scatterY(newScatterY) {
        RasterBrushApi.setScatterY(this.handle, newScatterY.handle);
        this.#scatterY = null; 
    }

    #hardness;
    get hardness() {
        if (!this.#hardness)
            this.#hardness = new BrushDynamic(RasterBrushApi.getHardness(this.handle));
        return this.#hardness;
    }

    set hardness(newHardness) {
        RasterBrushApi.setHardness(this.handle, newHardness.handle);
        this.#hardness = null; 
    }

    #shape;
    get shape() {
        if (!this.#shape)
            this.#shape = new BrushDynamic(RasterBrushApi.getShape(this.handle));
        return this.#shape;
    }

    set shape(newShape) {
        RasterBrushApi.setShape(this.handle, newShape.handle);
        this.#shape = null; 
    }

    #hueShift;
    get hueShift() {
        if (!this.#hueShift)
            this.#hueShift = new BrushDynamic(RasterBrushApi.getHueShift(this.handle));
        return this.#hueShift;
    }

    set hueShift(newHueShift) {
        RasterBrushApi.setHueShift(this.handle, newHueShift.handle);
        this.#hueShift = null; 
    }

    #satShift;
    get satShift() {
        if (!this.#satShift)
            this.#satShift = new BrushDynamic(RasterBrushApi.getSatShift(this.handle));
        return this.#satShift;
    }

    set satShift(newSatShift) {
        RasterBrushApi.setSatShift(this.handle, newSatShift.handle);
        this.#satShift = null; 
    }

    #lumShift;
    get lumShift() {
        if (!this.#lumShift)
            this.#lumShift = new BrushDynamic(RasterBrushApi.getLumShift(this.handle));
        return this.#lumShift;
    }

    set lumShift(newLumShift) {
        RasterBrushApi.setLumShift(this.handle, newLumShift.handle);
        this.#lumShift = null; 
    }

    get spacing() {
        return RasterBrushApi.getSpacing(this.handle);
    }

    set spacing(newSpacing) {
        RasterBrushApi.setSpacing(this.handle, newSpacing);
    }

    get opacity() {
        return RasterBrushApi.getOpacity(this.handle);
    }

    set opacity(newOpacity) {
        RasterBrushApi.setOpacity(this.handle, newOpacity);
    }

    get blendMode() {
        return RasterBrushApi.getBlendMode(this.handle);
    }

    set blendMode(newBlendMode) {
        RasterBrushApi.setBlendMode(this.handle, newBlendMode);
    }

    get wetEdges() {
        return RasterBrushApi.getWetEdges(this.handle);
    }

    set wetEdges(newWetEdges) {
        RasterBrushApi.setWetEdges(this.handle, newWetEdges);
    }

    get shouldApplyWetEdges() {
        return RasterBrushApi.getShouldApplyWetEdges(this.handle);
    }

    set shouldApplyWetEdges(newShouldApplyWetEdges) {
        RasterBrushApi.setShouldApplyWetEdges(this.handle, newShouldApplyWetEdges);
    }

    get shouldInterpolateTips() {
        return RasterBrushApi.getShouldInterpolateTips(this.handle);
    }

    set shouldInterpolateTips(newShouldInterpolateTips) {
        RasterBrushApi.setShouldInterpolateTips(this.handle, newShouldInterpolateTips);
    }

    get maskTextureMode() {
        return RasterBrushApi.getMaskTextureMode(this.handle);
    }

    set maskTextureMode(newMaskTextureMode) {
        RasterBrushApi.setMaskTextureMode(this.handle, newMaskTextureMode);
    }

    get maskTextureScale() {
        return RasterBrushApi.getMaskTextureScale(this.handle);
    }

    set maskTextureScale(newMaskTextureScale) {
        RasterBrushApi.setMaskTextureScale(this.handle, newMaskTextureScale);
    }
}

module.exports.BlendMode = BlendMode;
module.exports.BrushDynamic = BrushDynamic;
module.exports.BrushDynamicControllerType = BrushDynamicControllerType;
module.exports.RasterBrush = RasterBrush;
module.exports.RasterBrushTextureMode = RasterBrushTextureMode;
