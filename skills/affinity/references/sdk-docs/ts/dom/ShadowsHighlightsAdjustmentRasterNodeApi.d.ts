// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShadowsHighlightsAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ShadowsHighlightsAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ShadowsHighlightsAdjustmentRasterNodeHandle;
        getParameters(node: ShadowsHighlightsAdjustmentRasterNodeHandle): ShadowsHighlightsAdjustmentParametersHandle;
    }
    export const ShadowsHighlightsAdjustmentRasterNodeApi: ShadowsHighlightsAdjustmentRasterNodeApi;

}
