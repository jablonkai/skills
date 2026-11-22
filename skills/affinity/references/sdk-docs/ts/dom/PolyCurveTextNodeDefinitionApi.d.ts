// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", PolyCurveTextNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface PolyCurveTextNodeDefinitionApi extends Omit<TextNodeDefinitionApi, "fromNodeDefinition"> {
        createFromStoryBuilder(polyCurve: PolyCurveHandle, storyBuilder: StoryBuilderHandle): PolyCurveTextNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): PolyCurveTextNodeDefinitionHandle;
    }
    export const PolyCurveTextNodeDefinitionApi: PolyCurveTextNodeDefinitionApi;

}
