// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BloomFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BloomFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): BloomFilterRasterNodeHandle;
        getParameters(node: BloomFilterRasterNodeHandle): BloomFilterParametersHandle;
    }
    export const BloomFilterRasterNodeApi: BloomFilterRasterNodeApi;

}
