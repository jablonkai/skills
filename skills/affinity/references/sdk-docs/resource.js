/*
BSD 3-Clause License

Copyright (c) 2026, Canva Pty Ltd.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

Neither the name of the copyright holder nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

'use strict';

const { ResourceApi, ResourceBundleApi, ResourceIteratorApi } = require('affinity:application');
const { EnumerationResult } = require('affinity:common');
const { Buffer } = require('./buffer.js');
const { Collection } = require('./collection.js');
const { HandleObject } = require('./handleobject.js');

// A file in the running script's resource bundle, obtained from Environment.resources. Paths are
// bundle-relative with '/' separators.
class Resource extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Resource';
    }

    get name() {
        return ResourceApi.getName(this.handle);
    }

    get path() {
        return ResourceApi.getPath(this.handle);
    }

    // uncompressed byte length; never loads the resource
    get size() {
        return ResourceApi.getSize(this.handle);
    }

    // the whole resource as a Buffer; repeated calls re-read
    readBytes() {
        return new Buffer(ResourceApi.readBytes(this.handle));
    }

    readBytesAsync(callback) {
        return ResourceApi.readBytesAsync(this.handle, (err, h) => callback(err, h == null ? null : new Buffer(h)));
    }

    // the whole resource decoded as text; encoding as for Buffer.toString, UTF-8 by default
    readString(encoding = 'utf8') {
        return this.readBytes().toString(encoding);
    }

    #promises;
    get promises() {
        if (!this.#promises)
            this.#promises = new ResourcePromises(this);
        return this.#promises;
    }
}


class ResourcePromises {
    #resource;
    constructor(resource) {
        this.#resource = resource;
    }

    get resource() {
        return this.#resource;
    }

    readBytes() {
        const resource = this.resource;
        return new Promise((resolve, reject) => {
            resource.readBytesAsync((err, buffer) => {
                if (err)
                    reject(err);
                else
                    resolve(buffer);
            });
        });
    }

    readString(encoding = 'utf8') {
        return this.readBytes().then(buffer => buffer.toString(encoding));
    }
}


// The running script's resource bundle: a flat set of resources keyed by path. Any directory
// structure is whatever you read into a common prefix. A leading '/' is accepted, '.' and empty
// segments collapse, '..' may climb but not above the root.
class ResourceBundle extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ResourceBundle';
    }

    // the resource at path, or null when nothing is there; throws for a malformed path
    get(path) {
        const h = ResourceBundleApi.get(this.handle, path);
        return (h == null) ? null : new Resource(h);
    }

    // every resource, in byte order of path; the callback returns an EnumerationResult
    enumerate(callback) {
        if (typeof callback === 'function') {
            function wrapped(resourceHandle) {
                return callback(new Resource(resourceHandle));
            }
            return ResourceBundleApi.enumerate(this.handle, wrapped);
        }
        return ResourceBundleApi.enumerate(this.handle, callback);
    }

    // a forward-only iterator positioned on the first resource; live, in the backend's natural order
    // (use enumerate for byte order of path)
    iterator() {
        return new ResourceIterator(ResourceBundleApi.createIterator(this.handle));
    }

    // one resource at a time, so `for (const r of Environment.resources)` never builds an array
    *[Symbol.iterator]() {
        for (const it = this.iterator(); !it.done; it.next())
            yield it.resource;
    }

    // every resource as an array, in byte order of path
    get all() {
        let res = [];
        this.enumerate(resource => {
            res.push(resource);
            return EnumerationResult.Continue;
        });
        return res;
    }

    // every resource as a lazy Collection; each pass runs a fresh iterator, so it can be walked more than once
    get items() {
        return Collection.over(this);
    }
}


class ResourceIterator extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ResourceIterator';
    }

    isDone() {
        return ResourceIteratorApi.isDone(this.handle);
    }

    get done() {
        return this.isDone();
    }

    // advances; throws once done
    next() {
        ResourceIteratorApi.next(this.handle);
    }

    // the Resource at the current position; throws once done
    get resource() {
        return new Resource(ResourceIteratorApi.getResource(this.handle));
    }
}


module.exports.Resource = Resource;
module.exports.ResourceBundle = ResourceBundle;
module.exports.ResourceIterator = ResourceIterator;
