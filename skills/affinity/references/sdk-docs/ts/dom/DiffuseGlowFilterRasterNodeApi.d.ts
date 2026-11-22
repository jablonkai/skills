// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DiffuseGlowFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DiffuseGlowFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): DiffuseGlowFilterRasterNodeHandle;
        getParameters(node: DiffuseGlowFilterRasterNodeHandle): DiffuseGlowFilterParametersHandle;
    }
    export const DiffuseGlowFilterRasterNodeApi: DiffuseGlowFilterRasterNodeApi;

}
