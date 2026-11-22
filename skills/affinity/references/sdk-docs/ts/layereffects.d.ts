// Type declarations for the Affinity JavaScript SDK: module "affinity:layereffects".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:layereffects" {

    import { BlendMode, EnumerationResult } from "affinity:common";
    import { SplineProfile, Transform } from "affinity:geometry";
    import { StrokeAlignment } from "affinity:linestyles";

    export enum BevelEmbossType {
        Inner,
        Outer,
        Emboss,
        Pillow,
    }

    export enum LayerEffectType {
        BevelEmboss,
        Outline,
        PhongBevel,
        InnerShadow,
        InnerGlow,
        ColourOverlay,
        GradientOverlay,
        OuterGlow,
        OuterShadow,
        GaussianBlur,
    }

    export enum StrokeFillType {
        Solid,
        Contour,
        Gradient,
    }

    export interface BevelEmbossLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        clone(self: BevelEmbossLayerEffectHandle): BevelEmbossLayerEffectHandle;
        cloneAsBevelEmbossLayerEffect(self: BevelEmbossLayerEffectHandle): BevelEmbossLayerEffectHandle;
        create(): BevelEmbossLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): BevelEmbossLayerEffectHandle;
        getAzimuth(self: BevelEmbossLayerEffectHandle): number;
        getBevelEmbossType(self: BevelEmbossLayerEffectHandle): BevelEmbossType;
        getBevelProfile(self: BevelEmbossLayerEffectHandle): SplineHandle;
        getDepth(self: BevelEmbossLayerEffectHandle): number;
        getElevation(self: BevelEmbossLayerEffectHandle): number;
        getHighlightBlendMode(self: BevelEmbossLayerEffectHandle): BlendMode;
        getHighlightColour(self: BevelEmbossLayerEffectHandle): ColourHandle;
        getHighlightOpacity(self: BevelEmbossLayerEffectHandle): number;
        getInvert(self: BevelEmbossLayerEffectHandle): boolean;
        getRadius(self: BevelEmbossLayerEffectHandle): number;
        getShadowBlendMode(self: BevelEmbossLayerEffectHandle): BlendMode;
        getShadowColour(self: BevelEmbossLayerEffectHandle): ColourHandle;
        getShadowOpacity(self: BevelEmbossLayerEffectHandle): number;
        getSoften(self: BevelEmbossLayerEffectHandle): number;
        setAzimuth(self: BevelEmbossLayerEffectHandle, azimuth: number): void;
        setBevelEmbossType(self: BevelEmbossLayerEffectHandle, bevelEmbossType: BevelEmbossType): void;
        setBevelProfile(self: BevelEmbossLayerEffectHandle, bevelProfileOrNull: SplineHandle | null): void;
        setDepth(self: BevelEmbossLayerEffectHandle, depth: number): void;
        setElevation(self: BevelEmbossLayerEffectHandle, elevation: number): void;
        setHighlightBlendMode(self: BevelEmbossLayerEffectHandle, highlightBlendMode: BlendMode): void;
        setHighlightColour(self: BevelEmbossLayerEffectHandle, highlightColour: ColourHandle): void;
        setHighlightOpacity(self: BevelEmbossLayerEffectHandle, highlightOpacity: number): void;
        setInvert(self: BevelEmbossLayerEffectHandle, invert: boolean): void;
        setRadius(self: BevelEmbossLayerEffectHandle, radius: number): void;
        setShadowBlendMode(self: BevelEmbossLayerEffectHandle, shadowBlendMode: BlendMode): void;
        setShadowColour(self: BevelEmbossLayerEffectHandle, shadowColour: ColourHandle): void;
        setShadowOpacity(self: BevelEmbossLayerEffectHandle, shadowOpacity: number): void;
        setSoften(self: BevelEmbossLayerEffectHandle, soften: number): void;
        setStandardBevelProfile(self: BevelEmbossLayerEffectHandle, standardProfile: SplineProfile): void;
    }
    export const BevelEmbossLayerEffectApi: BevelEmbossLayerEffectApi;

    export interface ColourOverlayLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        clone(self: ColourOverlayLayerEffectHandle): ColourOverlayLayerEffectHandle;
        cloneAsColourOverlayLayerEffect(self: ColourOverlayLayerEffectHandle): ColourOverlayLayerEffectHandle;
        create(): ColourOverlayLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): ColourOverlayLayerEffectHandle;
        getColour(self: ColourOverlayLayerEffectHandle): ColourHandle;
        setColour(self: ColourOverlayLayerEffectHandle, colour: ColourHandle): void;
    }
    export const ColourOverlayLayerEffectApi: ColourOverlayLayerEffectApi;

    export interface GaussianBlurLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        clone(self: GaussianBlurLayerEffectHandle): GaussianBlurLayerEffectHandle;
        cloneAsGaussianBlurLayerEffect(self: GaussianBlurLayerEffectHandle): GaussianBlurLayerEffectHandle;
        create(): GaussianBlurLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): GaussianBlurLayerEffectHandle;
        getPreserveAlpha(self: GaussianBlurLayerEffectHandle): boolean;
        getRadius(self: GaussianBlurLayerEffectHandle): number;
        setPreserveAlpha(self: GaussianBlurLayerEffectHandle, preserveAlpha: boolean): void;
        setRadius(self: GaussianBlurLayerEffectHandle, radius: number): void;
    }
    export const GaussianBlurLayerEffectApi: GaussianBlurLayerEffectApi;

    export interface GradientOverlayLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        calculateTransform(scaleX: number, scaleY: number, offsetX: number, offsetY: number): Transform;
        clone(self: GradientOverlayLayerEffectHandle): GradientOverlayLayerEffectHandle;
        cloneAsGradientOverlayLayerEffect(self: GradientOverlayLayerEffectHandle): GradientOverlayLayerEffectHandle;
        create(): GradientOverlayLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): GradientOverlayLayerEffectHandle;
        getFillDescriptor(self: GradientOverlayLayerEffectHandle): FillDescriptorHandle;
        setFillDescriptor(self: GradientOverlayLayerEffectHandle, fillDescriptor: FillDescriptorHandle): void;
    }
    export const GradientOverlayLayerEffectApi: GradientOverlayLayerEffectApi;

    export interface InnerGlowLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        clone(self: InnerGlowLayerEffectHandle): InnerGlowLayerEffectHandle;
        cloneAsInnerGlowLayerEffect(self: InnerGlowLayerEffectHandle): InnerGlowLayerEffectHandle;
        create(): InnerGlowLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): InnerGlowLayerEffectHandle;
        getCentre(self: InnerGlowLayerEffectHandle): boolean;
        getColour(self: InnerGlowLayerEffectHandle): ColourHandle;
        getIntensity(self: InnerGlowLayerEffectHandle): number;
        getRadius(self: InnerGlowLayerEffectHandle): number;
        setCentre(self: InnerGlowLayerEffectHandle, centre: boolean): void;
        setColour(self: InnerGlowLayerEffectHandle, colour: ColourHandle): void;
        setIntensity(self: InnerGlowLayerEffectHandle, intensity: number): void;
        setRadius(self: InnerGlowLayerEffectHandle, radius: number): void;
    }
    export const InnerGlowLayerEffectApi: InnerGlowLayerEffectApi;

    export interface InnerShadowLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        clone(self: InnerShadowLayerEffectHandle): InnerShadowLayerEffectHandle;
        cloneAsInnerShadowLayerEffect(self: InnerShadowLayerEffectHandle): InnerShadowLayerEffectHandle;
        create(): InnerShadowLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): InnerShadowLayerEffectHandle;
        getAngle(self: InnerShadowLayerEffectHandle): number;
        getColour(self: InnerShadowLayerEffectHandle): ColourHandle;
        getIntensity(self: InnerShadowLayerEffectHandle): number;
        getOffset(self: InnerShadowLayerEffectHandle): number;
        getRadius(self: InnerShadowLayerEffectHandle): number;
        setAngle(self: InnerShadowLayerEffectHandle, angle: number): void;
        setColour(self: InnerShadowLayerEffectHandle, colour: ColourHandle): void;
        setIntensity(self: InnerShadowLayerEffectHandle, intensity: number): void;
        setOffset(self: InnerShadowLayerEffectHandle, offset: number): void;
        setRadius(self: InnerShadowLayerEffectHandle, radius: number): void;
    }
    export const InnerShadowLayerEffectApi: InnerShadowLayerEffectApi;

    export interface LayerEffectApi {
        clone(self: LayerEffectHandle): LayerEffectHandle;
        cloneAsLayerEffect(self: LayerEffectHandle): LayerEffectHandle;
        getBlendMode(self: LayerEffectHandle): BlendMode;
        getEnabled(self: LayerEffectHandle): boolean;
        getOpacity(self: LayerEffectHandle): number;
        getScaleWithObject(self: LayerEffectHandle): boolean;
        getType(self: LayerEffectHandle): LayerEffectType;
        setBlendMode(self: LayerEffectHandle, blendMode: BlendMode): void;
        setEnabled(self: LayerEffectHandle, enabled: boolean): void;
        setOpacity(self: LayerEffectHandle, opacity: number): void;
        setScaleWithObject(self: LayerEffectHandle, scaleWithObject: boolean): void;
    }
    export const LayerEffectApi: LayerEffectApi;

    export interface OuterGlowLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        clone(self: OuterGlowLayerEffectHandle): OuterGlowLayerEffectHandle;
        cloneAsOuterGlowLayerEffect(self: OuterGlowLayerEffectHandle): OuterGlowLayerEffectHandle;
        create(): OuterGlowLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): OuterGlowLayerEffectHandle;
        getColour(self: OuterGlowLayerEffectHandle): ColourHandle;
        getIntensity(self: OuterGlowLayerEffectHandle): number;
        getRadius(self: OuterGlowLayerEffectHandle): number;
        setColour(self: OuterGlowLayerEffectHandle, colour: ColourHandle): void;
        setIntensity(self: OuterGlowLayerEffectHandle, intensity: number): void;
        setRadius(self: OuterGlowLayerEffectHandle, radius: number): void;
    }
    export const OuterGlowLayerEffectApi: OuterGlowLayerEffectApi;

    export interface OuterShadowLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        clone(self: OuterShadowLayerEffectHandle): OuterShadowLayerEffectHandle;
        cloneAsOuterShadowLayerEffect(self: OuterShadowLayerEffectHandle): OuterShadowLayerEffectHandle;
        create(): OuterShadowLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): OuterShadowLayerEffectHandle;
        getAngle(self: OuterShadowLayerEffectHandle): number;
        getColour(self: OuterShadowLayerEffectHandle): ColourHandle;
        getFillKnocksOut(self: OuterShadowLayerEffectHandle): boolean;
        getIntensity(self: OuterShadowLayerEffectHandle): number;
        getOffset(self: OuterShadowLayerEffectHandle): number;
        getRadius(self: OuterShadowLayerEffectHandle): number;
        setAngle(self: OuterShadowLayerEffectHandle, angle: number): void;
        setColour(self: OuterShadowLayerEffectHandle, colour: ColourHandle): void;
        setFillKnocksOut(self: OuterShadowLayerEffectHandle, fillKnocksOut: boolean): void;
        setIntensity(self: OuterShadowLayerEffectHandle, intensity: number): void;
        setOffset(self: OuterShadowLayerEffectHandle, offset: number): void;
        setRadius(self: OuterShadowLayerEffectHandle, radius: number): void;
    }
    export const OuterShadowLayerEffectApi: OuterShadowLayerEffectApi;

    export interface OutlineLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        calculateTransform(scaleX: number, scaleY: number, offsetX: number, offsetY: number): Transform;
        clone(self: OutlineLayerEffectHandle): OutlineLayerEffectHandle;
        cloneAsOutlineLayerEffect(self: OutlineLayerEffectHandle): OutlineLayerEffectHandle;
        create(): OutlineLayerEffectHandle;
        fromLayerEffect(layerEffect: LayerEffectHandle): OutlineLayerEffectHandle;
        getAlignment(self: OutlineLayerEffectHandle): StrokeAlignment;
        getColour(self: OutlineLayerEffectHandle): ColourHandle;
        getFillDescriptor(self: OutlineLayerEffectHandle): FillDescriptorHandle;
        getFillType(self: OutlineLayerEffectHandle): StrokeFillType;
        getRadius(self: OutlineLayerEffectHandle): number;
        setAlignment(self: OutlineLayerEffectHandle, alignment: StrokeAlignment): void;
        setColour(self: OutlineLayerEffectHandle, colour: ColourHandle): void;
        setFillDescriptor(self: OutlineLayerEffectHandle, fillDescriptor: FillDescriptorHandle): void;
        setFillType(self: OutlineLayerEffectHandle, fillType: StrokeFillType): void;
        setRadius(self: OutlineLayerEffectHandle, radius: number): void;
    }
    export const OutlineLayerEffectApi: OutlineLayerEffectApi;

    export interface PhongBevelLayerEffectApi extends Omit<LayerEffectApi, "clone"> {
        appendLight(self: PhongBevelLayerEffectHandle, pointLight: PointLightHandle): void;
        clone(self: PhongBevelLayerEffectHandle): PhongBevelLayerEffectHandle;
        cloneAsPhongBevelLayerEffect(self: PhongBevelLayerEffectHandle): PhongBevelLayerEffectHandle;
        create(): PhongBevelLayerEffectHandle;
        enumerateLights(self: PhongBevelLayerEffectHandle, callback: (pointLight: PointLightHandle) => EnumerationResult): void;
        fromLayerEffect(layerEffect: LayerEffectHandle): PhongBevelLayerEffectHandle;
        getAmbient(self: PhongBevelLayerEffectHandle): number;
        getAmbientColour(self: PhongBevelLayerEffectHandle): ColourHandle;
        getBevelProfile(self: PhongBevelLayerEffectHandle): SplineHandle;
        getDepth(self: PhongBevelLayerEffectHandle): number;
        getDiffuse(self: PhongBevelLayerEffectHandle): number;
        getLight(self: PhongBevelLayerEffectHandle, index: number): PointLightHandle;
        getLightCount(self: PhongBevelLayerEffectHandle): number;
        getLinkDepth(self: PhongBevelLayerEffectHandle): boolean;
        getRadius(self: PhongBevelLayerEffectHandle): number;
        getShininess(self: PhongBevelLayerEffectHandle): number;
        getSoften(self: PhongBevelLayerEffectHandle): number;
        getSpecular(self: PhongBevelLayerEffectHandle): number;
        getSpecularColour(self: PhongBevelLayerEffectHandle): ColourHandle;
        insertLight(self: PhongBevelLayerEffectHandle, index: number, pointLight: PointLightHandle): void;
        removeLight(self: PhongBevelLayerEffectHandle, index: number): void;
        setAmbient(self: PhongBevelLayerEffectHandle, ambient: number): void;
        setAmbientColour(self: PhongBevelLayerEffectHandle, ambientColour: ColourHandle): void;
        setBevelProfile(self: PhongBevelLayerEffectHandle, bevelProfileOrNull: SplineHandle | null): void;
        setDepth(self: PhongBevelLayerEffectHandle, depth: number): void;
        setDiffuse(self: PhongBevelLayerEffectHandle, diffuse: number): void;
        setLinkDepth(self: PhongBevelLayerEffectHandle, linkDepth: boolean): void;
        setRadius(self: PhongBevelLayerEffectHandle, radius: number): void;
        setShininess(self: PhongBevelLayerEffectHandle, shininess: number): void;
        setSoften(self: PhongBevelLayerEffectHandle, soften: number): void;
        setSpecular(self: PhongBevelLayerEffectHandle, specular: number): void;
        setSpecularColour(self: PhongBevelLayerEffectHandle, specularColour: ColourHandle): void;
        setStandardBevelProfile(self: PhongBevelLayerEffectHandle, standardProfile: SplineProfile): void;
    }
    export const PhongBevelLayerEffectApi: PhongBevelLayerEffectApi;

    export interface PointLightApi {
        clone(self: PointLightHandle): PointLightHandle;
        cloneAsPointLight(self: PointLightHandle): PointLightHandle;
        getAzimuth(self: PointLightHandle): number;
        getColour(self: PointLightHandle): ColourHandle;
        getElevation(self: PointLightHandle): number;
        setAzimuth(self: PointLightHandle, azimuth: number): void;
        setColour(self: PointLightHandle, colour: ColourHandle): void;
        setElevation(self: PointLightHandle, elevation: number): void;
    }
    export const PointLightApi: PointLightApi;

}
