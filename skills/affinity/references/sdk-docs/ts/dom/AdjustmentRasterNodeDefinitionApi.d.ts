// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", AdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface AdjustmentRasterNodeDefinitionApi extends Omit<EnclosureRasterNodeDefinitionApi, "fromNodeDefinition"> {
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): AdjustmentRasterNodeDefinitionHandle;
    }
    export const AdjustmentRasterNodeDefinitionApi: AdjustmentRasterNodeDefinitionApi;

}
