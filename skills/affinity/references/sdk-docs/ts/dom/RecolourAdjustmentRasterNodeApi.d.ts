// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", RecolourAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface RecolourAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): RecolourAdjustmentRasterNodeHandle;
        getParameters(node: RecolourAdjustmentRasterNodeHandle): RecolourAdjustmentParametersHandle;
    }
    export const RecolourAdjustmentRasterNodeApi: RecolourAdjustmentRasterNodeApi;

}
