// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", MedianBlurFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface MedianBlurFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): MedianBlurFilterRasterNodeHandle;
        getParameters(node: MedianBlurFilterRasterNodeHandle): MedianBlurFilterParametersHandle;
    }
    export const MedianBlurFilterRasterNodeApi: MedianBlurFilterRasterNodeApi;

}
