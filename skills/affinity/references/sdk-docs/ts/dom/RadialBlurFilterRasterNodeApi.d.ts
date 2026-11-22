// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RadialBlurFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RadialBlurFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): RadialBlurFilterRasterNodeHandle;
        getParameters(node: RadialBlurFilterRasterNodeHandle): RadialBlurFilterParametersHandle;
    }
    export const RadialBlurFilterRasterNodeApi: RadialBlurFilterRasterNodeApi;

}
