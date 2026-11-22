// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BlendModeInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { BlendMode } from "affinity:common";

    export interface BlendModeInterfaceApi {
        fromNode(node: NodeHandle): BlendModeInterfaceHandle;
        getAntialiasingMode(self: BlendModeInterfaceHandle): AntialiasingMode;
        getBlendMode(self: BlendModeInterfaceHandle): BlendMode;
        getBlendOptions(self: BlendModeInterfaceHandle): BlendOptionsHandle;
        getNode(self: BlendModeInterfaceHandle): NodeHandle;
    }
    export const BlendModeInterfaceApi: BlendModeInterfaceApi;

}
