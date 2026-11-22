// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", TextVisibilityOptionsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface TextVisibilityOptionsApi {
        anySet(self: TextVisibilityOptionsHandle): boolean;
        clone(self: TextVisibilityOptionsHandle): TextVisibilityOptionsHandle;
        create(): TextVisibilityOptionsHandle;
        equals(self: TextVisibilityOptionsHandle, other: TextVisibilityOptionsHandle): boolean;
        getHighlightFields(self: TextVisibilityOptionsHandle): boolean;
        getShowAnchors(self: TextVisibilityOptionsHandle): boolean;
        getShowIndexMarks(self: TextVisibilityOptionsHandle): boolean;
        getShowNoteMarks(self: TextVisibilityOptionsHandle): boolean;
        getShowSpecialCharacters(self: TextVisibilityOptionsHandle): boolean;
        setHighlightFields(self: TextVisibilityOptionsHandle, value: boolean): void;
        setNewViewDefaults(self: TextVisibilityOptionsHandle): void;
        setNone(self: TextVisibilityOptionsHandle): void;
        setShowAnchors(self: TextVisibilityOptionsHandle, value: boolean): void;
        setShowIndexMarks(self: TextVisibilityOptionsHandle, value: boolean): void;
        setShowNoteMarks(self: TextVisibilityOptionsHandle, value: boolean): void;
        setShowSpecialCharacters(self: TextVisibilityOptionsHandle, value: boolean): void;
    }
    export const TextVisibilityOptionsApi: TextVisibilityOptionsApi;

}
