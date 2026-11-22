// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ToneStretchAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ToneStretchAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ToneStretchAdjustmentRasterNodeHandle;
        getParameters(node: ToneStretchAdjustmentRasterNodeHandle): ToneStretchAdjustmentParametersHandle;
    }
    export const ToneStretchAdjustmentRasterNodeApi: ToneStretchAdjustmentRasterNodeApi;

}
