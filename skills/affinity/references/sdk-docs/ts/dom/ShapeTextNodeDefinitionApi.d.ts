// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShapeTextNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Rectangle } from "affinity:geometry";

    export interface ShapeTextNodeDefinitionApi extends Omit<TextNodeDefinitionApi, "fromNodeDefinition"> {
        createFromStoryBuilder(shape: ShapeHandle, boundingRect: Rectangle, storyBuilder: StoryBuilderHandle): ShapeTextNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ShapeTextNodeDefinitionHandle;
    }
    export const ShapeTextNodeDefinitionApi: ShapeTextNodeDefinitionApi;

}
