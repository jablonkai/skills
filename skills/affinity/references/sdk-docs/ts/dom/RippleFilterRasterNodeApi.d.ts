// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RippleFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RippleFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): RippleFilterRasterNodeHandle;
        getParameters(node: RippleFilterRasterNodeHandle): RippleFilterParametersHandle;
    }
    export const RippleFilterRasterNodeApi: RippleFilterRasterNodeApi;

}
