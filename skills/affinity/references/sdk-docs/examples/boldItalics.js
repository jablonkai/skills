'use strict';

const { Document } = require('/document.js');
const { FontWeight } = require('/fonts.js');
const { StoryDelta } = require('/storydelta.js');

// Makes the selected text bold and italic by creating two StoryDeltas and combining them into a composite delta.
function main() {
    const doc = Document.current;
    const makeBold = StoryDelta.createWeight(FontWeight.Bold);
    const makeItalic = StoryDelta.createItalic(true);
    const composite = StoryDelta.createComposite([makeBold, makeItalic]);
    doc.formatText(composite);
}

module.exports.main = main;
