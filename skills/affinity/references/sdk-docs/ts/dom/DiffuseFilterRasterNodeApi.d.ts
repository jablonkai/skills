// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DiffuseFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DiffuseFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): DiffuseFilterRasterNodeHandle;
        getParameters(node: DiffuseFilterRasterNodeHandle): DiffuseFilterParametersHandle;
    }
    export const DiffuseFilterRasterNodeApi: DiffuseFilterRasterNodeApi;

}
