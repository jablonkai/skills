// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", FileExportOptionsApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { EnumerationResult } from "affinity:common";

    export interface FileExportOptionsApi {
        createForCanvaExport(dpi: number): FileExportOptionsHandle;
        createWithPresetName(presetName: string): FileExportOptionsHandle;
        enumeratePresetNames(callback: (presetNameRef: string) => EnumerationResult): void;
    }
    export const FileExportOptionsApi: FileExportOptionsApi;

}
