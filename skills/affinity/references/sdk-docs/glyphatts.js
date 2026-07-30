'use strict';

const {
    CapsType,
    GlyphAttDoubleType,
    GlyphAttsApi,
    GlyphAttStringType,
    LeadingOverrideType,
    OpticalAlignmentType,
    SuperSubType,
    TocRoleType,
    TypographicLineType
} = require('affinity:story');
const Fill = require('./fills.js');
const { Font } = require('./fonts.js');
const { HandleObject } = require('./handleobject.js');
const LineStyle = require('./linestyle.js');

class GlyphAtts extends HandleObject {

    get [Symbol.toStringTag]() {
        return 'GlyphAtts';
    }

    constructor(handle) {
        super(handle);
    }

    static create() {
        return new GlyphAtts(GlyphAttsApi.create());
    }

    clone() {
        return new GlyphAtts(GlyphAttsApi.clone(this.handle));
    }

    get underlineType() {
        return GlyphAttsApi.getUnderlineType(this.handle);
    }

    set underlineType(type) {
        GlyphAttsApi.setUnderlineType(this.handle, type);
    }

    get strikeoutType() {
        return GlyphAttsApi.getStrikeoutType(this.handle);
    }

    set strikeoutType(type) {
        GlyphAttsApi.setStrikeoutType(this.handle, type);
    }

    get superSubType() {
        return GlyphAttsApi.getSuperSubType(this.handle);
    }

    set superSubType(type) {
        GlyphAttsApi.setSuperSubType(this.handle, type);
    }

    get capsType() {
        return GlyphAttsApi.getCapsType(this.handle);
    }

    set capsType(type) {
        GlyphAttsApi.setCapsType(this.handle, type);
    }

    get leadingOverrideType() {
        return GlyphAttsApi.getLeadingOverrideType(this.handle);
    }

    set leadingOverrideType(type) {
        GlyphAttsApi.setLeadingOverrideType(this.handle, type);
    }

    get opticalAlignmentType() {
        return GlyphAttsApi.getOpticalAlignmentType(this.handle);
    }

    set opticalAlignmentType(type) {
        GlyphAttsApi.setOpticalAlignmentType(this.handle, type);
    }

    get tocRoleType() {
        return GlyphAttsApi.getTocRoleType(this.handle);
    }

    set tocRoleType(type) {
        GlyphAttsApi.setTocRoleType(this.handle, type);
    }

    get isNoBreak() {
        return GlyphAttsApi.getIsNoBreak(this.handle);
    }

    set isNoBreak(value) {
        GlyphAttsApi.setIsNoBreak(this.handle, value);
    }

    get openTypeScriptTag() {
        return GlyphAttsApi.getOpenTypeScriptTag(this.handle);
    }

    set openTypeScriptTag(tag) {
        GlyphAttsApi.setOpenTypeScriptTag(this.handle, tag);
    }

    get openTypeLanguageTag() {
        return GlyphAttsApi.getOpenTypeLanguageTag(this.handle);
    }

    set openTypeLanguageTag(tag) {
        GlyphAttsApi.setOpenTypeLanguageTag(this.handle, tag);
    }

    get height() {
        return this.getDoubleValue(GlyphAttDoubleType.Height);
    }

    set height(value) {
        this.setDoubleValue(GlyphAttDoubleType.Height, value);
    }

    get characterSpacing() {
        return this.getDoubleValue(GlyphAttDoubleType.CharacterSpacing);
    }

    set characterSpacing(value) {
        this.setDoubleValue(GlyphAttDoubleType.CharacterSpacing, value);
    }

    get baselineAdvance() {
        return this.getDoubleValue(GlyphAttDoubleType.BaselineAdvance);
    }

    set baselineAdvance(value) {
        this.setDoubleValue(GlyphAttDoubleType.BaselineAdvance, value);
    }

    get autoKernMinHeight() {
        return this.getDoubleValue(GlyphAttDoubleType.AutoKernMinHeight);
    }

    set autoKernMinHeight(value) {
        this.setDoubleValue(GlyphAttDoubleType.AutoKernMinHeight, value);
    }

    get offsetX() {
        return this.getDoubleValue(GlyphAttDoubleType.OffsetX);
    }

    set offsetX(value) {
        this.setDoubleValue(GlyphAttDoubleType.OffsetX, value);
    }

    get offsetY() {
        return this.getDoubleValue(GlyphAttDoubleType.OffsetY);
    }

    set offsetY(value) {
        this.setDoubleValue(GlyphAttDoubleType.OffsetY, value);
    }

    get manualKerning() {
        return this.getDoubleValue(GlyphAttDoubleType.ManualKerning);
    }

    set manualKerning(value) {
        this.setDoubleValue(GlyphAttDoubleType.ManualKerning, value);
    }

