// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VisibilityInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VisibilityInterfaceApi {
        getFillOpacity(self: VisibilityInterfaceHandle): number;
        getGlobalOpacity(self: VisibilityInterfaceHandle): number;
        getNode(self: VisibilityInterfaceHandle): NodeHandle;
        isVisible(self: VisibilityInterfaceHandle): boolean;
        isVisibleInDomain(self: VisibilityInterfaceHandle): boolean;
        isVisibleInExport(self: VisibilityInterfaceHandle): boolean;
        testVisibility(self: VisibilityInterfaceHandle, visibilityTestOptions: VisibilityTestOptionsHandle): boolean;
    }
    export const VisibilityInterfaceApi: VisibilityInterfaceApi;

}
