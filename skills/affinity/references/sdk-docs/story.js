'use strict';

const { GlyphType, HardBreakType, SoftBreakType, StoryApi, StoryIoFormat, StoryRange, TableAxis, WordPartType } = require('affinity:story');
const { Collection } = require('./collection.js');
const { GlyphAtts } = require('./glyphatts.js');
const { HandleObject } = require('./handleobject.js');
const { ParagraphAtts } = require('./paragraphatts.js');

// cyclics:
const GlyphsModule = require('./glyphs.js');

class Story extends HandleObject {
	constructor(handle) {
		super(handle);
	}

	static IoFormat = StoryIoFormat;
	static Range = StoryRange;

	get [Symbol.toStringTag]() {
		return 'Story';
	}

	get containsBookEndnotes() {
		return StoryApi.containsBookEndnotes(this.handle);
	}

	get containsIndex() {
		return StoryApi.containsIndex(this.handle);
	}

	get containsToc() {
		return StoryApi.containsToc(this.handle);
	}

	get isEmpty() {
		return StoryApi.isEmpty(this.handle);
	}

	get isRangenoteBodyStory() {
		return StoryApi.isRangenoteBodyStory(this.handle);
	}

	get isTable() {
		return StoryApi.isTable(this.handle);
	}

	get usesGlobalNumbering() {
		return StoryApi.usesGlobalNumbering(this.handle);
	}

	get length() {
		return StoryApi.getLength(this.handle);
	}

	getGlyph(pos) {
		const handle = StoryApi.getGlyph(this.handle, pos);
		return GlyphsModule.createTypedGlyph(handle);
	}

	getGlyphType(pos) {
		return StoryApi.getGlyphType(this.handle, pos);
	}

	isWordBegin(pos) {
		return StoryApi.isWordBegin(this.handle, pos);
	}

	isWordEnd(pos) {
		return StoryApi.isWordEnd(this.handle, pos);
	}

	isWordPart(pos) {
		return StoryApi.isWordPart(this.handle, pos);
	}

	isParagraphBreak(pos) {
		return StoryApi.isParagraphBreak(this.handle, pos);
	}

	getSoftBreakType(pos) {
		return StoryApi.getSoftBreakType(this.handle, pos);
	}

	getHardBreakType(pos) {
		return StoryApi.getHardBreakType(this.handle, pos);
	}

	getWordPartType(pos) {
		return StoryApi.getWordPartType(this.handle, pos);
	}

	findWordBegin(startPos = 0, maxNum = -1) {
		return StoryApi.findWordBegin(this.handle, startPos, maxNum);
	}

	findWordEnd(startPos = 0, maxNum = -1) {
		return StoryApi.findWordEnd(this.handle, startPos, maxNum);
	}

	findWordPart(startPos = 0, maxNum = -1) {
		return StoryApi.findWordPart(this.handle, startPos, maxNum);
	}

	findParagraphBreak(startPos = this.length - 1, maxNum = -1) {
		return StoryApi.findParagraphBreak(this.handle, startPos, maxNum);
	}

	rFindWordBegin(startPos = this.length - 1, maxNum = -1) {
		return StoryApi.rFindWordBegin(this.handle, startPos, maxNum);
	}

	rFindWordEnd(startPos = this.length - 1, maxNum = -1) {
		return StoryApi.rFindWordEnd(this.handle, startPos, maxNum);
	}

	rFindWordPart(startPos = this.length - 1, maxNum = -1) {
		return StoryApi.rFindWordPart(this.handle, startPos, maxNum);
	}

	rFindParagraphBreak(startPos, maxNum = -1) {
		return StoryApi.rFindParagraphBreak(this.handle, startPos, maxNum);
	}

	getWordRange(pos) {
		const begin = this.rFindWordBegin(pos);
		if (begin == -1)
			return new StoryRange(-1, -1);
		const end = this.findWordEnd(begin);
		if (end < pos)
			return new StoryRange(-1, -1);
		return new StoryRange(begin, end);
	}

	getParagraphRange(pos) {
		if (pos < 0)
			return new StoryRange(-1, -1);
		let end = this.findParagraphBreak(pos);
		if (end == -1) {
			const length = this.length;
			if (pos <= this.length)
				end = length;
			else
				return new StoryRange(-1, -1);
		}
		let begin = this.rFindParagraphBreak(end == pos ? pos - 1 : pos);
		if (begin == -1)
			begin = 0;
		else
			++begin;
		return new StoryRange(begin, end);
	}

