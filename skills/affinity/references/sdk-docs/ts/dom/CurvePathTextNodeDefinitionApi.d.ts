// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", CurvePathTextNodeDefinitionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface CurvePathTextNodeDefinitionApi extends Omit<TextNodeDefinitionApi, "fromNodeDefinition"> {
        createFromStoryBuilder(polyCurve: PolyCurveHandle, storyBuilder: StoryBuilderHandle): CurvePathTextNodeDefinitionHandle;
        fromNodeDefinition(nodeDefinition: NodeDefinitionHandle): CurvePathTextNodeDefinitionHandle;
    }
    export const CurvePathTextNodeDefinitionApi: CurvePathTextNodeDefinitionApi;

}
