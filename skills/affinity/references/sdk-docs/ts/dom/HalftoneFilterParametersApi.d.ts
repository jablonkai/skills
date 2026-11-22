// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HalftoneFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface HalftoneFilterParametersApi {
        create(): HalftoneFilterParametersHandle;
        getCellSize(self: HalftoneFilterParametersHandle): number;
        getContrast(self: HalftoneFilterParametersHandle): number;
        getDotType(self: HalftoneFilterParametersHandle): HalftoneDotType;
        getGreyComponentReplacement(self: HalftoneFilterParametersHandle): number;
        getScreenAngle(self: HalftoneFilterParametersHandle): number;
        getScreenType(self: HalftoneFilterParametersHandle): HalftoneScreenType;
        getUnderColourRemoval(self: HalftoneFilterParametersHandle): number;
        setCellSize(self: HalftoneFilterParametersHandle, cellSize: number): void;
        setContrast(self: HalftoneFilterParametersHandle, contrast: number): void;
        setDotType(self: HalftoneFilterParametersHandle, dotType: HalftoneDotType): void;
        setGreyComponentReplacement(self: HalftoneFilterParametersHandle, greyComponentReplacement: number): void;
        setScreenAngle(self: HalftoneFilterParametersHandle, screenAngle: number): void;
        setScreenType(self: HalftoneFilterParametersHandle, screenType: HalftoneScreenType): void;
        setUnderColourRemoval(self: HalftoneFilterParametersHandle, underColourRemoval: number): void;
    }
    export const HalftoneFilterParametersApi: HalftoneFilterParametersApi;

}
