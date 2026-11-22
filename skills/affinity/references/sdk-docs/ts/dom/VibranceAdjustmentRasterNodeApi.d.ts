// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VibranceAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VibranceAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): VibranceAdjustmentRasterNodeHandle;
        getParameters(node: VibranceAdjustmentRasterNodeHandle): VibranceAdjustmentParametersHandle;
    }
    export const VibranceAdjustmentRasterNodeApi: VibranceAdjustmentRasterNodeApi;

}
