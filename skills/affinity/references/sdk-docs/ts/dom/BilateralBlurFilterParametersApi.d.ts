// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BilateralBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BilateralBlurFilterParametersApi {
        create(): BilateralBlurFilterParametersHandle;
        getRadius(self: BilateralBlurFilterParametersHandle): number;
        getTolerance(self: BilateralBlurFilterParametersHandle): number;
        setRadius(self: BilateralBlurFilterParametersHandle, radius: number): void;
        setTolerance(self: BilateralBlurFilterParametersHandle, tolerance: number): void;
    }
    export const BilateralBlurFilterParametersApi: BilateralBlurFilterParametersApi;

}
