// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BaseBoxInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle } from "affinity:geometry";

    export interface BaseBoxInterfaceApi {
        fromNode(node: NodeHandle): BaseBoxInterfaceHandle;
        getBaseBox(self: BaseBoxInterfaceHandle, includeClips: boolean): Rectangle;
        getConstrainingBaseBox(self: BaseBoxInterfaceHandle, includeClips: boolean): Rectangle;
        getNode(node: BaseBoxInterfaceHandle): NodeHandle;
    }
    export const BaseBoxInterfaceApi: BaseBoxInterfaceApi;

}
