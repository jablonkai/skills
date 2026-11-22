// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PosteriseAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PosteriseAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: PosteriseAdjustmentParametersHandle): PosteriseAdjustmentRasterNodeDefinitionHandle;
        createDefault(): PosteriseAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): PosteriseAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: PosteriseAdjustmentRasterNodeDefinitionHandle): PosteriseAdjustmentParametersHandle;
        setParameters(node: PosteriseAdjustmentRasterNodeDefinitionHandle, parameters: PosteriseAdjustmentParametersHandle): void;
    }
    export const PosteriseAdjustmentRasterNodeDefinitionApi: PosteriseAdjustmentRasterNodeDefinitionApi;

}
