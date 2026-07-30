'use strict';

const { BlendMode, UnitType } = require('affinity:common');
const { BitmapFillApi, FillApi, FillDescriptorApi, FillMask, FillType, GradientFillApi, GradientFillType, HatchFillApi, NoFillApi, SolidFillApi } = require('affinity:fills');
const { RasterExtendType, RasterResamplerType } = require('affinity:raster');
const { Colour, ColourProfile, Gradient } = require('./colours.js');
const { HandleObject } = require('./handleobject.js');
const { HatchPattern } = require('./hatch.js');
const { RasterObject } = require('./rasterobject.js');

// monkey patches:
require('/geometry.js');

function createTypedFill(fillHandle) {
    if (fillHandle == null)
        return null;
    const fillType = FillApi.getFillType(fillHandle);
    switch (fillType.value) {
        case FillType.None.value:
            return new NoFill(NoFillApi.fromFill(fillHandle));
        case FillType.Solid.value:
            return new SolidFill(SolidFillApi.fromFill(fillHandle));
        case FillType.Gradient.value:
            return new GradientFill(GradientFillApi.fromFill(fillHandle));
        case FillType.Hatch.value:
            return new HatchFill(HatchFillApi.fromFill(fillHandle));
        case FillType.Bitmap.value:
            return new BitmapFill(BitmapFillApi.fromFill(fillHandle));
        default:
            return new Fill(fillHandle);
    }
}


class Fill extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Fill';
    }

    clone() {
        return new Fill(FillApi.clone(this.handle));
    }

    get alpha() {
        return FillApi.getAlpha(this.handle);
    }

    get fillType() {
        return FillApi.getFillType(this.handle);
    }

    get hasNonFullAlpha() {
        return FillApi.getHasNonFullAlpha(this.handle);
    }

    get hasFlatAlpha() {
        return FillApi.getHasFlatAlpha(this.handle);
    }

    get hasNoise() {
        return FillApi.getHasNoise(this.handle);
    }

    get intensity() {
        return FillApi.getIntensity(this.handle);
    }

    get isVisible() {
        return FillApi.getIsVisible(this.handle);
    }

    get isSpatiallyInvariant() {
        return FillApi.getIsSpatiallyInvariant(this.handle);
    }

    get meanAlpha() {
        return FillApi.getMeanAlpha(this.handle);
    }

    get noise() {
        return FillApi.getNoise(this.handle);
    }

    get tint() {
        return FillApi.getTint(this.handle);
    }

    set alpha(value) {
        FillApi.setAlpha(this.handle, value);
    }

    set intensity(value) {
        FillApi.setIntensity(this.handle, value);
    }

    set noise(value) {
        FillApi.setNoise(this.handle, value);
    }

    set tint(value) {
        FillApi.setTint(this.handle, value);
    }
}

class NoFill extends Fill {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'NoFill';
    }

    static create() {
        return new NoFill(NoFillApi.create());
    }

    static fromFill(fill) {
        return new NoFill(NoFillApi.fromFill(fill.handle));
    }

    clone() {
        return new NoFill(NoFillApi.clone(this.handle));
    }
}

class SolidFill extends Fill {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SolidFill';
    }

    static create(colour) {
        return new SolidFill(SolidFillApi.create(colour.handle));
    }

    static createDefault() {
        return new SolidFill(SolidFillApi.createDefault());
    }

    static fromFill(fill) {
        return new SolidFill(SolidFillApi.fromFill(fill.handle));
    }

    clone() {
        return new SolidFill(SolidFillApi.clone(this.handle));
    }

    get colour() {
        return new Colour(SolidFillApi.getColour(this.handle));
    }

    set colour(value) {
        SolidFillApi.setColour(this.handle, value.handle);
    }
}

class GradientFill extends Fill {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'GradientFill';
    }

    static create(gradient, gradientType) {
        return new GradientFill(GradientFillApi.create(gradient.handle, gradientType));
    }

    static createDefault() {
        return new GradientFill(GradientFillApi.createDefault());
    }

    static fromFill(fill) {
        return new GradientFill(GradientFillApi.fromFill(fill.handle));
    }

    clone() {
        return new GradientFill(GradientFillApi.clone(this.handle));
    }

    cloneWithNewGradient(gradient) {
        return new GradientFill(GradientFillApi.cloneWithNewGradient(this.handle, gradient.handle));
    }

    cloneWithNewGradientFillType(gradientFillType) {
        return new GradientFill(GradientFillApi.cloneWithNewGradientFillType(this.handle, gradientFillType));
    }

    get gradient() {
        return new Gradient(GradientFillApi.getGradient(this.handle));
    }

    get gradientFillType() {
        return GradientFillApi.getGradientFillType(this.handle);
    }
}


