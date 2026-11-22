// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DepthOfFieldFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DepthOfFieldFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): DepthOfFieldFilterRasterNodeHandle;
        getParameters(node: DepthOfFieldFilterRasterNodeHandle): DepthOfFieldFilterParametersHandle;
    }
    export const DepthOfFieldFilterRasterNodeApi: DepthOfFieldFilterRasterNodeApi;

}