	get paragraphRanges() {
		const self = this;
		const genFn = function*() {
			let r = self.getParagraphRange(0);
			while (r.begin != -1) {
				yield r;
				r = self.getParagraphRange(r.end + 1);
			}
		}
		return new Collection(genFn);
	}

	get wordRanges() {
		const self = this;
		const genFn = function*() {
			let i = self.findWordBegin(0);
			while (i != -1) {
				let j = self.findWordEnd(i + 1);
				if (j == -1)
					j = self.length;
				yield new StoryRange(i, j);
				i = self.findWordBegin(j + 1);
			}
		}
		return new Collection(genFn);
	}

	indexes(includeTerminator) {
		const length = this.length + Boolean(includeTerminator);
		return Collection.range(0, length);
	}

	get punctuationParts() {
		const self = this;
		return self.indexes().filter(i => self.getWordPartType(i).equals(WordPartType.Punctuation));
	}

	get spaceParts() {
		const self = this;
		return self.indexes().filter(i => self.getWordPartType(i).equals(WordPartType.Space));
	}

	get wordParts() {
		const self = this;
		return self.indexes().filter(i => self.getWordPartType(i).equals(WordPartType.Word));
	}

	get nonSpaceParts() {
		const self = this;
		return self.indexes().filter(i => !self.getWordPartType(i).equals(WordPartType.Space));
	}

	get glyphs() {
		const self = this;
		return self.indexes().map(i => self.getGlyph(i));
	}

    get anchorGlyphs() {
        return this.glyphs.filter(glyph => glyph.isAnchorGlyph);
    }

	get charGlyphs() {
		return this.glyphs.filter(glyph => glyph.isCharGlyph);
	}

    get crossReferenceSubGlyphs() {
        return this.glyphs.filter(glyph => glyph.isCrossReferenceSubGlyph);
    }

	get documentFieldGlyphs() {
		return this.glyphs.filter(glyph => glyph.isDocumentFieldGlyph);
	}

	get fieldGlyphs() {
		return this.glyphs.filter(glyph => glyph.isFieldGlyph);
	}

    get crossReferenceGlyphs() {
        return this.glyphs.filter(glyph => glyph.isCrossReferenceGlyph);
    }

    get fillerTextGlyphs() {
        return this.glyphs.filter(glyph => glyph.isFillerTextGlyph);
    }

	get formattableFieldGlyphs() {
		return this.glyphs.filter(glyph => glyph.isFormattableFieldGlyph);
	}

	get capturedDateTimeGlyphs() {
		return this.glyphs.filter(glyph => glyph.isCapturedDateTimeGlyph);
	}

    get customFieldGlyphs() {
        return this.glyphs.filter(glyph => glyph.isCustomFieldGlyph);
    }

	get dataMergeGlyphs() {
		return this.glyphs.filter(glyph => glyph.isDataMergeGlyph);
	}

	get dataMergeFieldGlyphs() {
		return this.glyphs.filter(glyph => glyph.isDataMergeFieldGlyph);
	}

	get dataMergeSourceGlyphs() {
		return this.glyphs.filter(glyph => glyph.isDataMergeSourceGlyph);
	}

	get runningHeaderGlyphs() {
		return this.glyphs.filter(glyph => glyph.isRunningHeaderGlyph);
	}

	get pageNumberGlyphs() {
		return this.glyphs.filter(glyph => glyph.isPageNumberGlyph);
	}

	get rangenoteBodyGlyphs() {
		return this.glyphs.filter(glyph => glyph.isRangenoteBodyGlyph);
	}

	get rangenoteReferenceGlyphs() {
		return this.glyphs.filter(glyph => glyph.isRangenoteReferenceGlyph);
	}

	get sectionNameGlyphs() {
		return this.glyphs.filter(glyph => glyph.isSectionNameGlyph);
	}
	
	get glyphIndexGlyphs() {
		return this.glyphs.filter(glyph => glyph.isGlyphIndexGlyph);
	}

    get hardBreakGlyphs() {
        return this.glyphs.filter(glyph => glyph.isHardBreakGlyph);
    }

    get indentToHereGlyphs() {
        return this.glyphs.filter(glyph => glyph.isIndentToHereGlyph);
    }
    
