// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PhysicalRootInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PhysicalRootInterfaceApi {
        fromNode(node: NodeHandle): PhysicalRootInterfaceHandle;
        getNode(self: PhysicalRootInterfaceHandle): NodeHandle;
        getPhysicalRootProperties(self: PhysicalRootInterfaceHandle): PhysicalRootPropertiesInterfaceHandle;
    }
    export const PhysicalRootInterfaceApi: PhysicalRootInterfaceApi;

}
