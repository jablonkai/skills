// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShadowsHighlightsFilterRasterNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ShadowsHighlightsFilterRasterNodeDefinitionApi extends Omit<FilterRasterNodeDefinitionApi, "create" | "fromNodeDefinition"> {
        create(parameters: ShadowsHighlightsFilterParametersHandle): ShadowsHighlightsFilterRasterNodeDefinitionHandle;
        createDefault(): ShadowsHighlightsFilterRasterNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ShadowsHighlightsFilterRasterNodeDefinitionHandle;
        getParameters(self: ShadowsHighlightsFilterRasterNodeDefinitionHandle): ShadowsHighlightsFilterParametersHandle;
        setParameters(self: ShadowsHighlightsFilterRasterNodeDefinitionHandle, parameters: ShadowsHighlightsFilterParametersHandle): void;
    }
    export const ShadowsHighlightsFilterRasterNodeDefinitionApi: ShadowsHighlightsFilterRasterNodeDefinitionApi;

}
