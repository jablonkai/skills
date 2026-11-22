// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TextFlowApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TextFlowApi {
        getDocumentPageIndex(self: TextFlowHandle, frameIndex: number): number;
        getDocumentSpreadIndex(self: TextFlowHandle, frameIndex: number): number;
        getFrameCount(self: TextFlowHandle): number;
        getOverflowInfo(self: TextFlowHandle): TextFlowOverflowInfoHandle;
        getOverflowInfoAsync(self: TextFlowHandle, callback: (result: Error | null, overflowInfo: TextFlowOverflowInfoHandle | null) => void): void;
        hideOverflow(self: TextFlowHandle): boolean;
        ignoreTextWraps(self: TextFlowHandle): boolean;
        isEmpty(self: TextFlowHandle): boolean;
        isMultiFrameTextFlow(self: TextFlowHandle): boolean;
    }
    export const TextFlowApi: TextFlowApi;

}
