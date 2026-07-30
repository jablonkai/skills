'use strict';

const {
    AnchorGlyphApi,
    CapturedDateTimeGlyphApi,
    CharGlyphApi,
    CrossReferenceGlyphApi,
    CrossReferenceSubGlyphApi,
    CrossReferenceSubGlyphType,
    CrossReferenceTargetType,
    CustomFieldGlyphApi,
    DataMergeFieldGlyphApi,
    DataMergeGlyphApi,
    DataMergeSourceGlyphApi,
    DataMergeSourceType,
    DocumentFieldGlyphApi,
    DocumentFieldType,
    FieldDataType,
    FieldGlyphApi,
    FillerTextGlyphApi,
    FillerTextType,
    FormattableFieldGlyphApi,
    GlyphApi,
    GlyphIndexGlyphApi,
    GlyphType,
    HardBreakGlyphApi,
    HardBreakType,
    IndentToHereGlyphApi,
    IndexMarkGlyphApi,
    ListNumberGlyphApi,
    NoteNumberGlyphApi,
    NotePosition,
    NoteType,
    PageNumberGlyphApi,
    PageNumberType,
    PinGlyphApi,
    RangenoteBodyGlyphApi,
    RangenoteEndGlyphApi,
    RangenoteReferenceGlyphApi,
    RightIndentTabGlyphApi,
    RunningHeaderGlyphApi,
    SectionNameGlyphApi,
    SoftBreakType,
    StoryIoFormat,
    WordPartType
} = require('affinity:story');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const StoryModule = require('./story.js');

