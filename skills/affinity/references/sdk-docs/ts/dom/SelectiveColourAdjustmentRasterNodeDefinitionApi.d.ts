// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SelectiveColourAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface SelectiveColourAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: SelectiveColourAdjustmentParametersHandle): SelectiveColourAdjustmentRasterNodeDefinitionHandle;
        createDefault(): SelectiveColourAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): SelectiveColourAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: SelectiveColourAdjustmentRasterNodeDefinitionHandle): SelectiveColourAdjustmentParametersHandle;
        setParameters(node: SelectiveColourAdjustmentRasterNodeDefinitionHandle, parameters: SelectiveColourAdjustmentParametersHandle): void;
    }
    export const SelectiveColourAdjustmentRasterNodeDefinitionApi: SelectiveColourAdjustmentRasterNodeDefinitionApi;

}
