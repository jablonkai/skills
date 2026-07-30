'use strict';

const {
    ArrowHeadApi,
    ArrowHeadStyle,
    LineCap,
    LineJoin,
    LineStyleApi,
    LineStyleDescriptorApi,
    LineStyleMask,
    LineType,
    StrokeAlignment
} = require('affinity:linestyles');
const { Curve } = require('./geometry.js');
const { HandleObject } = require('./handleobject.js');
const { VectorBrush } = require('./vectorbrush.js');

class ArrowHead extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ArrowHead';
    }

    static create(style, opts) {
        return new ArrowHead(ArrowHeadApi.create(
            style,
            opts?.internalAnchor,
            opts?.externalAnchor,
            opts?.solidLine,
            opts?.scaleX ?? 1.0,
            opts?.scaleY ?? 1.0
        ));
    }

    static createDefault() {
        return new ArrowHead(ArrowHeadApi.createDefault());
    }

    clone() {
        return new ArrowHead(ArrowHeadApi.clone(this.handle));
    }

    getAnchor(internal) {
        return ArrowHeadApi.getAnchor(this.handle, internal);
    }

    setAnchor(internal, value) {
        return ArrowHeadApi.setAnchor(this.handle, internal, value);
    }

    get isFilled() {
        return ArrowHeadApi.isFilled(this.handle);
    }

    get isOutlined() {
        return ArrowHeadApi.isOutlined(this.handle);
    }

    get isSolidLine() {
        return ArrowHeadApi.isSolidLine(this.handle);
    }

    set isSolidLine(value) {
        ArrowHeadApi.setSolidLine(this.handle, value);
    }

    get scaleX() {
        return ArrowHeadApi.getScaleX(this.handle);
    }

    set scaleX(value) {
        ArrowHeadApi.setScaleX(this.handle, value);
    }

    get scaleY() {
        return ArrowHeadApi.getScaleY(this.handle);
    }

    set scaleY(value) {
        ArrowHeadApi.setScaleY(this.handle, value);
    }
}


class LineStyle extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LineStyle';
    }

    static create(opts) {
        return new LineStyle(LineStyleApi.create(
            opts?.cap ?? LineCap.Round,
            opts?.join ?? LineJoin.Round,
            opts?.type ?? LineType.Solid,
            opts?.weight ?? 1.0,
            opts?.miterLimit ?? 1.0,
            opts?.dashPhase ?? 0.0,
            opts?.dashPattern ?? [1.0, 1.0],
            opts?.resIndependent,
            opts?.balancedDashes ?? true,
            opts?.vectorBrush ?? VectorBrush.createDefault() /// TODO: to be decided, there is no default atm.
        ));
    }

    static createDefault() {
        return new LineStyle(LineStyleApi.createDefault());
    }

    static createDefaultWithWeight(weight) {
        return new LineStyle(LineStyleApi.createDefaultWithWeight(weight));
    }

    clone() {
        return new LineStyle(LineStyleApi.clone(this.handle));
    }

    get cap() {
        return LineStyleApi.getCap(this.handle);
    }

    set cap(newCap) {
        LineStyleApi.setCap(this.handle, newCap);
    }

    get join() {
        return LineStyleApi.getJoin(this.handle);
    }

    set join(newJoin) {
        LineStyleApi.setJoin(this.handle, newJoin);
    }

    get type() {
        return LineStyleApi.getType(this.handle);
    }

    set type(newType) {
        LineStyleApi.setType(this.handle, newType);
    }

    get weight() {
        return LineStyleApi.getWeight(this.handle);
    }

    set weight(newWeight) {
        LineStyleApi.setWeight(this.handle, newWeight);
    }

    get miterLimit() {
        return LineStyleApi.getMiterLimit(this.handle);
    }

    set miterLimit(newMiterLimit) {
        LineStyleApi.setMiterLimit(this.handle, newMiterLimit);
    }

    get dashPhase() {
        return LineStyleApi.getDashPhase(this.handle);
    }

    set dashPhase(newPhase) {
        LineStyleApi.setDashPhase(this.handle, newPhase);
    }

    get dashPattern() {
        return LineStyleApi.getDashPattern(this.handle);
    }

    set dashPattern(newPattern) {
        LineStyleApi.setDashPattern(this.handle, newPattern);
    }

    get isResolutionIndependent() {
        return LineStyleApi.isResolutionIndependent(this.handle);
    }

    set isResolutionIndependent(resIndependent) {
        LineStyleApi.setIsResolutionIndependent(this.handle, resIndependent);
    }

    get hasBalancedDashes() {
        return LineStyleApi.hasBalancedDashes(this.handle);
    }

    set hasBalancedDashes(balanced) {
        LineStyleApi.setHasBalancedDashes(this.handle, balanced);
    }
    
    get vectorBrush() {
        const vbHandle = LineStyleApi.getVectorBrush(this.handle);
        return vbHandle ? new VectorBrush(vbHandle) : null;
    }
    
    set vectorBrush(brush) {
        return LineStyleApi.setVectorBrush(this.handle, brush.handle);
    }
}