function createTypedGlyph(glyphHandle) {
    const glyphType = GlyphApi.getGlyphType(glyphHandle);
        switch (glyphType.value) {
            case GlyphType.Anchor.value:
                return new AnchorGlyph(AnchorGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.CapturedDateTime.value:
                return new CapturedDateTimeGlyph(CapturedDateTimeGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.Char.value:
                return new CharGlyph(CharGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.CrossReference.value:
                return new CrossReferenceGlyph(CrossReferenceGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.CrossReferenceSub.value:
                return new CrossReferenceSubGlyph(CrossReferenceSubGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.CustomField.value:
                return new CustomFieldGlyph(CustomFieldGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.DataMergeField.value:
                return new DataMergeFieldGlyph(DataMergeFieldGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.DataMergeSource.value:
                return new DataMergeSourceGlyph(DataMergeSourceGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.DocumentField.value:
                return new DocumentFieldGlyph(DocumentFieldGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.FillerText.value:
                return new FillerTextGlyph(FillerTextGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.GlyphIndex.value:
                return new GlyphIndexGlyph(GlyphIndexGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.HardBreak.value:
                return new HardBreakGlyph(HardBreakGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.IndentToHere.value:
                return new IndentToHereGlyph(IndentToHereGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.IndexMark.value:
                return new IndexMarkGlyph(IndexMarkGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.ListNumber.value:
                return new ListNumberGlyph(ListNumberGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.NoteNumber.value:
                return new NoteNumberGlyph(NoteNumberGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.PageNumber.value:
                return new PageNumberGlyph(PageNumberGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.Pin.value:
                return new PinGlyph(PinGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.RangenoteBody.value:
                return new RangenoteBodyGlyph(RangenoteBodyGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.RangenoteReference.value:
                return new RangenoteReferenceGlyph(RangenoteReferenceGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.RangenoteEnd.value:
                return new RangenoteEndGlyph(RangenoteEndGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.RightIndentTab.value:
                return new RightIndentTabGlyph(RightIndentTabGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.RunningHeader.value:
                return new RunningHeaderGlyph(RunningHeaderGlyphApi.fromGlyph(glyphHandle));
            case GlyphType.SectionName.value:
                return new SectionNameGlyph(SectionNameGlyphApi.fromGlyph(glyphHandle));
            default:
                return new Glyph(glyphHandle);
        }
}

class Glyph extends HandleObject {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'Glyph';
	}
    
    static GlyphType = GlyphType;
    static HardBreakType = HardBreakType;
	static SoftBreakType = SoftBreakType;
	static WordPartType = WordPartType;
    
    get isGlyph() {
        return true;
    }
    
    clone() {
        return new Glyph(GlyphApi.cloneAsGlyph(this.handle));
    }

    get isConsolidated() {
        return GlyphApi.isConsolidated(this.handle);
    }

    get isMarking() {
        return GlyphApi.isMarking(this.handle);
    }

    get isZeroWidth() {
        return GlyphApi.isZeroWidth(this.handle);
    }

    get isJustificationSpace() {
        return GlyphApi.isJustificationSpace(this.handle);
    }

    get isParagraphBreak() {
        return GlyphApi.isParagraphBreak(this.handle);
    }

    get isSoftBreak() {
        return GlyphApi.isSoftBreak(this.handle);
    }

    get canSoftBreakBefore() {
        return GlyphApi.canSoftBreakBefore(this.handle);
    }

    get canSoftBreakAfter() {
        return GlyphApi.canSoftBreakAfter(this.handle);
    }

    get isAlphaNumeric() {
        return GlyphApi.isAlphaNumeric(this.handle);
    }

    get isAlpha() {
        return GlyphApi.isAlpha(this.handle);
    }

    get isNumeric() {
        return GlyphApi.isNumeric(this.handle);
    }

    get isUppercase() {
        return GlyphApi.isUppercase(this.handle);
    }

    get isLowercase() {
        return GlyphApi.isLowercase(this.handle);
    }

    get isStoryTerminator() {
        return GlyphApi.isStoryTerminator(this.handle);
    }

    get isDeletable() {
        return GlyphApi.isDeletable(this.handle);
    }

    get isTableCellBreak() {
        return GlyphApi.isTableCellBreak(this.handle);
    }

    get isMidWordPunctuation() {
        return GlyphApi.isMidWordPunctuation(this.handle);
    }

    get isTab() {
        return GlyphApi.isTab(this.handle);
    }

    get isCombining() {
        return GlyphApi.isCombining(this.handle);
    }

    get isMarkup() {
        return GlyphApi.isMarkup(this.handle);
    }

    get isHiddenFromOpenType() {
        return GlyphApi.isHiddenFromOpenType(this.handle);
    }

    get wantsFastFind() {
        return GlyphApi.wantsFastFind(this.handle);
    }

    getDescription(format = StoryModule.StoryIoFormat.ClipboardDescriptions) {
        return GlyphApi.getDescription(this.handle, format)
    }

    get description() {
        return this.getDescription();
    }
    
    get glyphType() {
        return GlyphApi.getGlyphType(this.handle);
    }

    get softBreakType() {
        return GlyphApi.getSoftBreakType(this.handle);
    }

    get hardBreakType() {
        return GlyphApi.getHardBreakType(this.handle);
    }

    get wordPartType() {
        return GlyphApi.getWordPartType(this.handle);
    }
}

class AnchorGlyph extends Glyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'AnchorGlyph';
    }
    
    get isAnchorGlyph() {
        return true;
    }

    clone() {
        return new AnchorGlyph(AnchorGlyphApi.cloneAsAnchorGlyph(this.handle));
    }
    
    static fromGlyph(glyph) {
        return new AnchorGlyph(AnchorGlyphApi.fromGlyph(glyph.handle));
    }
}

class CharGlyph extends Glyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'CharGlyph';
	}
    
    get isCharGlyph() {
        return true;
    }
    
    static create(char32) {
        return new CharGlyph(CharGlyphApi.create(char32));
    }

    clone() {
        return new CharGlyph(CharGlyphApi.cloneAsCharGlyph(this.handle));
    }

    get char32() {
        return CharGlyphApi.getChar32(this.handle);
    }

    get baseChar32() {
        return CharGlyphApi.getBaseChar32(this.handle);
    }

    get string() {
        return CharGlyphApi.getString(this.handle);
    }
}

class CrossReferenceSubGlyph extends Glyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CrossReferenceSubGlyph';
    }

    get isCrossReferenceSubGlyph() {
        return true;
    }

    clone() {
        return new CrossReferenceSubGlyph(CrossReferenceSubGlyphApi.cloneAsCrossReferenceSubGlyph(this.handle));
    }

    static create(crossReferenceSubGlyphType) {
        return new CrossReferenceSubGlyph(CrossReferenceSubGlyphApi.create(crossReferenceSubGlyphType));
    }

    static fromGlyph(glyph) {
        return new CrossReferenceSubGlyph(CrossReferenceSubGlyphApi.fromGlyph(glyph.handle));
    }
}

class FieldGlyph extends Glyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'FieldGlyph';
	}
    
    get isFieldGlyph() {
        return true;
    }

    clone() {
        return new FieldGlyph(FieldGlyphApi.cloneAsFieldGlyph(this.handle));
    }

    get fieldName() {
        return FieldGlyphApi.getFieldName(this.handle);
    }
}

class CrossReferenceGlyph extends FieldGlyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CrossReferenceGlyph';
    }

    get isCrossReferenceGlyph() {
        return true;
    }

    get targetType() {
        return CrossReferenceGlyphApi.getTargetType(this.handle);
    }

    get isTargetDifferentChapter() {
        return CrossReferenceGlyphApi.isTargetDifferentChapter(this.handle);
    }

    get usesStyles() {
        return CrossReferenceGlyphApi.usesStyles(this.handle);
    }

    clone() {
        return new CrossReferenceGlyph(CrossReferenceGlyphApi.cloneAsCrossReferenceGlyph(this.handle));
    }

    static create() {
        return new CrossReferenceGlyph(CrossReferenceGlyphApi.create());
    }

    static fromGlyph(glyph) {
        return new CrossReferenceGlyph(CrossReferenceGlyphApi.fromGlyph(glyph.handle));
    }
}

class FillerTextGlyph extends FieldGlyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FillerTextGlyph';
    }

    get isFillerTextGlyph() {
        return true;
    }

    get fillerTextType() {
        return FillerTextGlyphApi.getFillerTextType(this.handle);
    }

    get sourceBegin() {
        return FillerTextGlyphApi.getSourceBegin(this.handle);
    }

    clone() {
        return new FillerTextGlyph(FillerTextGlyphApi.cloneAsFillerTextGlyph(this.handle));
    }

    static fromGlyph(glyph) {
        return new FillerTextGlyph(FillerTextGlyphApi.fromGlyph(glyph.handle));
    }

    static create(fillerTextType, sourceBegin) {
        return new FillerTextGlyph(FillerTextGlyphApi.create(fillerTextType, sourceBegin));
    }
}

class FormattableFieldGlyph extends FieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'FormattableFieldGlyph';
	}
    
    get isFormattableFieldGlyph() {
        return true;
    }

    get fieldDataType() {
        return FormattableFieldGlyphApi.getFieldDataType(this.handle);
    }

    clone() {
        return new FormattableFieldGlyph(FormattableFieldGlyphApi.cloneAsFormattableFieldGlyph(this.handle));
    }
}

class CapturedDateTimeGlyph extends FormattableFieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'CapturedDateTimeGlyph';
	}
    
    get isCapturedDateTimeGlyph() {
        return true;
    }

    get dateTime() {
        return new Date(CapturedDateTimeGlyphApi.getDateTime(this.handle));
    }

    clone() {
        return new CapturedDateTimeGlyph(CapturedDateTimeGlyphApi.cloneAsCapturedDateTimeGlyph(this.handle));
    }
}

class CustomFieldGlyph extends FormattableFieldGlyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CustomFieldGlyph';
    }

    get isCustomFieldGlyph() {
        return true;
    }

    static fromGlyph(glyph) {
        return new CustomFieldGlyph(CustomFieldGlyphApi.fromGlyph(glyph.handle));
    }

    clone() {
        return new CustomFieldGlyph(CustomFieldGlyphApi.cloneAsCustomFieldGlyph(this.handle));
    }
}

class DataMergeGlyph extends FormattableFieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'DataMergeGlyph';
	}
    
    get isDataMergeGlyph() {
        return true;
    }

    clone() {
        return new DataMergeGlyph(DataMergeGlyphApi.cloneAsDataMergeGlyph(this.handle));
    }
}

class DataMergeFieldGlyph extends DataMergeGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'DataMergeFieldGlyph';
	}
    
    get isDataMergeFieldGlyph() {
        return true;
    }

    get dataMergeFieldId() {
        return DataMergeFieldGlyphApi.getDataMergeFieldId(this.handle);
    }

    clone() {
        return new DataMergeFieldGlyph(DataMergeFieldGlyphApi.cloneAsDataMergeFieldGlyph(this.handle));
    }
}

