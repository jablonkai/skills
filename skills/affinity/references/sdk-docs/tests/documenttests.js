'use strict';

const { EnumerationResult } = require('affinity:common')
const {ErrorCode} = require('affinity:common');
const {Document, DocumentPromises, LoadDocumentOptions, FileExportOptions, DrawingScale, DocumentPreset, NewDocumentOptions} = require("/document.js");
const { DocumentCommand } = require("/commands.js")
const { FileSystemPromises } = require("/fs.js")
const { TestUtils } = require("/tests/testUtils");
const { UnitType } = require('/units.js');

async function testLoadDocument(func, path)
{
	let ret;
	try {
		ret = await func();
	} catch (error) {
		console.log("result:", error.cause);
		console.log("description:", error);
		return error;
	}
	const doc = new Document(ret);
	console.assert(doc.path === path);
}

async function testSaveDocument(func, expected)
{
	let ret;
	try {
		ret = await func();
	} catch (error) {
		console.log("result:", error);
		ret = error;
	}
	console.assert(ret === expected);
}

function testGetAll() {
	const openedDocs = Document.opened;
	console.log("openedDocs.length: " + openedDocs.length);
	for (const doc of openedDocs) {
		console.log("doc: " + doc);
		console.log("path: " + doc.path);
		console.log("isOpen: " + doc.isOpen);
		console.log("title: " + doc.title);
		console.log("dpi: " + doc.dpi)
		console.log("viewDpi: " + doc.viewDpi)
		console.log("dims.width: " + doc.dims.width)
		console.log("dims.height: " + doc.dims.height)
	}
}

function testGetCurrent() {
	let doc = Document.current;
	console.assert(doc != null);
	console.log("doc: " + doc);
	console.log("path: " + doc.path);
	console.log("isOpen: " + doc.isOpen);
	console.log("title: " + doc.title);
	console.log("dpi: " + doc.dpi)
	console.log("viewDpi: " + doc.viewDpi)
	console.log("dims.width: " + doc.dims.width)
	console.log("dims.height: " + doc.dims.height)
	return doc;
}

async function testCloseDocument(func, expected)
{
    let ret;
    try {
        ret = await func();
    } catch (error) {
        console.log("result:", error);
        ret = error;
    }
    console.assert(ret === expected);
}

function testDrawingScale() {
    let defaultScales = DrawingScale.getDefaults(UnitType.Millimetres);
    for (const scale of defaultScales) {
        console.log(scale.asString());
    }
}

function testNewDocument() {
    let defaultOptions = NewDocumentOptions.createDefault();
    {
        let doc = Document.createFromOptions(defaultOptions);
        console.assert(doc.history.size == 0);
        doc.close();
    }
    let preset = DocumentPreset.all.filter(ps => ps.name == "A4").first;
    let newDocOptions = NewDocumentOptions.createFromPreset(preset);
    newDocOptions.dpi = 114;
    newDocOptions.viewDpi = 512;
    newDocOptions.width = 2048;
    newDocOptions.height = 4096;
    
    {
        let doc = Document.createFromOptions(newDocOptions);
        console.assert(TestUtils.floatEqual(doc.dims.height / doc.dims.width, 2.0));
        console.assert(TestUtils.floatEqual(doc.dpi, 114));
        console.assert(TestUtils.floatEqual(doc.viewDpi, 512));
        doc.close();
    }
    
    let maxDocOptions = NewDocumentOptions.createFromPreset(preset);
    maxDocOptions.dpi = 4000000;
    maxDocOptions.width = 3854;
    maxDocOptions.height = 23450;
    {
        try {
            let doc = Document.createFromOptions(maxDocOptions);
        } catch(err) {
            console.assert(err.errorCode.value == ErrorCode.INVALID_ARGS);
        }
    }
}

function printRecord(documentExportRecord) {
    console.log(documentExportRecord);
    console.log(documentExportRecord.path);
    console.log(documentExportRecord.result);
    console.log(documentExportRecord.isSuccess);
    console.log(documentExportRecord.hasWarnings);
    if (documentExportRecord.hasWarnings)
    {
        console.log("warningString:", documentExportRecord.warningString);
        console.log("warningMessage:", documentExportRecord.warningMessage.title, documentExportRecord.warningMessage.warning);
    }
    try {
        console.log("errorMessage:", documentExportRecord.errorMessage.title, documentExportRecord.errorMessage.reason);
    } catch (e) {
        console.log("No error message");
    }
	
	return EnumerationResult.Continue;
}

async function runTests() {
    testNewDocument();

	const load_path = "/path/to/doc.afdesign";
	const save_as_path = "/path/to/doc_copy.afdesign";
	const save_as_package_path = "/path/to/doc.afpackage";
    const export_path = "/path/to/doc.png";

	try {
        FileExportOptions.enumeratePresetNames((presetName) => { console.log(presetName); return EnumerationResult.Continue; });
		await testLoadDocument(DocumentPromises.load.bind(null, load_path, LoadDocumentOptions.createDefault(), false), load_path);
        testGetAll();
        let doc = testGetCurrent();

        const exportOptions = FileExportOptions.createWithPresetName("PNG");
        let documentExportRecords = doc.export(export_path, exportOptions, null, null);

        documentExportRecords.enumerate(printRecord);
		await testSaveDocument(doc.promises.saveAsPackage.bind(doc.promises, save_as_package_path, true, true), ErrorCode.OK.value);
		await testSaveDocument(doc.promises.save.bind(doc.promises, false), ErrorCode.OK.value); // TODO: fix assert on Windows
		await testSaveDocument(doc.promises.saveAs.bind(doc.promises, save_as_path, true), ErrorCode.OK.value);
        await testCloseDocument(doc.promises.close.bind(doc.promises), ErrorCode.OK.value); // TODO: implement on Windows
        
        testDrawingScale();
	} catch (error) {
		console.log(error.stack);
	}

	console.log("runTests() finished");
}

module.exports.runTests = runTests;
module.exports.testNewDocument = testNewDocument;
module.exports.testDrawingScale = testDrawingScale;
