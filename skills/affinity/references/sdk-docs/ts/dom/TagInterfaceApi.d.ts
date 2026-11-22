// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TagInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TagInterfaceApi {
        fromNode(node: NodeHandle): TagInterfaceHandle;
        getNode(self: TagInterfaceHandle): NodeHandle;
        getValueForKey(self: TagInterfaceHandle, key: string): string;
        getValueForPredefinedKey(self: TagInterfaceHandle, key: PredefinedTagKey): string;
        hasKey(self: TagInterfaceHandle, key: string): boolean;
        hasPredefinedKey(self: TagInterfaceHandle, key: PredefinedTagKey): boolean;
        isMarkAsDecoration(self: TagInterfaceHandle): boolean;
    }
    export const TagInterfaceApi: TagInterfaceApi;

}
