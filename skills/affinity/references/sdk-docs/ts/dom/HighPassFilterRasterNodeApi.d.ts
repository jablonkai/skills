// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HighPassFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface HighPassFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): HighPassFilterRasterNodeHandle;
        getParameters(node: HighPassFilterRasterNodeHandle): HighPassFilterParametersHandle;
    }
    export const HighPassFilterRasterNodeApi: HighPassFilterRasterNodeApi;

}
