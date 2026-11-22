// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DocumentNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DocumentNodeApi extends Omit<LogicalNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): DocumentNodeHandle;
        getBaselineGridInterface(self: DocumentNodeHandle): BaselineGridInterfaceHandle;
        getPageCount(self: DocumentNodeHandle): number;
        getSpreadCount(self: DocumentNodeHandle): number;
    }
    export const DocumentNodeApi: DocumentNodeApi;

}
