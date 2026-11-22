// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LensBlurFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface LensBlurFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): LensBlurFilterRasterNodeHandle;
        getParameters(node: LensBlurFilterRasterNodeHandle): LensBlurFilterParametersHandle;
    }
    export const LensBlurFilterRasterNodeApi: LensBlurFilterRasterNodeApi;

}
