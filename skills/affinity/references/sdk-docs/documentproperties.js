'use strict';

const { UnitType } = require('affinity:common');
const {
    ArtboardDocumentPropertiesApi,
    DocumentPropertiesApi,
    SpreadDocumentPropertiesApi,
    ImagePlacement,
    SpatialAnchor
} = require('affinity:dom');

const { RasterFormat, RasterResamplerType } = require('affinity:raster');

const { Colour, ColourProfile } = require('./colours.js');
const { DrawingScale } = require('./drawingscale.js');
const { FillDescriptor } = require('./fills.js');
const { HandleObject } = require('./handleobject.js');

class DocumentProperties extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DocumentProperties';
    }

    static create() {
        return new DocumentProperties(DocumentPropertiesApi.create());
    }

    get colourFormat() {
        return DocumentPropertiesApi.getColourFormat(this.handle);
    }

    get colourProfile() {
        return new ColourProfile(DocumentPropertiesApi.getColourProfile(this.handle));
    }

    setColourFormatAndProfile(rasterFormat, colourProfile) {
        DocumentPropertiesApi.setColourFormatAndProfile(this.handle, rasterFormat, colourProfile.handle);
    }

    get units() {
        return DocumentPropertiesApi.getUnits(this.handle);
    }

    set units(unitType) {
        DocumentPropertiesApi.setUnits(this.handle, unitType);
    }

    get shouldReflowPages() {
        return DocumentPropertiesApi.getShouldReflowPages(this.handle);
    }

    set shouldReflowPages(shouldReflowPages) {
        DocumentPropertiesApi.setShouldReflowPages(this.handle, shouldReflowPages);
    }

    get dpi() {
        return DocumentPropertiesApi.getDpi(this.handle);
    }

    get viewDpi() {
        return DocumentPropertiesApi.getViewDpi(this.handle);
    }

    setDpi(dpi, viewDpi) {
        DocumentPropertiesApi.setDpi(this.handle, dpi, viewDpi);
    }

    get drawingScale() {
        return new DrawingScale(DocumentPropertiesApi.getDrawingScale(this.handle));
    }

    set drawingScale(drawingScale) {
        DocumentPropertiesApi.setDrawingScale(this.handle, drawingScale.handle);
    }

    get pageWidth() {
        return DocumentPropertiesApi.getPageWidth(this.handle);
    }

    set pageWidth(width) {
        DocumentPropertiesApi.setPageWidth(this.handle, width);
    }

    get pageHeight() {
        return DocumentPropertiesApi.getPageHeight(this.handle);
    }

    set pageHeight(height) {
        DocumentPropertiesApi.setPageHeight(this.handle, height);
    }

    get margin() {
        return DocumentPropertiesApi.getMargin(this.handle);
    }

    set margin(margin) {
        DocumentPropertiesApi.setMargin(this.handle, margin);
    }

    get marginFill() {
        return new FillDescriptor(DocumentPropertiesApi.getMarginFill(this.handle));
    }

    set marginFill(fillDescriptor) {
        DocumentPropertiesApi.setMarginFill(this.handle, fillDescriptor.handle);
    }

    get bleed() {
        return DocumentPropertiesApi.getBleed(this.handle);
    }

    set bleed(bleed) {
        DocumentPropertiesApi.setBleed(this.handle, bleed);
    }

    get bleedFill() {
        return new FillDescriptor(DocumentPropertiesApi.getBleedFill(this.handle));
    }

    set bleedFill(fillDescriptor) {
        DocumentPropertiesApi.setBleedFill(this.handle, fillDescriptor.handle);
    }

    get includeMargins() {
        return DocumentPropertiesApi.getIncludeMargins(this.handle);
    }

    set includeMargins(includeMargins) {
        DocumentPropertiesApi.setIncludeMargins(this.handle, includeMargins);
    }

    get isRetina() {
        return DocumentPropertiesApi.getIsRetina(this.handle);
    }

    set isRetina(isRetina) {
        DocumentPropertiesApi.setIsRetina(this.handle, isRetina);
    }

    get isPortrait() {
        return DocumentPropertiesApi.getIsPortrait(this.handle);
    }

    set isPortrait(isPortrait) {
        DocumentPropertiesApi.setIsPortrait(this.handle, isPortrait);
    }

    get isTransparent() {
        return DocumentPropertiesApi.getIsTransparent(this.handle);
    }

    set isTransparent(isTransparent) {
        DocumentPropertiesApi.setIsTransparent(this.handle, isTransparent);
    }

    get saveHistory() {
        return DocumentPropertiesApi.getSaveHistory(this.handle);
    }

    set saveHistory(saveHistory) {
        DocumentPropertiesApi.setSaveHistory(this.handle, saveHistory);
    }

    get isFacingPages() {
        return DocumentPropertiesApi.getIsFacingPages(this.handle);
    }

    set isFacingPages(isFacingPages) {
        DocumentPropertiesApi.setIsFacingPages(this.handle, isFacingPages);
    }

    get isFullSpreadStart() {
        return DocumentPropertiesApi.getIsFullSpreadStart(this.handle);
    }

    set isFullSpreadStart(isFullSpreadStart) {
        DocumentPropertiesApi.setIsFullSpreadStart(this.handle, isFullSpreadStart);
    }

    get isVerticalStack() {
        return DocumentPropertiesApi.getIsVerticalStack(this.handle);
    }

    set isVerticalStack(isVerticalStack) {
        DocumentPropertiesApi.setIsVerticalStack(this.handle, isVerticalStack);
    }

    get imageResourcePolicy() {
        return DocumentPropertiesApi.getImageResourcePolicy(this.handle);
    }

    set imageResourcePolicy(imageResourcePolicy) {
        DocumentPropertiesApi.setImageResourcePolicy(this.handle, imageResourcePolicy);
    }

    get linkTextFiles() {
        return DocumentPropertiesApi.getLinkTextFiles(this.handle);
    }

    set linkTextFiles(linkTextFiles) {
        DocumentPropertiesApi.setLinkTextFiles(this.handle, linkTextFiles);
    }

    get preserveTextStyles() {
        return DocumentPropertiesApi.getPreserveTextStyles(this.handle);
    }

    set preserveTextStyles(preserveTextStyles) {
        DocumentPropertiesApi.setPreserveTextStyles(this.handle, preserveTextStyles);
    }

    get assignColourProfile() {
        return DocumentPropertiesApi.getAssignColourProfile(this.handle);
    }

    set assignColourProfile(assignColourProfile) {
        DocumentPropertiesApi.setAssignColourProfile(this.handle, assignColourProfile);
    }

    get resamplerType() {
        return DocumentPropertiesApi.getResamplerType(this.handle);
    }

    set resamplerType(resamplerType) {
        DocumentPropertiesApi.setResamplerType(this.handle, resamplerType);
    }

}

