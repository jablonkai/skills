// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RadialBlurFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Point } from "affinity:geometry";

    export interface RadialBlurFilterParametersApi {
        create(): RadialBlurFilterParametersHandle;
        getAngle(self: RadialBlurFilterParametersHandle): number;
        getPosition(self: RadialBlurFilterParametersHandle): Point;
        setAngle(self: RadialBlurFilterParametersHandle, angle: number): void;
        setPosition(self: RadialBlurFilterParametersHandle, position: Point): void;
    }
    export const RadialBlurFilterParametersApi: RadialBlurFilterParametersApi;

}
