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

// ---- Break ----------------------------------------------------------------------------------

// Unlink is "break the flow before this frame": the frames before keep the story, the frames
// from it onward form a new flow with an empty story. Breaking arbitrary frames therefore
// means unlinking everything after the head, relinking the kept frames in order, and then
// moving text between the resulting stories.
function breakFlow(doc, frames, breaking) {
    const story = frames[0].story;
    const ranges = visibleRanges(frames);
    const kept = frames.map((f, i) => i).filter(i => !breaking.has(i));
    const head = kept.length > 0 ? kept[0] : 0;

    const captured = new Map([...breaking].filter(i => i != 0).map(i => [i, captureRange(story, ranges[i])]));
    const tail = head > 0 ? captureRange(story, { begin: ranges[head].begin, end: story.length }) : null;

    // Unlink from the back so every frame after the first becomes a singleton.
    const cmds = [];
    for (let i = frames.length - 1; i >= 1; --i)
        cmds.push(DocumentCommand.createUnlinkTextFrame(frames[i]));
    // Relink the kept frames onto the head, in flow order.
    for (let j = 1; j < kept.length; ++j)
        cmds.push(DocumentCommand.createLinkTextFrame(frames[kept[j - 1]], frames[kept[j]]));
    executeAll(doc, cmds);

    cmds.length = 0;
    // The head flow's story: frame 0's if it is the head, otherwise rebuilt from the tail.
    const headOffset = head > 0 ? ranges[head].begin : 0;
    if (tail)
        restoreCommands(doc, frames[head], tail, cmds);
    // Remove broken frames' text from the head story, from the back so ranges stay valid.
    for (const i of [...breaking].filter(i => i > head).sort((a, b) => b - a))
        cmds.push(DocumentCommand.createSetText(textSelection(doc, frames[head], ranges[i].begin - headOffset, ranges[i].end - headOffset), ""));
    // Frame 0 keeps only its own text when it is not the head.
    if (head > 0)
        cmds.push(DocumentCommand.createSetText(textSelection(doc, frames[0], ranges[0].end, story.length), ""));
    // Give every other broken frame its text back.
    for (const [i, c] of captured)
        restoreCommands(doc, frames[i], c, cmds);
    executeAll(doc, cmds);
}

function breakFrames(doc, selected) {
    // Group the selection by flow, keyed on the first frame of each flow.
    const flows = new Map();
    for (const frame of selected) {
        const frames = framesInFlow(frame);
        const key = frames[0].textFrameInterface.textBegin + ":" + frames[0].story.text;
        if (!flows.has(key))
            flows.set(key, { frames, breaking: new Set() });
        flows.get(key).breaking.add(frames.findIndex(f => f.isSameNode(frame)));
    }
    for (const { frames, breaking } of flows.values())
        breakFlow(doc, frames, breaking);
}

function main() {
    const doc = Document.current;
    if (!doc) {
        alert("This script requires an open document");
        return;
    }
    const frames = doc.selection.nodes
        .filter(n => n.isTextNode && n.textFrameInterface.isMultiFrameTextFlow)
        .toArray();
    if (frames.length == 0) {
        alert("Please select one or more linked text frames");
        return;
    }
    breakFrames(doc, frames);
}

module.exports.main = main;