class LineStyleDescriptor extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LineStyleDescriptor';
    }

    static create(lineStyle, options) {
        const handle = LineStyleDescriptorApi.create(
            lineStyle.handle,
            options?.frontArrow,
            options?.backArrow,
            options?.pressure,
            options?.isBehind,
            options?.isScale,
            options?.strokeAlignment ?? StrokeAlignment.Centre
        );
        return new LineStyleDescriptor(handle);
    }

    static createDefault(weight) {
        const handle = weight != null
            ? LineStyleDescriptorApi.createDefaultWithWeight(weight)
            : LineStyleDescriptorApi.createDefault();
        return new LineStyleDescriptor(handle);
    }

    #lineStyle;
    get lineStyle() {
        if (!this.#lineStyle)
            this.#lineStyle = new LineStyle(LineStyleDescriptorApi.getLineStyle(this.handle));
        return this.#lineStyle;
    }

    get frontArrowHead() {
        const arrowHeadHandle = LineStyleDescriptorApi.getFrontArrowHead(this.handle);
        return arrowHeadHandle ? new ArrowHead(arrowHeadHandle) : null;
    }

    get backArrowHead() {
        const arrowHeadHandle = LineStyleDescriptorApi.getBackArrowHead(this.handle);
        return arrowHeadHandle ? new ArrowHead(arrowHeadHandle) : null;
    }

    get pressure() {
        const curveHandle = LineStyleDescriptorApi.getPressure(this.handle);
        return curveHandle ? new Curve(curveHandle) : null;
    }

    get isBehind() {
        return LineStyleDescriptorApi.isBehind(this.handle);
    }

    get isScale() {
        return LineStyleDescriptorApi.isScale(this.handle);
    }

    get strokeAlignment() {
        return LineStyleDescriptorApi.getStrokeAlignment(this.handle);
    }

    effectiveWeight(localTransform = null, worldTransform = null) {
        return LineStyleDescriptorApi.getEffectiveWeight(this.handle, localTransform, worldTransform);
    }

    clone() {
        return new LineStyleDescriptor(LineStyleDescriptorApi.clone(this.handle));
    }

    cloneWithNewArrowHeads(frontArrow = null, backArrow = null) {
        return new LineStyleDescriptor(LineStyleDescriptorApi.cloneWithNewArrowHeads(this.handle, frontArrow?.handle, backArrow?.handle));
    }

    cloneWithNewLineStyle(lineStyle) {
        return new LineStyleDescriptor(LineStyleDescriptorApi.cloneWithNewLineStyle(this.handle, lineStyle.handle));
    }

    cloneScaled(scale) {
        return new LineStyleDescriptor(LineStyleDescriptorApi.cloneScaled(this.handle, scale));
    }
}

module.exports.ArrowHead = ArrowHead;
module.exports.ArrowHeadStyle = ArrowHeadStyle;
module.exports.LineCap = LineCap;
module.exports.LineJoin = LineJoin;
module.exports.LineStyle = LineStyle;
module.exports.LineStyleDescriptor = LineStyleDescriptor;
module.exports.LineStyleMask = LineStyleMask;
module.exports.LineType = LineType;
module.exports.StrokeAlignment = StrokeAlignment;
