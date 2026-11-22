// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MaskRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MaskRasterNodeDefinitionApi extends Omit<EnclosureRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(): MaskRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): MaskRasterNodeDefinitionHandle;
    }
    export const MaskRasterNodeDefinitionApi: MaskRasterNodeDefinitionApi;

}
