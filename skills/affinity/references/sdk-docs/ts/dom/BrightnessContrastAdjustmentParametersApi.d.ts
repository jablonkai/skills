// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BrightnessContrastAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BrightnessContrastAdjustmentParametersApi {
        create(): BrightnessContrastAdjustmentParametersHandle;
        getBrightness(self: BrightnessContrastAdjustmentParametersHandle): number;
        getContrast(self: BrightnessContrastAdjustmentParametersHandle): number;
        getIsLinear(self: BrightnessContrastAdjustmentParametersHandle): boolean;
        setBrightness(self: BrightnessContrastAdjustmentParametersHandle, brightness: number): void;
        setContrast(self: BrightnessContrastAdjustmentParametersHandle, contrast: number): void;
        setIsLinear(self: BrightnessContrastAdjustmentParametersHandle, isLinear: boolean): void;
    }
    export const BrightnessContrastAdjustmentParametersApi: BrightnessContrastAdjustmentParametersApi;

}
