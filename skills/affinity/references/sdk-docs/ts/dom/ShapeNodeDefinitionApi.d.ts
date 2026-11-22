// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShapeNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle } from "affinity:geometry";

    export interface ShapeNodeDefinitionApi extends Omit<VectorNodeDefinitionApi, "fromNodeDefinition"> {
        create(shape: ShapeHandle, rectangle: Rectangle, brushFillDescriptorOrNull: FillDescriptorHandle | null, lineFillDescriptorOrNull: FillDescriptorHandle | null, lineStyleDescriptorOrNull: LineStyleDescriptorHandle | null, transparencyFillDescriptorOrNull: FillDescriptorHandle | null): ShapeNodeDefinitionHandle;
        createDefault(): ShapeNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ShapeNodeDefinitionHandle;
        getBoundingRectangle(self: ShapeNodeDefinitionHandle): Rectangle;
        getShape(self: ShapeNodeDefinitionHandle): ShapeHandle;
        setBoundingRectangle(self: ShapeNodeDefinitionHandle, rectangle: Rectangle): void;
        setShape(self: ShapeNodeDefinitionHandle, shape: ShapeHandle): void;
    }
    export const ShapeNodeDefinitionApi: ShapeNodeDefinitionApi;

}
