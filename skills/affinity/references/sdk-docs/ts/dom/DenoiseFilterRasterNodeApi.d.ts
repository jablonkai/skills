// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DenoiseFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DenoiseFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): DenoiseFilterRasterNodeHandle;
        getParameters(node: DenoiseFilterRasterNodeHandle): DenoiseFilterParametersHandle;
    }
    export const DenoiseFilterRasterNodeApi: DenoiseFilterRasterNodeApi;

}
