// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DustAndScratchFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DustAndScratchFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): DustAndScratchFilterRasterNodeHandle;
        getParameters(node: DustAndScratchFilterRasterNodeHandle): DustAndScratchFilterParametersHandle;
    }
    export const DustAndScratchFilterRasterNodeApi: DustAndScratchFilterRasterNodeApi;

}
