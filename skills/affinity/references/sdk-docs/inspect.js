'use strict';

// A Node.js-style util.inspect for Affinity scripts.
//
//   const { inspect } = require('/inspect.js');
//   console.log(inspect(document, { depth: 3 }));
//
// Exports:
//   inspect(value, options)        - returns a string representation of value
//   format(fmt, ...args)           - printf-style formatting (%s %d %i %f %j %o %O %%)
//   formatWithOptions(opts, ...)   - as format, but with inspect options for object args
//   patchConsole(options)          - route console.log/info/warn/error/debug/dir through inspect
//   unpatchConsole()               - restore the original console methods
//
// Options (defaults in inspect.defaultOptions):
//   depth (2)                    - recursion depth; null for unlimited
//   showHidden (false)           - include non-enumerable and symbol properties
//   getters (false)              - invoke own accessors: true | 'get' | 'set'
//   maxArrayLength (100)         - array/Map/Set entries shown; null for unlimited
//   maxStringLength (10000)      - string characters shown; null for unlimited
//   breakLength (80)             - line width before switching to multi-line layout
//   sorted (false)               - sort entries lexicographically
//   customInspect (true)         - honour [inspect.custom](depth, options, inspect) methods
//   expandNestedHandleObjects (false) - expand HandleObjects below the top level
//   enums ('brief')              - how to show Affinity enum values:
//                                  'brief' -> RGBA8 (matches console.log)
//                                  'full'  -> RasterFormat.RGBA8
//                                  'raw'   -> RasterFormat { value: 0 }
//
// Divergences from Node.js: no colours, no Proxy detection, Promise state is not
// available (prints 'Promise { <state unknown> }'), and the compact/breakLength
// layout logic is simplified (entries share one line only when they all fit).
//
// HandleObject instances (most Affinity API objects) keep their state behind
// prototype getters, so inspect evaluates those getters (each guarded, so a
// throwing getter renders as '<error: ...>' rather than failing the inspect).
// A class can take full control by implementing [inspect.custom].

const { HandleObject } = require('/handleobject.js');

const customInspectSymbol = Symbol.for('affinity.inspect.custom');
const nodeCustomInspectSymbol = Symbol.for('nodejs.util.inspect.custom');

const defaultOptions = {
    depth: 2,
    showHidden: false,
    getters: false,
    maxArrayLength: 100,
    maxStringLength: 10000,
    breakLength: 80,
    sorted: false,
    customInspect: true,
    expandNestedHandleObjects: false,
    enums: 'brief',
};

const identifierRegex = /^[a-zA-Z_$][a-zA-Z0-9_$]*$/;
const indexKeyRegex = /^(0|[1-9][0-9]*)$/;

const escapeMap = {
    '\\': '\\\\',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
    '\b': '\\b',
    '\f': '\\f',
    '\v': '\\v',
};

function inspect(value, options) {
    const ctx = Object.assign({}, defaultOptions, inspect.defaultOptions, options);
    if (ctx.depth === null) ctx.depth = Infinity;
    if (ctx.maxArrayLength === null) ctx.maxArrayLength = Infinity;
    if (ctx.maxStringLength === null) ctx.maxStringLength = Infinity;
    if (ctx.breakLength === null) ctx.breakLength = Infinity;
    ctx.seen = [];
    ctx.circular = new Map();
    ctx.indentationLvl = 0;
    try {
        return formatValue(ctx, value, 0);
    }
    catch (err) {
        return `<inspect failed: ${err && err.message ? err.message : String(err)}>`;
    }
}

inspect.custom = customInspectSymbol;
inspect.defaultOptions = {};

function formatValue(ctx, value, recurseTimes) {
    if (value === undefined)
        return 'undefined';
    if (value === null)
        return 'null';

    switch (typeof value) {
        case 'string':
            return formatString(ctx, value);
        case 'number':
            return formatNumber(value);
        case 'bigint':
            return `${value}n`;
        case 'boolean':
            return String(value);
        case 'symbol':
            return value.toString();
        default:
            return formatObject(ctx, value, recurseTimes);
    }
}

