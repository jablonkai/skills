// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DescriptionInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DescriptionInterfaceApi {
        fromNode(node: NodeHandle): DescriptionInterfaceHandle;
        getDefaultDescription(self: DescriptionInterfaceHandle): string;
        getDefaultDescriptionForDisplay(self: DescriptionInterfaceHandle): string;
        getDescription(self: DescriptionInterfaceHandle, getDefaultIfEmpty: boolean): string;
        getNode(self: DescriptionInterfaceHandle): NodeHandle;
        getTagColour(self: DescriptionInterfaceHandle, inferFromAncestors: boolean): ColourHandle;
        getUserDescription(self: DescriptionInterfaceHandle): string;
    }
    export const DescriptionInterfaceApi: DescriptionInterfaceApi;

}
