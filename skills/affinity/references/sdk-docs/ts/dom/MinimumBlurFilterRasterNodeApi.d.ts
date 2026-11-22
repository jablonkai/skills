// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MinimumBlurFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MinimumBlurFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): MinimumBlurFilterRasterNodeHandle;
        getParameters(node: MinimumBlurFilterRasterNodeHandle): MinimumBlurFilterParametersHandle;
    }
    export const MinimumBlurFilterRasterNodeApi: MinimumBlurFilterRasterNodeApi;

}
