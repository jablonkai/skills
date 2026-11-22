// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ArtTextNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Point } from "affinity:geometry";

    export interface ArtTextNodeDefinitionApi extends Omit<TextNodeDefinitionApi, "fromNodeDefinition"> {
        createFromStoryBuilder(position: Point, storyBuilder: StoryBuilderHandle): ArtTextNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): ArtTextNodeDefinitionHandle;
    }
    export const ArtTextNodeDefinitionApi: ArtTextNodeDefinitionApi;

}
