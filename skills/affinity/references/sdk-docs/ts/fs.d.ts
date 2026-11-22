// Type declarations for the Affinity JavaScript SDK: module "affinity:fs".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:fs" {

    export enum CopyOptions {
        None,
        SkipExisting,
        OverwriteExisting,
        UpdateExisting,
        Recursive,
        CopySymlinks,
        SkipSymlinks,
        DirectoriesOnly,
        CreateSymlinks,
        CreateHardLinks,
    }

    export enum FileOrigin {
        Begin,
        Current,
        End,
    }

    export enum FilePermissions {
        None,
        OwnerRead,
        OwnerWrite,
        OwnerExec,
        OwnerAll,
        GroupRead,
        GroupWrite,
        GroupExec,
        GroupAll,
        OthersRead,
        OthersWrite,
        OthersExec,
        OthersAll,
        All,
        SetUid,
        SetGid,
        StickyBit,
        Mask,
        Unknown,
    }

    export enum PathType {
        None,
        NotFound,
        File,
        Directory,
        Symlink,
        Block,
        Character,
        Fifo,
        Socket,
        Unknown,
    }

    export enum PermOptions {
        Replace,
        Add,
        Remove,
        NoFollow,
    }

    export class FileSystemSpace {
        available: number;
        free: number;
        capacity: number;
    }

    export interface DirectoryIteratorApi {
        create(path: string): DirectoryIteratorHandle;
        getFileSize(self: DirectoryIteratorHandle, asBigInt: boolean): number;
        getFileStatus(self: DirectoryIteratorHandle): FileStatusHandle;
        getPath(self: DirectoryIteratorHandle): string;
        getSymlinkStatus(self: DirectoryIteratorHandle): FileStatusHandle;
        isDone(self: DirectoryIteratorHandle): boolean;
        next(self: DirectoryIteratorHandle): void;
    }
    export const DirectoryIteratorApi: DirectoryIteratorApi;

    export interface FileApi {
        close(self: FileHandle): void;
        closeAsync(self: FileHandle, cancelOps: boolean, callback: (errorCode: Error | null) => void): void;
        create(): FileHandle;
        flush(self: FileHandle): void;
        flushAsync(self: FileHandle, callback: (errorCode: Error | null) => void): void;
        getLength(self: FileHandle, asBigInt: boolean): number;
        getLengthAsync(self: FileHandle, callback: (errorCode: Error | null, length: number) => void, asBigInt: boolean): void;
        isEof(self: FileHandle): boolean;
        isEofAsync(self: FileHandle, callback: (errorCode: Error | null, isEof: boolean) => void): void;
        isOpen(self: FileHandle): boolean;
        open(self: FileHandle, path: string, mode: string): void;
        openFromResource(self: FileHandle, resource: ResourceHandle): void;
        read(self: FileHandle, buffer: BufferHandle | ArrayBuffer | SharedArrayBuffer | ArrayBufferView, length: number): number;
        readAsync(self: FileHandle, buffer: BufferHandle | ArrayBuffer | SharedArrayBuffer | ArrayBufferView, offset: number, length: number, position: number, callback: (err: Error | null, bytesRead: number) => void): void;
        seek(self: FileHandle, offset: number, origin: FileOrigin): void;
        seekAsync(self: FileHandle, offset: number, origin: FileOrigin, callback: (errorCode: Error | null) => void): void;
        tell(self: FileHandle, asBigInt: boolean): number;
        tellAsync(self: FileHandle, asBigInt: boolean, callback: (errorCode: Error | null, pos: number) => void): void;
        write(self: FileHandle, buffer: BufferHandle | ArrayBuffer | SharedArrayBuffer | ArrayBufferView, length: number): number;
        writeAsync(self: FileHandle, buffer: BufferHandle | ArrayBuffer | SharedArrayBuffer | ArrayBufferView, offset: number, length: number, position: number, callback: (err: Error | null, bytesWritten: number) => void): void;
    }
    export const FileApi: FileApi;

    export interface FileStatusApi {
        clone(self: FileStatusHandle): FileStatusHandle;
        getPermissions(self: FileStatusHandle): FilePermissions;
        getType(self: FileStatusHandle): PathType;
    }
    export const FileStatusApi: FileStatusApi;

    export interface FileSystemApi {
        areEquivalent(path1: string, path2: string): boolean;
        areEquivalentAsync(path1: string, path2: string, callback: (errorCode: Error | null, areEquivalent: boolean) => void): void;
        copy(from: string, to: string, options: CopyOptions): void;
        copyAsync(src: string, dest: string, options: CopyOptions, callback: (errorCode: Error | null) => void): void;
        copyFile(from: string, to: string, options: CopyOptions): void;
        copyFileAsync(src: string, dest: string, options: CopyOptions, callback: (errorCode: Error | null) => void): void;
        createDirectories(path: string): void;
        createDirectoriesAsync(path: string, callback: (errorCode: Error | null) => void): void;
        createDirectory(path: string): void;
        createDirectoryAsync(path: string, callback: (errorCode: Error | null) => void): void;
        createDirectorySymlink(target: string, link: string): void;
        createDirectorySymlinkAsync(target: string, link: string, callback: (errorCode: Error | null) => void): void;
        createSymlink(target: string, link: string): void;
        createSymlinkAsync(target: string, link: string, callback: (errorCode: Error | null) => void): void;
        exists(path: string): boolean;
        existsAsync(path: string, callback: (errorCode: Error | null, exists: boolean) => void): void;
        getAbsolute(path: string): string;
        getAbsoluteAsync(path: string, callback: (errorCode: Error | null, absolutePath: string) => void): void;
        getCanonical(target: string): string;
        getCanonicalAsync(target: string, callback: (errorCode: Error | null, canonicalPath: string) => void): void;
        getFileSize(path: string, asBigInt: boolean): number;
        getFileSizeAsync(path: string, callback: (errorCode: Error | null, size: number) => void, asBigInt: boolean): void;
        getFileStatus(path: string): FileStatusHandle;
        getFileStatusAsync(path: string, callback: (errorCode: Error | null, fileStatus: FileStatusHandle | null) => void): void;
        getHardLinkCount(path: string): number;
        getHardLinkCountAsync(path: string, callback: (errorCode: Error | null, num: number) => void): void;
        getSpace(path: string, asBigInt: boolean): FileSystemSpace;
        getSpaceAsync(path: string, callback: (err: Error | null, space: FileSystemSpace | null) => void, asBigInt: boolean): void;
        getSymlinkStatus(path: string): FileStatusHandle;
        getSymlinkStatusAsync(path: string, callback: (errorCode: Error | null, fileStatus: FileStatusHandle | null) => void): void;
        getWeaklyCanonical(target: string): string;
        getWeaklyCanonicalAsync(target: string, callback: (errorCode: Error | null, canonicalPath: string) => void): void;
        isBlockFile(path: string): boolean;
        isBlockFileAsync(path: string, callback: (errorCode: Error | null, isBlockFile: boolean) => void): void;
        isCharacterFile(path: string): boolean;
        isCharacterFileAsync(path: string, callback: (errorCode: Error | null, isCharacterFile: boolean) => void): void;
        isDirectory(path: string): boolean;
        isDirectoryAsync(path: string, callback: (errorCode: Error | null, isDirectory: boolean) => void): void;
        isEmpty(path: string): boolean;
        isEmptyAsync(path: string, callback: (errorCode: Error | null, isEmpty: boolean) => void): void;
        isFifo(path: string): boolean;
        isFifoAsync(path: string, callback: (errorCode: Error | null, isFifo: boolean) => void): void;
        isOther(path: string): boolean;
        isOtherAsync(path: string, callback: (errorCode: Error | null, isOther: boolean) => void): void;
        isRegularFile(path: string): boolean;
        isRegularFileAsync(path: string, callback: (errorCode: Error | null, isRegularFile: boolean) => void): void;
        isSocket(path: string): boolean;
        isSocketAsync(path: string, callback: (errorCode: Error | null, isSocket: boolean) => void): void;
        isSymlink(path: string): boolean;
        isSymlinkAsync(path: string, callback: (errorCode: Error | null, isSymlink: boolean) => void): void;
        readSymlink(path: string): string;
        readSymlinkAsync(path: string, callback: (errorCode: Error | null, target: string) => void): void;
        remove(path: string): void;
        removeAll(path: string): void;
        removeAllAsync(path: string, callback: (errorCode: Error | null) => void): void;
        removeAsync(path: string, callback: (errorCode: Error | null) => void): void;
        rename(oldPath: string, newPath: string): void;
        renameAsync(oldPath: string, newPath: string, callback: (errorCode: Error | null) => void): void;
        resizeFile(path: string, newSize: number): void;
        resizeFileAsync(path: string, newSize: number, callback: (errorCode: Error | null) => void): void;
        setFilePermissions(path: string, filePermissions: FilePermissions, permOptions: PermOptions): void;
        setFilePermissionsAsync(path: string, filePermissions: FilePermissions, permOptions: PermOptions, callback: (errorCode: Error | null) => void): void;
    }
    export const FileSystemApi: FileSystemApi;

}
