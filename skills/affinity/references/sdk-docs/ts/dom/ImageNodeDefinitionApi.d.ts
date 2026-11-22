// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ImageNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { RasterFormat } from "affinity:raster";

    export interface ImageNodeDefinitionApi extends Omit<VectorNodeDefinitionApi, "fromNodeDefinition"> {
        create(format: RasterFormat): ImageNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ImageNodeDefinitionHandle;
        getBitmap(self: ImageNodeDefinitionHandle): RasterObjectHandle;
        setBitmap(self: ImageNodeDefinitionHandle, bitmap: RasterObjectHandle): void;
    }
    export const ImageNodeDefinitionApi: ImageNodeDefinitionApi;

}
