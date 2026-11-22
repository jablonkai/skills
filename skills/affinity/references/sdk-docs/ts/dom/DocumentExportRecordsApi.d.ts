// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DocumentExportRecordsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface DocumentExportRecordsApi {
        enumerate(self: DocumentExportRecordsHandle, callback: (documentExportRecordRef: DocumentExportRecordHandle) => EnumerationResult): void;
        getCount(self: DocumentExportRecordsHandle): number;
    }
    export const DocumentExportRecordsApi: DocumentExportRecordsApi;

}
