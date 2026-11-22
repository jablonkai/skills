// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ContainerNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ContainerNodeApi extends Omit<ColouredLogicalNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ContainerNodeHandle;
    }
    export const ContainerNodeApi: ContainerNodeApi;

}
