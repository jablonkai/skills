'use strict';

const { CopyOptions, DirectoryIteratorApi, FileApi, FileOrigin, FilePermissions, FileStatusApi, FileSystemApi, PathType, PermOptions } = require('affinity:fs');
const { Buffer } = require('./buffer');
const { Collection} = require('./collection.js');
const { HandleObject } = require('./handleobject.js');

class File extends HandleObject {
    constructor(path, mode) {
        super(FileApi.create());
        if (path != null) { // checks for undefined too
            this.open(path, mode);
        }
    }
        
    get [Symbol.toStringTag]() {
        return 'File';
    }
    
    static length(path) {
        return new File(path, 'rb').length;
    }
    
    static size(path) {
        return File.length(path);
    }
    
    open(path, mode) {
        if (!mode)
            mode = 'r';
        return FileApi.open(this.handle, path, mode);
    }
    
    seek(offset, origin) {
        return FileApi.seek(this.handle, offset, origin);
    }
    
    read(buffer, length) {
        if (buffer instanceof Buffer) {
            return FileApi.read(this.handle, buffer.handle, length);
        }
        return FileApi.read(this.handle, buffer, length);
    }
    
    write(buffer, length) {
        if (buffer instanceof Buffer) {
            return FileApi.write(this.handle, buffer.handle, length);
        }
        return FileApi.write(this.handle, buffer, length);
    }

    writeStringAsUtf8(str) {
        let buf = Buffer.utf8(str);
        return FileApi.write(this.handle, buf.handle, buf.length);
    }

    writeStringAsUtf16(str) {
        let buf = Buffer.utf16(str);
        return FileApi.write(this.handle, buf.handle, buf.length);
    }

    writeString(str) {
        return this.writeStringAsUtf8(str);
    }
    
    tell() {
        return FileApi.tell(this.handle);
    }
    
    get isEof() {
        return FileApi.isEof(this.handle);
    }
    
    get isOpen() {
        return FileApi.isOpen(this.handle);
    }
    
    flush() {
        return FileApi.flush(this.handle);
    }
    
    getLength(asBigInt) {
        return FileApi.getLength(this.handle, asBigInt);
    }
    
    close() {
        return FileApi.close(this.handle);
    }

    seekAsync(offset, origin, callback) {
        return FileApi.seekAsync(this.handle, offset, origin, callback);
    }
    
    readAsync(buffer, offset, length, position, callback) {
        if (buffer instanceof Buffer) {
            let wrapped = callback;
            if (typeof callback === 'function') {
                wrapped = (errorCode, numBytes) => callback(errorCode, numBytes, buffer);
            }
            return FileApi.readAsync(this.handle, buffer.handle, offset, length, position, wrapped);
        }
        return FileApi.readAsync(this.handle, buffer, offset, length, position, callback);
    }
    
    writeAsync(buffer, offset, length, position, callback) {
        if (buffer instanceof Buffer) {
            let wrapped = callback;
            if (typeof callback === 'function') {
                wrapped = (errorCode, numBytes) => callback(errorCode, numBytes, buffer);
            }
            return FileApi.writeAsync(this.handle, buffer.handle, offset, length, position, wrapped);
        }
        return FileApi.writeAsync(this.handle, buffer, offset, length, position, callback);
    }

    writeStringAsUtf8Async(str, position, callback) {
        let buf = Buffer.utf8(str);
        return FileApi.writeAsync(this.handle, buf.handle, 0, buf.length, position, callback);
    }

    writeStringAsUtf16Async(str, position, callback) {
        let buf = Buffer.utf16(str);
        return FileApi.writeAsync(this.handle, buf.handle, 0, buf.length, position, callback);
    }

    writeStringAsync(str, position, callback) {
        return this.writeStringAsUtf8Async(str, position, callback);
    }
    
    tellAsync(callback) {
        return FileApi.tellAsync(this.handle, callback);
    }
    
    isEofAsync(callback) {
        return FileApi.isEofAsync(this.handle, callback);
    }
    
    flushAsync(callback) {
        return FileApi.flushAsync(this.handle, callback);
    }
    
