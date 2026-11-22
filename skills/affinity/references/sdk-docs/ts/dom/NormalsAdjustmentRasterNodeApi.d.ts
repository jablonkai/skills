// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", NormalsAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface NormalsAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): NormalsAdjustmentRasterNodeHandle;
        getParameters(node: NormalsAdjustmentRasterNodeHandle): NormalsAdjustmentParametersHandle;
    }
    export const NormalsAdjustmentRasterNodeApi: NormalsAdjustmentRasterNodeApi;

}
