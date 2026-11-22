// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ToneStretchAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ToneStretchAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: ToneStretchAdjustmentParametersHandle): ToneStretchAdjustmentRasterNodeDefinitionHandle;
        createDefault(): ToneStretchAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ToneStretchAdjustmentRasterNodeDefinitionHandle;
        getParameters(node: ToneStretchAdjustmentRasterNodeDefinitionHandle): ToneStretchAdjustmentParametersHandle;
        setParameters(node: ToneStretchAdjustmentRasterNodeDefinitionHandle, parameters: ToneStretchAdjustmentParametersHandle): void;
    }
    export const ToneStretchAdjustmentRasterNodeDefinitionApi: ToneStretchAdjustmentRasterNodeDefinitionApi;

}
