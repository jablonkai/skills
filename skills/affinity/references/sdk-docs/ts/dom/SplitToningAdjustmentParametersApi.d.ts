// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", SplitToningAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface SplitToningAdjustmentParametersApi {
        create(): SplitToningAdjustmentParametersHandle;
        getBalance(self: SplitToningAdjustmentParametersHandle): number;
        getHighlightsHue(self: SplitToningAdjustmentParametersHandle): number;
        getHighlightsSaturation(self: SplitToningAdjustmentParametersHandle): number;
        getShadowsHue(self: SplitToningAdjustmentParametersHandle): number;
        getShadowsSaturation(self: SplitToningAdjustmentParametersHandle): number;
        setBalance(self: SplitToningAdjustmentParametersHandle, balance: number): void;
        setHighlightsHue(self: SplitToningAdjustmentParametersHandle, highlightsHue: number): void;
        setHighlightsSaturation(self: SplitToningAdjustmentParametersHandle, highlightsSaturation: number): void;
        setShadowsHue(self: SplitToningAdjustmentParametersHandle, shadowsHue: number): void;
        setShadowsSaturation(self: SplitToningAdjustmentParametersHandle, shadowsSaturation: number): void;
    }
    export const SplitToningAdjustmentParametersApi: SplitToningAdjustmentParametersApi;

}
