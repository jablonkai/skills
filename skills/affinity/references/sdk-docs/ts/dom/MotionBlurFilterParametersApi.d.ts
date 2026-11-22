// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MotionBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MotionBlurFilterParametersApi {
        create(): MotionBlurFilterParametersHandle;
        getAngle(self: MotionBlurFilterParametersHandle): number;
        getRadius(self: MotionBlurFilterParametersHandle): number;
        setAngle(self: MotionBlurFilterParametersHandle, angle: number): void;
        setRadius(self: MotionBlurFilterParametersHandle, radius: number): void;
    }
    export const MotionBlurFilterParametersApi: MotionBlurFilterParametersApi;

}