class DataMergeSourceGlyph extends DataMergeGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'DataMergeSourceGlyph';
	}
    
    get isDataMergeSourceGlyph() {
        return true;
    }

    get dataMergeSourceType() {
        return DataMergeSourceGlyphApi.getDataMergeSourceType(this.handle);
    }

    clone() {
        return new DataMergeSourceGlyph(DataMergeSourceGlyphApi.cloneAsDataMergeSourceGlyph(this.handle));
    }
}

class DocumentFieldGlyph extends FormattableFieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'DocumentFieldGlyph';
	}
    
    get isDocumentFieldGlyph() {
        return true;
    }

    get documentFieldType() {
        return DocumentFieldGlyphApi.getDocumentFieldType(this.handle);
    }

    clone() {
        return new DocumentFieldGlyph(DocumentFieldGlyphApi.cloneAsDocumentFieldGlyph(this.handle));
    }
}

class RunningHeaderGlyph extends FormattableFieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'RunningHeaderGlyph';
	}
    
    get isRunningHeaderGlyph() {
        return true;
    }

    clone() {
        return new RunningHeaderGlyph(RunningHeaderGlyphApi.cloneAsRunningHeaderGlyph(this.handle));
    }
}

class PageNumberGlyph extends FieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'PageNumberGlyph';
	}
    
    get isPageNumberGlyph() {
        return true;
    }

    get pageNumberType() {
        return PageNumberGlyphApi.getPageNumberType(this.handle);
    }

    clone() {
        return new PageNumberGlyph(PageNumberGlyphApi.cloneAsPageNumberGlyph(this.handle));
    }
}

