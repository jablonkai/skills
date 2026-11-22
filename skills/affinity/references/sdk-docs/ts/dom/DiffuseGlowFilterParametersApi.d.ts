// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DiffuseGlowFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DiffuseGlowFilterParametersApi {
        create(): DiffuseGlowFilterParametersHandle;
        getIntensity(self: DiffuseGlowFilterParametersHandle): number;
        getOpacity(self: DiffuseGlowFilterParametersHandle): number;
        getRadius(self: DiffuseGlowFilterParametersHandle): number;
        getThreshold(self: DiffuseGlowFilterParametersHandle): number;
        setIntensity(self: DiffuseGlowFilterParametersHandle, intensity: number): void;
        setOpacity(self: DiffuseGlowFilterParametersHandle, opacity: number): void;
        setRadius(self: DiffuseGlowFilterParametersHandle, radius: number): void;
        setThreshold(self: DiffuseGlowFilterParametersHandle, threshold: number): void;
    }
    export const DiffuseGlowFilterParametersApi: DiffuseGlowFilterParametersApi;

}
