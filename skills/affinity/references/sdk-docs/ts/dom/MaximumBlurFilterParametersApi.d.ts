// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MaximumBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MaximumBlurFilterParametersApi {
        create(): MaximumBlurFilterParametersHandle;
        getIsCircular(self: MaximumBlurFilterParametersHandle): boolean;
        getRadius(self: MaximumBlurFilterParametersHandle): number;
        setIsCircular(self: MaximumBlurFilterParametersHandle, isCircular: boolean): void;
        setRadius(self: MaximumBlurFilterParametersHandle, radius: number): void;
    }
    export const MaximumBlurFilterParametersApi: MaximumBlurFilterParametersApi;

}
