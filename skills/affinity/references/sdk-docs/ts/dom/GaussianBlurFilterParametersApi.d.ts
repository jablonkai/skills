// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", GaussianBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface GaussianBlurFilterParametersApi {
        create(): GaussianBlurFilterParametersHandle;
        getRadius(self: GaussianBlurFilterParametersHandle): number;
        setRadius(self: GaussianBlurFilterParametersHandle, radius: number): void;
    }
    export const GaussianBlurFilterParametersApi: GaussianBlurFilterParametersApi;

}
