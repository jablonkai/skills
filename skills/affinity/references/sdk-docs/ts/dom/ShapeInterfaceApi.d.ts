// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShapeInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle, ShapeType, Transform } from "affinity:geometry";

    export interface ShapeInterfaceApi {
        fromNode(node: NodeHandle): ShapeInterfaceHandle;
        getDomainTransform(self: ShapeInterfaceHandle): Transform;
        getNode(self: ShapeInterfaceHandle): NodeHandle;
        getShape(self: ShapeInterfaceHandle): ShapeHandle;
        getShapeBoundingBox(self: ShapeInterfaceHandle): Rectangle;
        getType(self: ShapeInterfaceHandle): ShapeType;
    }
    export const ShapeInterfaceApi: ShapeInterfaceApi;

}