function formatNumber(value) {
    return Object.is(value, -0) ? '-0' : String(value);
}

function formatString(ctx, str) {
    let suffix = '';
    if (str.length > ctx.maxStringLength) {
        const remaining = str.length - ctx.maxStringLength;
        str = str.slice(0, ctx.maxStringLength);
        suffix = `... ${remaining} more character${remaining > 1 ? 's' : ''}`;
    }
    return quoteString(str) + suffix;
}

function quoteString(str) {
    let quote = "'";
    if (str.includes("'")) {
        if (!str.includes('"'))
            quote = '"';
        else if (!str.includes('`'))
            quote = '`';
    }
    let out = quote;
    for (const ch of str) {
        if (ch === quote)
            out += '\\' + ch;
        else if (escapeMap[ch] !== undefined)
            out += escapeMap[ch];
        else {
            const code = ch.codePointAt(0);
            if (code < 0x20 || code === 0x7f)
                out += '\\x' + code.toString(16).padStart(2, '0');
            else
                out += ch;
        }
    }
    return out + quote;
}

function formatKey(key) {
    if (typeof key === 'symbol')
        return `[${key.toString()}]`;
    if (identifierRegex.test(key))
        return key;
    return quoteString(key);
}

function isIndexKey(key) {
    return indexKeyRegex.test(key) && Number(key) < 4294967295;
}

function getConstructorName(value) {
    try {
        const proto = Object.getPrototypeOf(value);
        if (proto === null)
            return null;
        const ctor = proto.constructor;
        if (typeof ctor === 'function' && typeof ctor.name === 'string' && ctor.name !== '')
            return ctor.name;
    }
    catch (err) {
        // e.g. a Proxy with a throwing getPrototypeOf trap
    }
    return '';
}

function getToStringTag(value) {
    try {
        const tag = value[Symbol.toStringTag];
        if (typeof tag === 'string' && tag !== '')
            return tag;
    }
    catch (err) {
        // a throwing tag getter should not break inspection
    }
    return '';
}

function getHandleObjectClassName(value) {
    const tag = getToStringTag(value);
    if (tag)
        return tag;
    const ctorName = getConstructorName(value);
    return ctorName || 'HandleObject';
}

function shortForm(value) {
    if (Array.isArray(value))
        return '[Array]';
    if (typeof value === 'function')
        return '[Function]';
    if (value instanceof HandleObject)
        return `[${getHandleObjectClassName(value)}]`;
    const name = getConstructorName(value);
    return `[${name || 'Object'}]`;
}

function tryCustomInspect(ctx, value, recurseTimes) {
    if (!ctx.customInspect)
        return undefined;
    let fn;
    try {
        fn = value[customInspectSymbol];
        if (typeof fn !== 'function')
            fn = value[nodeCustomInspectSymbol];
    }
    catch (err) {
        return undefined;
    }
    if (typeof fn !== 'function')
        return undefined;
    let result;
    try {
        const publicOptions = Object.assign({}, ctx);
        delete publicOptions.seen;
        delete publicOptions.circular;
        delete publicOptions.indentationLvl;
        result = fn.call(value, ctx.depth - recurseTimes, publicOptions, inspect);
    }
    catch (err) {
        return `<inspect error: ${err && err.message ? err.message : String(err)}>`;
    }
    if (typeof result === 'string')
        return result;
    if (result === value)
        return undefined;
    return formatValue(ctx, result, recurseTimes);
}

function formatObject(ctx, value, recurseTimes) {
    const custom = tryCustomInspect(ctx, value, recurseTimes);
    if (custom !== undefined)
        return custom;

    // Affinity enum values (native Enum template instances) carry an
    // isEnumValue marker on their prototype and stringify to their key name.
    if (ctx.enums !== 'raw') {
        const enumStr = tryFormatEnumValue(value, ctx.enums);
        if (enumStr !== undefined)
            return enumStr;
    }

    if (ctx.seen.includes(value)) {
        let id = ctx.circular.get(value);
        if (id === undefined) {
            id = ctx.circular.size + 1;
            ctx.circular.set(value, id);
        }
        return `[Circular *${id}]`;
    }

    if (recurseTimes > ctx.depth)
        return shortForm(value);

    ctx.seen.push(value);
    ctx.indentationLvl += 2;
    let result;
    try {
        result = formatRaw(ctx, value, recurseTimes);
    }
    finally {
        ctx.indentationLvl -= 2;
        ctx.seen.pop();
    }

    const refId = ctx.circular.get(value);
    if (refId !== undefined)
        result = `<ref *${refId}> ${result}`;
    return result;
}

