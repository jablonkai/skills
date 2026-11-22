// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", HSLShiftAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface HSLShiftAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): HSLShiftAdjustmentRasterNodeHandle;
        getParameters(node: HSLShiftAdjustmentRasterNodeHandle): HSLShiftAdjustmentParametersHandle;
    }
    export const HSLShiftAdjustmentRasterNodeApi: HSLShiftAdjustmentRasterNodeApi;

}
