// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TextFrameInterfaceApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";
    import { Transform } from "affinity:geometry";

    export interface TextFrameInterfaceApi {
        canHideOverflow(self: TextFrameInterfaceHandle): boolean;
        canUseBaselineGrid(self: TextFrameInterfaceHandle): boolean;
        canUseTextWraps(self: TextFrameInterfaceHandle): boolean;
        enumerateTextFlowNodes(self: TextFrameInterfaceHandle, callback: (node: TextNodeHandle) => EnumerationResult): void;
        fromNode(node: NodeHandle): TextFrameInterfaceHandle;
        getNode(self: TextFrameInterfaceHandle): NodeHandle;
        getScalarStoryToDomainTransform(self: TextFrameInterfaceHandle): Transform;
        getSpreadNode(self: TextFrameInterfaceHandle): SpreadNodeHandle;
        getStoryToDomainTransform(self: TextFrameInterfaceHandle): Transform;
        getTextBegin(self: TextFrameInterfaceHandle): number;
        getTextFlow(self: TextFrameInterfaceHandle): TextFlowHandle;
        getTextFlowIndex(self: TextFrameInterfaceHandle): number;
        getTextRenderScale(self: TextFrameInterfaceHandle): Transform;
        getTextUiScale(self: TextFrameInterfaceHandle): Transform;
        hasScaledText(self: TextFrameInterfaceHandle): boolean;
        ignoreBaselineGrid(self: TextFrameInterfaceHandle): boolean;
        ignoreTextWraps(self: TextFrameInterfaceHandle): boolean;
        isMultiFrameTextFlow(self: TextFrameInterfaceHandle): boolean;
        isTextFlowBack(self: TextFrameInterfaceHandle): boolean;
        isTextFlowFront(self: TextFrameInterfaceHandle): boolean;
        isWrappingText(self: TextFrameInterfaceHandle): boolean;
    }
    export const TextFrameInterfaceApi: TextFrameInterfaceApi;

}
