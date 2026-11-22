// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", GroupNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface GroupNodeApi extends Omit<LogicalNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): GroupNodeHandle;
    }
    export const GroupNodeApi: GroupNodeApi;

}
