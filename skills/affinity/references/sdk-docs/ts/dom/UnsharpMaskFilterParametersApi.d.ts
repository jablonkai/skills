// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", UnsharpMaskFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface UnsharpMaskFilterParametersApi {
        create(): UnsharpMaskFilterParametersHandle;
        getFactor(self: UnsharpMaskFilterParametersHandle): number;
        getRadius(self: UnsharpMaskFilterParametersHandle): number;
        getThreshold(self: UnsharpMaskFilterParametersHandle): number;
        setFactor(self: UnsharpMaskFilterParametersHandle, factor: number): void;
        setRadius(self: UnsharpMaskFilterParametersHandle, radius: number): void;
        setThreshold(self: UnsharpMaskFilterParametersHandle, threshold: number): void;
    }
    export const UnsharpMaskFilterParametersApi: UnsharpMaskFilterParametersApi;

}
