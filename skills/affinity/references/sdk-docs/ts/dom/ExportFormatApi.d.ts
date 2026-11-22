// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ExportFormatApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface ExportFormatApi {
        appendSize(self: ExportFormatHandle, exportSize: ExportSizeHandle): void;
        createWithFileExportOptions(fileExportOptions: FileExportOptionsHandle): ExportFormatHandle;
        deleteSize(self: ExportFormatHandle, index: number): void;
        enumerateSizes(self: ExportFormatHandle, callback: (exportSize: ExportSizeHandle) => EnumerationResult): void;
        getSizeCount(self: ExportFormatHandle): number;
        replaceSize(self: ExportFormatHandle, index: number, exportSize: ExportSizeHandle): void;
    }
    export const ExportFormatApi: ExportFormatApi;

}
