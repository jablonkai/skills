// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HSLShiftAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface HSLShiftAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: HSLShiftAdjustmentParametersHandle): HSLShiftAdjustmentRasterNodeDefinitionHandle;
        createDefault(): HSLShiftAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): HSLShiftAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: HSLShiftAdjustmentRasterNodeDefinitionHandle): HSLShiftAdjustmentParametersHandle;
        setParameters(node: HSLShiftAdjustmentRasterNodeDefinitionHandle, parameters: HSLShiftAdjustmentParametersHandle): void;
    }
    export const HSLShiftAdjustmentRasterNodeDefinitionApi: HSLShiftAdjustmentRasterNodeDefinitionApi;

}
