// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DocumentHistoryItemApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface DocumentHistoryItemApi {
        dispose(self: DocumentHistoryItemHandle): void;
        getCommand(self: DocumentHistoryItemHandle): DocumentCommandHandle;
        getDescription(self: DocumentHistoryItemHandle): string;
        getThumbnail(self: DocumentHistoryItemHandle): RasterObjectHandle;
        hasAlternateFutures(self: DocumentHistoryItemHandle): boolean;
    }
    export const DocumentHistoryItemApi: DocumentHistoryItemApi;

}
