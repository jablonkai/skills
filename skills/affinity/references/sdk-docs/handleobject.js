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

// A live view of a struct-valued member (e.g. a point, or one channel of a set)
// that a HandleObject exposes through get/set functions on its API.
//
// Reads fetch the current value from the handle each time; writing one field
// re-sends the whole struct with that field replaced. The handle therefore stays
// the single source of truth, and both of these keep working for scripts:
//
//     params.position = {x: 100, y: 200};
//     params.position.x = 567.9;
//
// `fields` lists the struct's field names; `get` returns the current struct from
// the API; `set` sends a struct to the API.
function liveStruct(fields, get, set) {
    const view = {};
    for (const field of fields) {
        Object.defineProperty(view, field, {
            enumerable: true,
            get: () => get()[field],
            set: value => set({...get(), [field]: value}),
        });
    }
    Object.defineProperty(view, 'toJSON', {value: () => get()});
    return view;
}

// liveStruct specialised for an {x, y} point.
function livePoint(get, set) {
    return liveStruct(['x', 'y'], get, set);
}

// An integer-looking property key ("0", "5", "-1"), or null for anything else.
function integerKey(property) {
    return typeof property === 'string' && /^-?(0|[1-9][0-9]*)$/.test(property) ? Number(property) : null;
}

// An array-like live view over `count` struct-valued elements reached through
// indexed get/set functions on the API (e.g. the per-channel parameters of an
// adjustment). Element reads return a liveStruct, so both of these write through:
//
//     params.channelParameters[1] = {gamma: 1.5, ...};
//     params.channelParameters[1].gamma = 1.5;
//
// Reading an out-of-range index gives undefined; writing one throws a RangeError,
// as the native array proxies did.
//
// `fields` lists the element struct's field names; `get(index)` returns the current
// element from the API; `set(index, value)` sends an element to the API.
function liveStructArray(count, fields, get, set) {
    const view = {};
    for (let index = 0; index < count; ++index) {
        Object.defineProperty(view, index, {
            enumerable: true,
            get: () => liveStruct(fields, () => get(index), value => set(index, value)),
            set: value => set(index, value),
        });
    }
    Object.defineProperty(view, 'length', {value: count});
    Object.defineProperty(view, Symbol.iterator, {value: function* () {
        for (let index = 0; index < count; ++index) {
            yield view[index];
        }
    }});
    Object.defineProperty(view, 'toJSON', {value: () => Array.from({length: count}, (_, index) => get(index))});
    return new Proxy(view, {
        set(target, property, value, receiver) {
            const index = integerKey(property);
            if (index !== null && (index < 0 || index >= count)) {
                throw new RangeError('index out of range');
            }
            return Reflect.set(target, property, value, receiver);
        },
    });
}

// Whole-array assignment for a liveStructArray-backed member: sends elements 0 to
// count - 1 of `values` (an array, or another live view) to the API through
// `set(index, value)`. Each element must be an object; `typeName` names the
// element type in the error.
function setStructArray(count, values, set, typeName) {
    if (values === null || typeof values !== 'object') {
        throw new TypeError('expected an array of ' + count + ' ' + typeName);
    }
    for (let index = 0; index < count; ++index) {
        const value = values[index];
        if (value === null || typeof value !== 'object') {
            throw new TypeError('expected ' + typeName + ' at index ' + index);
        }
        set(index, value);
    }
}

module.exports.HandleObject = HandleObject;
module.exports.liveStruct = liveStruct;
module.exports.livePoint = livePoint;
module.exports.liveStructArray = liveStructArray;
module.exports.setStructArray = setStructArray;
