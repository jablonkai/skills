// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { RasterFormat } from "affinity:raster";

    export interface RasterNodeDefinitionApi extends Omit<PhysicalNodeDefinitionApi, "fromNodeDefinition"> {
        create(format: RasterFormat): RasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): RasterNodeDefinitionHandle;
        getBitmap(self: RasterNodeDefinitionHandle): RasterObjectHandle;
        setBitmap(self: RasterNodeDefinitionHandle, bitmapOrNull: RasterObjectHandle | null): void;
    }
    export const RasterNodeDefinitionApi: RasterNodeDefinitionApi;

}