class RangenoteBodyGlyph extends FieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'RangenoteBodyGlyph';
	}
    
    get isRangenoteBodyGlyph() {
        return true;
    }

    get isLive() {
        return RangenoteBodyGlyphApi.isLive(this.handle);
    }

    clone() {
        return new RangenoteBodyGlyph(RangenoteBodyGlyphApi.cloneAsRangenoteBodyGlyph(this.handle));
    }
}

class RangenoteReferenceGlyph extends FieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'RangenoteReferenceGlyph';
	}
    
    get isRangenoteReferenceGlyph() {
        return true;
    }

    get noteType() {
        return RangenoteReferenceGlyphApi.getNoteType(this.handle);
    }

    get notePosition() {
        return RangenoteReferenceGlyphApi.getNotePosition(this.handle);
    }

    clone() {
        return new RangenoteReferenceGlyph(RangenoteReferenceGlyphApi.cloneAsRangenoteReferenceGlyph(this.handle));
    }
}

class SectionNameGlyph extends FieldGlyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'SectionNameGlyph';
	}
    
    get isSectionNameGlyph() {
        return true;
    }

    clone() {
        return new SectionNameGlyph(SectionNameGlyphApi.cloneAsSectionNameGlyph(this.handle));
    }
}

class GlyphIndexGlyph extends Glyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'GlyphIndexGlyph';
	}
    
    get isGlyphIndexGlyph() {
        return true;
    }

    clone() {
        return new GlyphIndexGlyph(GlyphIndexGlyphApi.cloneAsGlyphIndexGlyph(this.handle));
    }

    get index() {
        return GlyphIndexGlyphApi.getIndex(this.handle);
    }
}

class HardBreakGlyph extends Glyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'HardBreakGlyph';
	}
    
    get isHardBreakGlyph() {
        return true;
    }

    clone() {
        return new HardBreakGlyph(HardBreakGlyphApi.cloneAsHardBreakGlyph(this.handle));
    }
}

class IndentToHereGlyph extends Glyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'IndentToHereGlyph';
	}
    
    get isIndentToHereGlyph() {
        return true;
    }

    clone() {
        return new IndentToHereGlyph(IndentToHereGlyphApi.cloneAsIndentToHereGlyph(this.handle));
    }
}

class IndexMarkGlyph extends Glyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'IndexMarkGlyph';
    }
    
    get isIndexMarkGlyph() {
        return true;
    }

    get glyphStyle() {
        return IndexMarkGlyphApi.getGlyphStyle(this.handle);
    }

    clone() {
        return new IndexMarkGlyph(IndexMarkGlyphApi.cloneAsIndexMarkGlyph(this.handle));
    }
    
    static fromGlyph(glyph) {
        return new IndexMarkGlyph(IndexMarkGlyphApi.fromGlyph(glyph.handle));
    }
}

class ListNumberGlyph extends Glyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ListNumberGlyph';
    }
    
    get isListNumberGlyph() {
        return true;
    }

    get level() {
        return ListNumberGlyphApi.getLevel(this.handle);
    }

    clone() {
        return new ListNumberGlyph(ListNumberGlyphApi.cloneAsListNumberGlyph(this.handle));
    }
    
    static fromGlyph(glyph) {
        return new ListNumberGlyph(ListNumberGlyphApi.fromGlyph(glyph.handle));
    }
}

class NoteNumberGlyph extends Glyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'NoteNumberGlyph';
    }
    
    get isNoteNumberGlyph() {
        return true;
    }

    clone() {
        return new NoteNumberGlyph(NoteNumberGlyphApi.cloneAsNoteNumberGlyph(this.handle));
    }
    
    static fromGlyph(glyph) {
        return new NoteNumberGlyph(NoteNumberGlyphApi.fromGlyph(glyph.handle));
    }
}

class PinGlyph extends Glyph {
    constructor(handle) {
		super(handle);
	}

