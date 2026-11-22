// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", VisibilityTestOptionsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface VisibilityTestOptionsApi {
        clone(self: VisibilityTestOptionsHandle): VisibilityTestOptionsHandle;
        create(): VisibilityTestOptionsHandle;
        getAllowInvisibleLayers(self: VisibilityTestOptionsHandle): boolean;
        getApplyExportableVisibility(self: VisibilityTestOptionsHandle): boolean;
        getClipToSpread(self: VisibilityTestOptionsHandle): boolean;
        getIgnoreVisibilityFlags(self: VisibilityTestOptionsHandle): boolean;
        getShowEmptyRects(self: VisibilityTestOptionsHandle): boolean;
        getShowPictureFrames(self: VisibilityTestOptionsHandle): boolean;
        getTextVisibilityOptions(self: VisibilityTestOptionsHandle): TextVisibilityOptionsHandle;
        setAllowInvisibleLayers(self: VisibilityTestOptionsHandle, value: boolean): void;
        setApplyExportableVisibility(self: VisibilityTestOptionsHandle, value: boolean): void;
        setClipToSpread(self: VisibilityTestOptionsHandle, value: boolean): void;
        setIgnoreVisibilityFlags(self: VisibilityTestOptionsHandle, value: boolean): void;
        setShowEmptyRects(self: VisibilityTestOptionsHandle, value: boolean): void;
        setShowPictureFrames(self: VisibilityTestOptionsHandle, value: boolean): void;
        setTextVisibilityOptions(self: VisibilityTestOptionsHandle, textVisibilityOptions: TextVisibilityOptionsHandle): void;
    }
    export const VisibilityTestOptionsApi: VisibilityTestOptionsApi;

}
