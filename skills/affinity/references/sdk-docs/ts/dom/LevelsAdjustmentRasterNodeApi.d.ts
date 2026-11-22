// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", LevelsAdjustmentRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { ColourSpaceType } from "affinity:colours";

    export interface LevelsAdjustmentRasterNodeApi extends Omit<AdjustmentRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): LevelsAdjustmentRasterNodeHandle;
        getColourSpace(node: LevelsAdjustmentRasterNodeHandle): ColourSpaceType;
        getParameters(node: LevelsAdjustmentRasterNodeHandle): LevelsAdjustmentParametersHandle;
    }
    export const LevelsAdjustmentRasterNodeApi: LevelsAdjustmentRasterNodeApi;

}
