// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DocumentHistoryApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface DocumentHistoryApi {
        canRedo(self: DocumentHistoryHandle): boolean;
        canUndo(self: DocumentHistoryHandle): boolean;
        enumerateItems(self: DocumentHistoryHandle, callback: (documentHistoryItemRef: DocumentHistoryItemHandle) => EnumerationResult): void;
        getItem(self: DocumentHistoryHandle, index: number): DocumentHistoryItemHandle;
        getRedoDescription(self: DocumentHistoryHandle): string;
        getSize(self: DocumentHistoryHandle): number;
        getUndoDescription(self: DocumentHistoryHandle): string;
        getUndoPosition(self: DocumentHistoryHandle): number;
    }
    export const DocumentHistoryApi: DocumentHistoryApi;

}
