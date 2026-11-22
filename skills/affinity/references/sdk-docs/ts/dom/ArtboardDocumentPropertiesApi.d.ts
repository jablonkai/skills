// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ArtboardDocumentPropertiesApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Size } from "affinity:geometry";

    export interface ArtboardDocumentPropertiesApi {
        clone(self: ArtboardDocumentPropertiesHandle): ArtboardDocumentPropertiesHandle;
        create(): ArtboardDocumentPropertiesHandle;
        getAnchorType(self: ArtboardDocumentPropertiesHandle): SpatialAnchor;
        getDimensions(self: ArtboardDocumentPropertiesHandle): Size;
        getDrawingScale(self: ArtboardDocumentPropertiesHandle): DrawingScaleHandle;
        getMargin(self: ArtboardDocumentPropertiesHandle): LTRB;
        getMarginFill(self: ArtboardDocumentPropertiesHandle): FillDescriptorHandle;
        getUseDrawingScale(self: ArtboardDocumentPropertiesHandle): boolean;
        getUseMargin(self: ArtboardDocumentPropertiesHandle): boolean;
        setAnchorType(self: ArtboardDocumentPropertiesHandle, anchorType: SpatialAnchor): void;
        setDimensions(self: ArtboardDocumentPropertiesHandle, dimensions: Size): void;
        setDrawingScale(self: ArtboardDocumentPropertiesHandle, drawingScale: DrawingScaleHandle): void;
        setMargin(self: ArtboardDocumentPropertiesHandle, margin: LTRB): void;
        setMarginFill(self: ArtboardDocumentPropertiesHandle, marginFill: FillDescriptorHandle): void;
        setUseDrawingScale(self: ArtboardDocumentPropertiesHandle, useDrawingScale: boolean): void;
        setUseMargin(self: ArtboardDocumentPropertiesHandle, useMargin: boolean): void;
    }
    export const ArtboardDocumentPropertiesApi: ArtboardDocumentPropertiesApi;

}
