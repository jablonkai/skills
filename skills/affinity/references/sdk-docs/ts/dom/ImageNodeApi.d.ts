// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ImageNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { RasterExtendType, RasterResamplerType } from "affinity:raster";

    export interface ImageNodeApi extends Omit<VectorNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ImageNodeHandle;
        getBitmapBrushFillDescriptor(self: ImageNodeHandle): FillDescriptorHandle;
        getExtendType(self: ImageNodeHandle): RasterExtendType;
        getImageResourceInterface(self: ImageNodeHandle): ImageResourceInterfaceHandle;
        getLastRendered(self: ImageNodeHandle): number;
        getRasterInterface(self: ImageNodeHandle): RasterInterfaceHandle;
        getStockAuthor(self: ImageNodeHandle): string;
        getStockURL(self: ImageNodeHandle): string;
        getStockUserProfileURL(self: ImageNodeHandle): string;
        getUpsamplerType(self: ImageNodeHandle): RasterResamplerType;
        isKOnly(self: ImageNodeHandle): boolean;
    }
    export const ImageNodeApi: ImageNodeApi;

}