function tryFormatEnumValue(value, mode) {
    try {
        if (value.isEnumValue === true) {
            const str = value.toString();
            if (typeof str === 'string') {
                if (mode === 'full') {
                    const typeName = getToStringTag(value) || getConstructorName(value);
                    if (typeName)
                        return `${typeName}.${str}`;
                }
                return str;
            }
        }
    }
    catch (err) {
        // not an enum after all; fall through to normal formatting
    }
    return undefined;
}

function formatRaw(ctx, value, recurseTimes) {
    if (typeof value === 'function')
        return formatFunction(ctx, value, recurseTimes);

    if (Array.isArray(value)) {
        const entries = formatArrayEntries(ctx, value, recurseTimes);
        appendPropertyEntries(entries, ctx, value, recurseTimes, { skipIndices: true, skipKeys: ['length'] });
        const ctorName = getConstructorName(value);
        const base = (ctorName === 'Array' || ctorName === '') ? '' : `${ctorName}(${value.length})`;
        return reduceToSingleString(ctx, base, ['[', ']'], entries);
    }

    if (ArrayBuffer.isView(value) && !(value instanceof DataView)) {
        const entries = [];
        const maxLength = Math.min(value.length, ctx.maxArrayLength);
        for (let i = 0; i < maxLength; ++i)
            entries.push(formatValue(ctx, value[i], recurseTimes + 1));
        const remaining = value.length - maxLength;
        if (remaining > 0)
            entries.push(`... ${remaining} more item${remaining > 1 ? 's' : ''}`);
        const base = `${getConstructorName(value) || 'TypedArray'}(${value.length})`;
        return reduceToSingleString(ctx, base, ['[', ']'], entries);
    }

    if (value instanceof Map) {
        const entries = [];
        let remaining = 0;
        for (const [k, v] of value) {
            if (entries.length >= ctx.maxArrayLength) {
                ++remaining;
                continue;
            }
            entries.push(`${formatValue(ctx, k, recurseTimes + 1)} => ${formatValue(ctx, v, recurseTimes + 1)}`);
        }
        maybeSort(ctx, entries);
        if (remaining > 0)
            entries.push(`... ${remaining} more item${remaining > 1 ? 's' : ''}`);
        appendPropertyEntries(entries, ctx, value, recurseTimes, {});
        return reduceToSingleString(ctx, `${getConstructorName(value) || 'Map'}(${value.size})`, ['{', '}'], entries);
    }

    if (value instanceof Set) {
        const entries = [];
        let remaining = 0;
        for (const v of value) {
            if (entries.length >= ctx.maxArrayLength) {
                ++remaining;
                continue;
            }
            entries.push(formatValue(ctx, v, recurseTimes + 1));
        }
        maybeSort(ctx, entries);
        if (remaining > 0)
            entries.push(`... ${remaining} more item${remaining > 1 ? 's' : ''}`);
        appendPropertyEntries(entries, ctx, value, recurseTimes, {});
        return reduceToSingleString(ctx, `${getConstructorName(value) || 'Set'}(${value.size})`, ['{', '}'], entries);
    }

    if (value instanceof WeakMap || value instanceof WeakSet)
        return `${getConstructorName(value)} { <items unknown> }`;

    if (value instanceof Promise)
        return 'Promise { <state unknown> }';

    if (value instanceof Date) {
        const time = value.getTime();
        return Number.isNaN(time) ? 'Invalid Date' : value.toISOString();
    }

    if (value instanceof RegExp)
        return String(value);

    if (value instanceof Error)
        return formatError(ctx, value, recurseTimes);

    if (value instanceof ArrayBuffer)
        return `ArrayBuffer { byteLength: ${value.byteLength} }`;

    if (typeof SharedArrayBuffer !== 'undefined' && value instanceof SharedArrayBuffer)
        return `SharedArrayBuffer { byteLength: ${value.byteLength} }`;

    if (value instanceof DataView)
        return `DataView { byteLength: ${value.byteLength}, byteOffset: ${value.byteOffset} }`;

    const boxed = formatBoxedPrimitive(ctx, value);
    if (boxed !== undefined)
        return boxed;

    if (value instanceof HandleObject)
        return formatHandleObject(ctx, value, recurseTimes);

    // Plain (or user-class) object
    const entries = [];
    appendPropertyEntries(entries, ctx, value, recurseTimes, {});
    maybeSort(ctx, entries);
    const ctorName = getConstructorName(value);
    const tag = getToStringTag(value);
    let base = '';
    if (ctorName === null)
        base = '[Object: null prototype]';
    else if (ctorName !== '' && ctorName !== 'Object')
        base = ctorName;
    if (tag && tag !== ctorName)
        base = `${base || 'Object'} [${tag}]`;
    return reduceToSingleString(ctx, base, ['{', '}'], entries);
}

