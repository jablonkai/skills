// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VibranceAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VibranceAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: VibranceAdjustmentParametersHandle): VibranceAdjustmentRasterNodeDefinitionHandle;
        createDefault(): VibranceAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): VibranceAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: VibranceAdjustmentRasterNodeDefinitionHandle): VibranceAdjustmentParametersHandle;
        setParameters(node: VibranceAdjustmentRasterNodeDefinitionHandle, parameters: VibranceAdjustmentParametersHandle): void;
    }
    export const VibranceAdjustmentRasterNodeDefinitionApi: VibranceAdjustmentRasterNodeDefinitionApi;

}