    get indexMarkGlyphs() {
        return this.glyphs.filter(glyph => glyph.isIndexMarkGlyph);
    }
    
    get listNumberGlyphs() {
        return this.glyphs.filter(glyph => glyph.isListNumberGlyph);
    }
    
    get noteNumberGlyphs() {
        return this.glyphs.filter(glyph => glyph.isNoteNumberGlyph);
    }

    get pinGlyphs() {
        return this.glyphs.filter(glyph => glyph.isPinGlyph);
    }
    
    get rangenoteEndGlyphs() {
        return this.glyphs.filter(glyph => glyph.isRangenoteEndGlyph);
    }
    
    get rightIndentTabGlyphs() {
        return this.glyphs.filter(glyph => glyph.isRightIndentTabGlyph);
    }

	getText(startPos = 0, maxLength = -1, format = StoryIoFormat.ClipboardDescriptions) {
		return StoryApi.getText(this.handle, startPos, maxLength, format);
	}

	getGlyphAtts(pos) {
		return new GlyphAtts(StoryApi.getGlyphAtts(this.handle, pos));
	}

	getGlyphAttsRunEnd(pos, maxPos) {
		return StoryApi.getGlyphAttsRunEnd(this.handle, pos, maxPos);
	}

	getParagraphAtts(pos) {
		return new ParagraphAtts(StoryApi.getParagraphAtts(this.handle, pos));
	}

	getParagraphAttsRunEnd(pos, maxPos) {
		return StoryApi.getParagraphAttsRunEnd(this.handle, pos, maxPos);
	}

	getTextRange(range, format = StoryIoFormat.ClipboardDescriptions) {
		return this.getText(range.begin, range.length, format);
	}

	get text() {
		return this.getText();
	}

	getGlyphAttRunsFrom(start) {
		const self = this;
		const genFn = function*() {
			const end = self.length;
			if (start < end) {
				let pos = start;
				while (pos < end) {
					const runEnd = self.getGlyphAttsRunEnd(pos, end);
					const atts = self.getGlyphAtts(pos);
					yield {glyphAtts:atts, begin:pos, end:runEnd};
					pos = runEnd;
				}
			}
		}
		return new Collection(genFn);
	}

	getParagraphAttRunsFrom(start) {
		const self = this;
		const genFn = function*() {
			const end = self.length;
			if (start < end) {
				let pos = start;
				while (pos < end) {
					const runEnd = self.getParagraphAttsRunEnd(pos, end);
					const atts = self.getParagraphAtts(pos);
					yield {paragraphAtts:atts, begin:pos, end:runEnd};
					pos = runEnd;
				}
			}
		}
		return new Collection(genFn);
	}

	getAttRunsFrom(start) {
		const self = this;
		const genFn = function*() {
			const end = self.length;
			if (start < end) {
				let pos = start;
				let glyphRunEnd = start;
				let paragraphRunEnd = start;
				let glyphAtts;
				let paragraphAtts;
				while (pos < end) {
					if (glyphRunEnd < paragraphRunEnd)
						glyphAtts = self.getGlyphAtts(pos);
					else if (paragraphRunEnd < glyphRunEnd)
						paragraphAtts = self.getParagraphAtts(pos);
					else {
						glyphAtts = self.getGlyphAtts(pos);
						paragraphAtts = self.getParagraphAtts(pos);
					}
					glyphRunEnd = self.getGlyphAttsRunEnd(pos, end);
					paragraphRunEnd = self.getParagraphAttsRunEnd(pos, end);
					const runEnd = Math.min(glyphRunEnd, paragraphRunEnd);
					yield {glyphAtts:glyphAtts, paragraphAtts:paragraphAtts, begin:pos, end:runEnd};
					pos = runEnd;
				}
			}
		}
		return new Collection(genFn);
	}

	get glyphAttRuns() {
		return this.getGlyphAttRunsFrom(0);
	}

	get paragraphAttRuns() {
		return this.getParagraphAttRunsFrom(0);
	}

	get attRuns() {
		return this.getAttRunsFrom(0);
	}
}

module.exports.GlyphType = GlyphType;
module.exports.Story = Story;
module.exports.StoryIoFormat = StoryIoFormat;
module.exports.StoryRange = StoryRange;
module.exports.HardBreakType = HardBreakType;
module.exports.SoftBreakType = SoftBreakType;
module.exports.TableAxis = TableAxis;
module.exports.WordPartType = WordPartType;
