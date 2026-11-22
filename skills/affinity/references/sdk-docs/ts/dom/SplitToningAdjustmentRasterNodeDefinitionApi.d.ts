// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SplitToningAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface SplitToningAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: SplitToningAdjustmentParametersHandle): SplitToningAdjustmentRasterNodeDefinitionHandle;
        createDefault(): SplitToningAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): SplitToningAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: SplitToningAdjustmentRasterNodeDefinitionHandle): SplitToningAdjustmentParametersHandle;
        setParameters(node: SplitToningAdjustmentRasterNodeDefinitionHandle, parameters: SplitToningAdjustmentParametersHandle): void;
    }
    export const SplitToningAdjustmentRasterNodeDefinitionApi: SplitToningAdjustmentRasterNodeDefinitionApi;

}
