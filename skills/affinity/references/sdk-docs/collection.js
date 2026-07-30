'use strict';

class Collection {
    #genFunc;
    constructor(genFunc) {
        this.#genFunc = genFunc;
    }

    get [Symbol.toStringTag]() {
		return 'Collection';
	}

    get generator() {
        return this.#genFunc;
    }

    *[Symbol.iterator]() {
        for (const v of this.generator()) {
            yield v;
        }
    }

    static empty() {
        return Collection.of();
    }

    static fibonacci(i = 0, j = 1) {
        return new Collection(fibonacci(this.generator));
    }

    static of(...items) {
        return new SpanCollection(items);
    }

    static over(seq) {
        if (Array.isArray(seq) || ArrayBuffer.isView(seq) || typeof seq === 'string') {
            return new SpanCollection(seq);
        }
        return new Collection(over(seq));
    }

    static random() {
        return new Collection(random());
    }

    static range(start, count) {
        return new RangeCollection(start, count);
    }

    append(...others) {
        if (others.length == 0)
            return this;
        let generator = this.generator;
        for (const other of others) {
            if (isIterable(other)) {
                generator = concat(generator, over(other));
            }
            else { // assume generator function
                generator = concat(generator, other);
            }
        }
        return new Collection(generator);
    }

    entries() {
        return new Collection(entries(this.generator));
    }

    filter(predicate, thisArg) {
        return new Collection(filter(this.generator, predicate, thisArg));
    }

    flat(depth = 1, flattenStrings = false) {
        return new Collection(flat(this.generator, depth, flattenStrings));
    }

    keys() {
        return new Collection(keys(this.generator));
    }

    lastN(num) {
        return new Collection(lastN(this.generator, num));
    }

    map(mapFunc, thisArg) {
        return new Collection(map(this.generator, mapFunc, thisArg));
    }

    notNull(noCoercion) {
        if (noCoercion)
            return this.filter(item => item !== null);
        else    
            return this.filter(item => item != null);
    }

    repeat(num) {
        return new Collection(repeat(this.generator, num));
    }

    repeatForever() {
        return new Collection(repeatForever(this.generator));
    }

    reverse() {
        return new Collection(reverse(this.generator));
    }

    skip(num) {
        return new Collection(skip(this.generator, num));
    }

    skipWhile(whileFunc, thisArg) {
        return new Collection(skipWhile(this.generator, whileFunc, thisArg));
    }

    some(predicate, thisArg) {
        return some(this.generator, predicate, thisArg);
    }

    take(num) {
        return new Collection(take(this.generator, num));
    }

    takeWhile(whileFunc, thisArg) {
        return new Collection(takeWhile(this.generator, whileFunc, thisArg));
    }

    zip(other) {
        if (isIterable(other)) {
            return new Collection(zip(this.generator, over(other)));
        }
        else { // assume generator function
            return new Collection(zip(this.generator, other))
        }
    }

    leftZip(other) {
        if (isIterable(other)) {
            return new Collection(leftZip(this.generator, over(other)));
        }
        else { // assume generator function
            return new Collection(leftZip(this.generator, other))
        }
    }

    rightZip(other) {
        if (isIterable(other)) {
            return new Collection(rightZip(this.generator, over(other)));
        }
        else { // assume generator function
            return new Collection(rightZip(this.generator, other))
        }
    }

    all(predicate, thisArg) {
        return all(this.generator, predicate, thisArg);
    }

    any(predicate, thisArg) {
        return any(this.generator, predicate, thisArg);
    }

    at(index) {
        return nthValue(this.generator, index);
    }

    countIf(predicate, thisArg) {
        return countIf(this.generator, predicate, thisArg);
    }

    get first() {
        return first(this.generator);
    }

    forEach(callback, thisArg) {
        return forEach(this.generator, callback, thisArg);
    }

    get last() {
        return last(this.generator);
    }

    get length() {
        return length(this.generator);
    }

    get isEmpty() {
        return isEmpty(this.generator);
    }

    none(predicate, thisArg) {
        return none(this.generator, predicate, thisArg);
    }

