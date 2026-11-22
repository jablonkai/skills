// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PageDocumentPropertiesApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Size } from "affinity:geometry";

    export interface PageDocumentPropertiesApi {
        clone(self: PageDocumentPropertiesHandle): PageDocumentPropertiesHandle;
        create(): PageDocumentPropertiesHandle;
        getAnchorType(self: PageDocumentPropertiesHandle): SpatialAnchor;
        getDimensions(self: PageDocumentPropertiesHandle): Size;
        getMargin(self: PageDocumentPropertiesHandle): LTRB;
        getMarginFill(self: PageDocumentPropertiesHandle): FillDescriptorHandle;
        getMoveFollowingPages(self: PageDocumentPropertiesHandle): boolean;
        getPageOriginDelta(self: PageDocumentPropertiesHandle): PageOriginDelta;
        getUseMargin(self: PageDocumentPropertiesHandle): boolean;
        getUseMasterMargin(self: PageDocumentPropertiesHandle): boolean;
        setAnchorType(self: PageDocumentPropertiesHandle, anchorType: SpatialAnchor): void;
        setDimensions(self: PageDocumentPropertiesHandle, dimensions: Size): void;
        setMargin(self: PageDocumentPropertiesHandle, margin: LTRB): void;
        setMarginFill(self: PageDocumentPropertiesHandle, marginFill: FillDescriptorHandle): void;
        setMoveFollowingPages(self: PageDocumentPropertiesHandle, moveFollowingPages: boolean): void;
        setPageOriginDelta(self: PageDocumentPropertiesHandle, pageOriginDelta: PageOriginDelta): void;
        setUseMargin(self: PageDocumentPropertiesHandle, useMargin: boolean): void;
        setUseMasterMargin(self: PageDocumentPropertiesHandle, useMasterMargin: boolean): void;
    }
    export const PageDocumentPropertiesApi: PageDocumentPropertiesApi;

}
