// Type declarations for the Affinity JavaScript SDK: module "affinity:application".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:application" {

    import { EnumerationResult, LogLevel } from "affinity:common";

    export enum BuildKind {
        AffinityRetail,
        AppStoreRetail,
        InternalAlpha,
        CustomerBeta,
        PublicBeta,
    }

    export enum EnvironmentPermission {
        FileSystem,
        Network,
        GenAI,
    }

    export enum UiParadigm {
        Desktop,
        Tablet,
    }

    export class HeapStatistics {
        totalHeapSize: number;
        totalHeapSizeExecutable: number;
        totalPhysicalSize: number;
        totalAvailableSize: number;
        totalGlobalHandlesSize: number;
        usedGlobalHandlesSize: number;
        usedHeapSize: number;
        heapSizeLimit: number;
        mallocedMemory: number;
        externalMemory: number;
        peakMallocedMemory: number;
        numberOfNativeContexts: number;
        numberOfDetachedContexts: number;
        doesZapGarbage: boolean;
    }

    export interface ApplicationApi {
        getArgC(): number;
        getArgV(): string[];
        getBuildKind(): BuildKind;
        getBuildVersion(): number;
        getCompileDate(): string;
        getDocumentVersion(): number;
        getMajorVersion(): number;
        getMinorVersion(): number;
        getPlatformName(): string;
        getProductCopyrightMessage(): string;
        getProductFullName(): string;
        getProductLongName(): string;
        getProductPrimaryFileExtension(): string;
        getProductShortName(): string;
        getProductVersionName(): string;
        getResourcesPath(): string;
        getRevisionVersion(): number;
        getShortVersion(): string;
        getSuiteFullName(): string;
        getUiParadigm(): UiParadigm;
        getUserDesktopPath(): string;
        getVersion(): string;
    }
    export const ApplicationApi: ApplicationApi;

    export interface ApplicationSettingsApi {
        getAllowCodeGenerationFromStrings(): boolean;
        getLoadPSDWithEditableText(): boolean;
        getUndoLimit(): number;
        setLoadPSDWithEditableText(value: boolean): void;
    }
    export const ApplicationSettingsApi: ApplicationSettingsApi;

    export interface EnvironmentApi {
        enumerateFileSystemRoots(callback: (root: string) => EnumerationResult): void;
        getConfiguration(): ConfigurationItemHandle;
        getHeapStatistics(): HeapStatistics;
        getLogLevel(): LogLevel;
        getResources(): ResourceBundleHandle;
        getSDKVersionStr(): string;
        getV8VersionStr(): string;
        hasPermission(permission: EnvironmentPermission): boolean;
        postTask(taskProc: () => void): void;
        quit(): void;
        setLogLevel(logLevel: LogLevel): void;
    }
    export const EnvironmentApi: EnvironmentApi;

    export interface ResourceApi {
        getName(self: ResourceHandle): string;
        getPath(self: ResourceHandle): string;
        getSize(self: ResourceHandle): number;
        readBytes(self: ResourceHandle): BufferHandle;
        readBytesAsync(self: ResourceHandle, callback: (errorCode: Error | null, buffer: BufferHandle | null) => void): void;
    }
    export const ResourceApi: ResourceApi;

    export interface ResourceBundleApi {
        containsNativePath(self: ResourceBundleHandle, path: string): boolean;
        createIterator(self: ResourceBundleHandle): ResourceIteratorHandle;
        enumerate(self: ResourceBundleHandle, callback: (resource: ResourceHandle) => EnumerationResult): void;
        get(self: ResourceBundleHandle, path: string): ResourceHandle;
    }
    export const ResourceBundleApi: ResourceBundleApi;

    export interface ResourceIteratorApi {
        getResource(self: ResourceIteratorHandle): ResourceHandle;
        isDone(self: ResourceIteratorHandle): boolean;
        next(self: ResourceIteratorHandle): void;
    }
    export const ResourceIteratorApi: ResourceIteratorApi;

}