    reduce(reduceFunc, initialValue) {
        return reduce(this.generator, reduceFunc, initialValue);
    }

    join(sep = ",") {
        return join(this.generator, sep);
    }

    toArray() {
        return [...this.generator()];
    }
}

// Optimised version for a blob of data with random access index support e.g. arrays
class SpanCollection extends Collection {
    #span;
    #begin;
    #end;
    #reverse;
    constructor(span, begin = 0, end = span.length - begin) {
        const reverse = end < begin;
        super(function*() {
            if (reverse) {
                for (let i = begin; i > end; --i) {
                    yield span.at(i);
                }
            }
            else {
                for (let i = begin; i < end; ++i) {
                    yield span.at(i);
                }
            }
        });
        this.#span = span;
        this.#begin = begin;
        this.#end = end;
        this.#reverse = reverse;
    }

    get first() {
        if (this.length > 0)
            return this.#span.at(this.#begin);
    }

    get last() {
        if (this.length > 0) {
            const inc = this.#reverse ? 1 : -1;
            return this.#span.at(this.#end + inc);
        }
    }

    get length() {
        return Math.abs(this.#end - this.#begin);
    }

    take(num) {
        const n = Math.min(this.length, Math.max(0, Number(num) || 0));
        const newEnd = this.#reverse ? this.#begin - n : this.#begin + n;
        return new SpanCollection(this.#span, this.#begin, newEnd);
    }

    skip(num) {
        const n = Math.min(this.length, Math.max(0, Number(num) || 0));
        const newBegin = this.#reverse ? this.#begin - n : this.#begin + n;
        return new SpanCollection(this.#span, newBegin, this.#end);
    }

    reverse() {
        let newBegin = this.#end;
        let newEnd = this.#begin;
        if (newBegin != newEnd) {
            if (this.#reverse) {
                ++newBegin;
                ++newEnd;
            }
            else {
                --newBegin;
                --newEnd;
            }
        }
        return new SpanCollection(this.#span, newBegin, newEnd);
    }

    at(index) {
        if (index >= 0 && index < this.length) {
            if (this.#reverse) {
                return this.#span.at(this.#begin - index);
            }
            else {
                return this.#span.at(this.#begin + index);
            }
        }
    }

    get isEmpty() {
        return this.length === 0;
    }
}

// optimised for range() collections
class RangeCollection extends Collection {
    #start;
    #length;
    #decrementing;
    constructor(start, length, decrementing) {
        super(function*() {
            let value = start;
            if (decrementing) {
                for (let i = 0; i < length; ++i) {
                    yield value--;
                }
            }
            else {
                for (let i = 0; i < length; ++i) {
                    yield value++;
                }
            }
        });
        this.#start = start;
        this.#length = length
        this.#decrementing = decrementing;
    }

    reverse() {
        if (this.length == 0) {
            return new RangeCollection(this.#start, this.#length, !this.decrementing);
        }
        const newDecrementing = !this.#decrementing;
        const newStart = (this.#decrementing ? this.#start - this.length : this.#start + this.length) - 1;
        return new RangeCollection(newStart, this.length, newDecrementing);
    }

    skip(num) {
        const n = Number(num) || 0;
        const skipped = Math.min(n, this.length);
        const newStart = this.#decrementing ? this.#start - skipped : this.#start + skipped;
        const newLength = this.length - skipped;
        return new RangeCollection(newStart, newLength, this.#decrementing);
    }

    take(num) {
        const n = Number(num) || 0;
        const newLength = Math.min(n, this.length);
        return new RangeCollection(this.#start, newLength, this.#decrementing);
    }

    at(index) {
        if (index >= 0 && index < this.length) {
            if (this.#decrementing) {
                return this.#start - index;
            }
            else {
                return this.#start + index;
            }
        }
    }

    get first() {
        if (this.length > 0)
            return this.#start;
    }

    get last() {
        if (this.length > 0) {
            const offset = this.length - 1;
            if (this.#decrementing)
                return this.#start - offset;
            else
                return this.#start + offset;
        }
    }

    get length() {
        return this.#length;
    }

    get isEmpty() {
        return this.length === 0;
    }
}

function isIterable(obj) {
    return obj != null && typeof obj[Symbol.iterator] === 'function';
}

function canFlatten(obj, flattenStrings) {
    return isIterable(obj) && (flattenStrings || typeof(obj) != 'string');
}

function fibonacci(i = 0, j = 1) {
    return function*() {
        yield i;
        yield j;
        let arr = [i, j];
        while (true) {
            let next = arr[0] + arr[1];
            yield next
            arr[0] = arr[1];
            arr[1] = next;
        }
    }
}

function over(seq) {
    return function*() {
        if (isIterable(seq)) {
            for (const value of seq) {
                yield value;
            }
        }
        else yield seq;
    }
}

function random() {
    return function*() {
        while (true) {
            yield Math.random();
        }
    }
}

function range(start, count) {
    const s = Number(start) || 0;
    const c = Number(count) || 0;
    return function*() {
        let start = s;
        let count = c;
        while (count-- > 0) {
            yield start++;
        }
    }
}

function concat(genFunc1, genFunc2) {
    return function*() {
        for (const value of genFunc1()) {
            yield value;
        }
        for (const value of genFunc2()) {
            yield value;
        }
    }
}

function entries(genFunc) {
    return function*() {
        let i = 0;
        for (const item of genFunc()) {
            yield [i++, item];
        }
    }
}

function filter(genFunc, predicateFunc, thisArg) {
    return function*() {
        let index = 0;
        for (const item of genFunc()) {
            if (predicateFunc.call(thisArg, item, index++))
                yield item;
        }
    }
}

function flat(genFunc, depth = 1, flattenStrings) {
    function* safeInner(genFunc, depth) {
        if (depth <= 0) {
            for (const value of genFunc())
                yield value;
        }
        else {
            for (const value of genFunc()) {
                if (canFlatten(value, flattenStrings)) {
                    for (const value2 of safeInner(over(value), depth - 1))
                        yield value2;
                }
                else
                    yield value;
            }
        }
    }

    function safeDepth(v) {
        if (typeof v === 'number')
        return v;
        let num = Number(v);
        return isNaN(num) ? 1 : num;
    } 

    return function*() {
        for (const value of safeInner(genFunc, safeDepth(depth))) {
            yield value;
        }
    }
}

function keys(genFunc) {
    return function*() {
        let i = 0;
        for (const _ of genFunc()) {
            yield i++;
        }
    }
}

function lastN(genFunc, num) {
    const n = Number(num) || 0;
    return function*() {
        let arr = toArray(genFunc);
        if (n < arr.length) {
            for (let i = arr.length - num; i < arr.length; ++i) {
                yield arr[i];
            }
        }
    }
}

function map(genFunc, mapFunc, thisArg) {
    return function*() {
        let index = 0;
        for (const item of genFunc()) {
            yield mapFunc.call(thisArg, item, index++);
        }
    }
}

function repeat(genFunc, num) {
    const n = Number(num) || 0;
    return function*() {
        for (let i = 0; i < n; ++i) {
            for (const value of genFunc()) {
                yield value;
            }
        }
    }
}

function repeatForever(genFunc) {
    return function*() {
        while (true) {
            for (const value of genFunc()) {
                yield value;
            }
        }
    }
}

function reverse(genFunc) {
    return function*() {
        const arr = toArray(genFunc);
        let i = arr.length - 1;
        while (i >= 0) {
            yield arr[i--];
        }
    }
}

function skip(genFunc, num) {
    const n = Number(num) || 0;
    return skipWhile(genFunc, (_, index) => index < n);
}

function skipWhile(genFunc, whileFunc, thisArg) {
    return function*() {
        const seq = genFunc();
        let it = seq.next();
        let index = 0;
        while (!it.done && whileFunc.call(thisArg, it.value, index++)) {
            it = seq.next();
        }
        while (!it.done) {
            yield it.value;
            it = seq.next();
        }
    }
}

function take(genFunc, num) {
    const n = Number(num) || 0;
    return takeWhile(genFunc, (_, index) => index < n);
}

function takeWhile(genFunc, whileFunc, thisArg) {
    return function*() {
        let index = 0;
        for (const item of genFunc()) {
            if (!whileFunc.call(thisArg, item, index++))
                return;
            yield item;
        }
    }
}

function zip(genFunc1, genFunc2) {
    return function*() {
        const seq1 = genFunc1();
        const seq2 = genFunc2();
        let i1 = seq1.next();
        let i2 = seq2.next();
        while (!i1.done && !i2.done) {
            yield [i1.value, i2.value];
            i1 = seq1.next();
            i2 = seq2.next();
        }
    }
}

function leftZip(genFunc1, genFunc2) {
    return function*() {
        const seq1 = genFunc1();
        const seq2 = genFunc2();
        let i1 = seq1.next();
        let i2 = seq2.next();
        while (!i1.done) {
            yield [i1.value, i2.done ? undefined : i2.value];
            i1 = seq1.next();
            if (!i2.done)
                i2 = seq2.next();
        }
    }
}

function rightZip(genFunc1, genFunc2) {
    return function*() {
        const seq1 = genFunc1();
        const seq2 = genFunc2();
        let i1 = seq1.next();
        let i2 = seq2.next();
        while (!i2.done) {
            yield [i1.done ? undefined : i1.value, i2.value];
            i2 = seq2.next();
            if (!i1.done)
                i1 = seq1.next();
        }
    }
}

function all(genFunc, predicate, thisArg) {
    let i = 0;
    for (const value of genFunc())
        if (!predicate.call(thisArg, value, i++))
            return false;
    return true;
}

function any(genFunc, predicate, thisArg) {
    let i = 0;
    for (const value of genFunc())
        if (predicate.call(thisArg, value, i++))
            return true;
    return false;
}

function countIf(genFunc, predicate, thisArg) {
    let res = 0;
    let index = 0;
    for (const value of genFunc()) {
        if (predicate.call(thisArg, value, index++))
            ++res;
    }
    return res;
}

function isEmpty(genFunc) {
    for (const value of genFunc()){
        return false;
    }
    return true;
}

function first(genFunc) {
    for (const value of genFunc()) {
        return value;
    }
}

function forEach(genFunc, callback, thisArg) {
    for (const value of genFunc()) {
        callback.call(thisArg, value);
    }
}

function join(genFunc, sep = ",") {
    let s = "";
    const seq = genFunc();
    let iter = seq.next();
    if (!iter.done) {
        s += String(iter.value);
        iter = seq.next();
    }
    while (!iter.done) {
        s += sep;
        s += String(iter.value);
        iter = seq.next();
    }
    return s;
}

function last(genFunc) {
    let last;
    for (const value of genFunc()) {
        last = value;
    }
    return last;
}

function length(genFunc) {
    let len = 0;
    const seq = genFunc();
    for (let it = seq.next(); !it.done; it = seq.next()) {
        ++len;
    }
    return len;
}

function none(genFunc, predicate, thisArg) {
    let i = 0;
    for (const value of genFunc())
        if (predicate.call(thisArg, value, i++))
            return false;
    return true;
}

function nthValue(genFunc, n) {
    const iter = take(skip(genFunc, n), 1)();
    const result = iter.next();
    if (!result.done)
        return result.value;
}

function reduce(genFunc, reduceFunc, initialValue) {
    const seq = genFunc();
    let iter = seq.next();
    if (iter.done)
        return initialValue;
    let i = 0;
    if (initialValue === undefined) {
        initialValue = iter.value;
        iter = seq.next();
        ++i;
    }
    while (!iter.done) {
        initialValue = reduceFunc(initialValue, iter.value, i);
        iter = seq.next();
        ++i;
    }
    return initialValue;
}

function some(genFunc, predicate, thisArg) {
    if (predicate == null) {
        for (const value of genFunc())
            return true;
    }
    else {
        let i = 0;
        for (const value of genFunc())
            if (predicate.call(thisArg, value, i++))
                return true;
    }
    return false;
}

function toArray(genFunc) {
    let res = [];
    for (const value of genFunc()) {
        res.push(value);
    }
    return res;
}

module.exports.Collection = Collection;
module.exports.SpanCollection = SpanCollection;
