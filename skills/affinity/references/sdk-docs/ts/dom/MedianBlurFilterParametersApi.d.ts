// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MedianBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MedianBlurFilterParametersApi {
        create(): MedianBlurFilterParametersHandle;
        getRadius(self: MedianBlurFilterParametersHandle): number;
        setRadius(self: MedianBlurFilterParametersHandle, radius: number): void;
    }
    export const MedianBlurFilterParametersApi: MedianBlurFilterParametersApi;

}
