// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PatternRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PatternRasterNodeApi extends Omit<RasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): PatternRasterNodeHandle;
        getMirror(node: PatternRasterNodeHandle): boolean;
    }
    export const PatternRasterNodeApi: PatternRasterNodeApi;

}
