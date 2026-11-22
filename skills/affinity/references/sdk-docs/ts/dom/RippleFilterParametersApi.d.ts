// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RippleFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Point } from "affinity:geometry";

    export interface RippleFilterParametersApi {
        create(): RippleFilterParametersHandle;
        getIntensity(self: RippleFilterParametersHandle): number;
        getPosition(self: RippleFilterParametersHandle): Point;
        setIntensity(self: RippleFilterParametersHandle, intensity: number): void;
        setPosition(self: RippleFilterParametersHandle, position: Point): void;
    }
    export const RippleFilterParametersApi: RippleFilterParametersApi;

}
