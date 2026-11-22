// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PolyCurveNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PolyCurveNodeApi extends Omit<VectorNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): PolyCurveNodeHandle;
        getArtboardInterface(node: PolyCurveNodeHandle): ArtboardInterfaceHandle;
    }
    export const PolyCurveNodeApi: PolyCurveNodeApi;

}
