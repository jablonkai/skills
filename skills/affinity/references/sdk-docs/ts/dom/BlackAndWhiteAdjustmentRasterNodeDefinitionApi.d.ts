// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BlackAndWhiteAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BlackAndWhiteAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: BlackAndWhiteAdjustmentParametersHandle): BlackAndWhiteAdjustmentRasterNodeDefinitionHandle;
        createDefault(): BlackAndWhiteAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): BlackAndWhiteAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: BlackAndWhiteAdjustmentRasterNodeDefinitionHandle): BlackAndWhiteAdjustmentParametersHandle;
        setParameters(node: BlackAndWhiteAdjustmentRasterNodeDefinitionHandle, parameters: BlackAndWhiteAdjustmentParametersHandle): void;
    }
    export const BlackAndWhiteAdjustmentRasterNodeDefinitionApi: BlackAndWhiteAdjustmentRasterNodeDefinitionApi;

}
