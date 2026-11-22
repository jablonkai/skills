// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MaximumBlurFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MaximumBlurFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): MaximumBlurFilterRasterNodeHandle;
        getParameters(node: MaximumBlurFilterRasterNodeHandle): MaximumBlurFilterParametersHandle;
    }
    export const MaximumBlurFilterRasterNodeApi: MaximumBlurFilterRasterNodeApi;

}
