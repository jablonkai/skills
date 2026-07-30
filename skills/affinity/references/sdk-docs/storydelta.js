'use strict';

const { FontWidth } = require('affinity:fonts');
const {
    CapsType,
    GlyphAttDoubleType,
    GlyphAttStringType,
    LeadingOverrideType,
    OpticalAlignmentType,
    ParagraphAlignXType,
    ParagraphAttDoubleType,
    ParagraphAttStringType,
    ParagraphLeadingType,
    ParagraphLineBreakModeType,
    ParagraphPDFExportTagType,
    ParagraphStartAtHardBreakType,
    ParagraphUseSpaceBeforeMode,
    StoryDeltaApi,
    SuperSubType,
    TocRoleType,
    TypographicLineType
} = require('affinity:story');
const { HandleObject } = require('./handleobject.js');

class StoryDelta extends HandleObject {

    get [Symbol.toStringTag]() {
        return 'StoryDelta';
    }

    constructor(handle) {
        super(handle);
    }

    static createUnderlineType(type) {
        return new StoryDelta(StoryDeltaApi.createUnderlineTypeDelta(type));
    }

    static createStrikeoutType(type) {
        return new StoryDelta(StoryDeltaApi.createStrikeoutTypeDelta(type));
    }

    static createSuperSubType(type) {
        return new StoryDelta(StoryDeltaApi.createSuperSubTypeDelta(type));
    }

    static createCapsType(type) {
        return new StoryDelta(StoryDeltaApi.createCapsTypeDelta(type));
    }

    static createLeadingOverrideType(type) {
        return new StoryDelta(StoryDeltaApi.createLeadingOverrideTypeDelta(type));
    }

    static createOpticalAlignmentType(type) {
        return new StoryDelta(StoryDeltaApi.createOpticalAlignmentTypeDelta(type));
    }

    static createTocRoleType(type) {
        return new StoryDelta(StoryDeltaApi.createTocRoleTypeDelta(type));
    }

    static createIsNoBreak(isNoBreak) {
        return new StoryDelta(StoryDeltaApi.createIsNoBreakDelta(isNoBreak));
    }

    static createOpenTypeScriptTag(tag) {
        return new StoryDelta(StoryDeltaApi.createOpenTypeScriptTagDelta(tag));
    }

    static createOpenTypeLanguageTag(tag) {
        return new StoryDelta(StoryDeltaApi.createOpenTypeLanguageTagDelta(tag));
    }

    static createGlyphDouble(key, value) {
        return new StoryDelta(StoryDeltaApi.createGlyphDoubleDelta(key, value));
    }

    static createGlyphString(key, value) {
        return new StoryDelta(StoryDeltaApi.createGlyphStringDelta(key, value));
    }

    static createBrushFill(fillDescriptor) {
        return new StoryDelta(StoryDeltaApi.createBrushFillDelta(fillDescriptor?.handle));
    }

    static createPenFill(fillDescriptor) {
        return new StoryDelta(StoryDeltaApi.createPenFillDelta(fillDescriptor?.handle));
    }

    static createTransparency(fillDescriptor) {
        return new StoryDelta(StoryDeltaApi.createTransparencyDelta(fillDescriptor?.handle));
    }

    static createHighlightFill(fillDescriptor) {
        return new StoryDelta(StoryDeltaApi.createHighlightFillDelta(fillDescriptor?.handle));
    }

    static createUnderlineFill(fillDescriptor) {
        return new StoryDelta(StoryDeltaApi.createUnderlineFillDelta(fillDescriptor?.handle));
    }

    static createStrikeoutFill(fillDescriptor) {
        return new StoryDelta(StoryDeltaApi.createStrikeoutFillDelta(fillDescriptor?.handle));
    }

    static createGlyphLineStyleDescriptor(lineStyleDescriptor) {
        return new StoryDelta(StoryDeltaApi.createGlyphLineStyleDescriptorDelta(lineStyleDescriptor.handle));
    }

    static createFont(fields, font) {
        return new StoryDelta(StoryDeltaApi.createFontDelta(fields, font.handle));
    }

    static createPostscriptName(postscriptName) {
        return new StoryDelta(StoryDeltaApi.createPostscriptNameDelta(postscriptName));
    }

    static createFamilyName(familyName) {
        return new StoryDelta(StoryDeltaApi.createFamilyNameDelta(familyName));
    }

    static createWeight(weight) {
        return new StoryDelta(StoryDeltaApi.createWeightDelta(weight));
    }

    static createItalic(italic) {
        return new StoryDelta(StoryDeltaApi.createItalicDelta(italic));
    }

    static createWidth(width) {
        return new StoryDelta(StoryDeltaApi.createWidthDelta(width));
    }

    static createLeftIndent(value) {
        return new StoryDelta(StoryDeltaApi.createLeftIndentDelta(value));
    }

