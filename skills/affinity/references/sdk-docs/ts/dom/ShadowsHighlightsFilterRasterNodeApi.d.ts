// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShadowsHighlightsFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ShadowsHighlightsFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ShadowsHighlightsFilterRasterNodeHandle;
        getParameters(node: ShadowsHighlightsFilterRasterNodeHandle): ShadowsHighlightsFilterParametersHandle;
    }
    export const ShadowsHighlightsFilterRasterNodeApi: ShadowsHighlightsFilterRasterNodeApi;

}