    getLengthAsync(callback, asBigInt) {
        return FileApi.getLengthAsync(this.handle, callback, asBigInt);
    }

    closeAsync(cancelOps, callback) {
        return FileApi.closeAsync(this.handle, cancelOps, callback);
    }
    
    get position() {
        return this.tell();
    }
    
    set position(value) {
        this.seek(value, FileOrigin.Begin);
    }
    
    get isEof() {
        return FileApi.isEof(this.handle);
    }
    
    get length() {
        return FileApi.getLength(this.handle);
    }
    
    get size() {
        return this.length;
    }
        
    static readAll(path) {
        let f = new File(path, 'rb');
        let buf = Buffer.create(f.length);
        f.read(buf, buf.length);
        f.close();
        return buf;
    }
    
    static readAllAsync(path, callback) {
        try {
            const f = new File(path, 'rb');
            return f.getLengthAsync((err, length) => {
                if (err) {
                    f.close();
                    callback(err, 0, null);
                }
                else {
                    f.readAsync(Buffer.create(length), 0, length, -1, (err, bytesRead, buf) => {
                        f.close();
                        callback(err, bytesRead, buf);
                    });
                }
            });
        }
        catch (err) {
            callback(err, 0, null);
        }
    }
    
    #promises;
    get promises() {
        if (!this.#promises)
            this.#promises = new FilePromises(this);
        return this.#promises;
    }
    
}


class FilePromises {
    #file;
    constructor(file) {
        this.#file = file;
    }
    
    // get the original file back
    get file() {
        return this.#file;
    }
        
