// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", EditabilityInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface EditabilityInterfaceApi {
        fromNode(node: NodeHandle): EditabilityInterfaceHandle;
        getNode(self: EditabilityInterfaceHandle): NodeHandle;
        isEditable(self: EditabilityInterfaceHandle): boolean;
        isLocalEditable(self: EditabilityInterfaceHandle): boolean;
        isMasterEditable(self: EditabilityInterfaceHandle): boolean;
    }
    export const EditabilityInterfaceApi: EditabilityInterfaceApi;

}
