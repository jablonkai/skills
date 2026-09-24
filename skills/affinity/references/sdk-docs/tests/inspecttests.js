'use strict';

const { inspect, format, formatWithOptions, patchConsole, unpatchConsole } = require('/inspect.js');
const { HandleObject } = require('/handleobject.js');

function assertEq(actual, expected, label) {
    console.assert(actual === expected, `${label}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

function testPrimitives() {
    assertEq(inspect(undefined), 'undefined', 'undefined');
    assertEq(inspect(null), 'null', 'null');
    assertEq(inspect(true), 'true', 'boolean');
    assertEq(inspect(42), '42', 'number');
    assertEq(inspect(-0), '-0', 'negative zero');
    assertEq(inspect(NaN), 'NaN', 'NaN');
    assertEq(inspect(Infinity), 'Infinity', 'Infinity');
    assertEq(inspect(10n), '10n', 'bigint');
    assertEq(inspect(Symbol('x')), 'Symbol(x)', 'symbol');
}

function testStrings() {
    assertEq(inspect('foo'), "'foo'", 'plain string');
    assertEq(inspect("it's"), '"it\'s"', 'string with single quote');
    assertEq(inspect('a\'b"c'), '`a\'b"c`', 'string with both quotes');
    assertEq(inspect('a\nb\tc'), "'a\\nb\\tc'", 'string with escapes');
    assertEq(inspect('a\x01b'), "'a\\x01b'", 'control character');
    assertEq(inspect('aaaaa', { maxStringLength: 3 }), "'aaa'... 2 more characters", 'string truncation');
}

function testArrays() {
    assertEq(inspect([]), '[]', 'empty array');
    assertEq(inspect([1, 2, 3]), '[ 1, 2, 3 ]', 'flat array');
    assertEq(inspect([[1, 2], [3]]), '[ [ 1, 2 ], [ 3 ] ]', 'nested array');
    assertEq(inspect([1, , 3]), '[ 1, <1 empty item>, 3 ]', 'sparse array');
    assertEq(inspect([1, 2, 3, 4], { maxArrayLength: 2 }), '[ 1, 2, ... 2 more items ]', 'array truncation');

    const arr = [1];
    arr.x = 2;
    assertEq(inspect(arr), '[ 1, x: 2 ]', 'array with extra property');

    assertEq(inspect(new Uint8Array([1, 2])), 'Uint8Array(2) [ 1, 2 ]', 'typed array');
}

function testCollections() {
    assertEq(inspect(new Map([['a', 1]])), "Map(1) { 'a' => 1 }", 'map');
    assertEq(inspect(new Map()), 'Map(0) {}', 'empty map');
    assertEq(inspect(new Set([1, 2])), 'Set(2) { 1, 2 }', 'set');
    assertEq(inspect(new WeakMap()), 'WeakMap { <items unknown> }', 'weakmap');
    assertEq(inspect(new WeakSet()), 'WeakSet { <items unknown> }', 'weakset');
}

function testBuiltins() {
    assertEq(inspect(new Date(0)), '1970-01-01T00:00:00.000Z', 'date');
    assertEq(inspect(new Date(NaN)), 'Invalid Date', 'invalid date');
    assertEq(inspect(/ab/gi), '/ab/gi', 'regexp');
    assertEq(inspect(Promise.resolve(1)), 'Promise { <state unknown> }', 'promise');
    assertEq(inspect(new String('x')), "[String: 'x']", 'boxed string');
    assertEq(inspect(new Number(3)), '[Number: 3]', 'boxed number');
    assertEq(inspect(new ArrayBuffer(8)), 'ArrayBuffer { byteLength: 8 }', 'arraybuffer');
}

function testObjects() {
    assertEq(inspect({}), '{}', 'empty object');
    assertEq(inspect({ a: 1, b: 'x' }), "{ a: 1, b: 'x' }", 'plain object');
    assertEq(inspect({ 'a-b': 1 }), "{ 'a-b': 1 }", 'quoted key');
    assertEq(inspect({ 1: 'a' }), "{ '1': 'a' }", 'numeric key');
    assertEq(inspect({ [Symbol('s')]: 1 }), '{ [Symbol(s)]: 1 }', 'symbol key');

    class Foo {}
    assertEq(inspect(new Foo()), 'Foo {}', 'class instance');

    const nullProto = Object.create(null);
    nullProto.a = 1;
    assertEq(inspect(nullProto), '[Object: null prototype] { a: 1 }', 'null prototype');

    class Tagged {
        get [Symbol.toStringTag]() { return 'Custom'; }
    }
    assertEq(inspect(new Tagged()), 'Tagged [Custom] {}', 'toStringTag');
}

