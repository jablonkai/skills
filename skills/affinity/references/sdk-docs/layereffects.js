'use strict';

const { BlendMode } = require('affinity:common');
const { SplineProfile } = require('affinity:geometry');
const {
    BevelEmbossLayerEffectApi,
    BevelEmbossType,
    ColourOverlayLayerEffectApi,
    GaussianBlurLayerEffectApi,
    GradientOverlayLayerEffectApi,
    InnerGlowLayerEffectApi,
    InnerShadowLayerEffectApi,
    LayerEffectApi,
    LayerEffectType,
    OuterGlowLayerEffectApi,
    OuterShadowLayerEffectApi,
    OutlineLayerEffectApi,
    PhongBevelLayerEffectApi,
    PointLightApi,
    StrokeFillType
} = require('affinity:layereffects');
const { StrokeAlignment } = require('affinity:linestyles');
const { Colour } = require('./colours.js');
const { FillDescriptor } = require('./fills.js');
const { Spline } = require('./geometry.js');
const { HandleObject } = require('./handleobject.js');

function createTypedLayerEffect(handle) {
    if (!handle)
        return null;
    const layerEffectType = LayerEffectApi.getType(handle);
    switch (layerEffectType.value) {
        case LayerEffectType.GaussianBlur.value:
            return new GaussianBlurLayerEffect(GaussianBlurLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.OuterShadow.value:
            return new OuterShadowLayerEffect(OuterShadowLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.InnerShadow.value:
            return new InnerShadowLayerEffect(InnerShadowLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.OuterGlow.value:
            return new OuterGlowLayerEffect(OuterGlowLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.InnerGlow.value:
            return new InnerGlowLayerEffect(InnerGlowLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.Outline.value:
            return new OutlineLayerEffect(OutlineLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.ColourOverlay.value:
            return new ColourOverlayLayerEffect(ColourOverlayLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.GradientOverlay.value:
            return new GradientOverlayLayerEffect(GradientOverlayLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.BevelEmboss.value:
            return new BevelEmbossLayerEffect(BevelEmbossLayerEffectApi.fromLayerEffect(handle));
        case LayerEffectType.PhongBevel.value:
            return new PhongBevelLayerEffect(PhongBevelLayerEffectApi.fromLayerEffect(handle));
        default:
            return new LayerEffect(handle);
    }
}


class LayerEffect extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LayerEffect';
    }

    get isLayerEffect() {
        return true;
    }

    clone() {
        return new LayerEffect(LayerEffectApi.clone(this.handle));
    }

    get type() {
        return LayerEffectApi.getType(this.handle);
    }

    get enabled() {
        return LayerEffectApi.getEnabled(this.handle);
    }

    set enabled(value) {
        LayerEffectApi.setEnabled(this.handle, value);
    }

    get opacity() {
        return LayerEffectApi.getOpacity(this.handle);
    }

    set opacity(value) {
        LayerEffectApi.setOpacity(this.handle, value);
    }

    get blendMode() {
        return LayerEffectApi.getBlendMode(this.handle);
    }

    set blendMode(value) {
        LayerEffectApi.setBlendMode(this.handle, value);
    }

    get scaleWithObject() {
        return LayerEffectApi.getScaleWithObject(this.handle);
    }

    set scaleWithObject(value) {
        LayerEffectApi.setScaleWithObject(this.handle, value);
    }
}

class BevelEmbossLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BevelEmbossLayerEffect';
    }

    get isBevelEmbossLayerEffect() {
        return true;
    }

    clone() {
        return new BevelEmbossLayerEffect(BevelEmbossLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new BevelEmbossLayerEffect(BevelEmbossLayerEffectApi.create());
    }


    get radius() {
        return BevelEmbossLayerEffectApi.getRadius(this.handle);
    }

    set radius(value) {
        BevelEmbossLayerEffectApi.setRadius(this.handle, value);
    }

    get depth() {
        return BevelEmbossLayerEffectApi.getDepth(this.handle);
    }

    set depth(value) {
        BevelEmbossLayerEffectApi.setDepth(this.handle, value);
    }

    get soften() {
        return BevelEmbossLayerEffectApi.getSoften(this.handle);
    }

    set soften(value) {
        BevelEmbossLayerEffectApi.setSoften(this.handle, value);
    }

    get bevelProfile() {
        const splineHandle = BevelEmbossLayerEffectApi.getBevelProfile(this.handle);
        return splineHandle ? new Spline(splineHandle) : null;
    }

    set bevelProfile(value) {
        BevelEmbossLayerEffectApi.setBevelProfile(this.handle, value?.handle);
    }

    setStandardBevelProfile(standardProfile) {
        BevelEmbossLayerEffectApi.setStandardBevelProfile(this.handle, standardProfile);
    }

    get bevelEmbossType() {
        return BevelEmbossLayerEffectApi.getBevelEmbossType(this.handle);
    }

    set bevelEmbossType(value) {
        BevelEmbossLayerEffectApi.setBevelEmbossType(this.handle, value);
    }

    get azimuth() {
        return BevelEmbossLayerEffectApi.getAzimuth(this.handle);
    }

    set azimuth(value) {
        BevelEmbossLayerEffectApi.setAzimuth(this.handle, value);
    }

    get elevation() {
        return BevelEmbossLayerEffectApi.getElevation(this.handle);
    }

    set elevation(value) {
        BevelEmbossLayerEffectApi.setElevation(this.handle, value);
    }

    get invert() {
        return BevelEmbossLayerEffectApi.getInvert(this.handle);
    }

    set invert(value) {
        BevelEmbossLayerEffectApi.setInvert(this.handle, value);
    }

    get shadowColour() {
        const clrHandle = BevelEmbossLayerEffectApi.getShadowColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set shadowColour(value) {
        BevelEmbossLayerEffectApi.setShadowColour(this.handle, value?.handle);
    }

    get highlightColour() {
        const clrHandle = BevelEmbossLayerEffectApi.getHighlightColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set highlightColour(value) {
        BevelEmbossLayerEffectApi.setHighlightColour(this.handle, value?.handle);
    }

    get shadowBlendMode() {
        return BevelEmbossLayerEffectApi.getShadowBlendMode(this.handle);
    }

    set shadowBlendMode(value) {
        BevelEmbossLayerEffectApi.setShadowBlendMode(this.handle, value);
    }

    get shadowOpacity() {
        return BevelEmbossLayerEffectApi.getShadowOpacity(this.handle);
    }

    set shadowOpacity(value) {
        BevelEmbossLayerEffectApi.setShadowOpacity(this.handle, value);
    }
}

class ColourOverlayLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ColourOverlayLayerEffect';
    }

    get isColourOverlayLayerEffect() {
        return true;
    }

    clone() {
        return new ColourOverlayLayerEffect(ColourOverlayLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new ColourOverlayLayerEffect(ColourOverlayLayerEffectApi.create());
    }


    get colour() {
        const clrHandle = ColourOverlayLayerEffectApi.getColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set colour(value) {
        ColourOverlayLayerEffectApi.setColour(this.handle, value?.handle);
    }
}

class GaussianBlurLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'GaussianBlurLayerEffect';
    }

    get isGaussianBlurLayerEffect() {
        return true;
    }

    clone() {
        return new GaussianBlurLayerEffect(GaussianBlurLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new GaussianBlurLayerEffect(GaussianBlurLayerEffectApi.create());
    }


    get radius() {
        return GaussianBlurLayerEffectApi.getRadius(this.handle);
    }

    set radius(value) {
        GaussianBlurLayerEffectApi.setRadius(this.handle, value);
    }

    get preserveAlpha() {
        return GaussianBlurLayerEffectApi.getPreserveAlpha(this.handle);
    }

    set preserveAlpha(value) {
        GaussianBlurLayerEffectApi.setPreserveAlpha(this.handle, value);
    }
}

class GradientOverlayLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'GradientOverlayLayerEffect';
    }

    get isGradientOverlayLayerEffect() {
        return true;
    }

    clone() {
        return new GradientOverlayLayerEffect(GradientOverlayLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new GradientOverlayLayerEffect(GradientOverlayLayerEffectApi.create());
    }


    get fillDescriptor() {
        const descHandle = GradientOverlayLayerEffectApi.getFillDescriptor(this.handle);
        return descHandle ? new FillDescriptor(descHandle) : null;
    }

    set fillDescriptor(value) {
        GradientOverlayLayerEffectApi.setFillDescriptor(this.handle, value?.handle);
    }

    static calculateTransform(scaleX, scaleY, transformX, transformY) {
        return GradientOverlayLayerEffectApi.calculateTransform(scaleX, scaleY, transformX, transformY);
    }
}

class InnerGlowLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'InnerGlowLayerEffect';
    }

    get isInnerGlowLayerEffect() {
        return true;
    }

    clone() {
        return new InnerGlowLayerEffect(InnerGlowLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new InnerGlowLayerEffect(InnerGlowLayerEffectApi.create());
    }


    get radius() {
        return InnerGlowLayerEffectApi.getRadius(this.handle);
    }

    set radius(value) {
        InnerGlowLayerEffectApi.setRadius(this.handle, value);
    }

    get colour() {
        const clrHandle = InnerGlowLayerEffectApi.getColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set colour(value) {
        InnerGlowLayerEffectApi.setColour(this.handle, value?.handle);
    }

    get intensity() {
        return InnerGlowLayerEffectApi.getIntensity(this.handle);
    }

    set intensity(value) {
        InnerGlowLayerEffectApi.setIntensity(this.handle, value);
    }

    get centre() {
        return InnerGlowLayerEffectApi.getCentre(this.handle);
    }

    set centre(value) {
        InnerGlowLayerEffectApi.setCentre(this.handle, value);
    }
}

class InnerShadowLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'InnerShadowLayerEffect';
    }

    get isInnerShadowLayerEffect() {
        return true;
    }

    clone() {
        return new InnerShadowLayerEffect(InnerShadowLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new InnerShadowLayerEffect(InnerShadowLayerEffectApi.create());
    }


    get radius() {
        return InnerShadowLayerEffectApi.getRadius(this.handle);
    }

    set radius(value) {
        InnerShadowLayerEffectApi.setRadius(this.handle, value);
    }

    get colour() {
        const clrHandle = InnerShadowLayerEffectApi.getColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set colour(value) {
        InnerShadowLayerEffectApi.setColour(this.handle, value?.handle);
    }

    get offset() {
        return InnerShadowLayerEffectApi.getOffset(this.handle);
    }

    set offset(value) {
        InnerShadowLayerEffectApi.setOffset(this.handle, value);
    }

    get angle() {
        return InnerShadowLayerEffectApi.getAngle(this.handle);
    }

    set angle(value) {
        InnerShadowLayerEffectApi.setAngle(this.handle, value);
    }

    get intensity() {
        return InnerShadowLayerEffectApi.getIntensity(this.handle);
    }

    set intensity(value) {
        InnerShadowLayerEffectApi.setIntensity(this.handle, value);
    }
}

class OuterGlowLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'OuterGlowLayerEffect';
    }

    get isOuterGlowLayerEffect() {
        return true;
    }

    clone() {
        return new OuterGlowLayerEffect(OuterGlowLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new OuterGlowLayerEffect(OuterGlowLayerEffectApi.create());
    }


    get radius() {
        return OuterGlowLayerEffectApi.getRadius(this.handle);
    }

    set radius(value) {
        OuterGlowLayerEffectApi.setRadius(this.handle, value);
    }

    get colour() {
        const clrHandle = OuterGlowLayerEffectApi.getColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set colour(value) {
        OuterGlowLayerEffectApi.setColour(this.handle, value?.handle);
    }

    get intensity() {
        return OuterGlowLayerEffectApi.getIntensity(this.handle);
    }

    set intensity(value) {
        OuterGlowLayerEffectApi.setIntensity(this.handle, value);
    }
}

class OuterShadowLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'OuterShadowLayerEffect';
    }

    get isOuterShadowLayerEffect() {
        return true;
    }

    clone() {
        return new OuterShadowLayerEffect(OuterShadowLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new OuterShadowLayerEffect(OuterShadowLayerEffectApi.create());
    }


    get radius() {
        return OuterShadowLayerEffectApi.getRadius(this.handle);
    }

    set radius(value) {
        OuterShadowLayerEffectApi.setRadius(this.handle, value);
    }

    get colour() {
        const clrHandle = OuterShadowLayerEffectApi.getColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set colour(value) {
        OuterShadowLayerEffectApi.setColour(this.handle, value?.handle);
    }

    get offset() {
        return OuterShadowLayerEffectApi.getOffset(this.handle);
    }

    set offset(value) {
        OuterShadowLayerEffectApi.setOffset(this.handle, value);
    }

    get angle() {
        return OuterShadowLayerEffectApi.getAngle(this.handle);
    }

    set angle(value) {
        OuterShadowLayerEffectApi.setAngle(this.handle, value);
    }

    get intensity() {
        return OuterShadowLayerEffectApi.getIntensity(this.handle);
    }

    set intensity(value) {
        OuterShadowLayerEffectApi.setIntensity(this.handle, value);
    }

    get fillKnocksOut() {
        return OuterShadowLayerEffectApi.getFillKnocksOut(this.handle);
    }

    set fillKnocksOut(value) {
        OuterShadowLayerEffectApi.setFillKnocksOut(this.handle, value);
    }
}

class OutlineLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'OutlineLayerEffect';
    }

    get isOutlineLayerEffect() {
        return true;
    }

    clone() {
        return new OutlineLayerEffect(OutlineLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new OutlineLayerEffect(OutlineLayerEffectApi.create());
    }


    get radius() {
        return OutlineLayerEffectApi.getRadius(this.handle);
    }

    set radius(value) {
        OutlineLayerEffectApi.setRadius(this.handle, value);
    }

    get colour() {
        const clrHandle = OutlineLayerEffectApi.getColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set colour(value) {
        OutlineLayerEffectApi.setColour(this.handle, value?.handle);
    }

    get alignment() {
        return OutlineLayerEffectApi.getAlignment(this.handle);
    }

    set alignment(value) {
        OutlineLayerEffectApi.setAlignment(this.handle, value);
    }

    get fillType() {
        return OutlineLayerEffectApi.getFillType(this.handle);
    }

    set fillType(value) {
        OutlineLayerEffectApi.setFillType(this.handle, value);
    }

    get fillDescriptor() {
        const descHandle = OutlineLayerEffectApi.getFillDescriptor(this.handle);
        return descHandle ? new FillDescriptor(descHandle) : null;
    }

    set fillDescriptor(value) {
        OutlineLayerEffectApi.setFillDescriptor(this.handle, value?.handle);
    }

    static calculateTransform(scaleX, scaleY, transformX, transformY) {
        return OutlineLayerEffectApi.calculateTransform(scaleX, scaleY, transformX, transformY);
    }
}

class PhongBevelLayerEffect extends LayerEffect {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PhongBevelLayerEffect';
    }

    get isPhongBevelLayerEffect() {
        return true;
    }

    clone() {
        return new PhongBevelLayerEffect(PhongBevelLayerEffectApi.clone(this.handle));
    }

    static create() {
        return new PhongBevelLayerEffect(PhongBevelLayerEffectApi.create());
    }


    get radius() {
        return PhongBevelLayerEffectApi.getRadius(this.handle);
    }

    set radius(value) {
        PhongBevelLayerEffectApi.setRadius(this.handle, value);
    }

    get linkDepth() {
        return PhongBevelLayerEffectApi.getLinkDepth(this.handle);
    }

    set linkDepth(value) {
        PhongBevelLayerEffectApi.setLinkDepth(this.handle, value);
    }

    get depth() {
        return PhongBevelLayerEffectApi.getDepth(this.handle);
    }

    set depth(value) {
        PhongBevelLayerEffectApi.setDepth(this.handle, value);
    }

    get soften() {
        return PhongBevelLayerEffectApi.getSoften(this.handle);
    }

    set soften(value) {
        PhongBevelLayerEffectApi.setSoften(this.handle, value);
    }

    get bevelProfile() {
        const splineHandle = PhongBevelLayerEffectApi.getBevelProfile(this.handle);
        return splineHandle ? new Spline(splineHandle) : null;
    }

    set bevelProfile(value) {
        PhongBevelLayerEffectApi.setBevelProfile(this.handle, value?.handle);
    }

    setStandardBevelProfile(standardProfile) {
        PhongBevelLayerEffectApi.setStandardBevelProfile(this.handle, standardProfile);
    }

    get ambient() {
        return PhongBevelLayerEffectApi.getAmbient(this.handle);
    }

    set ambient(value) {
        PhongBevelLayerEffectApi.setAmbient(this.handle, value);
    }

    get diffuse() {
        return PhongBevelLayerEffectApi.getDiffuse(this.handle);
    }

    set diffuse(value) {
        PhongBevelLayerEffectApi.setDiffuse(this.handle, value);
    }

    get specular() {
        return PhongBevelLayerEffectApi.getSpecular(this.handle);
    }

    set specular(value) {
        PhongBevelLayerEffectApi.setSpecular(this.handle, value);
    }

    get shininess() {
        return PhongBevelLayerEffectApi.getShininess(this.handle);
    }

    set shininess(value) {
        PhongBevelLayerEffectApi.setShininess(this.handle, value);
    }

    get ambientColour() {
        const clrHandle = PhongBevelLayerEffectApi.getAmbientColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set ambientColour(value) {
        PhongBevelLayerEffectApi.setAmbientColour(this.handle, value?.handle);
    }

    get specularColour() {
        const clrHandle = PhongBevelLayerEffectApi.getSpecularColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set specularColour(value) {
        PhongBevelLayerEffectApi.setSpecularColour(this.handle, value?.handle);
    }

    get lightCount() {
        return PhongBevelLayerEffectApi.getLightCount(this.handle);
    }

    getLight(index) {
        return new PointLight(PhongBevelLayerEffectApi.getLight(this.handle, index));
    }

    enumerateLights(callback) {
        PhongBevelLayerEffectApi.enumerateLights(this.handle, (lightHandle) => {
            return callback(new PointLight(lightHandle));
        });
    }

    insertLight(index, pointLight) {
        PhongBevelLayerEffectApi.insertLight(this.handle, index, pointLight?.handle);
    }

    removeLight(index) {
        PhongBevelLayerEffectApi.removeLight(this.handle, index);
    }

    appendLight(pointLight) {
        PhongBevelLayerEffectApi.appendLight(this.handle, pointLight?.handle);
    }
}

class PointLight extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PointLight';
    }

    get isPointLight() {
        return true;
    }

    clone() {
        return new PointLight(PointLightApi.clone(this.handle));
    }

    get azimuth() {
        return PointLightApi.getAzimuth(this.handle);
    }

    set azimuth(value) {
        PointLightApi.setAzimuth(this.handle, value);
    }

    get elevation() {
        return PointLightApi.getElevation(this.handle);
    }

    set elevation(value) {
        PointLightApi.setElevation(this.handle, value);
    }

    get colour() {
        const clrHandle = PointLightApi.getColour(this.handle);
        return clrHandle ? new Colour(clrHandle) : null;
    }

    set colour(value) {
        PointLightApi.setColour(this.handle, value?.handle);
    }
}

module.exports.BevelEmbossLayerEffect = BevelEmbossLayerEffect;
module.exports.BlendMode = BlendMode;
module.exports.ColourOverlayLayerEffect = ColourOverlayLayerEffect;
module.exports.LayerEffect = LayerEffect;
module.exports.GaussianBlurLayerEffect = GaussianBlurLayerEffect;
module.exports.GradientOverlayLayerEffect = GradientOverlayLayerEffect;
module.exports.InnerGlowLayerEffect = InnerGlowLayerEffect;
module.exports.InnerShadowLayerEffect = InnerShadowLayerEffect;
module.exports.OuterShadowLayerEffect = OuterShadowLayerEffect;
module.exports.OuterGlowLayerEffect = OuterGlowLayerEffect;
module.exports.OutlineLayerEffect = OutlineLayerEffect;
module.exports.PhongBevelLayerEffect = PhongBevelLayerEffect;
module.exports.PointLight = PointLight;
module.exports.SplineProfile = SplineProfile;

module.exports.createTypedLayerEffect = createTypedLayerEffect;
module.exports.LayerEffectType = LayerEffectType;
module.exports.StrokeAlignment = StrokeAlignment;
module.exports.StrokeFillType = StrokeFillType;
module.exports.BevelEmbossType = BevelEmbossType;
