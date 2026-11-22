// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MinimumBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MinimumBlurFilterParametersApi {
        create(): MinimumBlurFilterParametersHandle;
        getIsCircular(self: MinimumBlurFilterParametersHandle): boolean;
        getRadius(self: MinimumBlurFilterParametersHandle): number;
        setIsCircular(self: MinimumBlurFilterParametersHandle, isCircular: boolean): void;
        setRadius(self: MinimumBlurFilterParametersHandle, radius: number): void;
    }
    export const MinimumBlurFilterParametersApi: MinimumBlurFilterParametersApi;

}
