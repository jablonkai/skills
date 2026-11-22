// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PhysicalRootPropertiesInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PhysicalRootPropertiesInterfaceApi {
        fromNode(node: NodeHandle): PhysicalRootPropertiesInterfaceHandle;
        getNode(self: PhysicalRootPropertiesInterfaceHandle): NodeHandle;
        getPageBoxInterface(self: PhysicalRootPropertiesInterfaceHandle): PageBoxInterfaceHandle;
        getPageCount(self: PhysicalRootPropertiesInterfaceHandle): number;
    }
    export const PhysicalRootPropertiesInterfaceApi: PhysicalRootPropertiesInterfaceApi;

}
