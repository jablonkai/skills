// Type declarations for the Affinity JavaScript SDK: module "affinity:linestyles".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:linestyles" {

    import { Rectangle, Transform } from "affinity:geometry";

    export enum ArrowHeadStyle {
        Triangle,
        TriangleTall,
        TriangleWide,
        Curved,
        Barbed,
        Simple,
        SimpleTall,
        SimpleWide,
        SimpleClosed,
        SimpleClosedTall,
        SimpleClosedWide,
        Circle,
        CircleSolid,
        Square,
        SquareSolid,
        Bar,
        Oblique,
        Oblique_Alternate,
        Origin,
        Origin_Alternate,
        Datum_60_Blank,
        Datum_60_Filled,
        Datum_45_Blank,
        Datum_45_Filled,
        Affinity,
    }

    export enum LineCap {
        Butt,
        Square,
        Round,
    }

    export enum LineJoin {
        MiterLegacy,
        Miter,
        Round,
        Bevel,
    }

    export enum LineStyleMask {
        Type,
        ScaledWeight,
        Brush,
        Cap,
        Join,
        Miter,
        DashPattern,
        DashPhase,
        Weight,
        BalancedDashes,
        Order,
        Scale,
        ArrowHeadFront,
        ArrowHeadBack,
        ArrowHeadPlacement,
        ArrowHeadFrontScale,
        ArrowHeadBackScale,
        Pressure,
        All,
    }

    export enum LineType {
        None,
        Solid,
        Dash,
        Texture,
    }

    export enum StrokeAlignment {
        Centre,
        Inside,
        Outside,
    }

    export interface ArrowHeadApi {
        clone(self: ArrowHeadHandle): ArrowHeadHandle;
        create(style: ArrowHeadStyle, anchorInternal: number, anchorExternal: number, isSolidLine: boolean, scaleX: number, scaleY: number): ArrowHeadHandle;
        createDefault(style: ArrowHeadStyle): ArrowHeadHandle;
        getAnchor(self: ArrowHeadHandle, isInternal: boolean): number;
        getBounds(self: ArrowHeadHandle): Rectangle;
        getCurves(self: ArrowHeadHandle): PolyPolyCurveHandle;
        getScaleX(self: ArrowHeadHandle): number;
        getScaleY(self: ArrowHeadHandle): number;
        isFilled(self: ArrowHeadHandle): boolean;
        isOutlined(self: ArrowHeadHandle): boolean;
        isSolidLine(self: ArrowHeadHandle): boolean;
        setAnchor(self: ArrowHeadHandle, isInternal: boolean, anchor: number): void;
        setScaleX(self: ArrowHeadHandle, scale: number): void;
        setScaleY(self: ArrowHeadHandle, scale: number): void;
        setSolidLine(self: ArrowHeadHandle, isSolidLine: boolean): void;
    }
    export const ArrowHeadApi: ArrowHeadApi;

    export interface LineStyleApi {
        clone(self: LineStyleHandle): LineStyleHandle;
        create(cap: LineCap, join: LineJoin, type: LineType, weight: number, miterLimit: number, dashPhase: number, dashPattern: number[], isResolutionIndependent: boolean, isBalancedDashes: boolean, pathBrushOrNull: PathBrushHandle | null): LineStyleHandle;
        createDefault(): LineStyleHandle;
        createDefaultWithWeight(weight: number): LineStyleHandle;
        getCap(self: LineStyleHandle): LineCap;
        getDashPattern(self: LineStyleHandle): number[];
        getDashPatternLength(self: LineStyleHandle): number;
        getDashPhase(self: LineStyleHandle): number;
        getJoin(self: LineStyleHandle): LineJoin;
        getMiterLimit(self: LineStyleHandle): number;
        getPathBrush(self: LineStyleHandle): PathBrushHandle;
        getType(self: LineStyleHandle): LineType;
        getWeight(self: LineStyleHandle): number;
        hasBalancedDashes(self: LineStyleHandle): boolean;
        isResolutionIndependent(self: LineStyleHandle): boolean;
        setCap(self: LineStyleHandle, cap: LineCap): void;
        setDashPattern(self: LineStyleHandle, dashPattern: number[]): void;
        setDashPhase(self: LineStyleHandle, dashPhase: number): void;
        setHasBalancedDashes(self: LineStyleHandle, hasBalancedDashes: boolean): void;
        setIsResolutionIndependent(self: LineStyleHandle, isResolutionIndependent: boolean): void;
        setJoin(self: LineStyleHandle, join: LineJoin): void;
        setMiterLimit(self: LineStyleHandle, miterLimit: number): void;
        setPathBrush(self: LineStyleHandle, pathBrush: PathBrushHandle): void;
        setType(self: LineStyleHandle, type: LineType): void;
        setWeight(self: LineStyleHandle, weight: number): void;
    }
    export const LineStyleApi: LineStyleApi;

    export interface LineStyleDescriptorApi {
        clone(self: LineStyleDescriptorHandle): LineStyleDescriptorHandle;
        cloneScaled(self: LineStyleDescriptorHandle, scale: number): LineStyleDescriptorHandle;
        cloneWithNewArrowHeads(self: LineStyleDescriptorHandle, frontArrowOrNull: ArrowHeadHandle | null, backArrowOrNull: ArrowHeadHandle | null): LineStyleDescriptorHandle;
        cloneWithNewLineStyle(self: LineStyleDescriptorHandle, lineStyle: LineStyleHandle): LineStyleDescriptorHandle;
        create(lineStyle: LineStyleHandle, frontArrowOrNull: ArrowHeadHandle | null, backArrowOrNull: ArrowHeadHandle | null, pressureOrNull: CurveHandle | null, isBehind: boolean, isScale: boolean, strokeAlignment: StrokeAlignment): LineStyleDescriptorHandle;
        createDefault(): LineStyleDescriptorHandle;
        createDefaultWithWeight(weight: number): LineStyleDescriptorHandle;
        getBackArrowHead(self: LineStyleDescriptorHandle): ArrowHeadHandle;
        getEffectiveWeight(self: LineStyleDescriptorHandle, worldTransform: Transform, scalarTransform: Transform): number;
        getFrontArrowHead(self: LineStyleDescriptorHandle): ArrowHeadHandle;
        getLineStyle(self: LineStyleDescriptorHandle): LineStyleHandle;
        getPressure(self: LineStyleDescriptorHandle): CurveHandle;
        getStrokeAlignment(self: LineStyleDescriptorHandle): StrokeAlignment;
        isBehind(self: LineStyleDescriptorHandle): boolean;
        isScale(self: LineStyleDescriptorHandle): boolean;
    }
    export const LineStyleDescriptorApi: LineStyleDescriptorApi;

}
