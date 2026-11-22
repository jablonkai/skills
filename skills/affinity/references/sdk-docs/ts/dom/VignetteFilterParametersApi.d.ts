// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VignetteFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VignetteFilterParametersApi {
        create(): VignetteFilterParametersHandle;
        getExposure(self: VignetteFilterParametersHandle): number;
        getHardness(self: VignetteFilterParametersHandle): number;
        getScale(self: VignetteFilterParametersHandle): number;
        getShape(self: VignetteFilterParametersHandle): number;
        setExposure(self: VignetteFilterParametersHandle, exposure: number): void;
        setHardness(self: VignetteFilterParametersHandle, hardness: number): void;
        setScale(self: VignetteFilterParametersHandle, scale: number): void;
        setShape(self: VignetteFilterParametersHandle, shape: number): void;
    }
    export const VignetteFilterParametersApi: VignetteFilterParametersApi;

}
