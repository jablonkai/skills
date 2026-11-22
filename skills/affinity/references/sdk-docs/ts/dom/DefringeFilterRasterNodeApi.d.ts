// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DefringeFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DefringeFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): DefringeFilterRasterNodeHandle;
        getParameters(node: DefringeFilterRasterNodeHandle): DefringeFilterParametersHandle;
    }
    export const DefringeFilterRasterNodeApi: DefringeFilterRasterNodeApi;

}
