// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", FileExportAreaApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface FileExportAreaApi {
        clone(self: FileExportAreaHandle): FileExportAreaHandle;
        createForArtboard(artboard: ArtboardInterfaceHandle): FileExportAreaHandle;
        createForCurrentPage(): FileExportAreaHandle;
        createForCurrentSpread(): FileExportAreaHandle;
        createForPages(pages: string): FileExportAreaHandle;
        createForSelection(selectionOrNull: SelectionHandle | null): FileExportAreaHandle;
        createForSelectionArea(selectionOrNull: SelectionHandle | null): FileExportAreaHandle;
        createForSpreads(pages: string): FileExportAreaHandle;
        createForWholeDocument(): FileExportAreaHandle;
    }
    export const FileExportAreaApi: FileExportAreaApi;

}
