// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TextSelectionApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";
    import { StoryRange } from "affinity:story";

    export interface TextSelectionApi extends SubSelectionApi {
        create(storyRanges: StoryRange[]): TextSelectionHandle;
        enumerateRanges(self: TextSelectionHandle, callback: (range: StoryRange) => EnumerationResult): void;
        fromSubSelection(subSelection: SubSelectionHandle): TextSelectionHandle;
        getAnchor(self: TextSelectionHandle): number;
        getCaret(self: TextSelectionHandle): number;
        getMarkedTextBegin(self: TextSelectionHandle): number;
        getMarkedTextEnd(self: TextSelectionHandle): number;
        getRange(self: TextSelectionHandle, index: number): StoryRange;
        getRangeCount(self: TextSelectionHandle): number;
        hasMarkedText(self: TextSelectionHandle): boolean;
        isEmpty(self: TextSelectionHandle): boolean;
    }
    export const TextSelectionApi: TextSelectionApi;

}
