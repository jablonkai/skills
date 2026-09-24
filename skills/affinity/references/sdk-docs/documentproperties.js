'use strict';

const { UnitType } = require('affinity:common');
const {
    ArtboardDocumentPropertiesApi,
    DocumentPropertiesApi,
    ImagePlacement,
    LTRB,
    PageDocumentPropertiesApi,
    PageOriginDelta,
    SpatialAnchor,
    SpreadDocumentPropertiesApi
} = require('affinity:dom');

const { Size } = require('affinity:geometry');

const { RasterFormat, RasterResamplerType } = require('affinity:raster');

const { Colour, ColourProfile } = require('/colours.js');
const { DrawingScale } = require('/drawingscale.js');
const { FillDescriptor, makeFillDescriptor, SolidFill } = require('/fills.js');
const { HandleObject } = require('/handleobject.js');

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

    clone() {
        return new DocumentProperties(DocumentPropertiesApi.clone(this.handle));
    }

    get dimensions() {
        return DocumentPropertiesApi.getDimensions(this.handle);
    }

    set dimensions(dimensions) {
        DocumentPropertiesApi.setDimensions(this.handle, dimensions);
    }

    setDimensions(dimensions) {
        this.dimensions = dimensions;
        return this;
    }

    get colourFormat() {
        return DocumentPropertiesApi.getColourFormat(this.handle);
    }

    get colourProfile() {
        return new ColourProfile(DocumentPropertiesApi.getColourProfile(this.handle));
    }

    setColourFormatAndProfile(rasterFormat, colourProfile) {
        DocumentPropertiesApi.setColourFormatAndProfile(this.handle, rasterFormat, colourProfile.handle);
        return this;
    }

    get units() {
        return DocumentPropertiesApi.getUnits(this.handle);
    }

    set units(unitType) {
        DocumentPropertiesApi.setUnits(this.handle, unitType);
    }

    setUnits(unitType) {
        this.units =  unitType;
        return this;
    }

    get shouldReflowPages() {
        return DocumentPropertiesApi.getShouldReflowPages(this.handle);
    }

    set shouldReflowPages(shouldReflowPages) {
        DocumentPropertiesApi.setShouldReflowPages(this.handle, shouldReflowPages);
    }

    setShouldReflowPages(shouldReflowPages) {
        this.shouldReflowPages = shouldReflowPages;
        return this;
    }

    get dpi() {
        return DocumentPropertiesApi.getDpi(this.handle);
    }

    set dpi(dpi) {
        DocumentPropertiesApi.setDpi(this.handle, dpi);
    }

    #viewDpi = -1;
    // Sets the DPI. The viewDpi parameter is deprecated and is no longer in use;
    // it is retained only for backwards compatibility with old scripts.
    setDpi(dpi, viewDpi) {
        this.dpi = dpi;
        if (viewDpi != undefined) {
            this.#viewDpi = viewDpi;
        }
        return this;
    }

    /**
    * @deprecated This property is no longer in use
    */
    get viewDpi() {
        console.warn("Using deprecated DocumentProperties get viewDpi() function. This property is no longer in use.");
        return this.#viewDpi;
    }

    get drawingScale() {
        return new DrawingScale(DocumentPropertiesApi.getDrawingScale(this.handle));
    }

    set drawingScale(drawingScale) {
        DocumentPropertiesApi.setDrawingScale(this.handle, drawingScale.handle);
    }

    setDrawingScale(drawingScale) {
        this.drawingScale = drawingScale;
        return this;
    }

    get widthPixels() {
        return this.dimensions.width;
    }

    set widthPixels(width) {
        const dimensions = this.dimensions;
        dimensions.width = width;
        this.dimensions = dimensions;
    }

    get heightPixels() {
        return this.dimensions.height;
    }

    set heightPixels(height) {
        const dimensions = this.dimensions;
        dimensions.height = height;
        this.dimensions = dimensions;
    }

    /**
    * @deprecated Use get widthPixels() instead
    */
    get pageWidth() {
        console.warn("Using deprecated DocumentProperties get pageWidth() function. Use get widthPixels() instead.");
        return this.widthPixels;
    }

    /**
    * @deprecated Use set widthPixels() instead
    */
    set pageWidth(width) {
        console.warn("Using deprecated DocumentProperties set pageWidth() function. Use set widthPixels() instead.");
        this.widthPixels = width;
    }

    /**
    * @deprecated Use get heightPixels() instead
    */
    get pageHeight() {
        console.warn("Using deprecated DocumentProperties get pageHeight() function. Use get heightPixels() instead.");
        return this.heightPixels;
    }

    /**
    * @deprecated Use set heightPixels() instead
    */
    set pageHeight(height) {
        console.warn("Using deprecated DocumentProperties set pageHeight() function. Use set heightPixels() instead.");
        this.heightPixels = height;
    }

    #margin = new LTRB(0, 0, 0, 0);
    /**
    * @deprecated This property is no longer in use
    */
    get margin() {
        console.warn("Using deprecated DocumentProperties get margin() function. This property is no longer in use.");
        return this.#margin;
    }

    /**
    * @deprecated This property is no longer in use
    */
    set margin(margin) {
        console.warn("Using deprecated DocumentProperties set margin() function. This property is no longer in use.");
        this.#margin = margin;
    }

    #marginFill = FillDescriptor.createNone();
    /**
    * @deprecated This property is no longer in use
    */
    get marginFill() {
        console.warn("Using deprecated DocumentProperties get marginFill() function. This property is no longer in use.");
        return this.#marginFill;
    }

    /**
    * @deprecated This property is no longer in use
    */
    set marginFill(marginFill) {
        console.warn("Using deprecated DocumentProperties set marginFill() function. This property is no longer in use.");
        this.#marginFill = marginFill;
    }

    get bleed() {
        return DocumentPropertiesApi.getBleed(this.handle);
    }

    set bleed(bleed) {
        DocumentPropertiesApi.setBleed(this.handle, bleed);
    }

    setBleed(bleed) {
        this.bleed = bleed;
        return this;
    }

    get bleedFill() {
        return new FillDescriptor(DocumentPropertiesApi.getBleedFill(this.handle));
    }

    set bleedFill(fillDescriptorOrColour) {
        const fillDescriptor = makeFillDescriptor(fillDescriptorOrColour);
        DocumentPropertiesApi.setBleedFill(this.handle, fillDescriptor.handle);
    }

    setBleedFill(fillDescriptorOrColour) {
        this.bleedFill = fillDescriptorOrColour;
        return this;
    }

    #includeMargins = false;
    /**
    * @deprecated This property is no longer in use
    */
    get includeMargins() {
        console.warn("Using deprecated DocumentProperties get includeMargins() function. This property is no longer in use.");
        return this.#includeMargins;
    }

    /**
    * @deprecated This property is no longer in use
    */
    set includeMargins(includeMargins) {
        console.warn("Using deprecated DocumentProperties set includeMargins() function. This property is no longer in use.");
        this.#includeMargins = includeMargins;
    }

    #isRetina = false;
    /**
    * @deprecated This property is no longer in use
    */
    get isRetina() {
        console.warn("Using deprecated DocumentProperties get isRetina() function. This property is no longer in use.");
        return this.#isRetina;
    }

    /**
    * @deprecated This property is no longer in use
    */
    set isRetina(isRetina) {
        console.warn("Using deprecated DocumentProperties set isRetina() function. This property is no longer in use.");
        this.#isRetina = isRetina;
    }

    #isPortrait = false;
    /**
    * @deprecated This property is no longer in use
    */
    get isPortrait() {
        console.warn("Using deprecated DocumentProperties get isPortrait() function. This property is no longer in use.");
        return this.#isPortrait;
    }

    /**
    * @deprecated This property is no longer in use
    */
    set isPortrait(isPortrait) {
        console.warn("Using deprecated DocumentProperties set isPortrait() function. This property is no longer in use.");
        this.#isPortrait = isPortrait;
    }

    get isTransparent() {
        return DocumentPropertiesApi.getIsTransparent(this.handle);
    }

    set isTransparent(isTransparent) {
        DocumentPropertiesApi.setIsTransparent(this.handle, isTransparent);
    }

    setIsTransparent(isTransparent) {
        this.isTransparent = isTransparent;
        return this;
    }

    #saveHistory = false;
    /**
    * @deprecated This property is no longer in use
    */
    get saveHistory() {
        console.warn("Using deprecated DocumentProperties get saveHistory() function. This property is no longer in use.");
        return this.#saveHistory;
    }

    /**
    * @deprecated This property is no longer in use
    */
    set saveHistory(saveHistory) {
        console.warn("Using deprecated DocumentProperties set saveHistory() function. This property is no longer in use.");
        this.#saveHistory = saveHistory;
    }

    get isFacingPages() {
        return DocumentPropertiesApi.getIsFacingPages(this.handle);
    }

    set isFacingPages(isFacingPages) {
        DocumentPropertiesApi.setIsFacingPages(this.handle, isFacingPages);
    }

    setIsFacingPages(isFacingPages) {
        this.isFacingPages = isFacingPages;
        return this;
    }

    get isFullSpreadStart() {
        return DocumentPropertiesApi.getIsFullSpreadStart(this.handle);
    }

    set isFullSpreadStart(isFullSpreadStart) {
        DocumentPropertiesApi.setIsFullSpreadStart(this.handle, isFullSpreadStart);
    }

    setIsFullSpreadStart(isFullSpreadStart) {
        this.isFullSpreadStart = isFullSpreadStart;
        return this;
    }

    get isVerticalStack() {
        return DocumentPropertiesApi.getIsVerticalStack(this.handle);
    }

    set isVerticalStack(isVerticalStack) {
        DocumentPropertiesApi.setIsVerticalStack(this.handle, isVerticalStack);
    }

    setIsVerticalStack(isVerticalStack) {
        this.isVerticalStack = isVerticalStack;
        return this;
    }

    get imageResourcePolicy() {
        return DocumentPropertiesApi.getImageResourcePolicy(this.handle);
    }

    set imageResourcePolicy(imageResourcePolicy) {
        DocumentPropertiesApi.setImageResourcePolicy(this.handle, imageResourcePolicy);
    }

    setImageResourcePolicy(imageResourcePolicy) {
        this.imageResourcePolicy = imageResourcePolicy;
        return this;
    }

    get linkTextFiles() {
        return DocumentPropertiesApi.getLinkTextFiles(this.handle);
    }

    set linkTextFiles(linkTextFiles) {
        DocumentPropertiesApi.setLinkTextFiles(this.handle, linkTextFiles);
    }

    setLinkTextFiles(linkTextFiles) {
        this.linkTextFiles = linkTextFiles;
        return this;
    }

    get preserveTextStyles() {
        return DocumentPropertiesApi.getPreserveTextStyles(this.handle);
    }

    set preserveTextStyles(preserveTextStyles) {
        DocumentPropertiesApi.setPreserveTextStyles(this.handle, preserveTextStyles);
    }

    setPreserveTextStyles(preserveTextStyles) {
        this.preserveTextStyles = preserveTextStyles;
        return this;
    }

    get assignColourProfile() {
        return DocumentPropertiesApi.getAssignColourProfile(this.handle);
    }

    set assignColourProfile(assignColourProfile) {
        DocumentPropertiesApi.setAssignColourProfile(this.handle, assignColourProfile);
    }

    setAssignColourProfile(assignColourProfile) {
        this.assignColourProfile = assignColourProfile;
        return this;
    }

    get resamplerType() {
        return DocumentPropertiesApi.getResamplerType(this.handle);
    }

    set resamplerType(resamplerType) {
        DocumentPropertiesApi.setResamplerType(this.handle, resamplerType);
    }

    setResamplerType(resamplerType) {
        this.resamplerType = resamplerType;
        return this;
    }
}

