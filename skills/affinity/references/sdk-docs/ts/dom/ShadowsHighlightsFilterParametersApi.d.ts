// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ShadowsHighlightsFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ShadowsHighlightsFilterParametersApi {
        create(): ShadowsHighlightsFilterParametersHandle;
        getHighlightsRadius(self: ShadowsHighlightsFilterParametersHandle): number;
        getHighlightsRange(self: ShadowsHighlightsFilterParametersHandle): number;
        getHighlightsStrength(self: ShadowsHighlightsFilterParametersHandle): number;
        getShadowsRadius(self: ShadowsHighlightsFilterParametersHandle): number;
        getShadowsRange(self: ShadowsHighlightsFilterParametersHandle): number;
        getShadowsStrength(self: ShadowsHighlightsFilterParametersHandle): number;
        getVersion(self: ShadowsHighlightsFilterParametersHandle): ShadowsHighlightsVersion;
        setHighlightsRadius(self: ShadowsHighlightsFilterParametersHandle, highlightsRadius: number): void;
        setHighlightsRange(self: ShadowsHighlightsFilterParametersHandle, highlightsRange: number): void;
        setHighlightsStrength(self: ShadowsHighlightsFilterParametersHandle, highlightsStrength: number): void;
        setShadowsRadius(self: ShadowsHighlightsFilterParametersHandle, shadowsRadius: number): void;
        setShadowsRange(self: ShadowsHighlightsFilterParametersHandle, shadowsRange: number): void;
        setShadowsStrength(self: ShadowsHighlightsFilterParametersHandle, shadowsStrength: number): void;
        setVersion(self: ShadowsHighlightsFilterParametersHandle, version: ShadowsHighlightsVersion): void;
    }
    export const ShadowsHighlightsFilterParametersApi: ShadowsHighlightsFilterParametersApi;

}
