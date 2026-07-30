'use strict';

const { app } = require("/application.js");
const { BuildKind, UiParadigm } = require("affinity:application");

function runTests() {
    console.assert(typeof app.compileDate === "string");
    console.assert(typeof app.platformName === "string");
    console.assert(typeof app.shortVersion === "string");
    console.assert(typeof app.version === "string");
    console.assert(typeof app.buildVersion === "number");
    console.assert(typeof app.majorVersion === "number");
    console.assert(typeof app.minorVersion === "number");
    console.assert(typeof app.revisionVersion === "number");

    console.assert(app.buildKind instanceof BuildKind);
    console.assert(typeof app.productCopyrightMessage === "string");
    console.assert(typeof app.productFullName === "string");
    console.assert(typeof app.productLongName === "string");
    console.assert(typeof app.productPrimaryFileExtension === "string");
    console.assert(typeof app.productShortName === "string");
    console.assert(typeof app.productVersionName === "string");
    console.assert(typeof app.suiteFullName === "string");
    console.assert(app.uiParadigm instanceof UiParadigm);
    console.log(app.argC);
    console.log(app.argV);
}

module.exports.runTests = runTests;
