// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PinchPunchFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Point } from "affinity:geometry";

    export interface PinchPunchFilterParametersApi {
        create(): PinchPunchFilterParametersHandle;
        getIntensity(self: PinchPunchFilterParametersHandle): number;
        getPosition(self: PinchPunchFilterParametersHandle): Point;
        getRadius(self: PinchPunchFilterParametersHandle): number;
        setIntensity(self: PinchPunchFilterParametersHandle, intensity: number): void;
        setPosition(self: PinchPunchFilterParametersHandle, position: Point): void;
        setRadius(self: PinchPunchFilterParametersHandle, radius: number): void;
    }
    export const PinchPunchFilterParametersApi: PinchPunchFilterParametersApi;

}
