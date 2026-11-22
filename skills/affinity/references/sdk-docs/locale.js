'use strict';

const { EnumerationResult, LocaleApi } = require('affinity:common');
const { HandleObject } = require('/handleobject.js');

class Locale extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Locale';
    }

    get id() {
        return LocaleApi.getID(this.handle);
    }

    get isoCode() {
        return LocaleApi.getISOCode(this.handle);
    }

    static get current() {
        return new Locale(LocaleApi.getCurrent());
    }

    static enumerateUserPreferredLanguageIDs(callback) {
        return LocaleApi.enumerateUserPreferredLanguageIDs(callback);
    }

    static get userPreferredLanguageIDs() {
        const languageIDs = [];
        Locale.enumerateUserPreferredLanguageIDs(languageID => {
            languageIDs.push(languageID);
            return EnumerationResult.Continue;
        });
        return languageIDs;
    }
}

module.exports.Locale = Locale;
