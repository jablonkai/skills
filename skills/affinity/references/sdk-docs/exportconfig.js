'use strict';

const { ExportConfigApi, ExportFormatApi, ExportScaleApi, ExportScalePreset, ExportScaleSizeType, ExportSizeApi } = require('affinity:dom');
const { EnumerationResult } = require('affinity:common');
const { HandleObject } = require('./handleobject.js');

class ExportScale extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ExportScale';
    }

    get sizeType() {
        return ExportScaleApi.getSizeType(this.handle);
    }

    get hasMultiplier() {
        return ExportScaleApi.hasMultiplier(this.handle);
    }

    get multiplier() {
        return ExportScaleApi.getMultiplier(this.handle);
    }

    get size() {
        return ExportScaleApi.getSize(this.handle);
    }

    get width() {
        return ExportScaleApi.getWidth(this.handle);
    }

    get height() {
        return ExportScaleApi.getHeight(this.handle);
    }

    static createWithPreset(exportScalePreset) {
        return new ExportScale(ExportScaleApi.createWithPreset(exportScalePreset));
    }

    static createWithMultiplier(multiplier) {
        return new ExportScale(ExportScaleApi.createWithMultiplier(multiplier));
    }

    static createWithWidth(width) {
        return new ExportScale(ExportScaleApi.createWithWidth(width));
    }

    static createWithHeight(height) {
        return new ExportScale(ExportScaleApi.createWithHeight(height));
    }

    static createWithSquare(size) {
        return new ExportScale(ExportScaleApi.createWithSquare(size));
    }

    static createWithMultiplierSquare(multiplier, size) {
        return new ExportScale(ExportScaleApi.createWithMultiplierSquare(multiplier, size));
    }

    static createWithWidthHeight(width, height) {
        return new ExportScale(ExportScaleApi.createWithWidthHeight(width, height));
    }
}

class ExportSize extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ExportSize';
    }

    get exportScale() {
        return new ExportScale(ExportSizeApi.getExportScale(this.handle));
    }

    setExportScale(exportScale) {
        return ExportSizeApi.setExportScale(this.handle, exportScale.handle);
    }

    static createWithExportScale(exportScale) {
        return new ExportSize(ExportSizeApi.createWithExportScale(exportScale.handle));
    }
}

class ExportFormat extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ExportFormat';
    }

    appendSize(exportSize) {
        return ExportFormatApi.appendSize(this.handle, exportSize.handle);
    }

    deleteSize(index) {
        return ExportFormatApi.deleteSize(this.handle, index);
    }

    replaceSize(index, exportSize) {
        return ExportFormatApi.replaceSize(this.handle, index, exportSize.handle);
    }

    get sizeCount() {
        return ExportFormatApi.getSizeCount(this.handle);
    }

    enumerateSizes(callback) {
        if (typeof callback === 'function') {
            function wrapped(exportSizeHandle) {
                return callback(new ExportSize(exportSizeHandle));
            }
            return ExportFormatApi.enumerateSizes(this.handle, wrapped);
        }
        return ExportFormatApi.enumerateSizes(this.handle, callback);
    }

    get sizes() {
        let res = [];
        function callback(exportSize) {
            res.push(exportSize);
            return EnumerationResult.Continue;
        }
        this.enumerateSizes(callback);
        return res;
    }

    static createWithFileExportOptions(fileExportOptions) {
        return new ExportFormat(ExportFormatApi.createWithFileExportOptions(fileExportOptions.handle));
    }
}

class ExportConfig extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ExportConfig';
    }

    appendFormat(exportFormat) {
        return ExportConfigApi.appendFormat(this.handle, exportFormat.handle);
    }

    deleteFormat(index) {
        return ExportConfigApi.deleteFormat(this.handle, index);
    }

    replaceFormat(index, exportFormat) {
        return ExportConfigApi.replaceFormat(this.handle, index, exportFormat.handle);
    }

    get formatCount() {
        return ExportConfigApi.getFormatCount(this.handle);
    }

    enumerateFormats(callback) {
        if (typeof callback === 'function') {
            function wrapped(exportFormatHandle) {
                return callback(new ExportFormat(exportFormatHandle));
            }
            return ExportConfigApi.enumerateFormats(this.handle, wrapped);
        }
        return ExportConfigApi.enumerateFormats(this.handle, callback);
    }

    get formats() {
        let res = [];
        function callback(exportFormat) {
            res.push(exportFormat);
            return EnumerationResult.Continue;
        }
        this.enumerateFormats(callback);
        return res;
    }
}

module.exports.ExportConfig = ExportConfig;
module.exports.ExportFormat = ExportFormat;
module.exports.ExportScale = ExportScale;
module.exports.ExportScalePreset = ExportScalePreset;
module.exports.ExportScaleSizeType = ExportScaleSizeType;
module.exports.ExportSize = ExportSize;
