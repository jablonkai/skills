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

// Builds a new A4 landscape document containing a TableTextNode populated
// from the countries.json dataset (first 20 entries), with field names as a
// bold 14pt header row. Tries to fetch the dataset over the network; if
// networking is disabled it falls back to the bundled local copy.

const { ErrorCode } = require('affinity:common');
const { Document, DocumentPreset } = require('/document');
const { HttpRequest, RequestMethod } = require('/network');
const { TableTextNodeDefinition } = require('/nodes');
const { AddChildNodesCommandBuilder } = require('/commands');
const { Selection, TextSelection } = require('/selections');
const { HardBreakType } = require('/story');
const { StoryDelta } = require('/storydelta');
const { GlyphAttDoubleType } = require('/glyphatts');
const { FontWeight } = require('/fonts');

const DATA_URL = "https://jsonlint.com/datasets/countries.json";
const LOCAL_FALLBACK = require('/examples/countries.json');
const NUM_ROWS = 20;
const HEADER_PT = 14;
const BODY_PT = 10;

function newA4Empty(landscape) {
    const a4 = DocumentPreset.all.filter(p => p.name.includes("A4"))[0];
    return Document.createFromPreset(a4, landscape);
}

// Returns the parsed JSON body, or null if the request is not denied
function fetchJson(url) {
    let result;
    try {
        result = HttpRequest.create(url, RequestMethod.Get).do();
    } catch (e) {
        if (e.errorCode && e.errorCode === ErrorCode.PERMISSION_DENIED) {
            return null;
        }
        throw e;
    }
    const content = result.response.content;
    const text = (typeof content === 'string')
        ? content
        : new TextDecoder().decode(content.buffer ? content : new Uint8Array(content));
    return JSON.parse(text);
}

function loadCountries() {
    const data = fetchJson(DATA_URL) || LOCAL_FALLBACK;
    return data.countries;
}

// Cells of a TableTextNode are separated by HardBreakType.TableCell glyphs.
// starts[k] is the StoryPos of the first glyph of cell k; cellCount equals
// starts.length, with the final cell ending at story.length (no trailing
// break glyph).
function getCellStarts(story) {
    const starts = [0];
    for (let i = 0; i < story.length; i++) {
        const ht = story.getHardBreakType(i);
        if (ht && ht.value === HardBreakType.TableCell.value) {
            starts.push(i + 1);
        }
    }
    return starts;
}

function selectRange(doc, table, begin, end) {
    const sel = Selection.create(doc, table);
    sel.addSubSelectionForNode(table, TextSelection.create([{ begin, end }]));
    return sel;
}

// For non-last cells, end is the position of the trailing TableCell break
// (the exclusive end of the cell's content). The last cell has no trailing
// break and runs to story.length.
function selectCell(doc, table, starts, k) {
    const end = (k + 1 < starts.length) ? starts[k + 1] - 1 : table.story.length;
    return selectRange(doc, table, starts[k], end);
}

// Reverse order keeps earlier positions stable as the story grows.
function fillCells(doc, table, texts) {
    const starts = getCellStarts(table.story);
    const n = Math.min(starts.length, texts.length);
    for (let k = n - 1; k >= 0; k--) {
        doc.setText(String(texts[k]), selectCell(doc, table, starts, k));
    }
}

function main() {
    const data = loadCountries().slice(0, NUM_ROWS);
    const fields = Object.keys(data[0]);
    const cols = fields.length;
    const rows = NUM_ROWS + 1;

    const doc = newA4Empty(true);
    const margin = 40;
    const box = {
        x: margin,
        y: margin,
        width: doc.widthPixels - 2 * margin,
        height: doc.heightPixels - 2 * margin,
    };

    const def = TableTextNodeDefinition.create(box, { width: cols, height: rows });
    doc.addNode(def);
    let table = doc.layers.first;

    const cellTexts = [];
    for (const f of fields) cellTexts.push(f);
    for (const row of data) {
        for (const f of fields) {
            cellTexts.push(row[f] == null ? "" : String(row[f]));
        }
    }
    fillCells(doc, table, cellTexts);
    
    // A fresh TableTextNode has a 1px default glyph height; set the body
    // size on the whole (empty) story so every cell inherits it as text
    // is inserted.
    const pxPerPt = doc.dpi / 72;
    const setSize = pt => StoryDelta.createGlyphDouble(GlyphAttDoubleType.Height, pt * pxPerPt);
    doc.formatText(setSize(BODY_PT), selectRange(doc, table, 0, table.story.length));

    // Header row spans cells [0, cols); the range ends just before the
    // break preceding the first body cell.
    const starts = getCellStarts(table.story);
    const headerSel = selectRange(doc, table, 0, starts[cols] - 1);
    const makeBold = StoryDelta.createWeight(FontWeight.Bold);
    doc.formatText(StoryDelta.createComposite([makeBold, setSize(HEADER_PT)]), headerSel);
}

module.exports.main = main;
