// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BlackAndWhiteAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BlackAndWhiteAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): BlackAndWhiteAdjustmentRasterNodeHandle;
        getParameters(node: BlackAndWhiteAdjustmentRasterNodeHandle): BlackAndWhiteAdjustmentParametersHandle;
    }
    export const BlackAndWhiteAdjustmentRasterNodeApi: BlackAndWhiteAdjustmentRasterNodeApi;

}
