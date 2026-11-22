// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CurvesAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { ColourSpaceType } from "affinity:colours";

    export interface CurvesAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): CurvesAdjustmentRasterNodeHandle;
        getColourSpace(node: CurvesAdjustmentRasterNodeHandle): ColourSpaceType;
        getParameters(node: CurvesAdjustmentRasterNodeHandle): CurvesAdjustmentParametersHandle;
    }
    export const CurvesAdjustmentRasterNodeApi: CurvesAdjustmentRasterNodeApi;

}
