'use strict';

const { BufferApi } = require('affinity:buffer');
const { SpanCollection } = require('./collection.js');
const { HandleObject } = require('./handleobject.js');

// The highest codepoint that can be encoded with 1 byte in UTF-8
const UTF8_1_MAX = 0x7F;
// The highest codepoint that can be encoded with 2 bytes in UTF-8
const UTF8_2_MAX = 0x7FF;
// The highest codepoint that can be encoded with 3 bytes in UTF-8
const UTF8_3_MAX = 0xFFFF;
// The highest codepoint that can be encoded with 4 bytes in UTF-8
const UTF8_4_MAX = 0x10FFFF;
// If a character, masked with UTF8_CONTINUATION_MASK, matches this value, it is a UTF-8 continuation byte
const UTF8_CONTINUATION_VALUE = 0x80;
// The mask to a apply to a character before testing it against UTF8_CONTINUATION_VALUE
const UTF8_CONTINUATION_MASK = 0xC0;
// The number of bits of a codepoint that are contained in a UTF-8 continuation byte
const UTF8_CONTINUATION_CODEPOINT_BITS = 6;

const utf8_leading_bytes =
[
    // mask, value
    [ 0x80, 0x00 ], // 0xxxxxxx
    [ 0xE0, 0xC0 ], // 110xxxxx
    [ 0xF0, 0xE0 ], // 1110xxxx
    [ 0xF8, 0xF0 ]  // 11110xxx
];

function calculate_utf8_len(codepoint) {
    if (codepoint <= UTF8_1_MAX)
        return 1;

    if (codepoint <= UTF8_2_MAX)
        return 2;

    if (codepoint <= UTF8_3_MAX)
        return 3;

    return 4;
}

function encode_utf8(codepoint, uint8Array, len, index)
{
    const size = calculate_utf8_len(codepoint);
    
    // Not enough space left on the string
    if (index + size > len)
        return 0;

    // Write the continuation bytes in reverse order first
    for (let cont_index = size - 1; cont_index > 0; cont_index--)
    {
        let cont = codepoint & ~UTF8_CONTINUATION_MASK;
        cont |= UTF8_CONTINUATION_VALUE;

        uint8Array[index + cont_index] = cont;
        codepoint >>= UTF8_CONTINUATION_CODEPOINT_BITS;
    }

    // Write the leading byte
    let pattern = utf8_leading_bytes[size - 1];
    let lead = codepoint & ~(pattern[0]);
    lead |= pattern[1];
    uint8Array[index] = lead;

    return size;
}



class Buffer extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Buffer';
    }

    *[Symbol.iterator]() {
        const arr = this.array;
        for (const item of arr) {
            yield item;
        }
    }

    static create(sz) {
        return new Buffer(BufferApi.create(sz));
    }

    clone() {
        return new Buffer(BufferApi.clone(this.handle));
    }

    static #convStart(start, length) {
        if (start == null)
            return 0;
        else if (start < 0)
            return Math.max(0, start + length);
        else
            return start;
    }

    static #convEnd(end, length) {
        if (end == null || end >= length)
            return length;
        else if (end < 0)
            return Math.max(0, end + length);
        else
            return Math.min(end, length);
    }

    span(start, end) {
        // start and end follow the same rules as Array.splice()
        const length = this.length;
        
        start = Buffer.#convStart(start, length);
        if (start >= length)
            return Buffer.create(0);
        
        end = Buffer.#convEnd(end, length);
        if (end <= start)
            return Buffer.create(0);

        return new Buffer(BufferApi.createSpan(this.handle, start, end - start));
    }

    slice(start, end) {
        // start and end follow the same rules as Array.splice()
        const length = this.length;
        
        start = Buffer.#convStart(start, length);
        if (start >= length)
            return Buffer.create(0);
        
        end = Buffer.#convEnd(end, length);
        if (end <= start)
            return Buffer.create(0);
        
        return new Buffer(BufferApi.createSlice(this.handle, start, end - start));
    }

    get size() {
        return BufferApi.getSize(this.handle);
    }

    get arrayBuffer() {
        return BufferApi.getArrayBuffer(this.handle);
    }

    equals(other) {
        return BufferApi.equals(this.handle, other.handle);
    }

    compare(other) {
        return BufferApi.compare(this.handle, other.handle);
    }

    compareSome(start1, end1, other, start2, end2) {
        const length1 = this.length;
        const length2 = other.length;
        start1 = Buffer.#convStart(start1, length1);
        end1 = Buffer.#convEnd(end1, length1);
        start2 = Buffer.#convStart(start2, length2);
        end2 = Buffer.#convEnd(end2, length2);
        return BufferApi.compareSome(this.handle, start1, end1 - start1, other.handle, start2, end2 - start2);
    }

    // optional args are encoding[, start[, end]]
    toString() {
        return BufferApi.toString(this.handle, ...arguments);
    }

    // aliases
    get length() {
        return BufferApi.getSize(this.handle);
    }

    get buffer() {
        return BufferApi.getArrayBuffer(this.handle);
    }

    // helpers
    get array() {
        return new Uint8Array(this.buffer);
    }

    get items() {
        return new SpanCollection(this.array);
    }

    concat(other) {
        const length = this.length;
        const otherLength = other.length;
        const res = Buffer.create(length + otherLength);
        const arr = res.array;
        arr.set(this.array);
        arr.set(other.array, length);  
        return res;
    }

    reverse() {
        this.array.reverse();
        return this;
    }

    static utf16(str) {
        const buf = Buffer.create(str.length * 2);
        const bufView = new Uint16Array(buf.buffer);
        for (let i = 0, strLen = str.length; i < strLen; i++) {
            bufView[i] = str.charCodeAt(i);
        }
        return buf;
    }

    static utf8(str) {
        let utf8Len = 0;
        for (const c of str) {
            utf8Len += calculate_utf8_len(c.codePointAt(0));
        }
        const buf = Buffer.create(utf8Len);
        const arr = new Uint8Array(buf.buffer);
        let j = 0;
        for (const c of str) {
            j += encode_utf8(c.codePointAt(0), arr, utf8Len, j);
        }
        return buf;
    }
}

module.exports.Buffer = Buffer;
