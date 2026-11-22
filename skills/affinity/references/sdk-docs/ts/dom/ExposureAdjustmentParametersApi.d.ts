// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ExposureAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ExposureAdjustmentParametersApi {
        create(): ExposureAdjustmentParametersHandle;
        getExposure(self: ExposureAdjustmentParametersHandle): number;
        setExposure(self: ExposureAdjustmentParametersHandle, exposure: number): void;
    }
    export const ExposureAdjustmentParametersApi: ExposureAdjustmentParametersApi;

}
