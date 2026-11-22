// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TransparencyInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Transform } from "affinity:geometry";

    export interface TransparencyInterfaceApi {
        fromNode(node: NodeHandle): TransparencyInterfaceHandle;
        getContentType(self: TransparencyInterfaceHandle): ContentType;
        getDomainTransform(self: TransparencyInterfaceHandle): Transform;
        getFillDescriptor(self: TransparencyInterfaceHandle): FillDescriptorHandle;
        getNode(self: TransparencyInterfaceHandle): NodeHandle;
        isTransparencyNone(self: TransparencyInterfaceHandle): boolean;
    }
    export const TransparencyInterfaceApi: TransparencyInterfaceApi;

}
