// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ExportScaleApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ExportScaleApi {
        createWithHeight(height: number): ExportScaleHandle;
        createWithMultiplier(multiplier: number): ExportScaleHandle;
        createWithMultiplierSquare(multiplier: number, size: number): ExportScaleHandle;
        createWithPreset(scalePreset: ExportScalePreset): ExportScaleHandle;
        createWithSquare(size: number): ExportScaleHandle;
        createWithWidth(width: number): ExportScaleHandle;
        createWithWidthHeight(width: number, height: number): ExportScaleHandle;
        getHeight(self: ExportScaleHandle): number;
        getMultiplier(self: ExportScaleHandle): number;
        getSize(self: ExportScaleHandle): number;
        getSizeType(self: ExportScaleHandle): ExportScaleSizeType;
        getWidth(self: ExportScaleHandle): number;
        hasMultiplier(self: ExportScaleHandle): boolean;
    }
    export const ExportScaleApi: ExportScaleApi;

}
