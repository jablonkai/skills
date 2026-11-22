// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", NormalsAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface NormalsAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: NormalsAdjustmentParametersHandle): NormalsAdjustmentRasterNodeDefinitionHandle;
        createDefault(): NormalsAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): NormalsAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: NormalsAdjustmentRasterNodeDefinitionHandle): NormalsAdjustmentParametersHandle;
        setParameters(node: NormalsAdjustmentRasterNodeDefinitionHandle, parameters: NormalsAdjustmentParametersHandle): void;
    }
    export const NormalsAdjustmentRasterNodeDefinitionApi: NormalsAdjustmentRasterNodeDefinitionApi;

}
