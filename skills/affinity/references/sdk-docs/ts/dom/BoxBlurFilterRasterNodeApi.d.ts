// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BoxBlurFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BoxBlurFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): BoxBlurFilterRasterNodeHandle;
        getParameters(node: BoxBlurFilterRasterNodeHandle): BoxBlurFilterParametersHandle;
    }
    export const BoxBlurFilterRasterNodeApi: BoxBlurFilterRasterNodeApi;

}
