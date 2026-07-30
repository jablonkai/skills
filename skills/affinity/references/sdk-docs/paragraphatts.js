'use strict';

const {
    ParagraphAlignXType,
    ParagraphAttDoubleType,
    ParagraphAttsApi,
    ParagraphAttStringType,
    ParagraphLeadingType,
    ParagraphLineBreakModeType,
    ParagraphPDFExportTagType,
    ParagraphStartAtHardBreakType,
    ParagraphUseSpaceBeforeMode
} = require('affinity:story');
const { HandleObject } = require('./handleobject.js');

class ParagraphAtts extends HandleObject {

    get [Symbol.toStringTag]() {
        return 'ParagraphAtts';
    }

    constructor(handle) {
        super(handle);
    }

    static create() {
        return new ParagraphAtts(ParagraphAttsApi.create());
    }

    clone() {
        return new ParagraphAtts(ParagraphAttsApi.clone(this.handle));
    }

    get alignXType() {
        return ParagraphAttsApi.getAlignXType(this.handle);
    }

    set alignXType(type) {
        ParagraphAttsApi.setAlignXType(this.handle, type);
    }

    get leadingType() {
        return ParagraphAttsApi.getLeadingType(this.handle);
    }

    set leadingType(type) {
        ParagraphAttsApi.setLeadingType(this.handle, type);
    }

    get startAtHardBreakType() {
        return ParagraphAttsApi.getStartAtHardBreakType(this.handle);
    }

    set startAtHardBreakType(type) {
        ParagraphAttsApi.setStartAtHardBreakType(this.handle, type);
    }

    get useSpaceBeforeMode() {
        return ParagraphAttsApi.getUseSpaceBeforeMode(this.handle);
    }

    set useSpaceBeforeMode(mode) {
        ParagraphAttsApi.setUseSpaceBeforeMode(this.handle, mode);
    }

    get pdfExportTagType() {
        return ParagraphAttsApi.getPDFExportTagType(this.handle);
    }

    set pdfExportTagType(type) {
        ParagraphAttsApi.setPDFExportTagType(this.handle, type);
    }

    get lineBreakModeType() {
        return ParagraphAttsApi.getLineBreakModeType(this.handle);
    }

    set lineBreakModeType(type) {
        ParagraphAttsApi.setLineBreakModeType(this.handle, type);
    }

    get isKeepWithPrevious() {
        return ParagraphAttsApi.getIsKeepWithPrevious(this.handle);
    }

    set isKeepWithPrevious(value) {
        ParagraphAttsApi.setIsKeepWithPrevious(this.handle, value);
    }

    get isKeepTogether() {
        return ParagraphAttsApi.getIsKeepTogether(this.handle);
    }

    set isKeepTogether(value) {
        ParagraphAttsApi.setIsKeepTogether(this.handle, value);
    }

    get isPreventWidows() {
        return ParagraphAttsApi.getIsPreventWidows(this.handle);
    }

    set isPreventWidows(value) {
        ParagraphAttsApi.setIsPreventWidows(this.handle, value);
    }

    get isPreventOrphans() {
        return ParagraphAttsApi.getIsPreventOrphans(this.handle);
    }

    set isPreventOrphans(value) {
        ParagraphAttsApi.setIsPreventOrphans(this.handle, value);
    }

    get alignToBaselineGrid() {
        return ParagraphAttsApi.getAlignToBaselineGrid(this.handle);
    }

    set alignToBaselineGrid(value) {
        ParagraphAttsApi.setAlignToBaselineGrid(this.handle, value);
    }

    get isAutoHyphenate() {
        return ParagraphAttsApi.getIsAutoHyphenate(this.handle);
    }

    set isAutoHyphenate(value) {
        ParagraphAttsApi.setIsAutoHyphenate(this.handle, value);
    }

    get isIndex() {
        return ParagraphAttsApi.getIsIndex(this.handle);
    }

    set isIndex(value) {
        ParagraphAttsApi.setIsIndex(this.handle, value);
    }

    get useSpaceBetweenSameStyles() {
        return ParagraphAttsApi.getUseSpaceBetweenSameStyles(this.handle);
    }

    set useSpaceBetweenSameStyles(value) {
        ParagraphAttsApi.setUseSpaceBetweenSameStyles(this.handle, value);
    }

    get isSumBeforeAndAfterSpace() {
        return ParagraphAttsApi.getIsSumBeforeAndAfterSpace(this.handle);
    }

