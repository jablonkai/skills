'use strict';

const { ApplicationApi, ApplicationSettingsApi, BuildKind, UiParadigm } = require('affinity:application');
const { UiApi } = require('affinity:ui');
const { Document } = require('/document.js');

class ApplicationDocuments {
    static get [Symbol.toStringTag]() {
        return 'ApplicationDocuments';
    }

    static toString() {
        return ApplicationDocuments[Symbol.toStringTag];
    }
    
    static get all() {
        return Document.all;
    }
    
    static get current() {
        return Document.current;
    }

    static load(path) {
        return Document.load(path);
    }
}


class ApplicationSettings {
    static get [Symbol.toStringTag]() {
        return 'ApplicationSettings';
    }

    static toString() {
        return ApplicationSettings[Symbol.toStringTag];
    }

    static get loadPSDWithEditableText() {
        return ApplicationSettingsApi.getLoadPSDWithEditableText();
    }

    static set loadPSDWithEditableText(value) {
        ApplicationSettingsApi.setLoadPSDWithEditableText(value);
    }

    static get undoLimit() {
        return ApplicationSettingsApi.getUndoLimit();
    }

    static get allowCodeGenerationFromStrings() {
        return ApplicationSettingsApi.getAllowCodeGenerationFromStrings();
    }
}


class Application {
    static get [Symbol.toStringTag]() {
        return 'Application';
    }

    static toString() {
        return Application[Symbol.toStringTag];
    }

    static get documents() {
        return ApplicationDocuments;
    }
    
    static alert(message, title) {
        return UiApi.alert(message, title);
    }
    
    static confirm(message, title) {
        return UiApi.confirm(message, title);
    }
    
    static prompt(message, title, initialText) {
        return UiApi.prompt(message, title, initialText);
    }
    
    static chooseFile() {
        return UiApi.chooseFile();
    }
    
    static alertAsync(message, title, callback) {
        return UiApi.alertAsync(message, title, callback);
    }
    
    static confirmAsync(message, title, callback) {
        return UiApi.confirmAsync(message, title, callback);
    }
    
    static promptAsync(message, title, initialText, callback) {
        return UiApi.promptAsync(message, title, initialText, callback);
    }
    
    static chooseFileAsync(callback) {
        return UiApi.chooseFileAsync(callback);
    }

    static get compileDate() {
        return ApplicationApi.getCompileDate();
    }

    static get platformName() {
        return ApplicationApi.getPlatformName();
    }

    static get shortVersion() {
        return ApplicationApi.getShortVersion();
    }

    static get version() {
        return ApplicationApi.getVersion();
    }

    static get buildVersion() {
        return ApplicationApi.getBuildVersion();
    }

    static get majorVersion() {
        return ApplicationApi.getMajorVersion();
    }

    static get minorVersion() {
        return ApplicationApi.getMinorVersion();
    }

    static get revisionVersion() {
        return ApplicationApi.getRevisionVersion();
    }

    static get documentVersion() {
        return ApplicationApi.getDocumentVersion();
    }

    static get buildKind() {
        return ApplicationApi.getBuildKind();
    }

    static get productCopyrightMessage() {
        return ApplicationApi.getProductCopyrightMessage();
    }

    static get productFullName() {
        return ApplicationApi.getProductFullName();
    }

    static get productLongName() {
        return ApplicationApi.getProductLongName();
    }

    static get productPrimaryFileExtension() {
        return ApplicationApi.getProductPrimaryFileExtension();
    }

    static get productVersionName() {
        return ApplicationApi.getProductVersionName();
    }

    static get productShortName() {
        return ApplicationApi.getProductShortName();
    }

    static get suiteFullName() {
        return ApplicationApi.getSuiteFullName();
    }

    static get uiParadigm() {
        return ApplicationApi.getUiParadigm();
    }
    
    static get argC() {
        return ApplicationApi.getArgC();
    }
    
    static get argV() {
        return ApplicationApi.getArgV();
    }

    static get args() {
        return ApplicationApi.getArgV();
    }

    static get settings() {
        return ApplicationSettings;
    }
    
    /**
    * @deprecated Use get userDesktopPath()
    */
    static get getUserDesktopPath() {
        console.warn("Using deprecated get getUserDesktopPath() property. Use get userDesktopPath() instead.");
        return this.userDesktopPath
    }

    static get userDesktopPath() {
        return ApplicationApi.getUserDesktopPath();
    }

    static get resourcesPath() {
        return ApplicationApi.getResourcesPath();
    }
}

module.exports.Application = Application;
module.exports.BuildKind = BuildKind;
module.exports.UiParadigm = UiParadigm;

// for backwards compatibility
module.exports.app = Application;
