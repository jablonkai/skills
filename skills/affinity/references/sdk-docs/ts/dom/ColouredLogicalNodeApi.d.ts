// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ColouredLogicalNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ColouredLogicalNodeApi extends Omit<LogicalNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ColouredLogicalNodeHandle;
        getLayerColour(node: ColouredLogicalNodeHandle): ColourHandle;
    }
    export const ColouredLogicalNodeApi: ColouredLogicalNodeApi;

}
