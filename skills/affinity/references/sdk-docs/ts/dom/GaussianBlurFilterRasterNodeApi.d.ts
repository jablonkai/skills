// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", GaussianBlurFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface GaussianBlurFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): GaussianBlurFilterRasterNodeHandle;
        getParameters(node: GaussianBlurFilterRasterNodeHandle): GaussianBlurFilterParametersHandle;
    }
    export const GaussianBlurFilterRasterNodeApi: GaussianBlurFilterRasterNodeApi;

}
