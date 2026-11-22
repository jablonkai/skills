// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PhysicalNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PhysicalNodeApi extends NodeApi {
        canTransformWhileProtectingChildList(node: PhysicalNodeHandle, nodeChildType: NodeChildType): boolean;
        fromNode(node: NodeHandle): PhysicalNodeHandle;
    }
    export const PhysicalNodeApi: PhysicalNodeApi;

}
