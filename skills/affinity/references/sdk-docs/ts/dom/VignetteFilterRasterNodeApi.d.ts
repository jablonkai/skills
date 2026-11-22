// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VignetteFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VignetteFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): VignetteFilterRasterNodeHandle;
        getParameters(node: VignetteFilterRasterNodeHandle): VignetteFilterParametersHandle;
    }
    export const VignetteFilterRasterNodeApi: VignetteFilterRasterNodeApi;

}
