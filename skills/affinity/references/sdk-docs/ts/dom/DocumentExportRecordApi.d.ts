// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DocumentExportRecordApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { ErrorCode } from "affinity:common";

    export interface DocumentExportRecordApi {
        getErrorMessage(self: DocumentExportRecordHandle): string;
        getPath(self: DocumentExportRecordHandle): string;
        getResult(self: DocumentExportRecordHandle): ErrorCode;
        getWarningMessage(self: DocumentExportRecordHandle): string;
        hasWarnings(self: DocumentExportRecordHandle): boolean;
    }
    export const DocumentExportRecordApi: DocumentExportRecordApi;

}
