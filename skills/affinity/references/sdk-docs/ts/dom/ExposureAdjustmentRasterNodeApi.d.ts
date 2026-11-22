// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ExposureAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ExposureAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ExposureAdjustmentRasterNodeHandle;
        getParameters(node: ExposureAdjustmentRasterNodeHandle): ExposureAdjustmentParametersHandle;
    }
    export const ExposureAdjustmentRasterNodeApi: ExposureAdjustmentRasterNodeApi;

}
