'use strict';

const {Buffer} = require('/buffer');

function testSlice() {
    // slice is a copy of the original buffer, so modifying it should not modify the original.
    const buf = Buffer.create(256);
    const bufArr = buf.array;
    for (let i = 0; i < bufArr.length; ++i) {
        bufArr[i] = i;
    }
    
    const slice = buf.slice(10, 20);
    const sliceArr = slice.array;
    for (let i = 0; i < sliceArr.length; ++i) {
        console.assert(sliceArr[i] === i + 10);
    }

    sliceArr[0] = 0;
    console.assert(sliceArr[0] === 0);
    console.assert(bufArr[10] === 10);
}


function testSpan() {
    // span is a subrange of the original buffer, so modifying it should modify the original too.
    const buf = Buffer.create(256);
    const bufArr = buf.array;
    for (let i = 0; i < bufArr.length; ++i) {
        bufArr[i] = i;
    }
    
    const span = buf.span(10, 20);
    const spanArr = span.array;
    for (let i = 0; i < spanArr.length; ++i) {
        console.assert(spanArr[i] === i + 10);
    }

    spanArr[0] = 0;
    console.assert(spanArr[0] === 0);
    console.assert(bufArr[10] === 0);
}


module.exports.runTests = function() {
    testSlice();
    testSpan();
}
