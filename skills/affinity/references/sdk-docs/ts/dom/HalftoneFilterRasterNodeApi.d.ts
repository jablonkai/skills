// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HalftoneFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface HalftoneFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): HalftoneFilterRasterNodeHandle;
        getParameters(node: HalftoneFilterRasterNodeHandle): HalftoneFilterParametersHandle;
    }
    export const HalftoneFilterRasterNodeApi: HalftoneFilterRasterNodeApi;

}
