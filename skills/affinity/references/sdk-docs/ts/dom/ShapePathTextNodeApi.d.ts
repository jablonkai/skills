// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShapePathTextNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ShapePathTextNodeApi extends Omit<TextNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ShapePathTextNodeHandle;
        getShapeInterface(self: ShapePathTextNodeHandle): ShapeInterfaceHandle;
    }
    export const ShapePathTextNodeApi: ShapePathTextNodeApi;

}
