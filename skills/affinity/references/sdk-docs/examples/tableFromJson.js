'use strict';

// Builds a new A4 landscape document containing a TableTextNode populated
// from the countries.json dataset (first 20 entries), with field names as a
// bold 14pt header row. Tries to fetch the dataset over the network; if
// networking is disabled it falls back to the bundled local copy.

const { ErrorCode } = require('affinity:common');
const { Document, DocumentPreset } = require('/document.js');
const { HttpRequest, RequestMethod } = require('/network.js');
const { TableTextNodeDefinition } = require('/nodes.js');
const { AddChildNodesCommandBuilder } = require('/commands.js');
const { Selection, TextSelection } = require('/selections.js');
const { HardBreakType } = require('/story.js');
const { StoryDelta } = require('/storydelta.js');
const { GlyphAttDoubleType } = require('/glyphatts.js');
const { FontWeight } = require('/fonts.js');

const DATA_URL = "https://jsonlint.com/datasets/countries.json";
const LOCAL_FALLBACK = require('/examples/countries.json');
const NUM_ROWS = 20;
const HEADER_PT = 14;
const BODY_PT = 10;

function newA4Empty(isLandscape) {
    const a4 = DocumentPreset.all.filter(p => p.name.includes("A4"))[0];
    return Document.createFromPreset(a4, isLandscape);
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
