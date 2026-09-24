'use strict';

const { BlendMode, UnitType } = require('affinity:common');
const { BitmapFillApi, ColourMeshApi, DiffusionCurveKind, DiffusionCurveParametric, DiffusionCurveSetApi, DiffusionCurveSide, DiffusionFillApi, FillApi, FillDescriptorApi, FillMask, FillType, GradientFillApi, GradientFillType, HatchFillApi, MeshFillApi, NoFillApi, SolidFillApi, TransformInfo } = require('affinity:fills');
const { RasterExtendType, RasterResamplerType } = require('affinity:raster');
const { Colour, ColourProfile, Gradient } = require('/colours.js');
const { Curve, Mesh, Transform } = require('/geometry.js');
const { HandleObject } = require('/handleobject.js');
const { HatchPattern } = require('/hatch.js');
const { RasterObject } = require('/rasterobject.js');

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
        case FillType.Mesh.value:
            return new MeshFill(MeshFillApi.fromFill(fillHandle));
        case FillType.Diffusion.value:
            return new DiffusionFill(DiffusionFillApi.fromFill(fillHandle));
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


class DiffusionCurveSet extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DiffusionCurveSet';
    }

    static create() {
        return new DiffusionCurveSet(DiffusionCurveSetApi.create());
    }

    static createDefault(colourA, colourB) {
        return new DiffusionCurveSet(DiffusionCurveSetApi.createDefault(colourA.handle, colourB.handle));
    }

    clone() {
        return new DiffusionCurveSet(DiffusionCurveSetApi.clone(this.handle));
    }

    get curveCount() {
        return DiffusionCurveSetApi.getCurveCount(this.handle);
    }

    addCurve(points, leftColour, rightColour) {
        DiffusionCurveSetApi.addCurve(this.handle, points, leftColour?.handle, rightColour?.handle);
    }

    removeCurve(index) {
        DiffusionCurveSetApi.removeCurve(this.handle, index);
    }

    getCurvePointCount(index) {
        return DiffusionCurveSetApi.getCurvePointCount(this.handle, index);
    }

    getCurvePoint(index, pointIndex) {
        return DiffusionCurveSetApi.getCurvePoint(this.handle, index, pointIndex);
    }

    // Convenience over the SDK's count + index accessors
    getCurvePoints(index) {
        const count = DiffusionCurveSetApi.getCurvePointCount(this.handle, index);
        const points = [];
        for (let n = 0; n < count; ++n) {
            points.push(DiffusionCurveSetApi.getCurvePoint(this.handle, index, n));
        }
        return points;
    }

    setCurvePoints(index, points) {
        DiffusionCurveSetApi.setCurvePoints(this.handle, index, points);
    }

    getCurveColour(index, side) {
        const clrHandle = DiffusionCurveSetApi.getCurveColour(this.handle, index, side);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    setCurveColour(index, side, colour) {
        DiffusionCurveSetApi.setCurveColour(this.handle, index, side, colour?.handle);
    }

    getCurveBlur(index) {
        return DiffusionCurveSetApi.getCurveBlur(this.handle, index);
    }

    setCurveBlur(index, blur) {
        DiffusionCurveSetApi.setCurveBlur(this.handle, index, blur);
    }

    getCurveStrength(index) {
        return DiffusionCurveSetApi.getCurveStrength(this.handle, index);
    }

    setCurveStrength(index, strength) {
        DiffusionCurveSetApi.setCurveStrength(this.handle, index, strength);
    }

    getCurvePressure(index) {
        const curveHandle = DiffusionCurveSetApi.getCurvePressure(this.handle, index);
        return curveHandle ? new Curve(curveHandle) : null;
    }

    setCurvePressure(index, curve) {
        DiffusionCurveSetApi.setCurvePressure(this.handle, index, curve?.handle);
    }

    get backgroundColour() {
        const clrHandle = DiffusionCurveSetApi.getBackgroundColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set backgroundColour(value) {
        DiffusionCurveSetApi.setBackgroundColour(this.handle, value?.handle);
    }

    get backgroundStrength() {
        return DiffusionCurveSetApi.getBackgroundStrength(this.handle);
    }

    set backgroundStrength(value) {
        DiffusionCurveSetApi.setBackgroundStrength(this.handle, value);
    }

    // Parametric primitives: ellipses, elliptical arcs and straight lines
    // project to Bezier chains internally (their points remain readable) and
    // are stable under affine transforms of the owning shape. Setting
    // explicit points on a parametric curve demotes it to a Bezier chain.
    // Compare getCurveKind against DiffusionCurveKind values.

    getCurveKind(index) {
        return DiffusionCurveSetApi.getCurveKind(this.handle, index);
    }

    // Returns a DiffusionCurveParametric ({ centre, radiusX, radiusY,
    // rotation, angle0, angle1 }); for a line, centre is the start point and
    // (angle0, angle1) the end point. Throws for a plain Bezier curve
    getCurveParametric(index) {
        return DiffusionCurveSetApi.getCurveParametric(this.handle, index);
    }

    setCurveEllipse(index, centre, radiusX, radiusY, rotation = 0) {
        DiffusionCurveSetApi.setCurveEllipse(this.handle, index, centre, radiusX, radiusY, rotation);
    }

    setCurveArc(index, centre, radiusX, radiusY, rotation, angle0, angle1) {
        DiffusionCurveSetApi.setCurveArc(this.handle, index, centre, radiusX, radiusY, rotation, angle0, angle1);
    }

    setCurveLine(index, start, end) {
        DiffusionCurveSetApi.setCurveLine(this.handle, index, start, end);
    }

    addEllipse(centre, radiusX, radiusY, rotation = 0, leftColour, rightColour) {
        DiffusionCurveSetApi.addEllipse(this.handle, centre, radiusX, radiusY, rotation, leftColour?.handle, rightColour?.handle);
    }

    addArc(centre, radiusX, radiusY, rotation, angle0, angle1, leftColour, rightColour) {
        DiffusionCurveSetApi.addArc(this.handle, centre, radiusX, radiusY, rotation, angle0, angle1, leftColour?.handle, rightColour?.handle);
    }

    addLine(start, end, leftColour, rightColour) {
        DiffusionCurveSetApi.addLine(this.handle, start, end, leftColour?.handle, rightColour?.handle);
    }

    // Node styles (Bezier curves only): smooth nodes keep their two off-curve
    // handles collinear when edited in the tool

    getCurveNodeCount(index) {
        return DiffusionCurveSetApi.getCurveNodeCount(this.handle, index);
    }

    getCurveNodeSmooth(index, node) {
        return DiffusionCurveSetApi.getCurveNodeSmooth(this.handle, index, node);
    }

    setCurveNodeSmooth(index, node, smooth) {
        DiffusionCurveSetApi.setCurveNodeSmooth(this.handle, index, node, smooth);
    }
}


class DiffusionFill extends Fill {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DiffusionFill';
    }

    static create(curveSet) {
        return new DiffusionFill(DiffusionFillApi.create(curveSet.handle));
    }

    static createDefault() {
        return new DiffusionFill(DiffusionFillApi.createDefault());
    }

    static fromFill(fill) {
        return new DiffusionFill(DiffusionFillApi.fromFill(fill.handle));
    }

    clone() {
        return new DiffusionFill(DiffusionFillApi.clone(this.handle));
    }

    cloneWithNewCurves(curveSet) {
        return new DiffusionFill(DiffusionFillApi.cloneWithNewCurves(this.handle, curveSet.handle));
    }

    get curveSet() {
        return new DiffusionCurveSet(DiffusionFillApi.getCurves(this.handle));
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

class ColourMesh extends Mesh {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ColourMesh';
    }

    static createDefaultNone() {
        return new ColourMesh(ColourMeshApi.createDefaultNone());
    }

    static createDefaultWhite() {
        return new ColourMesh(ColourMeshApi.createDefaultWhite());
    }

    static createFromColour(colour, size) {
        return new ColourMesh(ColourMeshApi.createFromColour(colour.handle, size));
    }

    static createFromGradient(gradient, isRadial) {
        return new ColourMesh(ColourMeshApi.createFromGradient(gradient.handle, isRadial));
    }

    clone() {
        return new ColourMesh(ColourMeshApi.cloneAsColourMesh(this.handle));
    }

    getNodeColour(xIndex, yIndex) {
        const clrHandle = ColourMeshApi.getNodeColour(this.handle, xIndex, yIndex);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    setNodeColour(xIndex, yIndex, colour) {
        ColourMeshApi.setNodeColour(this.handle, xIndex, yIndex, colour?.handle);
    }
}


class MeshFill extends Fill {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'MeshFill';
    }

    static create(colourMesh) {
        return new MeshFill(MeshFillApi.create(colourMesh.handle));
    }

    static fromFill(fill) {
        return new MeshFill(MeshFillApi.fromFill(fill.handle));
    }

    clone() {
        return new MeshFill(MeshFillApi.cloneAsMeshFill(this.handle));
    }

    get colourMesh() {
        return new ColourMesh(MeshFillApi.getColourMesh(this.handle));
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

    // bounds ({x, y, width, height}, typically the node's baseBox) maps the
    // curve set's unit square onto that box, like the fill tool does when
    // converting a fill. Without it the transform is identity, which is only
    // useful for fills anchored to pre-transformed geometry.
    static create(fill, scaleWithObject, transform, blendMode, anchoredToSpread) {
        return new FillDescriptor(FillDescriptorApi.create(fill.handle, scaleWithObject, transform, blendMode, anchoredToSpread));
    }

    get fillType() {
        return this.fill.fillType;
    }
}

function makeFillDescriptor(fillDescriptor) {
    if (fillDescriptor == null) {
        return FillDescriptor.createNone();
    }
    if (fillDescriptor instanceof SolidFill || fillDescriptor instanceof Colour) {
        return FillDescriptor.createSolid(fillDescriptor);
    }
    return fillDescriptor;
}

module.exports.BitmapFill = BitmapFill;
module.exports.BlendMode = BlendMode;
module.exports.ColourMesh = ColourMesh;
module.exports.createTypedFill = createTypedFill;
module.exports.DiffusionCurveKind = DiffusionCurveKind;
module.exports.DiffusionCurveParametric = DiffusionCurveParametric;
module.exports.DiffusionCurveSet = DiffusionCurveSet;
module.exports.DiffusionCurveSide = DiffusionCurveSide;
module.exports.DiffusionFill = DiffusionFill;
module.exports.Fill = Fill;
module.exports.FillDescriptor = FillDescriptor;
module.exports.FillMask = FillMask;
module.exports.FillType = FillType;
module.exports.GradientFill = GradientFill;
module.exports.GradientFillType = GradientFillType;
module.exports.HatchFill = HatchFill;
module.exports.makeFillDescriptor = makeFillDescriptor;
module.exports.MeshFill = MeshFill;
module.exports.NoFill = NoFill;
module.exports.RasterExtendType = RasterExtendType;
module.exports.RasterResamplerType = RasterResamplerType;
module.exports.SolidFill = SolidFill;
module.exports.TransformInfo = TransformInfo;
module.exports.UnitType = UnitType;
