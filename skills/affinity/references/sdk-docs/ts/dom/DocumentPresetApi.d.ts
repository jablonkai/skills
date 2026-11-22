// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DocumentPresetApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult, UnitType } from "affinity:common";
    import { RasterFormat } from "affinity:raster";

    export interface DocumentPresetApi {
        enumerateAll(callback: (self: DocumentPresetHandle) => EnumerationResult): void;
        getBleed(self: DocumentPresetHandle): LTRB;
        getColourProfileName(self: DocumentPresetHandle): string;
        getCreateArtboard(self: DocumentPresetHandle): boolean;
        getDoublePageStart(self: DocumentPresetHandle): boolean;
        getDpi(self: DocumentPresetHandle): number;
        getDrawingScale(self: DocumentPresetHandle): DrawingScaleHandle;
        getFacing(self: DocumentPresetHandle): boolean;
        getHeight(self: DocumentPresetHandle): number;
        getImagePlacement(self: DocumentPresetHandle): ImagePlacement;
        getIsFavourite(self: DocumentPresetHandle): boolean;
        getIsMultiPage(self: DocumentPresetHandle): boolean;
        getIsTransparentBackground(self: DocumentPresetHandle): boolean;
        getMargins(self: DocumentPresetHandle): LTRB;
        getMarginsEnabled(self: DocumentPresetHandle): boolean;
        getName(self: DocumentPresetHandle): string;
        getRasterFormat(self: DocumentPresetHandle): RasterFormat;
        getUnits(self: DocumentPresetHandle): UnitType;
        getUseDrawingScale(self: DocumentPresetHandle): boolean;
        getVerticalStack(self: DocumentPresetHandle): boolean;
        getViewDpi(self: DocumentPresetHandle): number;
        getWidth(self: DocumentPresetHandle): number;
    }
    export const DocumentPresetApi: DocumentPresetApi;

}
