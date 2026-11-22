// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RecolourAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RecolourAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: RecolourAdjustmentParametersHandle): RecolourAdjustmentRasterNodeDefinitionHandle;
        createDefault(): RecolourAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): RecolourAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: RecolourAdjustmentRasterNodeDefinitionHandle): RecolourAdjustmentParametersHandle;
        setParameters(node: RecolourAdjustmentRasterNodeDefinitionHandle, parameters: RecolourAdjustmentParametersHandle): void;
    }
    export const RecolourAdjustmentRasterNodeDefinitionApi: RecolourAdjustmentRasterNodeDefinitionApi;

}
