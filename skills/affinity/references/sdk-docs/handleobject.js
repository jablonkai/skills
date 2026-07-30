'use strict';

// An object with a private, immutable handle.
class HandleObject {
    #handle;

    constructor(handle) {
        if (handle == null) {
            throw new Error("Invalid handle");
        }
        this.#handle = handle;
    }

    get handle() {
        return this.#handle;
    }
}

module.exports.HandleObject = HandleObject;
