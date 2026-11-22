// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RecolourAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RecolourAdjustmentParametersApi {
        create(): RecolourAdjustmentParametersHandle;
        getHue(self: RecolourAdjustmentParametersHandle): number;
        getLightness(self: RecolourAdjustmentParametersHandle): number;
        getSaturation(self: RecolourAdjustmentParametersHandle): number;
        setHue(self: RecolourAdjustmentParametersHandle, hue: number): void;
        setLightness(self: RecolourAdjustmentParametersHandle, lightness: number): void;
        setSaturation(self: RecolourAdjustmentParametersHandle, saturation: number): void;
    }
    export const RecolourAdjustmentParametersApi: RecolourAdjustmentParametersApi;

}
