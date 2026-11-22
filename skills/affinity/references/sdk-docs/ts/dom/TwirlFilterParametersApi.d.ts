// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TwirlFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Point } from "affinity:geometry";

    export interface TwirlFilterParametersApi {
        create(): TwirlFilterParametersHandle;
        getAngle(self: TwirlFilterParametersHandle): number;
        getPosition(self: TwirlFilterParametersHandle): Point;
        getRadius(self: TwirlFilterParametersHandle): number;
        setAngle(self: TwirlFilterParametersHandle, angle: number): void;
        setPosition(self: TwirlFilterParametersHandle, position: Point): void;
        setRadius(self: TwirlFilterParametersHandle, radius: number): void;
    }
    export const TwirlFilterParametersApi: TwirlFilterParametersApi;

}