    seek(offset, origin) {
        let file = this.file;
        return new Promise((resolve, reject) => {
            file.seekAsync(offset, origin, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    read(buffer, offset, length, position) {
        let file = this.file;
        return new Promise((resolve, reject) => {
            file.readAsync(buffer, offset, length, position, (err, numBytes, buffer) => {
                if (err)
                    reject(err);
                else
                    resolve({bytesRead:numBytes, buffer:buffer});
            });
        });
    }
    
    write(buffer, offset, length, position) {
        let file = this.file;
        return new Promise((resolve, reject) => {
            file.writeAsync(buffer, offset, length, position, (err, numBytes, buffer) => {
                if (err)
                    reject(err);
                else
                    resolve({bytesWritten:numBytes, buffer:buffer});
            });
        });
    }
    
    tell() {
        let file = this.file;
        return new Promise((resolve, reject) => {
            file.tellAsync((err, pos) => {
                if (err)
                    reject(err);
                else
                    resolve(pos);
            });
        });
    }
    
    isEof() {
        let file = this.file;
        return new Promise((resolve, reject) => {
            file.isEofAsync((err, isEof) => {
                if (err)
                    reject(err);
                else
                    resolve(isEof);
            });
        });
    }
    
    flush() {
        let file = this.file;
        return new Promise((resolve, reject) => {
            file.flushAsync((err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    getLength(asBigInt) {
        let file = this.file;
        return new Promise((resolve, reject) => {
            file.getLengthAsync((err, pos) => {
                if (err)
                    reject(err);
                else
                    resolve(pos);
            }, asBigInt);
        });
    }
    
    get position() {
        return this.tell();
    }
    
    get eof() {
        return this.isEof();
    }
    
    get length() {
        return this.getLength();
    }
}


class DirectoryIterator extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    static at(path) {
        return new DirectoryIterator(DirectoryIteratorApi.create(path));
    }
    
    get [Symbol.toStringTag]() {
        return 'DirectoryIterator';
    }
    
    isDone() {
        return DirectoryIteratorApi.isDone(this.handle);
    }
    
    next() {
        DirectoryIteratorApi.next(this.handle);
    }
    
    get path() {
        return DirectoryIteratorApi.getPath(this.handle);
    }
    
    get fileSize() {
        return DirectoryIteratorApi.getFileSize(this.handle);
    }
    
    getFileSize(asBigInt) {
        return DirectoryIteratorApi.getFileSize(this.handle, asBigInt);
    }

    get fileStatus() {
        return new FileStatus(DirectoryIteratorApi.getFileStatus(this.handle));
    }

    get symlinkStatus() {
        return new FileStatus(DirectoryIteratorApi.getSymlinkStatus(this.handle));
    }

    entry(resolveSymlink = true) {
        return {
            path: this.path,
            status: resolveSymlink ? this.fileStatus : this.symlinkStatus,
        };
    }

    get done() {
        return this.isDone();
    }
}


class DirectoryEntries extends Collection {
    #path;
    constructor(path, resolveSymlink = true) {
        const gen = function*() {
            const iter = DirectoryIterator.at(path);
            while (!iter.done) {
                yield iter.entry(resolveSymlink);
                iter.next();
            }
        };
        super(gen);
        this.#path = path;
    }
    
    get all() {
        return new RecursiveDirectoryEntries(this.#path);
    }
    
    get files() {
        return this.filter(entry => entry.status.type.value == PathType.File);
    }
    
    get filePaths() {
        return this.files.map(item => item.path);
    }
}


class RecursiveDirectoryEntries extends Collection {
    #path;
    constructor(path, resolveSymlink = true) {
        const gen = function*() {
            const iter = DirectoryIterator.at(path);
            while (!iter.done) {
                const entry = iter.entry(resolveSymlink);
                yield entry;
                if (entry.status.type.value == PathType.Directory) {
                    const sub = new RecursiveDirectoryEntries(entry.path);
                    for (const e of sub) {
                        yield e;
                    }
                }
                iter.next();
            }
        };
        super(gen);
        this.#path = path;
    }
    
    get files() {
        return this.filter(entry => entry.status.type.value == PathType.File);
    }
    
    get filePaths() {
        return this.files.map(item => item.path);
    }
}


class Directory {
    #path;
    constructor(path) {
        this.#path = path;
    }
    
    get path() {
        return this.#path;
    }

    get entries() {
        return new DirectoryEntries(this.#path);
    }
}

class FileStatus extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FileStatus';
    }

    get permissions() {
        return FileStatusApi.getPermissions(this.handle);
    }

    get type() {
        return FileStatusApi.getType(this.handle);
    }

    // "ls -l" !
    get statusString() {
        const type = this.type.value;

        let str;
        if (type == PathType.File)
            str = '-';
        else if (type == PathType.Block)
            str = 'b';
        else if (type == PathType.Character)
            str = 'c';
        else if (type == PathType.Directory)
            str = 'd';
        else if (type == PathType.Symlink)
            str = 'l';
        else if (type == PathType.Fifo)
            str = 'p';
        else if (type == PathType.Socket)
            str = 's';
        else // Unsupported (C,D,M,n,P) and "some other file type" (?)
            str = '?';

        const perms = this.permissions;

        str += (perms & FilePermissions.OwnerRead) ? 'r' : '-';
        str += (perms & FilePermissions.OwnerWrite) ? 'w' : '-';
        if (perms & FilePermissions.SetUid)
            str += (perms & FilePermissions.OwnerExec) ? 's' : 'S';
        else
            str += (perms & FilePermissions.OwnerExec) ? 'x' : '-';

        str += (perms & FilePermissions.GroupRead) ? 'r' : '-';
        str += (perms & FilePermissions.GroupWrite) ? 'w' : '-';
        if (perms & FilePermissions.SetGid)
            str += (perms & FilePermissions.GroupExec) ? 's' : 'S';
        else
            str += (perms & FilePermissions.GroupExec) ? 'x' : '-';

        str += (perms & FilePermissions.OthersRead) ? 'r' : '-';
        str += (perms & FilePermissions.OthersWrite) ? 'w' : '-';
        if (perms & FilePermissions.StickyBit)
            str += (perms & FilePermissions.OthersExec) ? 't' : 'T';
        else
            str += (perms & FilePermissions.OthersExec) ? 'x' : '-';

        return str;
    }

    clone() {
        return new FileStatus(FileStatusApi.clone(this.handle));
    }
}

class FileSystemPromises
{
    static areEquivalent(path1, path2) {
        return new Promise((resolve, reject) => {
            FileSystemApi.areEquivalentAsync(path1, path2, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static copy(path1, path2, options) {
        return new Promise((resolve, reject) => {
            FileSystemApi.copyAsync(path1, path2, options, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    static copyFile(path1, path2, options) {
        return new Promise((resolve, reject) => {
            FileSystemApi.copyFileAsync(path1, path2, options, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }

    static createDirectories(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.createDirectoriesAsync(path, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }

    static createDirectory(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.createDirectoryAsync(path, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    static createDirectorySymlink(target, link) {
        return new Promise((resolve, reject) => {
            FileSystemApi.createDirectorySymlinkAsync(target, link, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    static createSymlink(target, link) {
        return new Promise((resolve, reject) => {
            FileSystemApi.createSymlinkAsync(target, link, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    static exists(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.existsAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static getAbsolute(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.getAbsoluteAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static getCanonical(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.getCanonicalAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static getFileSize(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.getFileSizeAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }

    static getFileStatus(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.getFileStatusAsync(path, (err, filestatus) => {
                if (err)
                    reject(err);
                else
                    resolve(new FileStatus(filestatus));
            });
        });
    }

    static getHardLinkCount(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.getHardLinkCountAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static getSpace(path, useBigInts) {
        return new Promise((resolve, reject) => {
            FileSystemApi.getSpaceAsync(path, (err, available, free, capacity) => {
                if (err)
                    reject(err);
                else
                    resolve({available:available, free:free, capacity:capacity});
            }, useBigInts);
        });
    }

    static getSymlinkStatus(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.getSymlinkStatusAsync(path, (err, filestatus) => {
                if (err)
                    reject(err);
                else
                    resolve(new FileStatus(filestatus));
            });
        });
    }

    static getWeaklyCanonical(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.getWeaklyCanonicalAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isBlockFile(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isBlockFileAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isCharacterFile(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isCharacterFileAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isDirectory(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isDirectoryAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isEmpty(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isEmptyAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isFifo(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isFifoAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isOther(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isOtherAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isRegularFile(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isRegularFileAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isSocket(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isSocketAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }
    
    static isSymlink(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.isSymlinkAsync(path, (err, res) => {
                if (err)
                    reject(err);
                else
                    resolve(res);
            });
        });
    }

    static readSymlink(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.readSymlinkAsync(path, (err, path) => {
                if (err)
                    reject(err);
                else
                    resolve(path);
            });
        });
    }

    static remove(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.removeAsync(path, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    static removeAll(path) {
        return new Promise((resolve, reject) => {
            FileSystemApi.removeAllAsync(path, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    static rename(oldPath, newPath) {
        return new Promise((resolve, reject) => {
            FileSystemApi.renameAsync(oldPath, newPath, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }
    
    static resizeFile(path, newSize) {
        return new Promise((resolve, reject) => {
            FileSystemApi.resizeFileAsync(path, newSize, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }

    static setFilePermissions(path, filePermissions, permOptions) {
        return new Promise((resolve, reject) => {
            FileSystemApi.setFilePermissionsAsync(path, filePermissions, permOptions, (err) => {
                if (err)
                    reject(err);
                else
                    resolve();
            });
        });
    }

    static open(path, mode) {
        return new Promise((resolve, reject) => {
            try {
                resolve(new File(path, mode));
            }
            catch (err) {
                reject(err);
            }
        });
    }

    static readAll(path) {
        return FileSystemPromises.open(path)
            .then(file => file.promises.length.then(length => {
                const buffer = Buffer.create(length);
                return file.promises.read(buffer, 0, length)
                    .then(() => { return buffer;})
                    .finally(() => file.close());
            }));
    }
}

module.exports.CopyOptions = CopyOptions;
module.exports.DirectoryIterator = DirectoryIterator;
module.exports.Directory = Directory;
module.exports.File = File;
module.exports.FileOrigin = FileOrigin;
module.exports.FilePermissions = FilePermissions;
module.exports.FileStatus = FileStatus;
module.exports.PathType = PathType;
module.exports.PermOptions = PermOptions;
module.exports.FileSystemApi = FileSystemApi;
module.exports.FileSystemPromises = FileSystemPromises;

// convenience names
module.exports.fs = FileSystemApi;
module.exports.promises = FileSystemPromises;
Object.assign(module.exports, Object.getPrototypeOf(FileSystemApi));
