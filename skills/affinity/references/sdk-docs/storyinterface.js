'use strict';

const { StoryInterfaceApi, TextDefaultType } = require('affinity:dom');
const { StoryIoFormat } = require('affinity:story');
const { Collection } = require('./collection.js');
const { HandleObject} = require('./handleobject.js');

// cyclics:
const GlyphsModule = require('./glyphs.js');
const NodesModule = require('./nodes.js');
const StoryModule = require('./story.js');

// monkey patches:
require('/geometry.js');

class StoryInterface extends HandleObject {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'StoryInterface';
	}

	get domainTransform() {
		return StoryInterfaceApi.getDomainTransform(this.handle);
	}

	get scalarDomainTransform() {
		return StoryInterfaceApi.getScalarDomainTransform(this.handle);
	}

	get textDefaultType() {
		return StoryInterfaceApi.getTextDefaultType(this.handle);
	}

	get textRenderScale() {
		return StoryInterfaceApi.getTextRenderScale(this.handle);
	}

	get textUiScale() {
		return StoryInterfaceApi.getTextUiScale(this.handle);
	}

	get isMultiFrameTextFlow() {
		return StoryInterfaceApi.isMultiFrameTextFlow(this.handle);
	}

	get story() {
		return new StoryModule.Story(StoryInterfaceApi.getStory(this.handle));
	}

	get storyRange() {
		return StoryInterfaceApi.getStoryRange(this.handle);
	}

	getText(startPos = 0, maxLength = -1, format = StoryIoFormat.ClipboardDescriptions) {
		const range = this.storyRange;
		if (startPos > range.length)
			return "";
		if (maxLength < 0)
			maxLength = range.length;
		return this.story.getText(range.begin + startPos, maxLength, format);
	}

	get text() {
		return this.story.getTextRange(this.storyRange);
	}
	
	get glyphIndexes() {
		const range = this.storyRange;
		return Collection.range(range.begin, range.length);
	}

	get glyphs() {
		const story = this.story;
		return this.glyphIndexes.map(i => story.getGlyph(i));
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

	get node() {
		return NodesModule.createTypedNode(StoryInterfaceApi.getNode(this.handle));
	}
}

module.exports.StoryInterface = StoryInterface;
module.exports.TextDefaultType = TextDefaultType;
