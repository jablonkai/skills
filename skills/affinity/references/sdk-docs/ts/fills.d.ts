// Type declarations for the Affinity JavaScript SDK: module "affinity:fills".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:fills" {

    import { BlendMode, UnitType } from "affinity:common";
    import { MeshApi, Point, Transform } from "affinity:geometry";
    import { RasterExtendType, RasterResamplerType } from "affinity:raster";

    export enum DiffusionCurveKind {
        Bezier,
        Ellipse,
        Arc,
        Line,
    }

    export enum DiffusionCurveSide {
        Left,
        Right,
    }

    export enum FillMask {
        None,
        Alpha,
        Noise,
        Intensity,
        All,
    }

    export enum FillType {
        Unknown,
        None,
        Solid,
        Gradient,
        Bitmap,
        Mesh,
        Hatch,
        Diffusion,
    }

    export enum GradientFillType {
        Linear,
        Elliptical,
        Radial,
        Conical,
    }

    export class DiffusionCurveParametric {
        centre: Point;
        radiusX: number;
        radiusY: number;
        rotation: number;
        angle0: number;
        angle1: number;
    }

    export class TransformInfo {
        transform: Transform;
        isAnchoredToSpread: boolean;
    }

    export interface BitmapFillApi extends Omit<FillApi, "clone"> {
        clone(self: BitmapFillHandle): BitmapFillHandle;
        cloneAsBitmapFill(self: BitmapFillHandle): BitmapFillHandle;
        create(bitmap: RasterObjectHandle, extendType: RasterExtendType, resamplerType: RasterResamplerType, ignoreAlpha: boolean): BitmapFillHandle;
        fromFill(fill: FillHandle): BitmapFillHandle;
        getBitmap(self: BitmapFillHandle): RasterObjectHandle;
        getExtendType(self: BitmapFillHandle): RasterExtendType;
        getIsIgnoreAlpha(self: BitmapFillHandle): boolean;
        getIsKOnly(self: BitmapFillHandle): boolean;
        getProfile(self: BitmapFillHandle): ColourProfileHandle;
        getUpsamplerType(self: BitmapFillHandle): RasterResamplerType;
        setExtendType(self: BitmapFillHandle, extendType: RasterExtendType): void;
        setIsKOnly(self: BitmapFillHandle, isKOnly: boolean): void;
        setProfile(self: BitmapFillHandle, colourProfile: ColourProfileHandle): void;
        setUpsamplerType(self: BitmapFillHandle, upsamplerType: RasterResamplerType): void;
    }
    export const BitmapFillApi: BitmapFillApi;

    export interface ColourMeshApi extends Omit<MeshApi, "clone"> {
        clone(self: ColourMeshHandle): ColourMeshHandle;
        cloneAsColourMesh(self: ColourMeshHandle): ColourMeshHandle;
        createDefaultNone(): ColourMeshHandle;
        createDefaultWhite(): ColourMeshHandle;
        createFromColour(colour: ColourHandle, size: number): ColourMeshHandle;
        createFromGradient(gradient: GradientHandle, isRadial: boolean): ColourMeshHandle;
        getNodeColour(self: ColourMeshHandle, xIndex: number, yIndex: number): ColourHandle;
        setNodeColour(self: ColourMeshHandle, xIndex: number, yIndex: number, colourOrNull: ColourHandle | null): void;
    }
    export const ColourMeshApi: ColourMeshApi;

    export interface DiffusionCurveSetApi {
        addArc(self: DiffusionCurveSetHandle, centre: Point, radiusX: number, radiusY: number, rotation: number, angle0: number, angle1: number, leftColourOrNull: ColourHandle | null, rightColourOrNull: ColourHandle | null): void;
        addCurve(self: DiffusionCurveSetHandle, points: Point[], leftColourOrNull: ColourHandle | null, rightColourOrNull: ColourHandle | null): void;
        addEllipse(self: DiffusionCurveSetHandle, centre: Point, radiusX: number, radiusY: number, rotation: number, leftColourOrNull: ColourHandle | null, rightColourOrNull: ColourHandle | null): void;
        addLine(self: DiffusionCurveSetHandle, start: Point, end: Point, leftColourOrNull: ColourHandle | null, rightColourOrNull: ColourHandle | null): void;
        clone(self: DiffusionCurveSetHandle): DiffusionCurveSetHandle;
        create(): DiffusionCurveSetHandle;
        createDefault(colourA: ColourHandle, colourB: ColourHandle): DiffusionCurveSetHandle;
        getBackgroundColour(self: DiffusionCurveSetHandle): ColourHandle;
        getBackgroundStrength(self: DiffusionCurveSetHandle): number;
        getCurveBlur(self: DiffusionCurveSetHandle, index: number): number;
        getCurveColour(self: DiffusionCurveSetHandle, index: number, side: DiffusionCurveSide): ColourHandle;
        getCurveCount(self: DiffusionCurveSetHandle): number;
        getCurveKind(self: DiffusionCurveSetHandle, index: number): DiffusionCurveKind;
        getCurveNodeCount(self: DiffusionCurveSetHandle, index: number): number;
        getCurveNodeSmooth(self: DiffusionCurveSetHandle, index: number, nodeIndex: number): boolean;
        getCurveParametric(self: DiffusionCurveSetHandle, index: number): DiffusionCurveParametric;
        getCurvePoint(self: DiffusionCurveSetHandle, index: number, pointIndex: number): Point;
        getCurvePointCount(self: DiffusionCurveSetHandle, index: number): number;
        getCurvePressure(self: DiffusionCurveSetHandle, index: number): CurveHandle;
        getCurveStrength(self: DiffusionCurveSetHandle, index: number): number;
        removeCurve(self: DiffusionCurveSetHandle, index: number): void;
        setBackgroundColour(self: DiffusionCurveSetHandle, colourOrNull: ColourHandle | null): void;
        setBackgroundStrength(self: DiffusionCurveSetHandle, strength: number): void;
        setCurveArc(self: DiffusionCurveSetHandle, index: number, centre: Point, radiusX: number, radiusY: number, rotation: number, angle0: number, angle1: number): void;
        setCurveBlur(self: DiffusionCurveSetHandle, index: number, blur: number): void;
        setCurveColour(self: DiffusionCurveSetHandle, index: number, side: DiffusionCurveSide, colourOrNull: ColourHandle | null): void;
        setCurveEllipse(self: DiffusionCurveSetHandle, index: number, centre: Point, radiusX: number, radiusY: number, rotation: number): void;
        setCurveLine(self: DiffusionCurveSetHandle, index: number, start: Point, end: Point): void;
        setCurveNodeSmooth(self: DiffusionCurveSetHandle, index: number, nodeIndex: number, smooth: boolean): void;
        setCurvePoints(self: DiffusionCurveSetHandle, index: number, points: Point[]): void;
        setCurvePressure(self: DiffusionCurveSetHandle, index: number, pressureOrNull: CurveHandle | null): void;
        setCurveStrength(self: DiffusionCurveSetHandle, index: number, strength: number): void;
    }
    export const DiffusionCurveSetApi: DiffusionCurveSetApi;

    export interface DiffusionFillApi extends Omit<FillApi, "clone"> {
        clone(self: DiffusionFillHandle): DiffusionFillHandle;
        cloneAsDiffusionFill(self: DiffusionFillHandle): DiffusionFillHandle;
        cloneWithNewCurves(self: DiffusionFillHandle, curveSet: DiffusionCurveSetHandle): DiffusionFillHandle;
        create(curveSet: DiffusionCurveSetHandle): DiffusionFillHandle;
        createDefault(): DiffusionFillHandle;
        fromFill(fill: FillHandle): DiffusionFillHandle;
        getCurves(self: DiffusionFillHandle): DiffusionCurveSetHandle;
    }
    export const DiffusionFillApi: DiffusionFillApi;

    export interface FillApi {
        clone(self: FillHandle): FillHandle;
        cloneAsFill(self: FillHandle): FillHandle;
        getAlpha(self: FillHandle): number;
        getFillType(self: FillHandle): FillType;
        getHasFlatAlpha(self: FillHandle): boolean;
        getHasNoise(self: FillHandle): boolean;
        getHasNonFullAlpha(self: FillHandle): boolean;
        getIntensity(self: FillHandle): number;
        getIsSpatiallyInvariant(self: FillHandle): boolean;
        getIsVisible(self: FillHandle, minAlpha: number): boolean;
        getMeanAlpha(self: FillHandle): number;
        getNoise(self: FillHandle): number;
        getTint(self: FillHandle): number;
        setAlpha(self: FillHandle, alpha: number): void;
        setIntensity(self: FillHandle, intensity: number): void;
        setNoise(self: FillHandle, noise: number): void;
        setTint(self: FillHandle, tint: number): void;
    }
    export const FillApi: FillApi;

    export interface FillDescriptorApi {
        clone(self: FillDescriptorHandle): FillDescriptorHandle;
        cloneWithNewBlendMode(self: FillDescriptorHandle, blendMode: BlendMode): FillDescriptorHandle;
        cloneWithNewFill(self: FillDescriptorHandle, fill: FillHandle): FillDescriptorHandle;
        cloneWithNewIsAnchoredToSpread(self: FillDescriptorHandle, isAnchoredToSpread: boolean): FillDescriptorHandle;
        cloneWithNewIsScaleWithObject(self: FillDescriptorHandle, isScaleWithObject: boolean): FillDescriptorHandle;
        cloneWithNewTransform(self: FillDescriptorHandle, transformOrNull: Transform | null): FillDescriptorHandle;
        cloneWithNewTransformInfo(self: FillDescriptorHandle, transformOrNull: Transform | null, anchoredToSpread: boolean): FillDescriptorHandle;
        create(fill: FillHandle, scaleWithObject: boolean, transformOrNull: Transform | null, blendMode: BlendMode, anchoredToSpread: boolean): FillDescriptorHandle;
        createNone(): FillDescriptorHandle;
        createSolid(solidFill: SolidFillHandle, blendMode: BlendMode): FillDescriptorHandle;
        getBlendMode(self: FillDescriptorHandle): BlendMode;
        getFill(self: FillDescriptorHandle): FillHandle;
        getIsAnchoredToSpread(self: FillDescriptorHandle): boolean;
        getIsScaleWithObject(self: FillDescriptorHandle): boolean;
        getTransform(self: FillDescriptorHandle): Transform;
        getTransformInfo(self: FillDescriptorHandle): TransformInfo;
    }
    export const FillDescriptorApi: FillDescriptorApi;

    export interface GradientFillApi extends Omit<FillApi, "clone"> {
        clone(self: GradientFillHandle): GradientFillHandle;
        cloneAsGradientFill(self: GradientFillHandle): GradientFillHandle;
        cloneWithNewGradient(self: GradientFillHandle, gradient: GradientHandle): GradientFillHandle;
        cloneWithNewGradientFillType(self: GradientFillHandle, gradientFillType: GradientFillType): GradientFillHandle;
        create(gradient: GradientHandle, gradientFillType: GradientFillType): GradientFillHandle;
        createDefault(): GradientFillHandle;
        fromFill(fill: FillHandle): GradientFillHandle;
        getGradient(self: GradientFillHandle): GradientHandle;
        getGradientFillType(self: GradientFillHandle): GradientFillType;
    }
    export const GradientFillApi: GradientFillApi;

    export interface HatchFillApi extends Omit<FillApi, "clone"> {
        clone(self: HatchFillHandle): HatchFillHandle;
        cloneAsHatchFill(self: HatchFillHandle): HatchFillHandle;
        create(hatchPattern: HatchPatternHandle, units: UnitType, penColourOrNull: ColourHandle | null, brushColourOrNull: ColourHandle | null, lineWeight: number): HatchFillHandle;
        fromFill(fill: FillHandle): HatchFillHandle;
        getBrushColour(self: HatchFillHandle): ColourHandle;
        getLineWeight(self: HatchFillHandle): number;
        getPattern(self: HatchFillHandle): HatchPatternHandle;
        getPenColour(self: HatchFillHandle): ColourHandle;
        getUnits(self: HatchFillHandle): UnitType;
        setBrushColour(self: HatchFillHandle, colourOrNull: ColourHandle | null): void;
        setLineWeight(self: HatchFillHandle, lineWeight: number): void;
        setPattern(self: HatchFillHandle, hatchPattern: HatchPatternHandle): void;
        setPenColour(self: HatchFillHandle, colourOrNull: ColourHandle | null): void;
        setUnits(self: HatchFillHandle, unitType: UnitType): void;
    }
    export const HatchFillApi: HatchFillApi;

    export interface MeshFillApi extends Omit<FillApi, "clone"> {
        clone(self: MeshFillHandle): MeshFillHandle;
        cloneAsMeshFill(self: MeshFillHandle): MeshFillHandle;
        create(colourMesh: ColourMeshHandle): MeshFillHandle;
        fromFill(fill: FillHandle): MeshFillHandle;
        getColourMesh(self: MeshFillHandle): ColourMeshHandle;
    }
    export const MeshFillApi: MeshFillApi;

    export interface NoFillApi extends Omit<FillApi, "clone"> {
        clone(self: NoFillHandle): NoFillHandle;
        cloneAsNoFill(self: NoFillHandle): NoFillHandle;
        create(): NoFillHandle;
        fromFill(fill: FillHandle): NoFillHandle;
    }
    export const NoFillApi: NoFillApi;

    export interface SolidFillApi extends Omit<FillApi, "clone"> {
        clone(self: SolidFillHandle): SolidFillHandle;
        cloneAsSolidFill(self: SolidFillHandle): SolidFillHandle;
        create(colour: ColourHandle): SolidFillHandle;
        createDefault(): SolidFillHandle;
        fromFill(fill: FillHandle): SolidFillHandle;
        getColour(self: SolidFillHandle): ColourHandle;
        setColour(self: SolidFillHandle, colour: ColourHandle): void;
    }
    export const SolidFillApi: SolidFillApi;

}
