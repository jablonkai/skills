// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DefringeFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DefringeFilterParametersApi {
        create(): DefringeFilterParametersHandle;
        getEdgeBrightnessThreshold(self: DefringeFilterParametersHandle): number;
        getHue(self: DefringeFilterParametersHandle): number;
        getRadius(self: DefringeFilterParametersHandle): number;
        getRemoveComplementary(self: DefringeFilterParametersHandle): boolean;
        getTolerance(self: DefringeFilterParametersHandle): number;
        setEdgeBrightnessThreshold(self: DefringeFilterParametersHandle, edgeBrightnessThreshold: number): void;
        setHue(self: DefringeFilterParametersHandle, hue: number): void;
        setRadius(self: DefringeFilterParametersHandle, radius: number): void;
        setRemoveComplementary(self: DefringeFilterParametersHandle, removeComplementary: boolean): void;
        setTolerance(self: DefringeFilterParametersHandle, tolerance: number): void;
    }
    export const DefringeFilterParametersApi: DefringeFilterParametersApi;

}