    static createRightIndent(value) {
        return new StoryDelta(StoryDeltaApi.createRightIndentDelta(value));
    }

    static createAlignX(type) {
        return new StoryDelta(StoryDeltaApi.createAlignXDelta(type));
    }

    static createLeadingType(type) {
        return new StoryDelta(StoryDeltaApi.createLeadingTypeDelta(type));
    }

    static createStartAtHardBreak(type) {
        return new StoryDelta(StoryDeltaApi.createStartAtHardBreakDelta(type));
    }

    static createUseSpaceBeforeMode(mode) {
        return new StoryDelta(StoryDeltaApi.createUseSpaceBeforeModeDelta(mode));
    }

    static createPDFExportTag(type) {
        return new StoryDelta(StoryDeltaApi.createPDFExportTagDelta(type));
    }

    static createLineBreakMode(mode) {
        return new StoryDelta(StoryDeltaApi.createLineBreakModeDelta(mode));
    }

    static createIsKeepWithPrevious(value) {
        return new StoryDelta(StoryDeltaApi.createIsKeepWithPreviousDelta(value));
    }

    static createIsKeepTogether(value) {
        return new StoryDelta(StoryDeltaApi.createIsKeepTogetherDelta(value));
    }

    static createIsPreventWidows(value) {
        return new StoryDelta(StoryDeltaApi.createIsPreventWidowsDelta(value));
    }

    static createIsPreventOrphans(value) {
        return new StoryDelta(StoryDeltaApi.createIsPreventOrphansDelta(value));
    }

    static createAlignToBaselineGrid(value) {
        return new StoryDelta(StoryDeltaApi.createAlignToBaselineGridDelta(value));
    }

    static createIsAutoHyphenate(value) {
        return new StoryDelta(StoryDeltaApi.createIsAutoHyphenateDelta(value));
    }

    static createUseSpaceBetweenSameStyles(value) {
        return new StoryDelta(StoryDeltaApi.createUseSpaceBetweenSameStylesDelta(value));
    }

    static createIsSumBeforeAndAfterSpace(value) {
        return new StoryDelta(StoryDeltaApi.createIsSumBeforeAndAfterSpaceDelta(value));
    }

    static createUseModernLeading(value) {
        return new StoryDelta(StoryDeltaApi.createUseModernLeadingDelta(value));
    }

    static createKeepWithNext(value) {
        return new StoryDelta(StoryDeltaApi.createKeepWithNextDelta(value));
    }

    static createHyphenateMinLength(value) {
        return new StoryDelta(StoryDeltaApi.createHyphenateMinLengthDelta(value));
    }

    static createHyphenateMinPrefix(value) {
        return new StoryDelta(StoryDeltaApi.createHyphenateMinPrefixDelta(value));
    }

    static createHyphenateMinSuffix(value) {
        return new StoryDelta(StoryDeltaApi.createHyphenateMinSuffixDelta(value));
    }

    static createMaxConsecutiveHyphens(value) {
        return new StoryDelta(StoryDeltaApi.createMaxConsecutiveHyphensDelta(value));
    }

    static createParagraphDouble(key, value) {
        return new StoryDelta(StoryDeltaApi.createParagraphDoubleDelta(key, value));
    }

    static createParagraphString(key, value) {
        return new StoryDelta(StoryDeltaApi.createParagraphStringDelta(key, value));
    }

    static createComposite(deltas) {
        return new StoryDelta(StoryDeltaApi.createCompositeDelta(deltas.map((d) => d.handle)));
    }
}

module.exports.CapsType = CapsType;
module.exports.FontWidth = FontWidth;
module.exports.GlyphAttDoubleType = GlyphAttDoubleType;
module.exports.GlyphAttStringType = GlyphAttStringType;
module.exports.LeadingOverrideType = LeadingOverrideType;
module.exports.OpticalAlignmentType = OpticalAlignmentType;
module.exports.ParagraphAlignXType = ParagraphAlignXType;
module.exports.ParagraphAttDoubleType = ParagraphAttDoubleType;
module.exports.ParagraphAttStringType = ParagraphAttStringType;
module.exports.ParagraphLeadingType = ParagraphLeadingType;
module.exports.ParagraphLineBreakModeType = ParagraphLineBreakModeType;
module.exports.ParagraphPDFExportTagType = ParagraphPDFExportTagType;
module.exports.ParagraphStartAtHardBreakType = ParagraphStartAtHardBreakType;
module.exports.ParagraphUseSpaceBeforeMode = ParagraphUseSpaceBeforeMode;
module.exports.StoryDelta = StoryDelta;
module.exports.SuperSubType = SuperSubType;
module.exports.TocRoleType = TocRoleType;
module.exports.TypographicLineType = TypographicLineType;
