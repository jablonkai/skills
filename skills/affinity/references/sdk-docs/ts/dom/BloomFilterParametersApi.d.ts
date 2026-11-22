// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", BloomFilterParametersApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface BloomFilterParametersApi {
        create(): BloomFilterParametersHandle;
        getColour(self: BloomFilterParametersHandle): number;
        getHighlightBlend(self: BloomFilterParametersHandle): number;
        getIsStrong(self: BloomFilterParametersHandle): boolean;
        getMethod(self: BloomFilterParametersHandle): BloomMethod;
        getMidtoneBlend(self: BloomFilterParametersHandle): number;
        getShadowBlend(self: BloomFilterParametersHandle): number;
        setColour(self: BloomFilterParametersHandle, colour: number): void;
        setHighlightBlend(self: BloomFilterParametersHandle, highlightBlend: number): void;
        setIsStrong(self: BloomFilterParametersHandle, isStrong: boolean): void;
        setMethod(self: BloomFilterParametersHandle, method: BloomMethod): void;
        setMidtoneBlend(self: BloomFilterParametersHandle, midtoneBlend: number): void;
        setShadowBlend(self: BloomFilterParametersHandle, shadowBlend: number): void;
    }
    export const BloomFilterParametersApi: BloomFilterParametersApi;

}
