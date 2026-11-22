// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", WhiteBalanceAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface WhiteBalanceAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): WhiteBalanceAdjustmentRasterNodeHandle;
        getParameters(node: WhiteBalanceAdjustmentRasterNodeHandle): WhiteBalanceAdjustmentParametersHandle;
    }
    export const WhiteBalanceAdjustmentRasterNodeApi: WhiteBalanceAdjustmentRasterNodeApi;

}
