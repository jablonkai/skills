// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ColourBalanceAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ColourBalanceAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ColourBalanceAdjustmentRasterNodeHandle;
        getParameters(node: ColourBalanceAdjustmentRasterNodeHandle): ColourBalanceAdjustmentParametersHandle;
    }
    export const ColourBalanceAdjustmentRasterNodeApi: ColourBalanceAdjustmentRasterNodeApi;

}
