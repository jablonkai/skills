// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", WhiteBalanceAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface WhiteBalanceAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: WhiteBalanceAdjustmentParametersHandle): WhiteBalanceAdjustmentRasterNodeDefinitionHandle;
        createDefault(): WhiteBalanceAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): WhiteBalanceAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: WhiteBalanceAdjustmentRasterNodeDefinitionHandle): WhiteBalanceAdjustmentParametersHandle;
        setParameters(node: WhiteBalanceAdjustmentRasterNodeDefinitionHandle, parameters: WhiteBalanceAdjustmentParametersHandle): void;
    }
    export const WhiteBalanceAdjustmentRasterNodeDefinitionApi: WhiteBalanceAdjustmentRasterNodeDefinitionApi;

}
