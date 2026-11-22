// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LensBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface LensBlurFilterParametersApi {
        create(): LensBlurFilterParametersHandle;
        getBladeCurvature(self: LensBlurFilterParametersHandle): number;
        getBloomColour(self: LensBlurFilterParametersHandle): number;
        getBloomFactor(self: LensBlurFilterParametersHandle): number;
        getBloomThreshold(self: LensBlurFilterParametersHandle): number;
        getNumberOfBlades(self: LensBlurFilterParametersHandle): number;
        getRadius(self: LensBlurFilterParametersHandle): number;
        setBladeCurvature(self: LensBlurFilterParametersHandle, bladeCurvature: number): void;
        setBloomColour(self: LensBlurFilterParametersHandle, bloomColour: number): void;
        setBloomFactor(self: LensBlurFilterParametersHandle, bloomFactor: number): void;
        setBloomThreshold(self: LensBlurFilterParametersHandle, bloomThreshold: number): void;
        setNumberOfBlades(self: LensBlurFilterParametersHandle, numberOfBlades: number): void;
        setRadius(self: LensBlurFilterParametersHandle, radius: number): void;
    }
    export const LensBlurFilterParametersApi: LensBlurFilterParametersApi;

}
