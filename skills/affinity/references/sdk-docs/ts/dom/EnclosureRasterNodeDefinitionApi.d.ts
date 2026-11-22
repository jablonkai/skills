// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", EnclosureRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface EnclosureRasterNodeDefinitionApi extends Omit<RasterNodeDefinitionApi, "fromNodeDefinition"> {
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): EnclosureRasterNodeDefinitionHandle;
        getExtendEmpty(self: EnclosureRasterNodeDefinitionHandle): boolean;
        setExtendEmpty(self: EnclosureRasterNodeDefinitionHandle, extendEmpty: boolean): void;
    }
    export const EnclosureRasterNodeDefinitionApi: EnclosureRasterNodeDefinitionApi;

}
