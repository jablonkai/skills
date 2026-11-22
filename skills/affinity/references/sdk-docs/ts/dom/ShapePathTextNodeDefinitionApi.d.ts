// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShapePathTextNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle } from "affinity:geometry";

    export interface ShapePathTextNodeDefinitionApi extends Omit<TextNodeDefinitionApi, "fromNodeDefinition"> {
        createFromStoryBuilder(shape: ShapeHandle, boundingRect: Rectangle, storyBuilder: StoryBuilderHandle): ShapePathTextNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ShapePathTextNodeDefinitionHandle;
    }
    export const ShapePathTextNodeDefinitionApi: ShapePathTextNodeDefinitionApi;

}
