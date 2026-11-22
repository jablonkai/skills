// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ExportableInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ExportableInterfaceApi {
        fromNode(node: NodeHandle): ExportableInterfaceHandle;
        getExportConfig(self: ExportableInterfaceHandle): ExportConfigHandle;
        getNode(self: ExportableInterfaceHandle): NodeHandle;
    }
    export const ExportableInterfaceApi: ExportableInterfaceApi;

}
