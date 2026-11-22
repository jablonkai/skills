// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", DocumentApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { InsertionMode } from "affinity:commands";
    import { EnumerationResult, UnitType } from "affinity:common";
    import { Size } from "affinity:geometry";
    import { RasterFormat } from "affinity:raster";

    export interface DocumentApi {
        close(self: DocumentHandle): void;
        closeAsync(self: DocumentHandle, callback: (result: Error | null) => void): void;
        createFromOptions(option: NewDocumentOptionsHandle): DocumentHandle;
        createFromOptionsAsync(option: NewDocumentOptionsHandle, callback: (result: Error | null, documentRef: DocumentHandle | null) => void): void;
        createFromPreset(preset: DocumentPresetHandle, isLandscape: boolean): DocumentHandle;
        createFromPresetAsync(preset: DocumentPresetHandle, isLandscape: boolean, callback: (result: Error | null, documentRef: DocumentHandle | null) => void): void;
        createFromSnapshot(snapshot: DocumentSnapshotHandle): DocumentHandle;
        createFromSnapshotAsync(snapshot: DocumentSnapshotHandle, callback: (result: Error | null, documentRef: DocumentHandle | null) => void): void;
        enumerateFontNames(self: DocumentHandle, callback: (name: string, isInstalled: boolean) => EnumerationResult): void;
        enumerateOpen(callback: (documentRef: DocumentHandle) => EnumerationResult): void;
        enumerateSnapshots(self: DocumentHandle, callback: (snapshotRef: DocumentSnapshotHandle) => EnumerationResult): void;
        executeCommand(self: DocumentHandle, command: DocumentCommandHandle, preview: boolean): void;
        executeCommandAsync(self: DocumentHandle, command: DocumentCommandHandle, preview: boolean, callback: (result: Error | null) => void): void;
        export(self: DocumentHandle, path: string, options: FileExportOptionsHandle, exportAreaOrNull: FileExportAreaHandle | null, sizeOrNull: Size | null): DocumentExportRecordsHandle;
        exportAsync(self: DocumentHandle, path: string, options: FileExportOptionsHandle, exportAreaOrNull: FileExportAreaHandle | null, sizeOrNull: Size | null, callback: (result: Error | null, documentExportRecordsRef: DocumentExportRecordsHandle | null) => void): void;
        getColourProfile(self: DocumentHandle): ColourProfileHandle;
        getCurrent(): DocumentHandle;
        getCurrentAsync(callback: (result: Error | null, documentRef: DocumentHandle | null) => void): void;
        getCurrentSelection(self: DocumentHandle): SelectionHandle;
        getCurrentSnapshot(self: DocumentHandle): DocumentSnapshotHandle;
        getCurrentSnapshotHistoryIndex(self: DocumentHandle): number;
        getCurrentSnapshotIndex(self: DocumentHandle): number;
        getCurrentSpread(self: DocumentHandle): SpreadNodeHandle;
        getDpi(self: DocumentHandle): number;
        getFormat(self: DocumentHandle): RasterFormat;
        getHistory(self: DocumentHandle): DocumentHistoryHandle;
        getInsertionMode(self: DocumentHandle): InsertionMode;
        getMaskFormat(self: DocumentHandle): RasterFormat;
        getPath(self: DocumentHandle): string;
        getPersistentUuid(self: DocumentHandle): string;
        getRasterSelection(self: DocumentHandle): RasterSelectionHandle;
        getRootNode(self: DocumentHandle): DocumentNodeHandle;
        getSessionUuid(self: DocumentHandle): string;
        getSnapshot(self: DocumentHandle, index: number): DocumentSnapshotHandle;
        getSnapshotCount(self: DocumentHandle): number;
        getTitle(self: DocumentHandle): string;
        getUnitValueConverter(self: DocumentHandle): UnitValueConverterHandle;
        getUnits(self: DocumentHandle): UnitType;
        getViewDpi(self: DocumentHandle): number;
        isDirty(self: DocumentHandle): boolean;
        isEmbedded(self: DocumentHandle): boolean;
        isOpen(self: DocumentHandle): boolean;
        isReadOnly(self: DocumentHandle): boolean;
        isSameObject(self: DocumentHandle, other: DocumentHandle): boolean;
        load(path: string, optionsOrNull: LoadDocumentOptionsHandle | null): DocumentLoadResult;
        loadAsync(path: string, optionsOrNull: LoadDocumentOptionsHandle | null, callback: (err: Error | null, result: DocumentLoadResult | null) => void): void;
        loadFromResource(resource: ResourceHandle, optionsOrNull: LoadDocumentOptionsHandle | null): DocumentLoadResult;
        loadFromResourceAsync(resource: ResourceHandle, optionsOrNull: LoadDocumentOptionsHandle | null, callback: (err: Error | null, result: DocumentLoadResult | null) => void): void;
        mustSaveAs(self: DocumentHandle): boolean;
        needsSaving(self: DocumentHandle): boolean;
        save(self: DocumentHandle): void;
        saveAs(self: DocumentHandle, path: string): void;
        saveAsAsync(self: DocumentHandle, path: string, callback: (result: Error | null) => void): void;
        saveAsPackage(self: DocumentHandle, path: string, policy: PackageResourcesPolicy): void;
        saveAsPackageAsync(self: DocumentHandle, path: string, policy: PackageResourcesPolicy, callback: (result: Error | null) => void): void;
        saveAsync(self: DocumentHandle, callback: (result: Error | null) => void): void;
    }
    export const DocumentApi: DocumentApi;

}
