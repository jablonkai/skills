// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TextFlowOverflowInfoApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TextFlowOverflowInfoApi {
        getPosition(self: TextFlowOverflowInfoHandle): number;
        getState(self: TextFlowOverflowInfoHandle): TextFlowOverflowState;
    }
    export const TextFlowOverflowInfoApi: TextFlowOverflowInfoApi;

}