function formatFunction(ctx, value, recurseTimes) {
    let source = '';
    try {
        source = Function.prototype.toString.call(value);
    }
    catch (err) {
        // bound functions and some proxies can refuse; treat as a plain function
    }
    let kind = 'Function';
    const protoCtor = Object.getPrototypeOf(value);
    const protoCtorName = protoCtor && protoCtor.constructor ? protoCtor.constructor.name : '';
    if (protoCtorName === 'AsyncFunction' || protoCtorName === 'GeneratorFunction' || protoCtorName === 'AsyncGeneratorFunction')
        kind = protoCtorName;
    let base;
    if (/^class[\s{]/.test(source))
        base = value.name ? `[class ${value.name}]` : '[class (anonymous)]';
    else
        base = value.name ? `[${kind}: ${value.name}]` : `[${kind} (anonymous)]`;

    const entries = [];
    appendPropertyEntries(entries, ctx, value, recurseTimes, { skipKeys: ['length', 'name', 'prototype'] });
    maybeSort(ctx, entries);
    if (entries.length === 0)
        return base;
    return reduceToSingleString(ctx, base, ['{', '}'], entries);
}

function formatError(ctx, value, recurseTimes) {
    let base;
    if (typeof value.stack === 'string' && value.stack !== '')
        base = value.stack;
    else
        base = `${value.name || 'Error'}: ${value.message || ''}`;
    const entries = [];
    appendPropertyEntries(entries, ctx, value, recurseTimes, { skipKeys: ['message', 'stack'] });
    maybeSort(ctx, entries);
    if (entries.length === 0)
        return base;
    return reduceToSingleString(ctx, base, ['{', '}'], entries);
}

function formatBoxedPrimitive(ctx, value) {
    try {
        if (value instanceof String)
            return `[String: ${formatString(ctx, String.prototype.valueOf.call(value))}]`;
        if (value instanceof Number)
            return `[Number: ${formatNumber(Number.prototype.valueOf.call(value))}]`;
        if (value instanceof Boolean)
            return `[Boolean: ${Boolean.prototype.valueOf.call(value)}]`;
        if (typeof value === 'object' && Object.prototype.toString.call(value) === '[object Symbol]')
            return `[Symbol: ${Symbol.prototype.valueOf.call(value).toString()}]`;
        if (typeof value === 'object' && Object.prototype.toString.call(value) === '[object BigInt]')
            return `[BigInt: ${BigInt.prototype.valueOf.call(value)}n]`;
    }
    catch (err) {
        // not actually boxed (e.g. subclass shenanigans); fall through
    }
    return undefined;
}

function formatHandleObject(ctx, value, recurseTimes) {
    const className = getHandleObjectClassName(value);
    if (recurseTimes > 0 && !ctx.expandNestedHandleObjects)
        return `[${className}]`;

    const entries = [];
    // Own data properties first (rare on handle objects, but honest).
    appendPropertyEntries(entries, ctx, value, recurseTimes, {});

    // The interesting state lives behind prototype getters. Walk the chain
    // derived-first (so overrides win) and stop before HandleObject.prototype,
    // which only exposes the raw native handle.
    const seenKeys = new Set();
    let proto = Object.getPrototypeOf(value);
    let guard = 0;
    while (proto && proto !== HandleObject.prototype && proto !== Object.prototype && ++guard < 32) {
        for (const key of Object.getOwnPropertyNames(proto)) {
            if (key === 'constructor' || seenKeys.has(key))
                continue;
            seenKeys.add(key);
            const desc = Object.getOwnPropertyDescriptor(proto, key);
            if (!desc || typeof desc.get !== 'function')
                continue;
            let str;
            try {
                str = formatValue(ctx, desc.get.call(value), recurseTimes + 1);
            }
            catch (err) {
                str = `<error: ${err && err.message ? err.message : String(err)}>`;
            }
            entries.push(`${formatKey(key)}: ${str}`);
        }
        proto = Object.getPrototypeOf(proto);
    }
    maybeSort(ctx, entries);
    return reduceToSingleString(ctx, className, ['{', '}'], entries);
}

function formatArrayEntries(ctx, arr, recurseTimes) {
    const entries = [];
    const maxLength = Math.min(arr.length, ctx.maxArrayLength);
    let emptyItems = 0;
    for (let i = 0; i < maxLength; ++i) {
        if (!Object.prototype.hasOwnProperty.call(arr, i)) {
            ++emptyItems;
            continue;
        }
        if (emptyItems > 0) {
            entries.push(`<${emptyItems} empty item${emptyItems > 1 ? 's' : ''}>`);
            emptyItems = 0;
        }
        entries.push(formatValue(ctx, arr[i], recurseTimes + 1));
    }
    if (emptyItems > 0)
        entries.push(`<${emptyItems} empty item${emptyItems > 1 ? 's' : ''}>`);
    const remaining = arr.length - maxLength;
    if (remaining > 0)
        entries.push(`... ${remaining} more item${remaining > 1 ? 's' : ''}`);
    return entries;
}

function appendPropertyEntries(entries, ctx, value, recurseTimes, { skipIndices = false, skipKeys = [] }) {
    for (const key of Object.getOwnPropertyNames(value)) {
        if (skipKeys.includes(key))
            continue;
        if (skipIndices && isIndexKey(key))
            continue;
        const desc = Object.getOwnPropertyDescriptor(value, key);
        if (!desc || (!desc.enumerable && !ctx.showHidden))
            continue;
        const keyStr = desc.enumerable ? formatKey(key) : `[${formatKey(key)}]`;
        entries.push(`${keyStr}: ${formatPropertyValue(ctx, value, desc, recurseTimes)}`);
    }
    for (const sym of Object.getOwnPropertySymbols(value)) {
        if (sym === Symbol.toStringTag)
            continue;
        const desc = Object.getOwnPropertyDescriptor(value, sym);
        if (!desc || (!desc.enumerable && !ctx.showHidden))
            continue;
        entries.push(`${formatKey(sym)}: ${formatPropertyValue(ctx, value, desc, recurseTimes)}`);
    }
}

function formatPropertyValue(ctx, owner, desc, recurseTimes) {
    if (desc.get) {
        const invoke = ctx.getters === true
            || (ctx.getters === 'get' && !desc.set)
            || (ctx.getters === 'set' && !!desc.set);
        if (invoke) {
            try {
                return formatValue(ctx, desc.get.call(owner), recurseTimes + 1);
            }
            catch (err) {
                return `<error: ${err && err.message ? err.message : String(err)}>`;
            }
        }
        return desc.set ? '[Getter/Setter]' : '[Getter]';
    }
    if (desc.set)
        return '[Setter]';
    return formatValue(ctx, desc.value, recurseTimes + 1);
}

function maybeSort(ctx, entries) {
    if (ctx.sorted)
        entries.sort();
}

function reduceToSingleString(ctx, base, braces, entries) {
    if (entries.length === 0)
        return base ? `${base} ${braces[0]}${braces[1]}` : `${braces[0]}${braces[1]}`;

    const basePart = base ? `${base} ` : '';
    const multiline = base.includes('\n') || entries.some((e) => e.includes('\n'));
    if (!multiline) {
        const oneLine = `${basePart}${braces[0]} ${entries.join(', ')} ${braces[1]}`;
        if (oneLine.length + ctx.indentationLvl <= ctx.breakLength)
            return oneLine;
    }
    const inner = entries.map((e) => e.replace(/\n/g, '\n  ')).join(',\n  ');
    return `${basePart}${braces[0]}\n  ${inner}\n${braces[1]}`;
}

function format(...args) {
    return formatWithOptions(undefined, ...args);
}

function formatWithOptions(options, ...args) {
    const opts = options || {};
    let out = '';
    let argIndex = 0;

    if (typeof args[0] === 'string') {
        const fmt = args[0];
        argIndex = 1;
        let pos = 0;
        while (pos < fmt.length) {
            const ch = fmt[pos];
            if (ch !== '%' || pos + 1 >= fmt.length) {
                out += ch;
                ++pos;
                continue;
            }
            const spec = fmt[pos + 1];
            if (spec === '%') {
                out += '%';
                pos += 2;
                continue;
            }
            if (!'sdifjoO'.includes(spec) || argIndex >= args.length) {
                out += ch;
                ++pos;
                continue;
            }
            const arg = args[argIndex++];
            switch (spec) {
                case 's':
                    if (typeof arg === 'string')
                        out += arg;
                    else if (typeof arg === 'bigint')
                        out += `${arg}n`;
                    else if (typeof arg === 'object' && arg !== null)
                        out += inspect(arg, opts);
                    else
                        out += String(arg);
                    break;
                case 'd':
                    out += (typeof arg === 'bigint') ? `${arg}n` : formatNumber(Number(arg));
                    break;
                case 'i':
                    out += (typeof arg === 'bigint') ? `${arg}n` : String(parseInt(arg, 10));
                    break;
                case 'f':
                    out += String(parseFloat(arg));
                    break;
                case 'j':
                    try {
                        out += JSON.stringify(arg);
                    }
                    catch (err) {
                        out += '[Circular]';
                    }
                    break;
                case 'o':
                    out += inspect(arg, Object.assign({}, opts, { showHidden: true, depth: 4 }));
                    break;
                case 'O':
                    out += inspect(arg, opts);
                    break;
            }
            pos += 2;
        }
    }

    for (; argIndex < args.length; ++argIndex) {
        const arg = args[argIndex];
        if (out !== '')
            out += ' ';
        out += (typeof arg === 'string') ? arg : inspect(arg, opts);
    }
    return out;
}

// console patching ------------------------------------------------------

let patchedConsoleMethods = null;

function patchConsole(options) {
    if (patchedConsoleMethods)
        return;
    patchedConsoleMethods = {};
    for (const name of ['debug', 'log', 'info', 'warn', 'error']) {
        const original = console[name];
        if (typeof original !== 'function')
            continue;
        patchedConsoleMethods[name] = original;
        console[name] = function (...args) {
            return original.call(console, formatWithOptions(options, ...args));
        };
    }
    // console.dir gains inspect's options (and its HandleObject awareness);
    // output goes through the original log so it reaches the same sink.
    const originalDir = console.dir;
    const originalLog = patchedConsoleMethods.log;
    if (typeof originalDir === 'function' && typeof originalLog === 'function') {
        patchedConsoleMethods.dir = originalDir;
        console.dir = function (obj, dirOptions) {
            return originalLog.call(console, inspect(obj, Object.assign({}, options, dirOptions)));
        };
    }
}

function unpatchConsole() {
    if (!patchedConsoleMethods)
        return;
    for (const name of Object.keys(patchedConsoleMethods))
        console[name] = patchedConsoleMethods[name];
    patchedConsoleMethods = null;
}

module.exports.inspect = inspect;
module.exports.format = format;
module.exports.formatWithOptions = formatWithOptions;
module.exports.patchConsole = patchConsole;
module.exports.unpatchConsole = unpatchConsole;
