// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DepthOfFieldFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DepthOfFieldFilterParametersApi {
        create(): DepthOfFieldFilterParametersHandle;
        getClarity(self: DepthOfFieldFilterParametersHandle): number;
        getEllipticalParams(self: DepthOfFieldFilterParametersHandle): EllipticalDepthOfFieldParameters;
        getMode(self: DepthOfFieldFilterParametersHandle): DepthOfFieldMode;
        getRadius(self: DepthOfFieldFilterParametersHandle): number;
        getTiltShiftParams(self: DepthOfFieldFilterParametersHandle): TiltShiftDepthOfFieldParameters;
        getVibrance(self: DepthOfFieldFilterParametersHandle): number;
        setClarity(self: DepthOfFieldFilterParametersHandle, clarity: number): void;
        setEllipticalParams(self: DepthOfFieldFilterParametersHandle, params: EllipticalDepthOfFieldParameters): void;
        setRadius(self: DepthOfFieldFilterParametersHandle, radius: number): void;
        setTiltShiftParams(self: DepthOfFieldFilterParametersHandle, params: TiltShiftDepthOfFieldParameters): void;
        setVibrance(self: DepthOfFieldFilterParametersHandle, vibrance: number): void;
    }
    export const DepthOfFieldFilterParametersApi: DepthOfFieldFilterParametersApi;

}
