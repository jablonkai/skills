'use strict';

const { TestUtils } = require("/tests/testUtils");
const { DocumentCommand } = require("/commands.js");

const { sleep } = require("affinity:timers");

function runTests() {
    let doc = TestUtils.getFile("/TextTest.afdesign");

    console.assert(doc.snapshots.length === 0);
    console.assert(doc.currentSnapshotIndex === -1);
    console.assert(doc.currentSnapshotHistoryIndex === -1);

    doc.executeCommand(DocumentCommand.createAddDocumentSnapshot("snapshot0"), false);
    console.assert(doc.snapshots.length === 1);
    console.assert(doc.currentSnapshotIndex === -1);
    console.assert(doc.snapshots[0].description === "snapshot0");

    doc.executeCommand(DocumentCommand.createSetCurrentSnapshot(doc.snapshots[0]), false);
    console.assert(doc.currentSnapshotIndex === 0);

    doc.executeCommand(DocumentCommand.createSelectAll(), false);
    doc.executeCommand(DocumentCommand.createDeleteSelection(doc.selection, false, true), false);
    doc.executeCommand(DocumentCommand.createAddDocumentSnapshot("snapshot1"), false);
    console.assert(doc.snapshots.length === 2);
    console.assert(doc.currentSnapshotIndex === 0);
    console.assert(doc.snapshots[1].description === "snapshot1");

    let newdoc1 = doc.snapshots[0].createDocument();
    console.assert(newdoc1.snapshots.length === 0);
    console.assert(newdoc1.currentSnapshotIndex === -1);
    console.assert(newdoc1.currentSnapshotHistoryIndex === -1);

    /*
    TODO: commented out for now as document promise to be implemented.
    let promise = doc.promises.createFromSnapshot(doc.snapshots[0]);
    let newdoc2;
    try {
        newdoc2 = await promise;
    } catch (e) {
        console.assert(false, "DocumentPromises.createFromSnapshot:", e);
    }
    console.assert(newdoc2.snapshots.length === 0);
    console.assert(newdoc2.currentSnapshotIndex === -1);
    console.assert(newdoc2.currentSnapshotHistoryIndex === -1);*/

    doc.executeCommand(DocumentCommand.createSetCurrentSnapshot(doc.snapshots[0]), false);
    console.assert(doc.currentSnapshotIndex === 0);

    doc.executeCommand(DocumentCommand.createRestoreDocumentSnapshot(doc.snapshots[0]), false);
    doc.executeCommand(DocumentCommand.createRestoreDocumentSnapshot(doc.snapshots[1]), false);
    doc.executeCommand(DocumentCommand.createDeleteDocumentSnapshot(doc.snapshots[0]), false);
    console.assert(doc.snapshots.length === 1);
    console.assert(doc.currentSnapshotIndex === -1);
    console.assert(doc.snapshots[0].description === "snapshot1");

    doc.executeCommand(DocumentCommand.createDeleteDocumentSnapshot(doc.snapshots[0]), false);
    console.assert(doc.snapshots.length === 0);
    console.assert(doc.currentSnapshotIndex === -1);

    console.assert(doc.currentSnapshotHistoryIndex === -1);
    doc.executeCommand(DocumentCommand.createSetCurrentSnapshotFromHistoryIndex(0), false);
    console.assert(doc.currentSnapshotHistoryIndex === 0);
    doc.executeCommand(DocumentCommand.createSetCurrentSnapshotFromHistoryIndex(3), false);
    console.assert(doc.currentSnapshotHistoryIndex === 3);

    doc.undo();
    doc.undo();
    doc.undo();
    doc.undo();

    newdoc1.close();
    //newdoc2.close();
    doc.close();
}

module.exports.runTests = runTests
