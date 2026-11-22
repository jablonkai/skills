// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PosteriseAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PosteriseAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): PosteriseAdjustmentRasterNodeHandle;
        getParameters(node: PosteriseAdjustmentRasterNodeHandle): PosteriseAdjustmentParametersHandle;
    }
    export const PosteriseAdjustmentRasterNodeApi: PosteriseAdjustmentRasterNodeApi;

}
