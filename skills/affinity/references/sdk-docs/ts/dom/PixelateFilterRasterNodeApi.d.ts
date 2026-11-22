// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PixelateFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PixelateFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): PixelateFilterRasterNodeHandle;
        getParameters(node: PixelateFilterRasterNodeHandle): PixelateFilterParametersHandle;
    }
    export const PixelateFilterRasterNodeApi: PixelateFilterRasterNodeApi;

}
