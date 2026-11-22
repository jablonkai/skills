// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PinchPunchFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PinchPunchFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): PinchPunchFilterRasterNodeHandle;
        getParameters(node: PinchPunchFilterRasterNodeHandle): PinchPunchFilterParametersHandle;
    }
    export const PinchPunchFilterRasterNodeApi: PinchPunchFilterRasterNodeApi;

}
