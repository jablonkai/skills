// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BoxBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BoxBlurFilterParametersApi {
        create(): BoxBlurFilterParametersHandle;
        getRadius(self: BoxBlurFilterParametersHandle): number;
        setRadius(self: BoxBlurFilterParametersHandle, radius: number): void;
    }
    export const BoxBlurFilterParametersApi: BoxBlurFilterParametersApi;

}
