// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ShadowsHighlightsAdjustmentRasterNodeDefinitionApi extends Omit<AdjustmentRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: ShadowsHighlightsAdjustmentParametersHandle): ShadowsHighlightsAdjustmentRasterNodeDefinitionHandle;
        createDefault(): ShadowsHighlightsAdjustmentRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ShadowsHighlightsAdjustmentRasterNodeDefinitionHandle;
        getParameters(self: ShadowsHighlightsAdjustmentRasterNodeDefinitionHandle): ShadowsHighlightsAdjustmentParametersHandle;
        setParameters(self: ShadowsHighlightsAdjustmentRasterNodeDefinitionHandle, parameters: ShadowsHighlightsAdjustmentParametersHandle): void;
    }
    export const ShadowsHighlightsAdjustmentRasterNodeDefinitionApi: ShadowsHighlightsAdjustmentRasterNodeDefinitionApi;

}
