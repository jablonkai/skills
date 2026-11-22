// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DocumentPropertiesApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { UnitType } from "affinity:common";
    import { Size } from "affinity:geometry";
    import { RasterFormat, RasterResamplerType } from "affinity:raster";

    export interface DocumentPropertiesApi {
        clone(self: DocumentPropertiesHandle): DocumentPropertiesHandle;
        create(): DocumentPropertiesHandle;
        getAssignColourProfile(self: DocumentPropertiesHandle): boolean;
        getBleed(self: DocumentPropertiesHandle): LTRB;
        getBleedFill(self: DocumentPropertiesHandle): FillDescriptorHandle;
        getColourFormat(self: DocumentPropertiesHandle): RasterFormat;
        getColourProfile(self: DocumentPropertiesHandle): ColourProfileHandle;
        getDimensions(self: DocumentPropertiesHandle): Size;
        getDpi(self: DocumentPropertiesHandle): number;
        getDrawingScale(self: DocumentPropertiesHandle): DrawingScaleHandle;
        getImageResourcePolicy(self: DocumentPropertiesHandle): ImagePlacement;
        getIsFacingPages(self: DocumentPropertiesHandle): boolean;
        getIsFullSpreadStart(self: DocumentPropertiesHandle): boolean;
        getIsTransparent(self: DocumentPropertiesHandle): boolean;
        getIsVerticalStack(self: DocumentPropertiesHandle): boolean;
        getLinkTextFiles(self: DocumentPropertiesHandle): boolean;
        getPreserveTextStyles(self: DocumentPropertiesHandle): boolean;
        getResamplerType(self: DocumentPropertiesHandle): RasterResamplerType;
        getShouldReflowPages(self: DocumentPropertiesHandle): boolean;
        getUnits(self: DocumentPropertiesHandle): UnitType;
        setAssignColourProfile(self: DocumentPropertiesHandle, assignColourProfile: boolean): void;
        setBleed(self: DocumentPropertiesHandle, bleed: LTRB): void;
        setBleedFill(self: DocumentPropertiesHandle, bleedFill: FillDescriptorHandle): void;
        setColourFormatAndProfile(self: DocumentPropertiesHandle, format: RasterFormat, colourProfile: ColourProfileHandle): void;
        setDimensions(self: DocumentPropertiesHandle, dimensions: Size): void;
        setDpi(self: DocumentPropertiesHandle, dpi: number): void;
        setDrawingScale(self: DocumentPropertiesHandle, drawingScale: DrawingScaleHandle): void;
        setImageResourcePolicy(self: DocumentPropertiesHandle, imageResourcePolicy: ImagePlacement): void;
        setIsFacingPages(self: DocumentPropertiesHandle, isFacingPages: boolean): void;
        setIsFullSpreadStart(self: DocumentPropertiesHandle, isFullSpreadStart: boolean): void;
        setIsTransparent(self: DocumentPropertiesHandle, isTransparent: boolean): void;
        setIsVerticalStack(self: DocumentPropertiesHandle, isVerticalStack: boolean): void;
        setLinkTextFiles(self: DocumentPropertiesHandle, linkTextFiles: boolean): void;
        setPreserveTextStyles(self: DocumentPropertiesHandle, preserveTextStyles: boolean): void;
        setResamplerType(self: DocumentPropertiesHandle, resamplerType: RasterResamplerType): void;
        setShouldReflowPages(self: DocumentPropertiesHandle, shouldReflowPages: boolean): void;
        setUnits(self: DocumentPropertiesHandle, unitType: UnitType): void;
    }
    export const DocumentPropertiesApi: DocumentPropertiesApi;

}