    get scaleX() {
        return this.getDoubleValue(GlyphAttDoubleType.ScaleX);
    }

    set scaleX(value) {
        this.setDoubleValue(GlyphAttDoubleType.ScaleX, value);
    }

    get scaleY() {
        return this.getDoubleValue(GlyphAttDoubleType.ScaleY);
    }

    set scaleY(value) {
        this.setDoubleValue(GlyphAttDoubleType.ScaleY, value);
    }

    get shearX() {
        return this.getDoubleValue(GlyphAttDoubleType.ShearX);
    }

    set shearX(value) {
        this.setDoubleValue(GlyphAttDoubleType.ShearX, value);
    }

    get absoluteLeading() {
        return this.getDoubleValue(GlyphAttDoubleType.AbsoluteLeading);
    }

    set absoluteLeading(value) {
        this.setDoubleValue(GlyphAttDoubleType.AbsoluteLeading, value);
    }

    getDoubleValue(att) {
        return GlyphAttsApi.getDoubleValue(this.handle, att);
    }

    setDoubleValue(att, value) {
        GlyphAttsApi.setDoubleValue(this.handle, att, value);
    }

    get spellingLanguageId() {
        return this.getStringValue(GlyphAttStringType.SpellingLanguageId);
    }

    set spellingLanguageId(value) {
        this.setStringValue(GlyphAttStringType.SpellingLanguageId, value);
    }

    get styleName() {
        return this.getStringValue(GlyphAttStringType.StyleName);
    }

    set styleName(value) {
        this.setStringValue(GlyphAttStringType.StyleName, value);
    }

    get hyphenationLanguageId() {
        return this.getStringValue(GlyphAttStringType.HyphenationLanguageId);
    }

    set hyphenationLanguageId(value) {
        this.setStringValue(GlyphAttStringType.HyphenationLanguageId, value);
    }

    getStringValue(att) {
        return GlyphAttsApi.getStringValue(this.handle, att);
    }

    setStringValue(att, value) {
        GlyphAttsApi.setStringValue(this.handle, att, value);
    }

    get brushFill() {
        return new Fill.FillDescriptor(GlyphAttsApi.getBrushFill(this.handle));
    }

    set brushFill(fillDescriptor) {
        GlyphAttsApi.setBrushFill(this.handle, fillDescriptor?.handle);
    }

    get penFill() {
        return new Fill.FillDescriptor(GlyphAttsApi.getPenFill(this.handle));
    }

    set penFill(fillDescriptor) {
        GlyphAttsApi.setPenFill(this.handle, fillDescriptor?.handle);
    }

    get transparency() {
        return new Fill.FillDescriptor(GlyphAttsApi.getTransparency(this.handle));
    }

    set transparency(fillDescriptor) {
        GlyphAttsApi.setTransparency(this.handle, fillDescriptor?.handle);
    }

    get highlightFill() {
        return new Fill.FillDescriptor(GlyphAttsApi.getHighlightFill(this.handle));
    }

    set highlightFill(fillDescriptor) {
        GlyphAttsApi.setHighlightFill(this.handle, fillDescriptor?.handle);
    }

    get underlineFill() {
        return new Fill.FillDescriptor(GlyphAttsApi.getUnderlineFill(this.handle));
    }

    set underlineFill(fillDescriptor) {
        GlyphAttsApi.setUnderlineFill(this.handle, fillDescriptor?.handle);
    }

    get strikeoutFill() {
        return new Fill.FillDescriptor(GlyphAttsApi.getStrikeoutFill(this.handle));
    }

    set strikeoutFill(fillDescriptor) {
        GlyphAttsApi.setStrikeoutFill(this.handle, fillDescriptor?.handle);
    }

    get lineStyleDescriptor() {
        return new LineStyle.LineStyleDescriptor(GlyphAttsApi.getLineStyleDescriptor(this.handle));
    }

    set lineStyleDescriptor(descriptor) {
        GlyphAttsApi.setLineStyleDescriptor(this.handle, descriptor.handle);
    }

    get font() {
        return new Font(GlyphAttsApi.getFont(this.handle));
    }

    set font(font) {
        GlyphAttsApi.setFont(this.handle, font.handle);
    }
}

module.exports.GlyphAtts = GlyphAtts;
module.exports.TypographicLineType = TypographicLineType;
module.exports.SuperSubType = SuperSubType;
module.exports.CapsType = CapsType;
module.exports.LeadingOverrideType = LeadingOverrideType;
module.exports.OpticalAlignmentType = OpticalAlignmentType;
module.exports.TocRoleType = TocRoleType;
module.exports.GlyphAttDoubleType = GlyphAttDoubleType;
module.exports.GlyphAttStringType = GlyphAttStringType;
