// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TwirlFilterRasterNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TwirlFilterRasterNodeApi extends Omit<FilterRasterNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): TwirlFilterRasterNodeHandle;
        getParameters(node: TwirlFilterRasterNodeHandle): TwirlFilterParametersHandle;
    }
    export const TwirlFilterRasterNodeApi: TwirlFilterRasterNodeApi;

}