class ArtboardDocumentProperties extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ArtboardDocumentProperties';
    }

    static create() {
        return new ArtboardDocumentProperties(ArtboardDocumentPropertiesApi.create());
    }

    get margin() {
        return ArtboardDocumentPropertiesApi.getMargin(this.handle);
    }

    set margin(margin) {
        ArtboardDocumentPropertiesApi.setMargin(this.handle, margin);
    }

    setMargin(margin) {
        this.margin = margin;
        return this;
    }

    get useMargin() {
        return ArtboardDocumentPropertiesApi.getUseMargin(this.handle);
    }

    set useMargin(useMargin) {
        ArtboardDocumentPropertiesApi.setUseMargin(this.handle, useMargin);
    }

    setUseMargin(useMargin) {
        this.useMargin = useMargin;
        return this;
    }

    get drawingScale() {
        return new DrawingScale(ArtboardDocumentPropertiesApi.getDrawingScale(this.handle));
    }

    set drawingScale(drawingScale) {
        ArtboardDocumentPropertiesApi.setDrawingScale(this.handle, drawingScale.handle);
    }

    setDrawingScale(drawingScale) {
        this.drawingScale = drawingScale;
        return this;
    }

    get useDrawingScale() {
        return ArtboardDocumentPropertiesApi.getUseDrawingScale(this.handle);
    }

    set useDrawingScale(useDrawingScale) {
        ArtboardDocumentPropertiesApi.setUseDrawingScale(this.handle, useDrawingScale);
    }

    setUseDrawingScale(useDrawingScale) {
        this.useDrawingScale = useDrawingScale;
        return this;
    }

    get dimensions() {
        return ArtboardDocumentPropertiesApi.getDimensions(this.handle);
    }

    set dimensions(dimensions) {
        ArtboardDocumentPropertiesApi.setDimensions(this.handle, dimensions);
    }

    setDimensions(dimensions) {
        this.dimensions = dimensions;
        return this;
    }

    get anchorType() {
        return ArtboardDocumentPropertiesApi.getAnchorType(this.handle);
    }

    set anchorType(anchorType) {
        ArtboardDocumentPropertiesApi.setAnchorType(this.handle, anchorType);
    }

    setAnchorType(anchorType) {
        this.anchorType = anchorType;
        return this;
    }
}

class SpreadDocumentProperties extends ArtboardDocumentProperties {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SpreadDocumentProperties';
    }

    static create() {
        return new SpreadDocumentProperties(SpreadDocumentPropertiesApi.create());
    }

    get useMasterMargin() {
        return SpreadDocumentPropertiesApi.getUseMasterMargin(this.handle);
    }

    set useMasterMargin(useMasterMargin) {
        SpreadDocumentPropertiesApi.setUseMasterMargin(this.handle, useMasterMargin);
    }

    setUseMasterMargin(useMasterMargin) {
        this.useMasterMargin = useMasterMargin;
        return this;
    }

    get useMasterDrawingScale() {
        return SpreadDocumentPropertiesApi.getUseMasterDrawingScale(this.handle);
    }

    set useMasterDrawingScale(useMasterDrawingScale) {
        SpreadDocumentPropertiesApi.setUseMasterDrawingScale(this.handle, useMasterDrawingScale);
    }

    setUseMasterDrawingScale(useMasterDrawingScale) {
        this.useMasterDrawingScale = useMasterDrawingScale;
        return this;
    }

    get reflowPages() {
        return SpreadDocumentPropertiesApi.getReflowPages(this.handle);
    }

    set reflowPages(reflowPages) {
        SpreadDocumentPropertiesApi.setReflowPages(this.handle, reflowPages);
    }

    setReflowPages(reflowPages) {
        this.reflowPages = reflowPages;
        return this;
    }

    get resamplerType() {
        return SpreadDocumentPropertiesApi.getResamplerType(this.handle);
    }

    set resamplerType(resamplerType) {
        SpreadDocumentPropertiesApi.setResamplerType(this.handle, resamplerType);
    }

    setResamplerType(resamplerType) {
        this.resamplerType = resamplerType;
        return this;
    }
}

module.exports.ArtboardDocumentProperties = ArtboardDocumentProperties;
module.exports.DocumentProperties = DocumentProperties;
module.exports.ImagePlacement = ImagePlacement;
module.exports.RasterFormat = RasterFormat;
module.exports.RasterResamplerType = RasterResamplerType;
module.exports.SpatialAnchor = SpatialAnchor;
module.exports.SpreadDocumentProperties = SpreadDocumentProperties;
module.exports.UnitType = UnitType;
