// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ThresholdAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ThresholdAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: ThresholdAdjustmentParametersHandle): ThresholdAdjustmentRasterNodeDefinitionHandle;
        createDefault(): ThresholdAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ThresholdAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: ThresholdAdjustmentRasterNodeDefinitionHandle): ThresholdAdjustmentParametersHandle;
        setParameters(node: ThresholdAdjustmentRasterNodeDefinitionHandle, parameters: ThresholdAdjustmentParametersHandle): void;
    }
    export const ThresholdAdjustmentRasterNodeDefinitionApi: ThresholdAdjustmentRasterNodeDefinitionApi;

}