class HatchFill extends Fill {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'HatchFill';
    }

    static create(pattern, units, penColour, brushColour = null, lineWeight = 1.0) {
        return new HatchFill(HatchFillApi.create(pattern.handle, units, penColour?.handle, brushColour?.handle, lineWeight));
    }
    
    clone() {
        return new HatchFill(HatchFillApi.clone(this.handle));
    }

    get pattern() {
        return new HatchPattern(HatchFillApi.getPattern(this.handle));
    }
    
    get units() {
        return HatchFillApi.getUnits(this.handle);
    }

    get penColour() {
        const clrHandle = HatchFillApi.getPenColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    get brushColour() {
        const clrHandle = HatchFillApi.getBrushColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    get lineWeight() {
        return HatchFillApi.getLineWeight(this.handle);
    }

    set pattern(value) {
        HatchFillApi.setPattern(this.handle, value.handle);
    }

    set units(value) {
        HatchFillApi.setUnits(this.handle, value);
    }

    set penColour(value) {
        HatchFillApi.setPenColour(this.handle, value?.handle);
    }

    set brushColour(value) {
        HatchFillApi.setBrushColour(this.handle, value?.handle);
    }

    set lineWeight(value) {
        HatchFillApi.setLineWeight(this.handle, value);
    }
}


class BitmapFill extends Fill {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BitmapFill';
    }

    static create(bitmap, extendType, resamplerType, ignoreAlpha) {
        return new BitmapFill(BitmapFillApi.create(bitmap.handle, extendType, resamplerType, ignoreAlpha));
    }

    static fromFill(fill) {
        return new BitmapFill(BitmapFillApi.fromFill(fill.handle));
    }

    clone() {
        return new BitmapFill(BitmapFillApi.clone(this.handle));
    }

    get bitmap() {
        return new RasterObject(BitmapFillApi.getBitmap(this.handle));
    }

    get extendType() {
        return BitmapFillApi.getExtendType(this.handle);
    }

    get isIgnoreAlpha() {
        return BitmapFillApi.getIsIgnoreAlpha(this.handle);
    }

    get isKOnly() {
        return BitmapFillApi.getIsKOnly(this.handle);
    }

    get profile() {
        const profileHandle = BitmapFillApi.getProfile(this.handle);
        return profileHandle ? new ColourProfile(profileHandle) : null;
    }

    get upsamplerType() {
        return BitmapFillApi.getUpsamplerType(this.handle);
    }

    set extendType(value) {
        BitmapFillApi.setExtendType(this.handle, value);
    }

    set isKOnly(value) {
        BitmapFillApi.setIsKOnly(this.handle, value);
    }

    set profile(profile) {
        BitmapFillApi.setProfile(this.handle, profile?.handle);
    }

    set upsamplerType(value) {
        BitmapFillApi.setUpsamplerType(this.handle, value);
    }
}

class FillDescriptor extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FillDescriptor';
    }

    clone() {
        return new FillDescriptor(FillDescriptorApi.clone(this.handle));
    }

    cloneWithNewFill(fill) {
        return new FillDescriptor(FillDescriptorApi.cloneWithNewFill(this.handle, fill.handle));
    }

    cloneWithNewIsScaleWithObject(isScaleWithObject) {
        return new FillDescriptor(FillDescriptorApi.cloneWithNewIsScaleWithObject(this.handle, isScaleWithObject));
    }

    cloneWithNewTransform(transform) {
        return new FillDescriptor(FillDescriptorApi.cloneWithNewTransform(this.handle, transform));
    }

    cloneWithNewTransformInfo(transform, isAnchoredToSpread) {
        return new FillDescriptor(FillDescriptorApi.cloneWithNewTransformInfo(this.handle, transform, isAnchoredToSpread));
    }

    cloneWithNewBlendMode(blendMode) {
        return new FillDescriptor(FillDescriptorApi.cloneWithNewBlendMode(this.handle, blendMode));
    }

    cloneWithNewIsAnchoredToSpread(isAnchoredToSpread) {
        return new FillDescriptor(FillDescriptorApi.cloneWithNewIsAnchoredToSpread(this.handle, isAnchoredToSpread));
    }

    #fill;
    get fill() {
        if (!this.#fill) {
            const fillHandle = FillDescriptorApi.getFill(this.handle);
            this.#fill = createTypedFill(fillHandle);
        }
        return this.#fill;
    }
    
    get fillType() {
        return this.fill.fillType;
    }

    get blendMode() {
        return FillDescriptorApi.getBlendMode(this.handle);
    }

    get transform() {
        return FillDescriptorApi.getTransform(this.handle);
    }

    get isScaleWithObject() {
        return FillDescriptorApi.getIsScaleWithObject(this.handle);
    }

    get isAnchoredToSpread() {
        return FillDescriptorApi.getIsAnchoredToSpread(this.handle);
    }

    getTransformInfo() {
        return FillDescriptorApi.getTransformInfo(this.handle);
    }

    static createNone() {
        return new FillDescriptor(FillDescriptorApi.createNone());
    }

    static createSolid(solidFill, blendMode) {
        if (solidFill instanceof Colour) {
            solidFill = SolidFill.create(solidFill);
        }
        return new FillDescriptor(FillDescriptorApi.createSolid(solidFill.handle, blendMode));
    }

    static create(fill, scaleWithObject, transform, blendMode, anchoredToSpread) {
        return new FillDescriptor(FillDescriptorApi.create(fill.handle, scaleWithObject, transform, blendMode, anchoredToSpread));
    }

    get fillType() {
        return this.fill.fillType;
    }
}

module.exports.BitmapFill = BitmapFill;
module.exports.BlendMode = BlendMode;
module.exports.createTypedFill = createTypedFill;
module.exports.Fill = Fill;
module.exports.FillDescriptor = FillDescriptor;
module.exports.FillMask = FillMask;
module.exports.FillType = FillType;
module.exports.GradientFill = GradientFill;
module.exports.GradientFillType = GradientFillType;
module.exports.HatchFill = HatchFill;
module.exports.NoFill = NoFill;
module.exports.RasterExtendType = RasterExtendType;
module.exports.RasterResamplerType = RasterResamplerType;
module.exports.SolidFill = SolidFill;
module.exports.UnitType = UnitType;
