// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShadowsHighlightsAdjustmentParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ShadowsHighlightsAdjustmentParametersApi {
        create(): ShadowsHighlightsAdjustmentParametersHandle;
        getHighlights(self: ShadowsHighlightsAdjustmentParametersHandle): number;
        getShadows(self: ShadowsHighlightsAdjustmentParametersHandle): number;
        setHighlights(self: ShadowsHighlightsAdjustmentParametersHandle, highlights: number): void;
        setShadows(self: ShadowsHighlightsAdjustmentParametersHandle, shadows: number): void;
    }
    export const ShadowsHighlightsAdjustmentParametersApi: ShadowsHighlightsAdjustmentParametersApi;

}
