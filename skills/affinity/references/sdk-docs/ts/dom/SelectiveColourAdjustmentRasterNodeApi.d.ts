// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SelectiveColourAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface SelectiveColourAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): SelectiveColourAdjustmentRasterNodeHandle;
        getParameters(node: SelectiveColourAdjustmentRasterNodeHandle): SelectiveColourAdjustmentParametersHandle;
    }
    export const SelectiveColourAdjustmentRasterNodeApi: SelectiveColourAdjustmentRasterNodeApi;

}
