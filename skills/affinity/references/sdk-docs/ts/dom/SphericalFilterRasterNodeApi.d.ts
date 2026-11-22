// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SphericalFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface SphericalFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): SphericalFilterRasterNodeHandle;
        getParameters(node: SphericalFilterRasterNodeHandle): SphericalFilterParametersHandle;
    }
    export const SphericalFilterRasterNodeApi: SphericalFilterRasterNodeApi;

}
