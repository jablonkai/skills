// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ToneCompressionAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ToneCompressionAdjustmentParametersApi {
        create(): ToneCompressionAdjustmentParametersHandle;
        getColour(self: ToneCompressionAdjustmentParametersHandle): number;
        getExposure(self: ToneCompressionAdjustmentParametersHandle): number;
        getGamma(self: ToneCompressionAdjustmentParametersHandle): number;
        getMethod(self: ToneCompressionAdjustmentParametersHandle): ToneCompressionMethod;
        setColour(self: ToneCompressionAdjustmentParametersHandle, colour: number): void;
        setExposure(self: ToneCompressionAdjustmentParametersHandle, exposure: number): void;
        setGamma(self: ToneCompressionAdjustmentParametersHandle, gamma: number): void;
        setMethod(self: ToneCompressionAdjustmentParametersHandle, method: ToneCompressionMethod): void;
    }
    export const ToneCompressionAdjustmentParametersApi: ToneCompressionAdjustmentParametersApi;

}
