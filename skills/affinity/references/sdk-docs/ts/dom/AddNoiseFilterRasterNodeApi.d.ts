// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", AddNoiseFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface AddNoiseFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): AddNoiseFilterRasterNodeHandle;
        getParameters(node: AddNoiseFilterRasterNodeHandle): AddNoiseFilterParametersHandle;
    }
    export const AddNoiseFilterRasterNodeApi: AddNoiseFilterRasterNodeApi;

}
