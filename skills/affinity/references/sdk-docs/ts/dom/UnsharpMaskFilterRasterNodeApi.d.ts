// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", UnsharpMaskFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface UnsharpMaskFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): UnsharpMaskFilterRasterNodeHandle;
        getParameters(node: UnsharpMaskFilterRasterNodeHandle): UnsharpMaskFilterParametersHandle;
    }
    export const UnsharpMaskFilterRasterNodeApi: UnsharpMaskFilterRasterNodeApi;

}
