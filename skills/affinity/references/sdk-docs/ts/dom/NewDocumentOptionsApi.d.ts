// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", NewDocumentOptionsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { UnitType } from "affinity:common";
    import { RasterFormat } from "affinity:raster";

    export interface NewDocumentOptionsApi {
        clone(self: NewDocumentOptionsHandle): NewDocumentOptionsHandle;
        createDefault(): NewDocumentOptionsHandle;
        createFromPreset(preset: DocumentPresetHandle): NewDocumentOptionsHandle;
        getBleed(self: NewDocumentOptionsHandle): LTRB;
        getColourProfile(self: NewDocumentOptionsHandle): ColourProfileHandle;
        getCreateArtboard(self: NewDocumentOptionsHandle): boolean;
        getCreateMaster(self: NewDocumentOptionsHandle): boolean;
        getDpi(self: NewDocumentOptionsHandle): number;
        getDrawingScale(self: NewDocumentOptionsHandle): DrawingScaleHandle;
        getHeight(self: NewDocumentOptionsHandle): number;
        getImagePlacement(self: NewDocumentOptionsHandle): ImagePlacement;
        getIsDoublePageStart(self: NewDocumentOptionsHandle): boolean;
        getIsFacing(self: NewDocumentOptionsHandle): boolean;
        getIsMultiPage(self: NewDocumentOptionsHandle): boolean;
        getIsTransparentBackground(self: NewDocumentOptionsHandle): boolean;
        getIsVerticalStack(self: NewDocumentOptionsHandle): boolean;
        getMargins(self: NewDocumentOptionsHandle): LTRB;
        getMarginsEnabled(self: NewDocumentOptionsHandle): boolean;
        getMaxDpi(unit: UnitType, dimension: number): number;
        getMaxSize(unit: UnitType, dpi: number): number;
        getPageCount(self: NewDocumentOptionsHandle): number;
        getRasterFormat(self: NewDocumentOptionsHandle): RasterFormat;
        getUnits(self: NewDocumentOptionsHandle): UnitType;
        getUseDrawingScale(self: NewDocumentOptionsHandle): boolean;
        getViewDpi(self: NewDocumentOptionsHandle): number;
        getWidth(self: NewDocumentOptionsHandle): number;
        setBleed(self: NewDocumentOptionsHandle, bleed: LTRB): void;
        setColourProfile(self: NewDocumentOptionsHandle, colourProfile: ColourProfileHandle): void;
        setCreateArtboard(self: NewDocumentOptionsHandle, createArtboard: boolean): void;
        setCreateMaster(self: NewDocumentOptionsHandle, createMaster: boolean): void;
        setDpi(self: NewDocumentOptionsHandle, dpi: number): void;
        setDrawingScale(self: NewDocumentOptionsHandle, drawingScale: DrawingScaleHandle): void;
        setHeight(self: NewDocumentOptionsHandle, height: number): void;
        setImagePlacement(self: NewDocumentOptionsHandle, imagePlacement: ImagePlacement): void;
        setIsDoublePageStart(self: NewDocumentOptionsHandle, isDoublePageStart: boolean): void;
        setIsFacing(self: NewDocumentOptionsHandle, isFacing: boolean): void;
        setIsMultiPage(self: NewDocumentOptionsHandle, isMultiPage: boolean): void;
        setIsTransparentBackground(self: NewDocumentOptionsHandle, isTransparent: boolean): void;
        setIsVerticalStack(self: NewDocumentOptionsHandle, isVerticalStack: boolean): void;
        setMargins(self: NewDocumentOptionsHandle, margins: LTRB): void;
        setMarginsEnabled(self: NewDocumentOptionsHandle, marginsEnabled: boolean): void;
        setPageCount(self: NewDocumentOptionsHandle, pageCount: number): void;
        setRasterFormat(self: NewDocumentOptionsHandle, format: RasterFormat): void;
        setUnits(self: NewDocumentOptionsHandle, unitType: UnitType): void;
        setUseDrawingScale(self: NewDocumentOptionsHandle, useDrawingScale: boolean): void;
        setViewDpi(self: NewDocumentOptionsHandle, viewDpi: number): void;
        setWidth(self: NewDocumentOptionsHandle, width: number): void;
    }
    export const NewDocumentOptionsApi: NewDocumentOptionsApi;

}
