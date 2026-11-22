// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ToneCompressionAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ToneCompressionAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ToneCompressionAdjustmentRasterNodeHandle;
        getParameters(node: ToneCompressionAdjustmentRasterNodeHandle): ToneCompressionAdjustmentParametersHandle;
    }
    export const ToneCompressionAdjustmentRasterNodeApi: ToneCompressionAdjustmentRasterNodeApi;

}