class PageDocumentProperties extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PageDocumentProperties';
    }

    static create() {
        return new PageDocumentProperties(PageDocumentPropertiesApi.create());
    }

    clone() {
        return new PageDocumentProperties(PageDocumentPropertiesApi.clone(this.handle));
    }

    get moveFollowingPages() {
        return PageDocumentPropertiesApi.getMoveFollowingPages(this.handle);
    }

    set moveFollowingPages(moveFollowingPages) {
        PageDocumentPropertiesApi.setMoveFollowingPages(this.handle, moveFollowingPages);
    }

    setMoveFollowingPages(moveFollowingPages) {
        this.moveFollowingPages = moveFollowingPages;
        return this;
    }

    get pageOriginDelta() {
        return PageDocumentPropertiesApi.getPageOriginDelta(this.handle);
    }

    set pageOriginDelta(pageOriginDelta) {
        PageDocumentPropertiesApi.setPageOriginDelta(this.handle, pageOriginDelta);
    }

    setPageOriginDelta(pageOriginDelta) {
        this.pageOriginDelta = pageOriginDelta;
        return this;
    }

    get anchorType() {
        return PageDocumentPropertiesApi.getAnchorType(this.handle);
    }

    set anchorType(anchorType) {
        PageDocumentPropertiesApi.setAnchorType(this.handle, anchorType);
    }

    setAnchorType(anchorType) {
        this.anchorType = anchorType;
        return this;
    }

    get margin() {
        return PageDocumentPropertiesApi.getMargin(this.handle);
    }

    set margin(margin) {
        PageDocumentPropertiesApi.setMargin(this.handle, margin);
    }

    setMargin(margin) {
        this.margin = margin;
        return this;
    }

    get useMargin() {
        return PageDocumentPropertiesApi.getUseMargin(this.handle);
    }

    set useMargin(useMargin) {
        PageDocumentPropertiesApi.setUseMargin(this.handle, useMargin);
    }

    setUseMargin(useMargin) {
        this.useMargin = useMargin;
        return this;
    }

    get useMasterMargin() {
        return PageDocumentPropertiesApi.getUseMasterMargin(this.handle);
    }

    set useMasterMargin(useMasterMargin) {
        PageDocumentPropertiesApi.setUseMasterMargin(this.handle, useMasterMargin);
    }

    setUseMasterMargin(useMasterMargin) {
        this.useMasterMargin = useMasterMargin;
        return this;
    }

    get marginFill() {
        return new FillDescriptor(PageDocumentPropertiesApi.getMarginFill(this.handle));
    }

    set marginFill(fillDescriptorOrColour) {
        const fillDescriptor = makeFillDescriptor(fillDescriptorOrColour);
        PageDocumentPropertiesApi.setMarginFill(this.handle, fillDescriptor.handle);
    }

    setMarginFill(fillDescriptor) {
        this.marginFill = fillDescriptor;
        return this;
    }

    get dimensions() {
        return PageDocumentPropertiesApi.getDimensions(this.handle);
    }

    set dimensions(dimensions) {
        PageDocumentPropertiesApi.setDimensions(this.handle, dimensions);
    }

    setDimensions(dimensions) {
        this.dimensions = dimensions;
        return this;
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

    clone() {
        return new ArtboardDocumentProperties(ArtboardDocumentPropertiesApi.clone(this.handle));
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

    get marginFill() {
        return new FillDescriptor(ArtboardDocumentPropertiesApi.getMarginFill(this.handle));
    }

    set marginFill(fillDescriptorOrColour) {
        const fillDescriptor = makeFillDescriptor(fillDescriptorOrColour);
        ArtboardDocumentPropertiesApi.setMarginFill(this.handle, fillDescriptor.handle);
    }

    setMarginFill(fillDescriptor) {
        this.marginFill = fillDescriptor;
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

    clone() {
        return new SpreadDocumentProperties(SpreadDocumentPropertiesApi.clone(this.handle));
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
module.exports.Colour = Colour;
module.exports.ColourProfile = ColourProfile;
module.exports.DocumentProperties = DocumentProperties;
module.exports.DrawingScale = DrawingScale;
module.exports.FillDescriptor = FillDescriptor;
module.exports.ImagePlacement = ImagePlacement;
module.exports.LTRB = LTRB;
module.exports.PageDocumentProperties = PageDocumentProperties;
module.exports.PageOriginDelta = PageOriginDelta;
module.exports.RasterFormat = RasterFormat;
module.exports.RasterResamplerType = RasterResamplerType;
module.exports.Size = Size;
module.exports.SolidFill = SolidFill;
module.exports.SpatialAnchor = SpatialAnchor;
module.exports.SpreadDocumentProperties = SpreadDocumentProperties;
module.exports.UnitType = UnitType;
