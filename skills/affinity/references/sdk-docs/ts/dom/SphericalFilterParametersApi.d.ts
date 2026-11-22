// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SphericalFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Point } from "affinity:geometry";

    export interface SphericalFilterParametersApi {
        create(): SphericalFilterParametersHandle;
        getIntensity(self: SphericalFilterParametersHandle): number;
        getPosition(self: SphericalFilterParametersHandle): Point;
        getRadius(self: SphericalFilterParametersHandle): number;
        setIntensity(self: SphericalFilterParametersHandle, intensity: number): void;
        setPosition(self: SphericalFilterParametersHandle, position: Point): void;
        setRadius(self: SphericalFilterParametersHandle, radius: number): void;
    }
    export const SphericalFilterParametersApi: SphericalFilterParametersApi;

}
