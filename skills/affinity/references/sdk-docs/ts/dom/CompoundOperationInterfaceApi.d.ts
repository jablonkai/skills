// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CompoundOperationInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface CompoundOperationInterfaceApi {
        fromNode(node: NodeHandle): CompoundOperationInterfaceHandle;
        getCompoundOperation(self: CompoundOperationInterfaceHandle): CompoundOperation;
        getNode(node: CompoundOperationInterfaceHandle): NodeHandle;
    }
    export const CompoundOperationInterfaceApi: CompoundOperationInterfaceApi;

}
