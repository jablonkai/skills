// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CurvePathTextNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface CurvePathTextNodeApi extends Omit<TextNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): CurvePathTextNodeHandle;
    }
    export const CurvePathTextNodeApi: CurvePathTextNodeApi;

}
