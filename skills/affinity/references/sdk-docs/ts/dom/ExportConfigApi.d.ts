// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ExportConfigApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface ExportConfigApi {
        appendFormat(self: ExportConfigHandle, exportFormat: ExportFormatHandle): void;
        deleteFormat(self: ExportConfigHandle, index: number): void;
        enumerateFormats(self: ExportConfigHandle, callback: (exportFormat: ExportFormatHandle) => EnumerationResult): void;
        getFormatCount(self: ExportConfigHandle): number;
        replaceFormat(self: ExportConfigHandle, index: number, exportFormat: ExportFormatHandle): void;
    }
    export const ExportConfigApi: ExportConfigApi;

}