function testFunctions() {
    function foo() {}
    assertEq(inspect(foo), '[Function: foo]', 'named function');
    assertEq(inspect([function () {}][0]), '[Function (anonymous)]', 'anonymous function');

    class Bar {}
    assertEq(inspect(Bar), '[class Bar]', 'class');

    function f() {}
    f.x = 1;
    assertEq(inspect(f), '[Function: f] { x: 1 }', 'function with properties');
}

function testErrors() {
    const e = new Error('boom');
    console.assert(inspect(e).startsWith('Error: boom'), 'error starts with message');
    assertEq(inspect(e), e.stack, 'error is its stack');

    const e2 = new Error('boom');
    e2.code = 42;
    console.assert(inspect(e2).includes('{\n  code: 42\n}') || inspect(e2).includes('{ code: 42 }'),
        'error with extra property shows it');
}

function testDepth() {
    assertEq(inspect({ a: { b: { c: { d: 1 } } } }), '{ a: { b: { c: [Object] } } }', 'default depth');
    assertEq(inspect({ a: { b: 1 } }, { depth: 0 }), '{ a: [Object] }', 'depth 0');
    assertEq(inspect({ a: { b: { c: 1 } } }, { depth: null }), '{ a: { b: { c: 1 } } }', 'unlimited depth');
}

function testCircular() {
    const o = { a: 1 };
    o.self = o;
    assertEq(inspect(o), '<ref *1> { a: 1, self: [Circular *1] }', 'circular reference');
}

function testGetters() {
    const o = { get a() { return 1; } };
    assertEq(inspect(o), '{ a: [Getter] }', 'getter not invoked by default');
    assertEq(inspect(o, { getters: true }), '{ a: 1 }', 'getter invoked with getters:true');

    const o2 = { get a() { return 1; }, set a(v) {} };
    assertEq(inspect(o2), '{ a: [Getter/Setter] }', 'getter/setter');

    const o3 = { get a() { throw new Error('nope'); } };
    assertEq(inspect(o3, { getters: true }), '{ a: <error: nope> }', 'throwing getter');
}

function testShowHidden() {
    const o = {};
    Object.defineProperty(o, 'x', { value: 1, enumerable: false });
    assertEq(inspect(o), '{}', 'non-enumerable hidden by default');
    assertEq(inspect(o, { showHidden: true }), '{ [x]: 1 }', 'non-enumerable with showHidden');
}

function testSorted() {
    assertEq(inspect({ b: 2, a: 1 }, { sorted: true }), '{ a: 1, b: 2 }', 'sorted entries');
}

function testBreakLength() {
    assertEq(inspect({ a: 1, b: 2 }, { breakLength: 1 }), '{\n  a: 1,\n  b: 2\n}', 'multiline layout');
    assertEq(inspect({ a: { b: 1 } }, { breakLength: 1 }), '{\n  a: {\n    b: 1\n  }\n}', 'nested multiline indent');
}

function testCustomInspect() {
    const o = { [inspect.custom]() { return 'CUSTOM'; } };
    assertEq(inspect(o), 'CUSTOM', 'custom inspect string');

    const o2 = { [inspect.custom]() { return { replaced: true }; } };
    assertEq(inspect(o2), '{ replaced: true }', 'custom inspect object result');

    assertEq(inspect(o, { customInspect: false }).includes('CUSTOM'), false, 'customInspect disabled');
}

class MockChild extends HandleObject {
    constructor() { super('fake-child-handle'); }
    get [Symbol.toStringTag]() { return 'MockChild'; }
    get id() { return 7; }
}

class MockNode extends HandleObject {
    constructor() { super('fake-handle'); }
    get [Symbol.toStringTag]() { return 'MockNode'; }
    get width() { return 210; }
    get name() { return 'page'; }
    get bad() { throw new Error('dead handle'); }
    get child() { return new MockChild(); }
}

