// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CurvesAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface CurvesAdjustmentParametersApi {
        create(): CurvesAdjustmentParametersHandle;
        enumerateChannelSplines(self: CurvesAdjustmentParametersHandle, callback: (channel: number, spline: SplineHandle) => EnumerationResult): void;
        getChannelSpline(self: CurvesAdjustmentParametersHandle, channel: number): SplineHandle;
        getChannelSplineCount(self: CurvesAdjustmentParametersHandle): number;
        getMasterSpline(self: CurvesAdjustmentParametersHandle): SplineHandle;
        getMax(self: CurvesAdjustmentParametersHandle): number;
        getMin(self: CurvesAdjustmentParametersHandle): number;
        setChannelSpline(self: CurvesAdjustmentParametersHandle, channel: number, spline: SplineHandle): void;
        setMasterSpline(self: CurvesAdjustmentParametersHandle, spline: SplineHandle): void;
        setMax(self: CurvesAdjustmentParametersHandle, max: number): void;
        setMin(self: CurvesAdjustmentParametersHandle, min: number): void;
    }
    export const CurvesAdjustmentParametersApi: CurvesAdjustmentParametersApi;

}
