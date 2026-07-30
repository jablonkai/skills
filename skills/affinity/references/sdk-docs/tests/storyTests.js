'use strict';

const { StoryBuilder } = require('/storybuilder');
const {
    GlyphAtts,
    TypographicLineType,
    SuperSubType,
    CapsType,
    LeadingOverrideType,
    OpticalAlignmentType,
    TocRoleType,
    GlyphAttDoubleType,
    GlyphAttStringType,
} = require('/glyphatts');
const {
    ParagraphAtts,
    ParagraphAlignXType,
    ParagraphLeadingType,
    ParagraphStartAtHardBreakType,
    ParagraphUseSpaceBeforeMode,
    ParagraphPDFExportTagType,
    ParagraphLineBreakModeType,
    ParagraphAttDoubleType,
    ParagraphAttStringType,
} = require('/paragraphatts');
const { StoryDelta } = require('/storydelta');
const { ArtTextNodeDefinition, FrameTextNodeDefinition } = require('/nodes');
const { Document } = require('/document');
const { AddChildNodesCommandBuilder } = require('/commands');
const { TestUtils } = require('/tests/testUtils');

function runTests() {

    const doc = TestUtils.newA4Empty();
    const dpi = doc.dpi;
    const format = doc.rasterFormat;

    let passed = 0;
    let failed = 0;

    function addToDocument(def) {
        const builder = AddChildNodesCommandBuilder.create();
        builder.addNode(def);
        const cmd = builder.createCommand();
        Document.current.executeCommand(cmd);
    }

    function createBuilder(height) {
        const sb = StoryBuilder.create();
        sb.applyGlyphDelta(StoryDelta.createGlyphDouble(GlyphAttDoubleType.Height, height || 50));
        return sb;
    }

    function assert(condition, msg) {
        if (!condition) {
            failed++;
            console.log("FAIL: " + msg);
        } else {
            passed++;
        }
    }

    function assertClose(a, b, msg) {
        assert(Math.abs(a - b) < 0.0001, msg + " (got " + a + ", expected " + b + ")");
    }

    function assertThrows(fn, msg) {
        let threw = false;
        try { fn(); } catch (e) { threw = true; }
        if (threw) {
            passed++;
        } else {
            failed++;
            console.log("FAIL (no throw): " + msg);
        }
    }


    // ============================================================
    // PART 1: GlyphAtts standalone (has getters)
    // ============================================================

    console.log("[StoryTest-01] GlyphAtts create and defaults");
    {
        const ga = GlyphAtts.create();
        assert(ga !== null && ga !== undefined, "StoryTest-01: create returns non-null");
        assert(ga.isNoBreak === false, "StoryTest-01: default isNoBreak is false");
        assert(ga.underlineType.value === TypographicLineType.None.value, "StoryTest-01: default underline is None");
        assert(ga.strikeoutType.value === TypographicLineType.None.value, "StoryTest-01: default strikeout is None");
        assert(ga.superSubType.value === SuperSubType.None.value, "StoryTest-01: default superSub is None");
        assert(ga.capsType.value === CapsType.None.value, "StoryTest-01: default caps is None");
    }

    console.log("[StoryTest-02] GlyphAtts clone independence");
    {
        const ga = GlyphAtts.create();
        ga.isNoBreak = true;
        ga.underlineType = TypographicLineType.Single;
        const clone = ga.clone();
        assert(clone.isNoBreak === true, "StoryTest-02: clone copies isNoBreak");
        assert(clone.underlineType.value === TypographicLineType.Single.value, "StoryTest-02: clone copies underline");
        clone.isNoBreak = false;
        clone.underlineType = TypographicLineType.None;
        assert(ga.isNoBreak === true, "StoryTest-02: mutating clone doesn't affect original isNoBreak");
        assert(ga.underlineType.value === TypographicLineType.Single.value, "StoryTest-02: mutating clone doesn't affect original underline");
    }

    console.log("[StoryTest-03] GlyphAtts all enum setters roundtrip");
    {
        const ga = GlyphAtts.create();
        ga.underlineType = TypographicLineType.Single;
        assert(ga.underlineType.value === TypographicLineType.Single.value, "StoryTest-03: underlineType Single");
        ga.underlineType = TypographicLineType.Double;
        assert(ga.underlineType.value === TypographicLineType.Double.value, "StoryTest-03: underlineType Double");

        ga.strikeoutType = TypographicLineType.Double;
        assert(ga.strikeoutType.value === TypographicLineType.Double.value, "StoryTest-03: strikeoutType Double");

        ga.superSubType = SuperSubType.Superscript;
        assert(ga.superSubType.value === SuperSubType.Superscript.value, "StoryTest-03: superSub Superscript");
        ga.superSubType = SuperSubType.Subscript;
        assert(ga.superSubType.value === SuperSubType.Subscript.value, "StoryTest-03: superSub Subscript");

        ga.leadingOverrideType = LeadingOverrideType.AtLeast;
        assert(ga.leadingOverrideType.value === LeadingOverrideType.AtLeast.value, "StoryTest-03: leadingOverride AtLeast");

        ga.opticalAlignmentType = OpticalAlignmentType.Font;
        assert(ga.opticalAlignmentType.value === OpticalAlignmentType.Font.value, "StoryTest-03: opticalAlignment Font");

        ga.tocRoleType = TocRoleType.PageNumber;
        assert(ga.tocRoleType.value === TocRoleType.PageNumber.value, "StoryTest-03: tocRole PageNumber");
    }

    console.log("[StoryTest-04] GlyphAtts all CapsType enum values");
    {
        const names = [
            'None', 'CapsToSmallCaps', 'SmallCaps', 'AllCaps', 'AllSmallCaps',
            'CapsToPetiteCaps', 'PetiteCaps', 'AllPetiteCaps', 'Titling', 'Unicase'
        ];
        for (const name of names) {
            const enumVal = CapsType[name];
            assert(enumVal !== undefined, "StoryTest-04: CapsType." + name + " exists");
            if (enumVal === undefined) continue;
            const ga = GlyphAtts.create();
            ga.capsType = enumVal;
            assert(ga.capsType.value === enumVal.value, "StoryTest-04: CapsType." + name + " roundtrip");
        }
    }

    console.log("[StoryTest-05] GlyphAtts double values");
    {
        const ga = GlyphAtts.create();
        ga.setDoubleValue(GlyphAttDoubleType.Height, 14.5);
        assertClose(ga.getDoubleValue(GlyphAttDoubleType.Height), 14.5, "StoryTest-05: Height");
        ga.setDoubleValue(GlyphAttDoubleType.CharacterSpacing, 1.25);
        assertClose(ga.getDoubleValue(GlyphAttDoubleType.CharacterSpacing), 1.25, "StoryTest-05: CharacterSpacing");
        ga.setDoubleValue(GlyphAttDoubleType.ScaleX, 2.0);
        assertClose(ga.getDoubleValue(GlyphAttDoubleType.ScaleX), 2.0, "StoryTest-05: ScaleX");
        ga.setDoubleValue(GlyphAttDoubleType.ScaleY, 0.5);
        assertClose(ga.getDoubleValue(GlyphAttDoubleType.ScaleY), 0.5, "StoryTest-05: ScaleY");
        ga.setDoubleValue(GlyphAttDoubleType.ShearX, 15.0);
        assertClose(ga.getDoubleValue(GlyphAttDoubleType.ShearX), 15.0, "StoryTest-05: ShearX");
    }

    console.log("[StoryTest-06] GlyphAtts string values");
    {
        const ga = GlyphAtts.create();
        ga.setStringValue(GlyphAttStringType.SpellingLanguageId, "en-GB");
        assert(ga.getStringValue(GlyphAttStringType.SpellingLanguageId) === "en-GB", "StoryTest-06: SpellingLanguageId");
        ga.setStringValue(GlyphAttStringType.HyphenationLanguageId, "de-DE");
        assert(ga.getStringValue(GlyphAttStringType.HyphenationLanguageId) === "de-DE", "StoryTest-06: HyphenationLanguageId");
    }

    console.log("[StoryTest-07] GlyphAtts OpenType tags — high-bit values");
    {
        const ga = GlyphAtts.create();
        ga.openTypeScriptTag = 0x6C61746E; // 'latn'
        assert(ga.openTypeScriptTag === 0x6C61746E, "StoryTest-07: 'latn' tag roundtrip, got 0x" + ga.openTypeScriptTag.toString(16));
        ga.openTypeScriptTag = 0x44464C54; // 'DFLT'
        assert(ga.openTypeScriptTag === 0x44464C54, "StoryTest-07: 'DFLT' tag roundtrip, got 0x" + ga.openTypeScriptTag.toString(16));
        ga.openTypeLanguageTag = 0xFFFFFFFF;
        assert(ga.openTypeLanguageTag === 0xFFFFFFFF, "StoryTest-07: max uint32 tag, got 0x" + ga.openTypeLanguageTag.toString(16));
        ga.openTypeScriptTag = 0;
        assert(ga.openTypeScriptTag === 0, "StoryTest-07: zero tag");
    }

    console.log("[StoryTest-08] GlyphAtts bool toggle");
    {
        const ga = GlyphAtts.create();
        assert(ga.isNoBreak === false, "StoryTest-08: default false");
        ga.isNoBreak = true;
        assert(ga.isNoBreak === true, "StoryTest-08: set true");
        ga.isNoBreak = false;
        assert(ga.isNoBreak === false, "StoryTest-08: set false again");
    }


    // ============================================================
    // PART 2: ParagraphAtts standalone (has getters)
    // ============================================================

    console.log("[StoryTest-09] ParagraphAtts create and defaults");
    {
        const pa = ParagraphAtts.create();
        assert(pa !== null && pa !== undefined, "StoryTest-09: create returns non-null");
        assert(pa.isKeepTogether === false, "StoryTest-09: default isKeepTogether false");
        assert(pa.isKeepWithPrevious === false, "StoryTest-09: default isKeepWithPrevious false");
    }

    console.log("[StoryTest-10] ParagraphAtts all AlignX enum values");
    {
        const names = [
            'Left', 'Centre', 'Right', 'JustifyLeft', 'JustifyCentre',
            'JustifyRight', 'JustifyAll', 'AwayFromSpine', 'TowardsSpine'
        ];
        for (const name of names) {
            const enumVal = ParagraphAlignXType[name];
            assert(enumVal !== undefined, "StoryTest-10: ParagraphAlignXType." + name + " exists");
            if (enumVal === undefined) continue;
            const pa = ParagraphAtts.create();
            pa.alignXType = enumVal;
            assert(pa.alignXType.value === enumVal.value, "StoryTest-10: AlignX." + name + " roundtrip");
        }
    }

    console.log("[StoryTest-11] ParagraphAtts all bool fields");
    {
        const pa = ParagraphAtts.create();
        const boolFields = [
            'isKeepWithPrevious', 'isKeepTogether', 'isPreventWidows', 'isPreventOrphans',
            'alignToBaselineGrid', 'isAutoHyphenate', 'isIndex',
            'useSpaceBetweenSameStyles', 'isSumBeforeAndAfterSpace', 'isBookEndnotes', 'useModernLeading'
        ];
        for (const field of boolFields) {
            assert(pa[field] === false || pa[field] === true, "StoryTest-11: " + field + " is boolean");
            pa[field] = true;
            assert(pa[field] === true, "StoryTest-11: " + field + " set true");
            pa[field] = false;
            assert(pa[field] === false, "StoryTest-11: " + field + " set false");
        }
    }

    console.log("[StoryTest-12] ParagraphAtts int fields");
    {
        const pa = ParagraphAtts.create();
        pa.keepWithNext = 3;
        assert(pa.keepWithNext === 3, "StoryTest-12: keepWithNext=3, got " + pa.keepWithNext);
        pa.hyphenateMinLength = 6;
        assert(pa.hyphenateMinLength === 6, "StoryTest-12: hyphenateMinLength=6");
        pa.hyphenateMinPrefix = 3;
        assert(pa.hyphenateMinPrefix === 3, "StoryTest-12: hyphenateMinPrefix=3");
        pa.hyphenateMinSuffix = 2;
        assert(pa.hyphenateMinSuffix === 2, "StoryTest-12: hyphenateMinSuffix=2");
        pa.maxConsecutiveHyphens = 4;
        assert(pa.maxConsecutiveHyphens === 4, "StoryTest-12: maxConsecutiveHyphens=4");
    }

    console.log("[StoryTest-13] ParagraphAtts double/string values");
    {
        const pa = ParagraphAtts.create();
        pa.setDoubleValue(ParagraphAttDoubleType.SpaceBefore, 12.0);
        assertClose(pa.getDoubleValue(ParagraphAttDoubleType.SpaceBefore), 12.0, "StoryTest-13: SpaceBefore");
        pa.setDoubleValue(ParagraphAttDoubleType.SpaceAfter, 6.0);
        assertClose(pa.getDoubleValue(ParagraphAttDoubleType.SpaceAfter), 6.0, "StoryTest-13: SpaceAfter");

        pa.setStringValue(ParagraphAttStringType.StyleName, "Body");
        assert(pa.getStringValue(ParagraphAttStringType.StyleName) === "Body", "StoryTest-13: StyleName roundtrip");
    }

    console.log("[StoryTest-14] ParagraphAtts clone independence");
    {
        const pa = ParagraphAtts.create();
        pa.isKeepTogether = true;
        pa.alignXType = ParagraphAlignXType.Centre;
        const clone = pa.clone();
        assert(clone.isKeepTogether === true, "StoryTest-14: clone copies isKeepTogether");
        clone.isKeepTogether = false;
        assert(pa.isKeepTogether === true, "StoryTest-14: mutating clone doesn't affect original");
    }


    // ============================================================
    // PART 3: Delta factories (just creation — no getters)
    // ============================================================

    console.log("[StoryTest-15] Delta glyph enum factories");
    {
        const d1 = StoryDelta.createUnderlineType(TypographicLineType.Single);
        assert(d1 !== null, "StoryTest-15: createUnderlineType");
        const d2 = StoryDelta.createStrikeoutType(TypographicLineType.Double);
        assert(d2 !== null, "StoryTest-15: createStrikeoutType");
        const d3 = StoryDelta.createSuperSubType(SuperSubType.Superscript);
        assert(d3 !== null, "StoryTest-15: createSuperSubType");
        const d4 = StoryDelta.createCapsType(CapsType.AllCaps);
        assert(d4 !== null, "StoryTest-15: createCapsType");
        const d5 = StoryDelta.createLeadingOverrideType(LeadingOverrideType.AtLeast);
        assert(d5 !== null, "StoryTest-15: createLeadingOverrideType");
        const d6 = StoryDelta.createOpticalAlignmentType(OpticalAlignmentType.Font);
        assert(d6 !== null, "StoryTest-15: createOpticalAlignmentType");
        const d7 = StoryDelta.createTocRoleType(TocRoleType.PageNumber);
        assert(d7 !== null, "StoryTest-15: createTocRoleType");
        const d8 = StoryDelta.createIsNoBreak(true);
        assert(d8 !== null, "StoryTest-15: createIsNoBreak");
    }

    console.log("[StoryTest-16] Delta OpenType tag factories — high-bit");
    {
        const d1 = StoryDelta.createOpenTypeScriptTag(0x6C61746E);
        assert(d1 !== null, "StoryTest-16: script tag 'latn'");
        const d2 = StoryDelta.createOpenTypeLanguageTag(0xDEADBEEF);
        assert(d2 !== null, "StoryTest-16: language tag 0xDEADBEEF");
    }

    console.log("[StoryTest-17] Delta glyph double/string factories");
    {
        const d1 = StoryDelta.createGlyphDouble(GlyphAttDoubleType.Height, 24.0);
        assert(d1 !== null, "StoryTest-17: glyphDouble Height");
        const d2 = StoryDelta.createGlyphString(GlyphAttStringType.SpellingLanguageId, "en-GB");
        assert(d2 !== null, "StoryTest-17: glyphString SpellingLanguageId");
    }

    console.log("[StoryTest-18] Delta paragraph enum factories");
    {
        const d1 = StoryDelta.createAlignX(ParagraphAlignXType.Centre);
        assert(d1 !== null, "StoryTest-18: createAlignX");
        const d2 = StoryDelta.createLeadingType(ParagraphLeadingType.RelativeToHeight);
        assert(d2 !== null, "StoryTest-18: createLeadingType");
        const d3 = StoryDelta.createStartAtHardBreak(ParagraphStartAtHardBreakType.Page);
        assert(d3 !== null, "StoryTest-18: createStartAtHardBreak");
        const d4 = StoryDelta.createLineBreakMode(ParagraphLineBreakModeType.International);
        assert(d4 !== null, "StoryTest-18: createLineBreakMode");
    }

    console.log("[StoryTest-19] Delta paragraph bool factories");
    {
        const boolFactories = [
            'createIsKeepWithPrevious', 'createIsKeepTogether',
            'createIsPreventWidows', 'createIsPreventOrphans',
            'createAlignToBaselineGrid', 'createIsAutoHyphenate',
            'createUseSpaceBetweenSameStyles', 'createIsSumBeforeAndAfterSpace',
            'createUseModernLeading'
        ];
        for (const name of boolFactories) {
            const d = StoryDelta[name](true);
            assert(d !== null, "StoryTest-19: " + name + "(true)");
            const d2 = StoryDelta[name](false);
            assert(d2 !== null, "StoryTest-19: " + name + "(false)");
        }
    }

    console.log("[StoryTest-20] Delta paragraph int factories");
    {
        const d1 = StoryDelta.createKeepWithNext(3);
        assert(d1 !== null, "StoryTest-20: keepWithNext");
        const d2 = StoryDelta.createHyphenateMinLength(5);
        assert(d2 !== null, "StoryTest-20: hyphenateMinLength");
        const d3 = StoryDelta.createHyphenateMinPrefix(3);
        assert(d3 !== null, "StoryTest-20: hyphenateMinPrefix");
        const d4 = StoryDelta.createHyphenateMinSuffix(2);
        assert(d4 !== null, "StoryTest-20: hyphenateMinSuffix");
        const d5 = StoryDelta.createMaxConsecutiveHyphens(4);
        assert(d5 !== null, "StoryTest-20: maxConsecutiveHyphens");
    }

    console.log("[StoryTest-21] Delta paragraph double/string factories");
    {
        const d1 = StoryDelta.createParagraphDouble(ParagraphAttDoubleType.SpaceBefore, 12.0);
        assert(d1 !== null, "StoryTest-21: paragraphDouble SpaceBefore");
        const d2 = StoryDelta.createParagraphString(ParagraphAttStringType.StyleName, "Body");
        assert(d2 !== null, "StoryTest-21: paragraphString StyleName");
    }

    console.log("[StoryTest-22] Delta indent factories");
    {
        const d1 = StoryDelta.createLeftIndent(20.0);
        assert(d1 !== null, "StoryTest-22: leftIndent");
        const d2 = StoryDelta.createRightIndent(10.0);
        assert(d2 !== null, "StoryTest-22: rightIndent");
    }


    // ============================================================
    // PART 4: StoryBuilder — build & create nodes (visual check)
    // ============================================================

    console.log("[StoryTest-23] StoryBuilder basic creation");
    {
        const sb = StoryBuilder.create();
        assert(sb !== null && sb !== undefined, "StoryTest-23: create returns non-null");
    }

    console.log("[StoryTest-24] StoryBuilder chaining");
    {
        const sb = StoryBuilder.create();
        const ret = sb.addText("Hello").addText(" World").addParagraphBreak().addText("Line 2");
        assert(ret === sb, "StoryTest-24: chaining returns same builder");
    }

    console.log("[StoryTest-25] StoryBuilder empty string");
    {
        const sb = StoryBuilder.create();
        sb.addText("");
        sb.addText("After empty");
        assert(true, "StoryTest-25: empty addText did not crash");
    }

    console.log("[StoryTest-25a] StoryBuilder setToFrameTextDefaultStyle");
    {
        const sb = StoryBuilder.create();
        const ret = sb.setToFrameTextDefaultStyle(dpi, format);
        assert(ret === sb, "StoryTest-25a: setToFrameTextDefaultStyle returns this for chaining");

        const ga = sb.glyphAtts;
        assert(ga !== null, "StoryTest-25a: glyphAtts non-null after default style");
        const pa = sb.paragraphAtts;
        assert(pa !== null, "StoryTest-25a: paragraphAtts non-null after default style");
    }

    console.log("[StoryTest-25b] StoryBuilder setToArtisticTextDefaultStyle");
    {
        const sb = StoryBuilder.create();
        const ret = sb.setToArtisticTextDefaultStyle(dpi, format);
        assert(ret === sb, "StoryTest-25b: setToArtisticTextDefaultStyle returns this for chaining");

        const ga = sb.glyphAtts;
        assert(ga !== null, "StoryTest-25b: glyphAtts non-null after default style");
        const pa = sb.paragraphAtts;
        assert(pa !== null, "StoryTest-25b: paragraphAtts non-null after default style");
    }

    console.log("[StoryTest-25c] StoryBuilder clearText resets text but preserves style");
    {
        const sb = StoryBuilder.create();
        sb.setToArtisticTextDefaultStyle(dpi, format);
        sb.applyGlyphDelta(StoryDelta.createGlyphDouble(GlyphAttDoubleType.Height, 72));
        sb.addText("This will be cleared");

        const gaBefore = sb.glyphAtts;
        const paBefore = sb.paragraphAtts;

        const ret = sb.clearText();
        assert(ret === sb, "StoryTest-25c: clearText returns this for chaining");

        const gaAfter = sb.glyphAtts;
        assertClose(gaAfter.getDoubleValue(GlyphAttDoubleType.Height), 72, "StoryTest-25c: glyph height preserved after clear");

        sb.addText("Fresh text after clear");
        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 1100}, sb);
        assert(def !== null, "StoryTest-25c: can create node after clearText");
        addToDocument(def);
        console.log("  [StoryTest-25c] VISUAL: 'Fresh text after clear' at 72pt");
    }

    console.log("[StoryTest-25d] StoryBuilder clearText on empty builder");
    {
        const sb = StoryBuilder.create();
        sb.clearText();
        sb.addText("After clearing empty builder");
        assert(true, "StoryTest-25d: clearText on empty builder did not crash");
    }

    console.log("[StoryTest-25e] StoryBuilder frame vs artistic default styles differ");
    {
        const sbFrame = StoryBuilder.create();
        sbFrame.setToFrameTextDefaultStyle(dpi, format);
        sbFrame.addText("Frame");
        sbFrame.addParagraphBreak();
        sbFrame.addText("default");
        const frameDef = FrameTextNodeDefinition.createFromStoryBuilder({x: 100, y: 1200, width: 200, height: 100}, sbFrame);
        assert(frameDef !== null, "StoryTest-25e: frame text node created with frame defaults");
        addToDocument(frameDef);

        const sbArt = StoryBuilder.create();
        sbArt.setToArtisticTextDefaultStyle(dpi, format);
        sbArt.addText("Art default");
        const artDef = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 1320}, sbArt);
        assert(artDef !== null, "StoryTest-25e: art text node created with artistic defaults");
        addToDocument(artDef);
        console.log("  [StoryTest-25e] VISUAL: Frame text and art text with their respective default styles");
    }

    console.log("[StoryTest-26] StoryBuilder → ArtTextNode: plain text");
    {
        const sb = createBuilder();
        sb.addText("Hello World");
        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 100}, sb);
        assert(def !== null, "StoryTest-26: ArtTextNodeDefinition created");
        addToDocument(def);
        console.log("  [StoryTest-26] VISUAL: Should see 'Hello World' at (100,100)");
    }

    console.log("[StoryTest-27] StoryBuilder → ArtTextNode: styled text with deltas");
    {
        const sb = createBuilder(72);
        sb.addText("Big text. ");

        sb.applyGlyphDelta(StoryDelta.createUnderlineType(TypographicLineType.Single));
        sb.addText("Underlined. ");

        sb.applyGlyphDelta(StoryDelta.createSuperSubType(SuperSubType.Superscript));
        sb.addText("Super. ");

        const resetGa = GlyphAtts.create();
        resetGa.setDoubleValue(GlyphAttDoubleType.Height, 50);
        sb.setGlyphAtts(resetGa); // reset but keep 50pt
        sb.applyGlyphDelta(StoryDelta.createCapsType(CapsType.AllCaps));
        sb.addText("all caps text");

        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 200}, sb);
        assert(def !== null, "StoryTest-27: styled ArtTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-27] VISUAL: 72pt, then underlined, then superscript, then ALL CAPS at 50pt");
    }

    console.log("[StoryTest-28] StoryBuilder → ArtTextNode: multi-paragraph with paragraph styles");
    {
        const sb = createBuilder();
        sb.applyParagraphDelta(StoryDelta.createAlignX(ParagraphAlignXType.Left));
        sb.addText("Left aligned paragraph");
        sb.addParagraphBreak();

        sb.applyParagraphDelta(StoryDelta.createAlignX(ParagraphAlignXType.Centre));
        sb.addText("Centre aligned paragraph");
        sb.addParagraphBreak();

        sb.applyParagraphDelta(StoryDelta.createAlignX(ParagraphAlignXType.Right));
        sb.addText("Right aligned paragraph");

        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 400}, sb);
        assert(def !== null, "StoryTest-28: multi-paragraph ArtTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-28] VISUAL: Three paragraphs — left, centre, right aligned");
    }

    console.log("[StoryTest-29] StoryBuilder → FrameTextNode: basic");
    {
        const sb = createBuilder(30);
        sb.addText("Frame text content with enough words to potentially wrap in the frame.");
        const def = FrameTextNodeDefinition.createFromStoryBuilder({x: 300, y: 100, width: 200, height: 150}, sb);
        assert(def !== null, "StoryTest-29: FrameTextNodeDefinition created");
        addToDocument(def);
        console.log("  [StoryTest-29] VISUAL: Frame text at (300,100) 200x150");
    }

    console.log("[StoryTest-30] StoryBuilder → FrameTextNode: full paragraph formatting");
    {
        const sb = createBuilder(30);

        const pa = ParagraphAtts.create();
        pa.alignXType = ParagraphAlignXType.JustifyAll;
        pa.isKeepTogether = true;
        pa.setDoubleValue(ParagraphAttDoubleType.SpaceBefore, 6.0);
        pa.setDoubleValue(ParagraphAttDoubleType.SpaceAfter, 6.0);
        sb.setParagraphAtts(pa);

        sb.addText("Justified paragraph with spacing before and after. This text should fill the frame nicely.");
        sb.addParagraphBreak();

        sb.applyParagraphDelta(StoryDelta.createAlignX(ParagraphAlignXType.Centre));
        sb.addText("Second paragraph centred.");

        const def = FrameTextNodeDefinition.createFromStoryBuilder({x: 300, y: 300, width: 250, height: 200}, sb);
        assert(def !== null, "StoryTest-30: fully formatted FrameTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-30] VISUAL: Justified first para, centred second, 6pt spacing");
    }

    console.log("[StoryTest-31] StoryBuilder → ArtTextNode: setGlyphAtts replaces delta state");
    {
        const sb = createBuilder();
        sb.applyGlyphDelta(StoryDelta.createUnderlineType(TypographicLineType.Double));
        sb.applyGlyphDelta(StoryDelta.createIsNoBreak(true));
        sb.addText("Underlined. ");

        const resetGa = GlyphAtts.create();
        resetGa.setDoubleValue(GlyphAttDoubleType.Height, 50);
        sb.setGlyphAtts(resetGa); // reset but keep 50pt
        sb.addText("Not underlined.");

        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 600}, sb);
        assert(def !== null, "StoryTest-31: setGlyphAtts reset ArtTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-31] VISUAL: First part double-underlined, second part plain");
    }

    console.log("[StoryTest-32] StoryBuilder → ArtTextNode: unicode text");
    {
        const sb = createBuilder();
        sb.addText("日本語テキスト");
        sb.addParagraphBreak();
        sb.addText("Ελληνικά");
        sb.addParagraphBreak();
        sb.addText("café résumé naïve");
        sb.addParagraphBreak();
        sb.addText("简体中文。");
        sb.addParagraphBreak();
        sb.addText("🎨🖌️✏️");

        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 800}, sb);
        assert(def !== null, "StoryTest-32: unicode ArtTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-32] VISUAL: Japanese, Greek, accented, emoji text");
    }

    console.log("[StoryTest-33] StoryBuilder → ArtTextNode: very long text");
    {
        const sb = createBuilder(20);
        sb.addText("A".repeat(100000));
        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 600, y: 100}, sb);
        assert(def !== null, "StoryTest-33: 100k char ArtTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-33] VISUAL: Very long AAAA... text");
    }

    console.log("[StoryTest-34] StoryBuilder → ArtTextNode: many paragraph breaks");
    {
        const sb = createBuilder(20);
        for (let i = 0; i < 200; i++) {
            sb.addText("line " + i);
            sb.addParagraphBreak();
        }
        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 600, y: 300}, sb);
        assert(def !== null, "StoryTest-34: 200-paragraph ArtTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-34] VISUAL: 200 paragraphs");
    }

    console.log("[StoryTest-35] StoryBuilder → ArtTextNode: empty paragraphs");
    {
        const sb = createBuilder();
        sb.addParagraphBreak();
        sb.addParagraphBreak();
        sb.addParagraphBreak();
        sb.addText("After three empty paragraphs");
        const def = ArtTextNodeDefinition.createFromStoryBuilder({x: 600, y: 500}, sb);
        assert(def !== null, "StoryTest-35: empty paragraph ArtTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-35] VISUAL: 3 empty lines then text");
    }

    console.log("[StoryTest-36] Multiple builders are independent");
    {
        const sb1 = createBuilder();
        const sb2 = createBuilder();
        sb1.applyGlyphDelta(StoryDelta.createIsNoBreak(true));
        sb1.addText("Builder 1");
        sb2.addText("Builder 2");

        const def1 = ArtTextNodeDefinition.createFromStoryBuilder({x: 600, y: 700}, sb1);
        const def2 = ArtTextNodeDefinition.createFromStoryBuilder({x: 600, y: 780}, sb2);
        assert(def1 !== null, "StoryTest-36: builder 1 creates node");
        assert(def2 !== null, "StoryTest-36: builder 2 creates node");
        addToDocument(def1);
        addToDocument(def2);
        console.log("  [StoryTest-36] VISUAL: 'Builder 1' and 'Builder 2' independently");
    }

    console.log("[StoryTest-37] StoryBuilder reuse after consume");
    {
        const sb = createBuilder();
        sb.addText("First story");
        const def1 = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 900}, sb);
        assert(def1 !== null, "StoryTest-37: first consume");
        addToDocument(def1);

        // Builder should be reusable — ConsumeStory resets internally
        sb.addText("Second story");
        const def2 = ArtTextNodeDefinition.createFromStoryBuilder({x: 100, y: 980}, sb);
        assert(def2 !== null, "StoryTest-37: second consume after reuse");
        addToDocument(def2);
        console.log("  [StoryTest-37] VISUAL: 'First story' then 'Second story' — builder reused");
    }

    console.log("[StoryTest-38] StoryBuilder → FrameTextNode: rapid style changes per word");
    {
        const sb = createBuilder(30);
        const words = ["This ", "is ", "a ", "stress ", "test ", "of ", "style ", "changes."];
        for (let i = 0; i < words.length; i++) {
            if (i % 2 === 0) {
                sb.applyGlyphDelta(StoryDelta.createUnderlineType(TypographicLineType.Single));
            } else {
                sb.applyGlyphDelta(StoryDelta.createUnderlineType(TypographicLineType.None));
            }
            sb.addText(words[i]);
        }
        const def = FrameTextNodeDefinition.createFromStoryBuilder({x: 300, y: 500, width: 300, height: 150}, sb);
        assert(def !== null, "StoryTest-38: rapid style changes FrameTextNode created");
        addToDocument(def);
        console.log("  [StoryTest-38] VISUAL: Alternating underlined/plain words");
    }


    // ============================================================
    // Summary
    // ============================================================
    console.log("========================================");
    console.log("storyTests: " + passed + " passed, " + failed + " failed");
    if (failed === 0)
        console.log("ALL TESTS PASSED");
    else
        console.log("SOME TESTS FAILED — search for FAIL above");

} // end runTests

module.exports.runTests = runTests;