function testHandleObjects() {
    const node = new MockNode();
    assertEq(inspect(node, { breakLength: 200 }),
        "MockNode { width: 210, name: 'page', bad: <error: dead handle>, child: [MockChild] }",
        'handle object getter walk');

    assertEq(inspect(node, { breakLength: 200, expandNestedHandleObjects: true }),
        "MockNode { width: 210, name: 'page', bad: <error: dead handle>, child: MockChild { id: 7 } }",
        'nested handle object expansion');

    // The raw native handle must never be shown.
    console.assert(!inspect(node).includes('fake-handle'), 'handle value hidden');

    // Derived getters shadow base getters; base-only getters still appear.
    class Base extends HandleObject {
        constructor() { super('h'); }
        get v() { return 'base'; }
        get b() { return 1; }
    }
    class Derived extends Base {
        get v() { return 'derived'; }
        get d() { return 2; }
    }
    assertEq(inspect(new Derived()), "Derived { v: 'derived', d: 2, b: 1 }", 'derived handle object');
}

// Mirrors the shape the native Enum template gives enum values: an
// isEnumValue marker, toString and toStringTag on the prototype, and an own
// 'value' property on the instance.
function makeMockEnumValue() {
    function RasterFormat() {}
    RasterFormat.prototype.isEnumValue = true;
    RasterFormat.prototype.toString = function () { return 'RGBA8'; };
    Object.defineProperty(RasterFormat.prototype, Symbol.toStringTag, {
        get() { return 'RasterFormat'; },
    });
    const e = new RasterFormat();
    e.value = 0;
    return e;
}

function testEnums() {
    const e = makeMockEnumValue();
    assertEq(inspect(e), 'RGBA8', 'enum value prints its name by default');
    assertEq(inspect({ format: e }), '{ format: RGBA8 }', 'enum value inside object');
    assertEq(inspect(e, { enums: 'brief' }), 'RGBA8', 'enums brief');
    assertEq(inspect(e, { enums: 'full' }), 'RasterFormat.RGBA8', 'enums full');
    assertEq(inspect({ format: e }, { enums: 'full' }), '{ format: RasterFormat.RGBA8 }', 'enums full inside object');
    assertEq(inspect(e, { enums: 'raw' }), 'RasterFormat { value: 0 }', 'enums raw');
}

function testFormat() {
    assertEq(format('%s %d', 'a', 5), 'a 5', 'format %s %d');
    assertEq(format('%i', '42.9'), '42', 'format %i');
    assertEq(format('%f', '1.5x'), '1.5', 'format %f');
    assertEq(format('%j', { a: 1 }), '{"a":1}', 'format %j');
    assertEq(format('%%'), '%', 'format %%');
    assertEq(format('%s'), '%s', 'format missing arg');
    assertEq(format('a', 'b'), 'a b', 'format extra string arg');
    assertEq(format({ a: 1 }), '{ a: 1 }', 'format non-string first arg');
    assertEq(format('x:', { a: 1 }), 'x: { a: 1 }', 'format string then object');

    const circ = {};
    circ.self = circ;
    assertEq(format('%j', circ), '[Circular]', 'format %j circular');

    assertEq(formatWithOptions({ depth: 0 }, { a: { b: 1 } }), '{ a: [Object] }', 'formatWithOptions depth');
}

function testPatchConsole() {
    const captured = [];
    const recorder = function (...args) { captured.push(args); };
    const realLog = console.log;
    console.log = recorder;
    try {
        patchConsole();
        patchConsole(); // idempotent

        console.log('obj:', { a: 1 });
        console.assert(captured.length === 1, 'patched log called once');
        assertEq(captured[0].length, 1, 'patched log passes a single string');
        assertEq(captured[0][0], 'obj: { a: 1 }', 'patched log output');

        console.dir({ a: { b: 1 } }, { depth: 0 });
        assertEq(captured[1][0], '{ a: [Object] }', 'patched dir output');

        unpatchConsole();
        console.assert(console.log === recorder, 'unpatch restores previous log');
        unpatchConsole(); // idempotent
    }
    finally {
        unpatchConsole();
        console.log = realLog;
    }
}

module.exports.runTests = function () {
    testPrimitives();
    testStrings();
    testArrays();
    testCollections();
    testBuiltins();
    testObjects();
    testFunctions();
    testErrors();
    testDepth();
    testCircular();
    testGetters();
    testShowHidden();
    testSorted();
    testBreakLength();
    testCustomInspect();
    testHandleObjects();
    testEnums();
    testFormat();
    testPatchConsole();
};
