// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SpreadDocumentPropertiesApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { RasterResamplerType } from "affinity:raster";

    export interface SpreadDocumentPropertiesApi extends Omit<ArtboardDocumentPropertiesApi, "clone" | "create"> {
        clone(self: SpreadDocumentPropertiesHandle): SpreadDocumentPropertiesHandle;
        create(): SpreadDocumentPropertiesHandle;
        getReflowPages(self: SpreadDocumentPropertiesHandle): boolean;
        getResamplerType(self: SpreadDocumentPropertiesHandle): RasterResamplerType;
        getUseMasterDrawingScale(self: SpreadDocumentPropertiesHandle): boolean;
        getUseMasterMargin(self: SpreadDocumentPropertiesHandle): boolean;
        setReflowPages(self: SpreadDocumentPropertiesHandle, reflowPages: boolean): void;
        setResamplerType(self: SpreadDocumentPropertiesHandle, resamplerType: RasterResamplerType): void;
        setUseMasterDrawingScale(self: SpreadDocumentPropertiesHandle, useMasterDrawingScale: boolean): void;
        setUseMasterMargin(self: SpreadDocumentPropertiesHandle, useMasterMargin: boolean): void;
    }
    export const SpreadDocumentPropertiesApi: SpreadDocumentPropertiesApi;

}
