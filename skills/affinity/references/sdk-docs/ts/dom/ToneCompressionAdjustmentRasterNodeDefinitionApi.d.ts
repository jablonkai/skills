// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ToneCompressionAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ToneCompressionAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: ToneCompressionAdjustmentParametersHandle): ToneCompressionAdjustmentRasterNodeDefinitionHandle;
        createDefault(): ToneCompressionAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ToneCompressionAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: ToneCompressionAdjustmentRasterNodeDefinitionHandle): ToneCompressionAdjustmentParametersHandle;
        setParameters(node: ToneCompressionAdjustmentRasterNodeDefinitionHandle, parameters: ToneCompressionAdjustmentParametersHandle): void;
    }
    export const ToneCompressionAdjustmentRasterNodeDefinitionApi: ToneCompressionAdjustmentRasterNodeDefinitionApi;

}
