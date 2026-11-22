// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", StoryInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Transform } from "affinity:geometry";
    import { StoryRange } from "affinity:story";

    export interface StoryInterfaceApi {
        fromNode(node: NodeHandle): StoryInterfaceHandle;
        getDomainTransform(self: StoryInterfaceHandle): Transform;
        getNode(self: StoryInterfaceHandle): NodeHandle;
        getScalarDomainTransform(self: StoryInterfaceHandle): Transform;
        getStory(self: StoryInterfaceHandle): StoryHandle;
        getStoryRange(self: StoryInterfaceHandle): StoryRange;
        getTextDefaultType(self: StoryInterfaceHandle): TextDefaultType;
        getTextRenderScale(self: StoryInterfaceHandle): Transform;
        getTextUiScale(self: StoryInterfaceHandle): Transform;
        isMultiFrameTextFlow(self: StoryInterfaceHandle): boolean;
    }
    export const StoryInterfaceApi: StoryInterfaceApi;

}
