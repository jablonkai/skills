// Type declarations for the Affinity JavaScript SDK: module "affinity:brushes".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:brushes" {

    import { BlendMode } from "affinity:common";

    export enum BrushDynamicControllerType {
        None,
        Random,
        Pressure,
        Angle,
        Tilt,
        Rotation,
        Cyclic,
        Velocity,
        VelocityInverse,
        Direction,
        Wheel,
        Distance,
    }

    export enum CornerStrategy {
        Pull,
        Fold,
        Overlap,
    }

    export enum PathBrushDynamicControllerType {
        None,
        Pressure,
        Velocity,
        VelocityInverse,
    }

    export enum RasterBrushTextureMode {
        None,
        Nozzle,
        Final,
    }

    export interface BrushDynamicApi {
        clone(self: BrushDynamicHandle): BrushDynamicHandle;
        getControllerType(self: BrushDynamicHandle): BrushDynamicControllerType;
        getDynamicMax(self: BrushDynamicHandle): number;
        getDynamicMin(self: BrushDynamicHandle): number;
        getSpline(self: BrushDynamicHandle): SplineHandle;
        getValue(self: BrushDynamicHandle): number;
        getVariance(self: BrushDynamicHandle): number;
        setControllerType(self: BrushDynamicHandle, controllerType: BrushDynamicControllerType): void;
        setSpline(self: BrushDynamicHandle, spline: SplineHandle): void;
        setValue(self: BrushDynamicHandle, value: number): void;
        setVariance(self: BrushDynamicHandle, variance: number): void;
    }
    export const BrushDynamicApi: BrushDynamicApi;

    export interface PathBrushApi {
        clone(self: PathBrushHandle): PathBrushHandle;
        getBrushWidth(self: PathBrushHandle): number;
        getCornerStrategy(self: PathBrushHandle): CornerStrategy;
        getHeadOffset(self: PathBrushHandle): number;
        getOpacityVariance(self: PathBrushHandle): number;
        getSizeControllerType(self: PathBrushHandle): PathBrushDynamicControllerType;
        getSizeSpline(self: PathBrushHandle): SplineHandle;
        getSizeVariance(self: PathBrushHandle): number;
        getTailOffset(self: PathBrushHandle): number;
        isRepeat(self: PathBrushHandle): boolean;
        setBrushWidth(self: PathBrushHandle, brushWidth: number): void;
        setCornerStrategy(self: PathBrushHandle, cornerStrategy: CornerStrategy): void;
        setHeadOffset(self: PathBrushHandle, headOffset: number): void;
        setIsRepeat(self: PathBrushHandle, repeat: boolean): void;
        setOpacityVariance(self: PathBrushHandle, opacityVariance: number): void;
        setSizeControllerType(self: PathBrushHandle, sizeControllerType: PathBrushDynamicControllerType): void;
        setSizeSpline(self: PathBrushHandle, sizeSpline: SplineHandle): void;
        setSizeVariance(self: PathBrushHandle, sizeVariance: number): void;
        setTailOffset(self: PathBrushHandle, tailOffset: number): void;
    }
    export const PathBrushApi: PathBrushApi;

    export interface RasterBrushApi {
        clone(self: RasterBrushHandle): RasterBrushHandle;
        getAccumulation(self: RasterBrushHandle): BrushDynamicHandle;
        getAngle(self: RasterBrushHandle): BrushDynamicHandle;
        getBlendMode(self: RasterBrushHandle): BlendMode;
        getFlow(self: RasterBrushHandle): BrushDynamicHandle;
        getHardness(self: RasterBrushHandle): BrushDynamicHandle;
        getHueShift(self: RasterBrushHandle): BrushDynamicHandle;
        getLumShift(self: RasterBrushHandle): BrushDynamicHandle;
        getMaskTextureMode(self: RasterBrushHandle): RasterBrushTextureMode;
        getMaskTextureScale(self: RasterBrushHandle): number;
        getOpacity(self: RasterBrushHandle): number;
        getSatShift(self: RasterBrushHandle): BrushDynamicHandle;
        getScatterX(self: RasterBrushHandle): BrushDynamicHandle;
        getScatterY(self: RasterBrushHandle): BrushDynamicHandle;
        getShape(self: RasterBrushHandle): BrushDynamicHandle;
        getShouldApplyWetEdges(self: RasterBrushHandle): boolean;
        getShouldInterpolateTips(self: RasterBrushHandle): boolean;
        getSize(self: RasterBrushHandle): BrushDynamicHandle;
        getSpacing(self: RasterBrushHandle): number;
        getWetEdges(self: RasterBrushHandle): boolean;
        setAccumulation(self: RasterBrushHandle, accumulation: BrushDynamicHandle): void;
        setAngle(self: RasterBrushHandle, angle: BrushDynamicHandle): void;
        setBlendMode(self: RasterBrushHandle, blendMode: BlendMode): void;
        setFlow(self: RasterBrushHandle, flow: BrushDynamicHandle): void;
        setHardness(self: RasterBrushHandle, hardness: BrushDynamicHandle): void;
        setHueShift(self: RasterBrushHandle, hueShift: BrushDynamicHandle): void;
        setLumShift(self: RasterBrushHandle, lumShift: BrushDynamicHandle): void;
        setMaskTextureMode(self: RasterBrushHandle, maskTextureMode: RasterBrushTextureMode): void;
        setMaskTextureScale(self: RasterBrushHandle, maskTextureScale: number): void;
        setOpacity(self: RasterBrushHandle, opacity: number): void;
        setSatShift(self: RasterBrushHandle, satShift: BrushDynamicHandle): void;
        setScatterX(self: RasterBrushHandle, scatterX: BrushDynamicHandle): void;
        setScatterY(self: RasterBrushHandle, scatterY: BrushDynamicHandle): void;
        setShape(self: RasterBrushHandle, shape: BrushDynamicHandle): void;
        setShouldApplyWetEdges(self: RasterBrushHandle, shouldApplyWetEdges: boolean): void;
        setShouldInterpolateTips(self: RasterBrushHandle, shouldInterpolateTips: boolean): void;
        setSize(self: RasterBrushHandle, size: BrushDynamicHandle): void;
        setSpacing(self: RasterBrushHandle, spacing: number): void;
        setWetEdges(self: RasterBrushHandle, wetEdges: boolean): void;
    }
    export const RasterBrushApi: RasterBrushApi;

}
