// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VibranceAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VibranceAdjustmentParametersApi {
        create(): VibranceAdjustmentParametersHandle;
        getSaturation(self: VibranceAdjustmentParametersHandle): number;
        getVibrance(self: VibranceAdjustmentParametersHandle): number;
        setSaturation(self: VibranceAdjustmentParametersHandle, saturation: number): void;
        setVibrance(self: VibranceAdjustmentParametersHandle, vibrance: number): void;
    }
    export const VibranceAdjustmentParametersApi: VibranceAdjustmentParametersApi;

}
