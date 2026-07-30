'use strict';

const {Document, DocumentPromises} = require("/document.js");
const {DocumentView, DocumentViewPromises} = require("/documentView.js");
const timersmodule = require("affinity:timers");
const {ErrorCode} = require("affinity:common");

const sleep_interval = 2000;

async function testGetCurrent() {
	let docViewHandle = await DocumentViewPromises.current;
	return new DocumentView(docViewHandle);
}

async function testGetTitle(view) {
	await view.promises.title;
}

async function testSetGetZoom(view) {
	await view.promises.setZoom(50);
	let value = await view.promises.zoom;
	console.assert(Math.abs(value - 50) < 0.01);
}

async function testZoomInOut(view) {
	await view.promises.setZoom(50);
	timersmodule.sleep(sleep_interval);
	await view.promises.zoomIn();
	timersmodule.sleep(sleep_interval);
	await view.promises.zoomOut();
	timersmodule.sleep(sleep_interval);
	let value = await view.promises.zoom;
	console.assert(Math.abs(value - 50) < 0.01);
}

async function testZoomOps(view) {
	await view.promises.setZoom(50);
	timersmodule.sleep(sleep_interval);
	await view.promises.zoomToFit();
	timersmodule.sleep(sleep_interval);
	await view.promises.zoomToWidth();
	timersmodule.sleep(sleep_interval);
	await view.promises.zoomToSelection();
	timersmodule.sleep(sleep_interval);
	await view.promises.zoomToPixelSize();
	timersmodule.sleep(sleep_interval);
	await view.promises.zoomToPrintSize();
}

async function testRotate(view) {
	await view.promises.setZoom(50);
	timersmodule.sleep(sleep_interval);
	await view.promises.rotate(Math.PI);
	timersmodule.sleep(sleep_interval);
	await view.promises.rotate(Math.PI / 2);
	timersmodule.sleep(sleep_interval);
	await view.promises.rotate(-Math.PI / 2);
	timersmodule.sleep(sleep_interval);
	await view.promises.resetRotation();
	timersmodule.sleep(sleep_interval);
}

async function testNewView(view) {
    let newViewHandle = await view.promises.newView();

    timersmodule.sleep(sleep_interval);
    return new DocumentView(newViewHandle);
}

async function testSaveDocumentView(func, expected)
{
    let ret;
    try {
        ret = await func();
    } catch (error) {
        console.log("result:", error);
        ret = error;
    }
    console.assert(ret === expected);
    timersmodule.sleep(sleep_interval);
}

async function testCloseDocumentView(view, expected)
{
    let ret;
    try {
        ret = await view.promises.close();
    } catch (error) {
        console.log("result:", error);
        ret = error;
    }
    console.assert(ret === expected);
    timersmodule.sleep(sleep_interval);
}

async function testMakeCurrent(view) {
    await view.promises.makeCurrent();
    timersmodule.sleep(sleep_interval);
}

async function testCentreOn(view, point, expected)
{
    let ret;
    try {
        ret = await view.promises.centreOn(point);
    } catch (error) {
        console.log("result:", error);
        ret = error;
    }
    console.assert(ret === expected);
    timersmodule.sleep(sleep_interval);
}

async function runTests() {
	const loadPath = "/path/to/doc.afdesign";
	try {
        let docHandle = await DocumentPromises.load(loadPath);
        let doc = new Document(docHandle);
        let spreadSize = doc.currentSpread.getSpreadExtents(false, false, false);
		let view = await testGetCurrent();
        await testCentreOn(view, {x: 0, y: 0}, true);
        await testCentreOn(view, {x: spreadSize.width, y : 0}, true);
        await testCentreOn(view, {x: 0, y: spreadSize.height}, true);
        await testCentreOn(view, {x: spreadSize.width, y: spreadSize.height}, true);
        let newView = await testNewView(view);
		await testSetGetZoom(newView);
		await testZoomInOut(newView);
		await testZoomOps(newView);
		await testRotate(newView);
		await testGetTitle(newView);
        await testMakeCurrent(view);
        await testSaveDocumentView(view.promises.save.bind(view.promises), ErrorCode.OK.value);
        await testCloseDocumentView(newView, ErrorCode.OK.value);
        await testCloseDocumentView(view, ErrorCode.OK.value);
	} catch (error) {
		console.log(error.stack)
	}

    console.log("runTests() finished");
}

module.exports.runTests = runTests
