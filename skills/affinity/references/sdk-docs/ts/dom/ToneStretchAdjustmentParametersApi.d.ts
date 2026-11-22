// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ToneStretchAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ToneStretchAdjustmentParametersApi {
        create(): ToneStretchAdjustmentParametersHandle;
        getCompression(self: ToneStretchAdjustmentParametersHandle): number;
        getGamma(self: ToneStretchAdjustmentParametersHandle): number;
        getMethod(self: ToneStretchAdjustmentParametersHandle): ToneStretchMethod;
        getStretchFactor(self: ToneStretchAdjustmentParametersHandle): number;
        setCompression(self: ToneStretchAdjustmentParametersHandle, compression: number): void;
        setGamma(self: ToneStretchAdjustmentParametersHandle, gamma: number): void;
        setMethod(self: ToneStretchAdjustmentParametersHandle, method: ToneStretchMethod): void;
        setStretchFactor(self: ToneStretchAdjustmentParametersHandle, stretchFactor: number): void;
    }
    export const ToneStretchAdjustmentParametersApi: ToneStretchAdjustmentParametersApi;

}
