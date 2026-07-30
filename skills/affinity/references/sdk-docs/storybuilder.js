'use strict';

const { RasterFormat } = require('affinity:raster');
const { StoryBuilderApi } = require('affinity:story');
const { GlyphAtts } = require('./glyphatts.js');
const { HandleObject } = require('./handleobject.js');
const { ParagraphAtts } = require('./paragraphatts.js');

class StoryBuilder extends HandleObject {
    get [Symbol.toStringTag]() { return 'StoryBuilder'; }

    constructor(handle) { super(handle); }

    static create() {
        return new StoryBuilder(StoryBuilderApi.create());
    }

    setToFrameTextDefaultStyle(dpi, format) {
        StoryBuilderApi.setToFrameTextDefaultStyle(this.handle, dpi, format);
        return this;
    }

    setToArtisticTextDefaultStyle(dpi, format) {
        StoryBuilderApi.setToArtisticTextDefaultStyle(this.handle, dpi, format);
        return this;
    }

    clearText() {
        StoryBuilderApi.clearText(this.handle);
        return this;
    }

    addText(text) {
        StoryBuilderApi.addText(this.handle, text);
        return this;
    }

    addParagraphBreak() {
        StoryBuilderApi.addParagraphBreak(this.handle);
        return this;
    }

    setGlyphAtts(glyphAtts) {
        StoryBuilderApi.setGlyphAtts(this.handle, glyphAtts.handle);
        return this;
    }

    setParagraphAtts(paragraphAtts) {
        StoryBuilderApi.setParagraphAtts(this.handle, paragraphAtts.handle);
        return this;
    }

    applyGlyphDelta(delta) {
        StoryBuilderApi.applyGlyphDelta(this.handle, delta.handle);
        return this;
    }

    applyParagraphDelta(delta) {
        StoryBuilderApi.applyParagraphDelta(this.handle, delta.handle);
        return this;
    }

    get glyphAtts() {
        return new GlyphAtts(StoryBuilderApi.getGlyphAtts(this.handle));
    }

    get paragraphAtts() {
        return new ParagraphAtts(StoryBuilderApi.getParagraphAtts(this.handle));
    }
}

module.exports.RasterFormat = RasterFormat;
module.exports.StoryBuilder = StoryBuilder;
