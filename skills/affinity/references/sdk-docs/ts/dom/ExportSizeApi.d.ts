// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", ExportSizeApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface ExportSizeApi {
        createWithExportScale(exportScale: ExportScaleHandle): ExportSizeHandle;
        getExportScale(self: ExportSizeHandle): ExportScaleHandle;
        setExportScale(self: ExportSizeHandle, exportScale: ExportScaleHandle): void;
    }
    export const ExportSizeApi: ExportSizeApi;

}
