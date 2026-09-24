'use strict';

const { CompoundCommandBuilder, DocumentCommand } = require('/commands.js');
const { Document } = require('/document.js');
const { Selection, TextSelection } = require('/selections.js');
const { StoryDelta } = require('/storydelta.js');


function executeAll(doc, cmds) {
    if (cmds.length == 0)
        return;
    if (cmds.length == 1) {
        doc.executeCommand(cmds[0]);
        return;
    }
    const builder = CompoundCommandBuilder.create();
    for (const cmd of cmds)
        builder.addCommand(cmd);
    doc.executeCommand(builder.createCommand());
}

// Every frame of the flow the given frame belongs to, in flow order.
function framesInFlow(frame) {
    return frame.textFrameInterface.textFlowNodes;
}

// Story range each frame currently displays: from its text begin to the next frame's.
function visibleRanges(frames) {
    const story = frames[0].story;
    const begins = frames.map(f => f.textFrameInterface.textBegin);
    return begins.map((begin, i) => ({ begin, end: i + 1 < begins.length ? begins[i + 1] : story.length }));
}

function textSelection(doc, node, begin, end) {
    const selection = Selection.create(doc, node);
    selection.addSubSelectionForNode(node, TextSelection.create([{ begin, end }]));
    return selection;
}

// ---- Formatting capture -------------------------------------------------------------------

// Attribute runs within [begin, end), re-based to the range start, each with its full state.
function captureRuns(runs, range, attsKey, makeDelta) {
    const result = [];
    for (const run of runs) {
        if (run.begin >= range.end)
            break;
        result.push({
            begin: Math.max(run.begin, range.begin) - range.begin,
            end: Math.min(run.end, range.end) - range.begin,
            delta: makeDelta(run[attsKey])
        });
    }
    return result;
}

// Everything needed to rebuild a range of the story in another frame.
function captureRange(story, range) {
    const glyphs = [];
    for (let pos = range.begin; pos < range.end; ++pos)
        glyphs.push(story.getGlyph(pos));
    return {
        glyphs,
        glyphRuns: captureRuns(story.getGlyphAttRunsFrom(range.begin), range, "glyphAtts", StoryDelta.createFromGlyphAtts),
        paragraphRuns: captureRuns(story.getParagraphAttRunsFrom(range.begin), range, "paragraphAtts", StoryDelta.createFromParagraphAtts)
    };
}

// Re-insert the glyphs, then restore the full attribute state over each run.
function restoreCommands(doc, node, captured, cmds) {
    captured.glyphs.forEach((glyph, i) => cmds.push(DocumentCommand.createInsertGlyph(textSelection(doc, node, i, i), glyph)));
    for (const run of captured.paragraphRuns)
        cmds.push(DocumentCommand.createFormatText(textSelection(doc, node, run.begin, run.end), run.delta));
    for (const run of captured.glyphRuns)
        cmds.push(DocumentCommand.createFormatText(textSelection(doc, node, run.begin, run.end), run.delta));
}

// ---- Split ----------------------------------------------------------------------------------

function splitStory(doc, frames) {
    const story = frames[0].story;
    const ranges = visibleRanges(frames);
    const captured = ranges.slice(1).map(r => captureRange(story, r));

    // Unlink from the back; the first frame is left holding the whole story.
    executeAll(doc, frames.slice(1).reverse().map(n => DocumentCommand.createUnlinkTextFrame(n)));

    const cmds = [];
    if (ranges.length > 1)
        cmds.push(DocumentCommand.createSetText(textSelection(doc, frames[0], ranges[1].begin, story.length), ""));
    frames.slice(1).forEach((frame, i) => restoreCommands(doc, frame, captured[i], cmds));
    executeAll(doc, cmds);
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const frame = doc.selection.nodes.filter(n => n.isTextNode).first;
    if (!frame) {
        alert("Please select a text frame");
        return;
    }
    if (!frame.textFrameInterface.isMultiFrameTextFlow) {
        alert("Please select a story containing more than one text frame");
        return;
    }
    splitStory(doc, framesInFlow(frame));
}

module.exports.main = main;
