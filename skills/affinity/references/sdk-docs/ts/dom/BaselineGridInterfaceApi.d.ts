// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BaselineGridInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BaselineGridInterfaceApi {
        fromNode(node: NodeHandle): BaselineGridInterfaceHandle;
        getBaselineGridOptions(self: BaselineGridInterfaceHandle): BaselineGridOptionsHandle;
        getNode(self: BaselineGridInterfaceHandle): NodeHandle;
    }
    export const BaselineGridInterfaceApi: BaselineGridInterfaceApi;

}