    set isSumBeforeAndAfterSpace(value) {
        ParagraphAttsApi.setIsSumBeforeAndAfterSpace(this.handle, value);
    }

    get isBookEndnotes() {
        return ParagraphAttsApi.getIsBookEndnotes(this.handle);
    }

    set isBookEndnotes(value) {
        ParagraphAttsApi.setIsBookEndnotes(this.handle, value);
    }

    get useModernLeading() {
        return ParagraphAttsApi.getUseModernLeading(this.handle);
    }

    set useModernLeading(value) {
        ParagraphAttsApi.setUseModernLeading(this.handle, value);
    }

    get keepWithNext() {
        return ParagraphAttsApi.getKeepWithNext(this.handle);
    }

    set keepWithNext(value) {
        ParagraphAttsApi.setKeepWithNext(this.handle, value);
    }

    get hyphenateMinLength() {
        return ParagraphAttsApi.getHyphenateMinLength(this.handle);
    }

    set hyphenateMinLength(value) {
        ParagraphAttsApi.setHyphenateMinLength(this.handle, value);
    }

    get hyphenateMinPrefix() {
        return ParagraphAttsApi.getHyphenateMinPrefix(this.handle);
    }

    set hyphenateMinPrefix(value) {
        ParagraphAttsApi.setHyphenateMinPrefix(this.handle, value);
    }

    get hyphenateMinSuffix() {
        return ParagraphAttsApi.getHyphenateMinSuffix(this.handle);
    }

    set hyphenateMinSuffix(value) {
        ParagraphAttsApi.setHyphenateMinSuffix(this.handle, value);
    }

    get maxConsecutiveHyphens() {
        return ParagraphAttsApi.getMaxConsecutiveHyphens(this.handle);
    }

    set maxConsecutiveHyphens(value) {
        ParagraphAttsApi.setMaxConsecutiveHyphens(this.handle, value);
    }

    get relativeLeading() {
        return this.getDoubleValue(ParagraphAttDoubleType.RelativeLeading);
    }

    set relativeLeading(value) {
        this.setDoubleValue(ParagraphAttDoubleType.RelativeLeading, value);
    }

    get absoluteLeading() {
        return this.getDoubleValue(ParagraphAttDoubleType.AbsoluteLeading);
    }

    set absoluteLeading(value) {
        this.setDoubleValue(ParagraphAttDoubleType.AbsoluteLeading, value);
    }

    get leftIndent() {
        return this.getDoubleValue(ParagraphAttDoubleType.LeftIndent);
    }

    set leftIndent(value) {
        this.setDoubleValue(ParagraphAttDoubleType.LeftIndent, value);
    }

    get rightIndent() {
        return this.getDoubleValue(ParagraphAttDoubleType.RightIndent);
    }

    set rightIndent(value) {
        this.setDoubleValue(ParagraphAttDoubleType.RightIndent, value);
    }

    get firstLineIndent() {
        return this.getDoubleValue(ParagraphAttDoubleType.FirstLineIndent);
    }

    set firstLineIndent(value) {
        this.setDoubleValue(ParagraphAttDoubleType.FirstLineIndent, value);
    }

    get spaceBefore() {
        return this.getDoubleValue(ParagraphAttDoubleType.SpaceBefore);
    }

    set spaceBefore(value) {
        this.setDoubleValue(ParagraphAttDoubleType.SpaceBefore, value);
    }

    get spaceAfter() {
        return this.getDoubleValue(ParagraphAttDoubleType.SpaceAfter);
    }

    set spaceAfter(value) {
        this.setDoubleValue(ParagraphAttDoubleType.SpaceAfter, value);
    }

    get defaultTabStops() {
        return this.getDoubleValue(ParagraphAttDoubleType.DefaultTabStops);
    }

    set defaultTabStops(value) {
        this.setDoubleValue(ParagraphAttDoubleType.DefaultTabStops, value);
    }

    get minWordSpacing() {
        return this.getDoubleValue(ParagraphAttDoubleType.MinWordSpacing);
    }

    set minWordSpacing(value) {
        this.setDoubleValue(ParagraphAttDoubleType.MinWordSpacing, value);
    }

    get desiredWordSpacing() {
        return this.getDoubleValue(ParagraphAttDoubleType.DesiredWordSpacing);
    }

    set desiredWordSpacing(value) {
        this.setDoubleValue(ParagraphAttDoubleType.DesiredWordSpacing, value);
    }

    get maxWordSpacing() {
        return this.getDoubleValue(ParagraphAttDoubleType.MaxWordSpacing);
    }

