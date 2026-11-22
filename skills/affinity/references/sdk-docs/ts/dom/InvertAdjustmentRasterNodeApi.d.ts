// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", InvertAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface InvertAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): InvertAdjustmentRasterNodeHandle;
    }
    export const InvertAdjustmentRasterNodeApi: InvertAdjustmentRasterNodeApi;

}