    get [Symbol.toStringTag]() {
		return 'PinGlyph';
	}
    
    get isPinGlyph() {
        return true;
    }

    clone() {
        return new PinGlyph(PinGlyphApi.cloneAsPinGlyph(this.handle));
    }

    get isInline() {
        return PinGlyphApi.isInline(this.handle);
	}

    get isNote() {
        return PinGlyphApi.isNote(this.handle);
	}

    get notePosition() {
        return PinGlyphApi.getNotePosition(this.handle);
	}

    get noteType() {
        return PinGlyphApi.getNoteType(this.handle);
	}
}

class RangenoteEndGlyph extends Glyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RangenoteEndGlyph';
    }
    
    get isRangenoteEndGlyph() {
        return true;
    }

    get isLive() {
        return RangenoteEndGlyphApi.isLive(this.handle);
    }

    clone() {
        return new RangenoteEndGlyph(RangenoteEndGlyphApi.cloneAsRangenoteEndGlyph(this.handle));
    }
    
    static fromGlyph(glyph) {
        return new RangenoteEndGlyph(RangenoteEndGlyphApi.fromGlyph(glyph.handle));
    }
}

class RightIndentTabGlyph extends Glyph {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RightIndentTabGlyph';
    }
    
    get isRightIndentTabGlyph() {
        return true;
    }

    clone() {
        return new RightIndentTabGlyph(RightIndentTabGlyphApi.cloneAsRightIndentTabGlyph(this.handle));
    }
    
    static fromGlyph(glyph) {
        return new RightIndentTabGlyph(RightIndentTabGlyphApi.fromGlyph(glyph.handle));
    }
}

module.exports.createTypedGlyph = createTypedGlyph;
module.exports.AnchorGlyph = AnchorGlyph;
module.exports.CapturedDateTimeGlyph = CapturedDateTimeGlyph;
module.exports.CharGlyph = CharGlyph;
module.exports.CrossReferenceGlyph = CrossReferenceGlyph;
module.exports.CrossReferenceSubGlyph = CrossReferenceSubGlyph;
module.exports.CrossReferenceSubGlyphType = CrossReferenceSubGlyphType;
module.exports.CrossReferenceTargetType = CrossReferenceTargetType;
module.exports.CustomFieldGlyph = CustomFieldGlyph;
module.exports.DataMergeGlyph = DataMergeGlyph;
module.exports.DataMergeFieldGlyph = DataMergeFieldGlyph;
module.exports.DataMergeSourceGlyph = DataMergeSourceGlyph;
module.exports.DocumentFieldGlyph = DocumentFieldGlyph;
module.exports.FieldDataType = FieldDataType;
module.exports.FieldGlyph = FieldGlyph;
module.exports.FillerTextGlyph = FillerTextGlyph;
module.exports.FillerTextType = FillerTextType;
module.exports.FormattableFieldGlyph = FormattableFieldGlyph;
module.exports.Glyph = Glyph;
module.exports.GlyphIndexGlyph = GlyphIndexGlyph;
module.exports.GlyphType = GlyphType;
module.exports.HardBreakGlyph = HardBreakGlyph;
module.exports.HardBreakType = HardBreakType;
module.exports.IndentToHereGlyph = IndentToHereGlyph;
module.exports.IndexMarkGlyph = IndexMarkGlyph;
module.exports.ListNumberGlyph = ListNumberGlyph;
module.exports.NoteNumberGlyph = NoteNumberGlyph;
module.exports.NotePosition = NotePosition;
module.exports.NoteType = NoteType;
module.exports.PageNumberGlyph = PageNumberGlyph;
module.exports.RangenoteReferenceGlyph = RangenoteReferenceGlyph;
module.exports.RangenoteBodyGlyph = RangenoteBodyGlyph;
module.exports.SectionNameGlyph = SectionNameGlyph;
module.exports.DataMergeSourceType = DataMergeSourceType;
module.exports.DocumentFieldType = DocumentFieldType;
module.exports.GlyphType = GlyphType;
module.exports.HardBreakType = HardBreakType;
module.exports.PageNumberType = PageNumberType;
module.exports.PinGlyph = PinGlyph;
module.exports.RangenoteEndGlyph = RangenoteEndGlyph;
module.exports.RightIndentTabGlyph = RightIndentTabGlyph;
module.exports.RunningHeaderGlyph = RunningHeaderGlyph;
module.exports.SoftBreakType = SoftBreakType;
module.exports.StoryIoFormat = StoryIoFormat;
module.exports.WordPartType = WordPartType;