    set maxWordSpacing(value) {
        this.setDoubleValue(ParagraphAttDoubleType.MaxWordSpacing, value);
    }

    get minLetterSpacing() {
        return this.getDoubleValue(ParagraphAttDoubleType.MinLetterSpacing);
    }

    set minLetterSpacing(value) {
        this.setDoubleValue(ParagraphAttDoubleType.MinLetterSpacing, value);
    }

    get desiredLetterSpacing() {
        return this.getDoubleValue(ParagraphAttDoubleType.DesiredLetterSpacing);
    }

    set desiredLetterSpacing(value) {
        this.setDoubleValue(ParagraphAttDoubleType.DesiredLetterSpacing, value);
    }

    get maxLetterSpacing() {
        return this.getDoubleValue(ParagraphAttDoubleType.MaxLetterSpacing);
    }

    set maxLetterSpacing(value) {
        this.setDoubleValue(ParagraphAttDoubleType.MaxLetterSpacing, value);
    }

    get minHyphenScore() {
        return this.getDoubleValue(ParagraphAttDoubleType.MinHyphenScore);
    }

    set minHyphenScore(value) {
        this.setDoubleValue(ParagraphAttDoubleType.MinHyphenScore, value);
    }

    get hyphenationZone() {
        return this.getDoubleValue(ParagraphAttDoubleType.HyphenationZone);
    }

    set hyphenationZone(value) {
        this.setDoubleValue(ParagraphAttDoubleType.HyphenationZone, value);
    }

    get hyphenationZoneCapitals() {
        return this.getDoubleValue(ParagraphAttDoubleType.HyphenationZoneCapitals);
    }

    set hyphenationZoneCapitals(value) {
        this.setDoubleValue(ParagraphAttDoubleType.HyphenationZoneCapitals, value);
    }

    get hyphenationZoneParagraphEnd() {
        return this.getDoubleValue(ParagraphAttDoubleType.HyphenationZoneParagraphEnd);
    }

    set hyphenationZoneParagraphEnd(value) {
        this.setDoubleValue(ParagraphAttDoubleType.HyphenationZoneParagraphEnd, value);
    }

    get hyphenationZoneColumnEnd() {
        return this.getDoubleValue(ParagraphAttDoubleType.HyphenationZoneColumnEnd);
    }

    set hyphenationZoneColumnEnd(value) {
        this.setDoubleValue(ParagraphAttDoubleType.HyphenationZoneColumnEnd, value);
    }

    get lastLineOutdent() {
        return this.getDoubleValue(ParagraphAttDoubleType.LastLineOutdent);
    }

    set lastLineOutdent(value) {
        this.setDoubleValue(ParagraphAttDoubleType.LastLineOutdent, value);
    }

    get spaceBetweenSameStyles() {
        return this.getDoubleValue(ParagraphAttDoubleType.SpaceBetweenSameStyles);
    }

    set spaceBetweenSameStyles(value) {
        this.setDoubleValue(ParagraphAttDoubleType.SpaceBetweenSameStyles, value);
    }

    getDoubleValue(att) {
        return ParagraphAttsApi.getDoubleValue(this.handle, att);
    }

    setDoubleValue(att, value) {
        ParagraphAttsApi.setDoubleValue(this.handle, att, value);
    }

    get styleName() {
        return this.getStringValue(ParagraphAttStringType.StyleName);
    }

    set styleName(value) {
        this.setStringValue(ParagraphAttStringType.StyleName, value);
    }

    getStringValue(att) {
        return ParagraphAttsApi.getStringValue(this.handle, att);
    }

    setStringValue(att, value) {
        ParagraphAttsApi.setStringValue(this.handle, att, value);
    }
}

module.exports.ParagraphAtts = ParagraphAtts;
module.exports.ParagraphAlignXType = ParagraphAlignXType;
module.exports.ParagraphLeadingType = ParagraphLeadingType;
module.exports.ParagraphStartAtHardBreakType = ParagraphStartAtHardBreakType;
module.exports.ParagraphUseSpaceBeforeMode = ParagraphUseSpaceBeforeMode;
module.exports.ParagraphPDFExportTagType = ParagraphPDFExportTagType;
module.exports.ParagraphLineBreakModeType = ParagraphLineBreakModeType;
module.exports.ParagraphAttDoubleType = ParagraphAttDoubleType;
module.exports.ParagraphAttStringType = ParagraphAttStringType;
