// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShapeTextNodeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ShapeTextNodeApi extends Omit<TextNodeApi, "fromNode"> {
        fromNode(node: NodeHandle): ShapeTextNodeHandle;
        getShapeInterface(self: ShapeTextNodeHandle): ShapeInterfaceHandle;
    }
    export const ShapeTextNodeApi: ShapeTextNodeApi;

}
