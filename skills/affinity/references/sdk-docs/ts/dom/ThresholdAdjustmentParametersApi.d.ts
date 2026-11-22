// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ThresholdAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ThresholdAdjustmentParametersApi {
        create(): ThresholdAdjustmentParametersHandle;
        getThreshold(self: ThresholdAdjustmentParametersHandle): number;
        setThreshold(self: ThresholdAdjustmentParametersHandle, threshold: number): void;
    }
    export const ThresholdAdjustmentParametersApi: ThresholdAdjustmentParametersApi;

}
