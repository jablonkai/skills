// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SplitToningAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface SplitToningAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): SplitToningAdjustmentRasterNodeHandle;
        getParameters(node: SplitToningAdjustmentRasterNodeHandle): SplitToningAdjustmentParametersHandle;
    }
    export const SplitToningAdjustmentRasterNodeApi: SplitToningAdjustmentRasterNodeApi;

}
