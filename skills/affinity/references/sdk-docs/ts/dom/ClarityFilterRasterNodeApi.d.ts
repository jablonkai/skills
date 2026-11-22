// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ClarityFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ClarityFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ClarityFilterRasterNodeHandle;
        getParameters(node: ClarityFilterRasterNodeHandle): ClarityFilterParametersHandle;
    }
    export const ClarityFilterRasterNodeApi: ClarityFilterRasterNodeApi;

}
