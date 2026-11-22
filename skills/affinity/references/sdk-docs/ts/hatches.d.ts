// Type declarations for the Affinity JavaScript SDK: module "affinity:hatches".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:hatches" {

    import { EnumerationResult } from "affinity:common";
    import { Point, Vector } from "affinity:geometry";

    export interface HatchLineApi {
        clone(self: HatchLineHandle): HatchLineHandle;
        create(origin: Point, rot: number, step: Vector, pattern: number[]): HatchLineHandle;
        enumeratePattern(self: HatchLineHandle, callback: (dash: number) => EnumerationResult): void;
        getOrigin(self: HatchLineHandle): Point;
        getPatternDash(self: HatchLineHandle, index: number): number;
        getPatternDashCount(self: HatchLineHandle): number;
        getRotation(self: HatchLineHandle): number;
        getStep(self: HatchLineHandle): Vector;
        isSolid(self: HatchLineHandle): boolean;
        setOrigin(self: HatchLineHandle, origin: Point): void;
        setPattern(self: HatchLineHandle, pattern: number[]): void;
        setRotation(self: HatchLineHandle, rotationRads: number): void;
        setStep(self: HatchLineHandle, step: Vector): void;
    }
    export const HatchLineApi: HatchLineApi;

    export interface HatchPatternApi {
        appendHatchLine(self: HatchPatternHandle, hatchLine: HatchLineHandle): void;
        appendHatchLineData(self: HatchPatternHandle, origin: Point, rot: number, step: Vector, pattern: number[]): void;
        clearHatchLines(self: HatchPatternHandle): void;
        clone(self: HatchPatternHandle): HatchPatternHandle;
        createDefault(): HatchPatternHandle;
        createEmpty(): HatchPatternHandle;
        enumerateHatchLines(self: HatchPatternHandle, callback: (hatchLineRef: HatchLineHandle) => EnumerationResult): void;
        eraseHatchLine(self: HatchPatternHandle, index: number): void;
        getHatchLine(self: HatchPatternHandle, index: number): HatchLineHandle;
        getHatchLineCount(self: HatchPatternHandle): number;
        insertHatchLine(self: HatchPatternHandle, index: number, hatchLine: HatchLineHandle): void;
        insertHatchLineData(self: HatchPatternHandle, index: number, origin: Point, rot: number, step: Vector, pattern: number[]): void;
    }
    export const HatchPatternApi: HatchPatternApi;

}
