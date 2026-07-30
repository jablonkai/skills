'use strict';

const { ApplicationApi, ApplicationSettingsApi, BuildKind, UiParadigm } = require('affinity:application');
const { UiApi } = require('affinity:ui');
const { Document } = require('./document.js');

class AppDocuments {
    get [Symbol.toStringTag]() {
        return 'AppDocuments';
    }
    
    get all() {
        return Document.all;
    }
    
    get current() {
        return Document.current;
    }

    load(path) {
        return Document.load(path);
    }
}


class ApplicationSettings {
    get [Symbol.toStringTag]() {
        return 'ApplicationSettings';
    }

    get loadPSDWithEditableText() {
        return ApplicationSettingsApi.getLoadPSDWithEditableText();
    }

    set loadPSDWithEditableText(value) {
        ApplicationSettingsApi.setLoadPSDWithEditableText(value);
    }

    get undoLimit() {
        return ApplicationSettingsApi.getUndoLimit();
    }
}

const applicationSettings = new ApplicationSettings();


class Application {
    #documents;

    constructor() {
        this.#documents = new AppDocuments();
    }

    get [Symbol.toStringTag]() {
        return 'Application';
    }
    
    get documents() {
        return this.#documents;
    }
    
    alert(message, title) {
        return UiApi.alert(message, title);
    }
    
    confirm(message, title) {
        return UiApi.confirm(message, title);
    }
    
    prompt(message, title, initialText) {
        return UiApi.prompt(message, title, initialText);
    }
    
    chooseFile() {
        return UiApi.chooseFile();
    }
    
    alertAsync(message, title, callback) {
        return UiApi.alertAsync(message, title, callback);
    }
    
    confirmAsync(message, title, callback) {
        return UiApi.confirmAsync(message, title, callback);
    }
    
    promptAsync(message, title, initialText, callback) {
        return UiApi.promptAsync(message, title, initialText, callback);
    }
    
    chooseFileAsync(callback) {
        return UiApi.chooseFileAsync(callback);
    }

    get compileDate() {
        return ApplicationApi.getCompileDate();
    }

    get platformName() {
        return ApplicationApi.getPlatformName();
    }

    get shortVersion() {
        return ApplicationApi.getShortVersion();
    }

    get version() {
        return ApplicationApi.getVersion();
    }

    get buildVersion() {
        return ApplicationApi.getBuildVersion();
    }

    get majorVersion() {
        return ApplicationApi.getMajorVersion();
    }

    get minorVersion() {
        return ApplicationApi.getMinorVersion();
    }

    get revisionVersion() {
        return ApplicationApi.getRevisionVersion();
    }

    get documentVersion() {
        return ApplicationApi.getDocumentVersion();
    }

    get buildKind() {
        return ApplicationApi.getBuildKind();
    }

    get productCopyrightMessage() {
        return ApplicationApi.getProductCopyrightMessage();
    }

    get productFullName() {
        return ApplicationApi.getProductFullName();
    }

    get productLongName() {
        return ApplicationApi.getProductLongName();
    }

    get productPrimaryFileExtension() {
        return ApplicationApi.getProductPrimaryFileExtension();
    }

    get productVersionName() {
        return ApplicationApi.getProductVersionName();
    }

    get productShortName() {
        return ApplicationApi.getProductShortName();
    }

    get suiteFullName() {
        return ApplicationApi.getSuiteFullName();
    }

    get uiParadigm() {
        return ApplicationApi.getUiParadigm();
    }
    
    get argC() {
        return ApplicationApi.getArgC();
    }
    
    get argV() {
        return ApplicationApi.getArgV();
    }

    get args() {
        return ApplicationApi.getArgV();
    }

    get settings() {
        return applicationSettings;
    }
    
    /**
    * @deprecated Use get userDesktopPath()
    */
    get getUserDesktopPath() {
        console.warn("Using deprecated get getUserDesktopPath() property. Use get userDesktopPath() instead.");
        return this.userDesktopPath
    }

    get userDesktopPath() {
        return ApplicationApi.getUserDesktopPath();
    }
}

module.exports.app = new Application();
module.exports.BuildKind = BuildKind;
module.exports.UiParadigm = UiParadigm;
