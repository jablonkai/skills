'use strict';

const { EnumerationResult } = require('affinity:common');
const { FontApi, FontCollectionApi, FontFamilyApi, FontWeight, FontWidth, PanoseApi, PanoseType } = require('affinity:fonts');
const { HandleObject } = require('./handleobject.js');

class Panose extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Panose';
    }

    clone() {
        return new Panose(PanoseApi.clone(this.handle));
    }

    is(type) {
        return PanoseApi.is(this.handle, type);
    }
    
    get isSerif() {
        return PanoseApi.isSerif(this.handle);
    }

    get isSansSerif() {
        return PanoseApi.isSansSerif(this.handle);
    }

    get isMonospaced() {
        return PanoseApi.isMonospaced(this.handle);
    }

    get isEmpty() {
        return PanoseApi.isEmpty(this.handle);
    }

    toString() {
        return PanoseApi.toString(this.handle);
    }

    getDistance(other) {
        return PanoseApi.getDistance(this.handle, other.handle);
    }
}

class Font extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Font';
    }

    clone() {
        return new Font(FontApi.clone(this.handle));
    }

    get isValid() {
        return FontApi.isValid(this.handle);
    }

    get isNormal() {
        return FontApi.isNormal(this.handle);
    }

    get isBold() {
        return FontApi.isBold(this.handle);
    }
    
    get isVariableBold() {
        return FontApi.isVariableBold(this.handle);
    }

    get isItalic() {
        return FontApi.isItalic(this.handle);
    }

    get isVariableItalic() {
        return FontApi.isVariableItalic(this.handle);
    }

    get isBoldAvailable() {
        return FontApi.isBoldAvailable(this.handle);
    }

    get isItalicAvailable() {
        return FontApi.isItalicAvailable(this.handle);
    }

    get weight() {
        return FontApi.getWeight(this.handle);
    }

    get normalizedWeight() {
        return FontApi.getNormalizedWeight(this.handle);
    }

    get width() {
        return FontApi.getWidth(this.handle);
    }

    get normalizedWidth() {
        return FontApi.getNormalizedWidth(this.handle);
    }

    get isCondensed() {
        return FontApi.isCondensed(this.handle);
    }

    get isExpanded() {
        return FontApi.isExpanded(this.handle);
    }

    get panose() {
        return new Panose(FontApi.getPanose(this.handle));
    }

    get postscriptName() {
        return FontApi.getPostscriptName(this.handle);
    }

    get familyName() {
        return FontApi.getFamilyName(this.handle);
    }

    get ribbiFamily() {
        return FontApi.getRibbiFamily(this.handle);
    }

    get wwsFamily() {
        return FontApi.getWwsFamily(this.handle);
    }

    get postscriptPrefix() {
        return FontApi.getPostscriptPrefix(this.handle);
    }

    get traitsName() {
        return FontApi.getTraitsName(this.handle);
    }

    get variableBold() {
        return FontApi.getVariableBold(this.handle);
    }

    get variableItalic() {
        return FontApi.getVariableItalic(this.handle);
    }

    toString() {
        return FontApi.toString(this.handle);
    }

    get isSerif() {
        return this.panose.isSerif;
    }

    get isSansSerif() {
        return this.panose.isSansSerif;
    }

    get isMonospaced() {
        return this.panose.isMonospaced;
    }

    static enumerate(callback) {
        if (typeof callback === 'function') {
            function wrapped(fontHandle) {
                return callback(new Font(fontHandle));
            }
            return FontApi.enumerate(wrapped);
        }
        return FontApi.enumerate(callback);
    }

    static get all() {
        let res = [];
        Font.enumerate(font => {
            res.push(font);
            return EnumerationResult.Continue;
        });
        return res;
    }

    static createEmpty() {
        return new Font(FontApi.createEmpty());
    }

    static createDefault() {
        return new Font(FontApi.createDefault());
    }

    static createDefaultMonospaced() {
        return new Font(FontApi.createDefaultMonospaced());
    }

    static createDefaultSymbol() {
        return new Font(FontApi.createDefaultSymbol());
    }

    static create(family, weight, isItalic, width) {
        return new Font(FontApi.create(family, weight, isItalic, width));
    }

    getDistance(other) {
        return FontApi.getDistance(this.handle, other.handle);
    }
}

class FontCollection extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FontCollection';
    }

    get displayName() {
        return FontCollectionApi.getDisplayName(this.handle);
    }

    static enumerateCollections(callback) {
        if (typeof callback === 'function') {
            function wrapped(collectionHandle) {
                return callback(new FontCollection(collectionHandle));
            }
            return FontCollectionApi.enumerateCollections(wrapped);
        }
        return FontCollectionApi.enumerateCollections(callback);
    }

    static get all() {
        let res = [];
        FontCollection.enumerateCollections(collection => {
            res.push(collection);
            return EnumerationResult.Continue;
        });
        return res;
    }
}


class FontFamily extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FontFamily';
    }

    clone() {
        return new FontFamily(FontFamilyApi.clone(this.handle));
    }

    get name() {
        return FontFamilyApi.getName(this.handle);
    }

    get fontCount() {
        return FontFamilyApi.getFontCount(this.handle);
    }

    get length() {
        return this.fontCount;
    }

    getFont(index) {
        return new Font(FontFamilyApi.getFont(this.handle, index));
    }

    enumerateFonts(callback) {
        if (typeof callback === 'function') {
            function wrapped(fontHandle) {
                return callback(new Font(fontHandle));
            }
            return FontFamilyApi.enumerateFonts(this.handle, wrapped);
        }
        return FontFamilyApi.enumerateFonts(this.handle, callback);
    }

    get fonts() {
        let res = [];
        this.enumerateFonts(font => {
            res.push(font);
            return EnumerationResult.Continue;
        });
        return res;
    }

    static enumerate(callback) {
        if (typeof callback === 'function') {
            function wrapped(fontFamilyHandle) {
                return callback(new FontFamily(fontFamilyHandle));
            }
            return FontFamilyApi.enumerate(wrapped);
        }
        return FontFamilyApi.enumerate(callback);
    }

    static get all() {
        let res = [];
        FontFamily.enumerate(fontFamily => {
            res.push(fontFamily);
            return EnumerationResult.Continue;
        });
        return res;
    }
    
    get hasVariations() {
        return FontFamilyApi.hasVariations(this.handle);
    }
    
    get hasFixed() {
        return FontFamilyApi.hasFixed(this.handle);
    }
}

module.exports.Font = Font;
module.exports.FontCollection = FontCollection;
module.exports.FontFamily = FontFamily;
module.exports.FontWeight = FontWeight;
module.exports.FontWidth = FontWidth;
module.exports.Panose = Panose;
module.exports.PanoseType = PanoseType;
