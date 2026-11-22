// Type declarations for the Affinity JavaScript SDK: module "affinity:story".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:story" {

    import { FontField, FontWidth } from "affinity:fonts";
    import { RasterFormat } from "affinity:raster";

    export enum CapsType {
        None,
        CapsToSmallCaps,
        SmallCaps,
        AllCaps,
        AllSmallCaps,
        CapsToPetiteCaps,
        PetiteCaps,
        AllPetiteCaps,
        Titling,
        Unicase,
    }

    export enum CrossReferenceSubGlyphType {
        PageNumber,
        SectionName,
        AboveBelow,
        NumberedParagraph,
        ParagraphBody,
        ListNumber,
        NoteNumber,
        AnchorName,
        ChapterName,
        ObjectDescription,
    }

    export enum CrossReferenceTargetType {
        Anchor,
        Paragraph,
        IndexMark,
    }

    export enum DataMergeSourceType {
        RecordIndex,
        OriginalRecordIndex,
        SourceName,
    }

    export enum DocumentFieldType {
        Author,
        Tags,
        Comments,
        Title,
        LastEditedBy,
        Size,
        Created,
        Modified,
        PageCount,
        Revision,
        SaveCount,
        Printed,
        Filename,
        Path,
        Subject,
        Rating,
        Headline,
        AuthorPosition,
        DescriptionWriter,
        ImageLocation,
        ImageCity,
        ImageState,
        ImageCountry,
        ImageIsoCountryCode,
        Source,
        Credit,
        Genre,
        SubjectCodes,
        Scenes,
        JobId,
        Instructions,
        ContactAddress,
        ContactCity,
        ContactState,
        ContactPostcode,
        ContactCountry,
        ContactPhone,
        ContactEmail,
        ContactWebsite,
        IsCopyrighted,
        CopyrightTerms,
        CopyrightUrl,
        CcLicenceName,
        CcMorePermsUrl,
        CcAttributionUrl,
        CcAttributionName,
        CameraModel,
        CameraMaker,
        Lens,
        DateShot,
        Publisher,
        ISBN10,
        ISBN13,
        Illustrator,
    }

    export enum FieldDataType {
        String,
        Number,
        DateTime,
    }

    export enum FillerTextType {
        Lorem,
        Alice,
    }

    export enum GlyphAttDoubleType {
        Height,
        CharacterSpacing,
        BaselineAdvance,
        AutoKernMinHeight,
        OffsetX,
        OffsetY,
        ManualKerning,
        ScaleX,
        ScaleY,
        ShearX,
        AbsoluteLeading,
    }

    export enum GlyphAttStringType {
        SpellingLanguageId,
        StyleName,
        HyphenationLanguageId,
    }

    export enum GlyphType {
        Anchor,
        Char,
        CrossReference,
        CrossReferenceSub,
        FillerText,
        CapturedDateTime,
        CustomField,
        DataMergeField,
        DataMergeSource,
        DocumentField,
        RunningHeader,
        PageNumber,
        RangenoteBody,
        RangenoteReference,
        SectionName,
        GlyphIndex,
        HardBreak,
        IndentToHere,
        IndexMark,
        ListNumber,
        NoteNumber,
        Pin,
        RangenoteEnd,
        RightIndentTab,
    }

    export enum HardBreakType {
        None,
        Line,
        Paragraph,
        Column,
        TableCell,
        Frame,
        Page,
        OddPage,
        EvenPage,
        Story,
    }

    export enum LeadingOverrideType {
        None,
        AtLeast,
    }

    export enum NotePosition {
        Unknown,
        BottomOfColumn,
        BottomOfFrame,
        EndOfStory,
        StoryFrame,
        SectionFrame,
        DocumentFrame,
        BelowText,
        BelowFrame,
        LeftOfFrame,
        RightOfFrame,
        AwayFromSpine,
        TowardsSpine,
        AlternateSides,
        ClosestSide,
        EndOfBook,
    }

    export enum NoteType {
        None,
        Footnote,
        Endnote,
        Sidenote,
    }

    export enum OpticalAlignmentType {
        None,
        Manual,
        Font,
    }

    export enum PageNumberType {
        Current,
        Next,
        Previous,
        SectionTotal,
        RunLast,
    }

    export enum ParagraphAlignXType {
        Left,
        Centre,
        Right,
        JustifyLeft,
        JustifyCentre,
        JustifyRight,
        JustifyAll,
        AwayFromSpine,
        TowardsSpine,
    }

    export enum ParagraphAttDoubleType {
        RelativeLeading,
        AbsoluteLeading,
        LeftIndent,
        RightIndent,
        FirstLineIndent,
        SpaceBefore,
        SpaceAfter,
        DefaultTabStops,
        MinWordSpacing,
        DesiredWordSpacing,
        MaxWordSpacing,
        MinLetterSpacing,
        DesiredLetterSpacing,
        MaxLetterSpacing,
        MinHyphenScore,
        HyphenationZone,
        HyphenationZoneCapitals,
        HyphenationZoneParagraphEnd,
        HyphenationZoneColumnEnd,
        LastLineOutdent,
        SpaceBetweenSameStyles,
    }

    export enum ParagraphAttStringType {
        StyleName,
    }

    export enum ParagraphLeadingType {
        RelativeToIdeal,
        RelativeToHeight,
        ExactlyAbsolute,
        AtLeastAbsolute,
        RelativeToIdealAbsolute,
    }

    export enum ParagraphLineBreakModeType {
        Auto,
        Western,
        International,
    }

    export enum ParagraphPDFExportTagType {
        P,
        H1,
        H2,
        H3,
        H4,
        H5,
        H6,
    }

    export enum ParagraphStartAtHardBreakType {
        None,
        Column,
        Frame,
        Page,
        EvenPage,
        OddPage,
    }

    export enum ParagraphUseSpaceBeforeMode {
        OnlyBetweenParagraphs,
        OnlyAtColumnTop,
        Always,
    }

    export enum SoftBreakType {
        Normal,
        Space,
        Never,
        WithoutHyphen,
        SoftHyphen,
        Ideographic,
        Punctuation,
        OpenPunctuation,
        ClosePunctuation,
        CloseParenthesis,
        Solidus,
        InfixNumeric,
    }

    export enum StoryIoFormat {
        Raw,
        UserDescriptions,
        InternalDescriptions,
        MenuDescriptions,
        CppDescriptions,
        Returns,
        Newlines,
        CrLf,
        Tabs,
        HideStoryTerminator,
        ReplaceCrLfTabWithSpace,
        ReplaceTypographicQuotes,
        TokenDescriptions,
        FieldDescriptions,
        ClipboardDescriptions,
        CommandDescriptions,
        Debug,
    }

    export enum SuperSubType {
        None,
        Superscript,
        Subscript,
    }

    export enum TableAxis {
        Columns,
        Rows,
    }

    export enum TocRoleType {
        None,
        PageNumber,
    }

    export enum TypographicLineType {
        None,
        Single,
        Double,
    }

    export enum WordPartType {
        Word,
        Punctuation,
        Space,
    }

    export class StoryRange {
        begin: number;
        end: number;
    }

    export interface AnchorGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: AnchorGlyphHandle): AnchorGlyphHandle;
        cloneAsAnchorGlyph(self: AnchorGlyphHandle): AnchorGlyphHandle;
        fromGlyph(glyph: GlyphHandle): AnchorGlyphHandle;
    }
    export const AnchorGlyphApi: AnchorGlyphApi;

    export interface CapturedDateTimeGlyphApi extends Omit<FormattableFieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: CapturedDateTimeGlyphHandle): CapturedDateTimeGlyphHandle;
        cloneAsCapturedDateTimeGlyph(self: CapturedDateTimeGlyphHandle): CapturedDateTimeGlyphHandle;
        fromGlyph(glyph: GlyphHandle): CapturedDateTimeGlyphHandle;
        getDateTime(self: CapturedDateTimeGlyphHandle): number;
    }
    export const CapturedDateTimeGlyphApi: CapturedDateTimeGlyphApi;

    export interface CharGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: CharGlyphHandle): CharGlyphHandle;
        cloneAsCharGlyph(self: CharGlyphHandle): CharGlyphHandle;
        create(char32: number): CharGlyphHandle;
        fromGlyph(glyph: GlyphHandle): CharGlyphHandle;
        getBaseChar32(self: CharGlyphHandle): number;
        getChar32(self: CharGlyphHandle): number;
        getString(self: CharGlyphHandle): string;
    }
    export const CharGlyphApi: CharGlyphApi;

    export interface CrossReferenceGlyphApi extends Omit<FieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: CrossReferenceGlyphHandle): CrossReferenceGlyphHandle;
        cloneAsCrossReferenceGlyph(self: CrossReferenceGlyphHandle): CrossReferenceGlyphHandle;
        create(): CrossReferenceGlyphHandle;
        fromGlyph(glyph: GlyphHandle): CrossReferenceGlyphHandle;
        getTargetType(self: CrossReferenceGlyphHandle): CrossReferenceTargetType;
        isTargetDifferentChapter(self: CrossReferenceGlyphHandle): boolean;
        usesStyles(self: CrossReferenceGlyphHandle): boolean;
    }
    export const CrossReferenceGlyphApi: CrossReferenceGlyphApi;

    export interface CrossReferenceSubGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: CrossReferenceSubGlyphHandle): CrossReferenceSubGlyphHandle;
        cloneAsCrossReferenceSubGlyph(self: CrossReferenceSubGlyphHandle): CrossReferenceSubGlyphHandle;
        create(crossReferenceSubGlyphType: CrossReferenceSubGlyphType): CrossReferenceSubGlyphHandle;
        fromGlyph(glyph: GlyphHandle): CrossReferenceSubGlyphHandle;
    }
    export const CrossReferenceSubGlyphApi: CrossReferenceSubGlyphApi;

    export interface CustomFieldGlyphApi extends Omit<FormattableFieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: CustomFieldGlyphHandle): CustomFieldGlyphHandle;
        cloneAsCustomFieldGlyph(self: CustomFieldGlyphHandle): CustomFieldGlyphHandle;
        fromGlyph(glyph: GlyphHandle): CustomFieldGlyphHandle;
    }
    export const CustomFieldGlyphApi: CustomFieldGlyphApi;

    export interface DataMergeFieldGlyphApi extends Omit<DataMergeGlyphApi, "clone" | "fromGlyph"> {
        clone(self: DataMergeFieldGlyphHandle): DataMergeFieldGlyphHandle;
        cloneAsDataMergeFieldGlyph(self: DataMergeFieldGlyphHandle): DataMergeFieldGlyphHandle;
        fromGlyph(glyph: GlyphHandle): DataMergeFieldGlyphHandle;
        getDataMergeFieldId(self: DataMergeFieldGlyphHandle): string;
    }
    export const DataMergeFieldGlyphApi: DataMergeFieldGlyphApi;

    export interface DataMergeGlyphApi extends Omit<FormattableFieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: DataMergeGlyphHandle): DataMergeGlyphHandle;
        cloneAsDataMergeGlyph(self: DataMergeGlyphHandle): DataMergeGlyphHandle;
        fromGlyph(glyph: GlyphHandle): DataMergeGlyphHandle;
    }
    export const DataMergeGlyphApi: DataMergeGlyphApi;

    export interface DataMergeSourceGlyphApi extends Omit<DataMergeGlyphApi, "clone" | "fromGlyph"> {
        clone(self: DataMergeSourceGlyphHandle): DataMergeSourceGlyphHandle;
        cloneAsDataMergeSourceGlyph(self: DataMergeSourceGlyphHandle): DataMergeSourceGlyphHandle;
        fromGlyph(glyph: GlyphHandle): DataMergeSourceGlyphHandle;
        getDataMergeSourceType(self: DataMergeSourceGlyphHandle): DataMergeSourceType;
    }
    export const DataMergeSourceGlyphApi: DataMergeSourceGlyphApi;

    export interface DocumentFieldGlyphApi extends Omit<FormattableFieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: DocumentFieldGlyphHandle): DocumentFieldGlyphHandle;
        cloneAsDocumentFieldGlyph(self: DocumentFieldGlyphHandle): DocumentFieldGlyphHandle;
        fromGlyph(glyph: GlyphHandle): DocumentFieldGlyphHandle;
        getDocumentFieldType(self: DocumentFieldGlyphHandle): DocumentFieldType;
    }
    export const DocumentFieldGlyphApi: DocumentFieldGlyphApi;

    export interface FieldGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: FieldGlyphHandle): FieldGlyphHandle;
        cloneAsFieldGlyph(self: FieldGlyphHandle): FieldGlyphHandle;
        fromGlyph(glyph: GlyphHandle): FieldGlyphHandle;
        getFieldName(self: FieldGlyphHandle): string;
    }
    export const FieldGlyphApi: FieldGlyphApi;

    export interface FillerTextGlyphApi extends Omit<FieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: FillerTextGlyphHandle): FillerTextGlyphHandle;
        cloneAsFillerTextGlyph(self: FillerTextGlyphHandle): FillerTextGlyphHandle;
        create(fillerTextType: FillerTextType, sourceBegin: number): FillerTextGlyphHandle;
        fromGlyph(glyph: GlyphHandle): FillerTextGlyphHandle;
        getFillerTextType(self: FillerTextGlyphHandle): FillerTextType;
        getSourceBegin(self: FillerTextGlyphHandle): number;
    }
    export const FillerTextGlyphApi: FillerTextGlyphApi;

    export interface FormattableFieldGlyphApi extends Omit<FieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: FormattableFieldGlyphHandle): FormattableFieldGlyphHandle;
        cloneAsFormattableFieldGlyph(self: FormattableFieldGlyphHandle): FormattableFieldGlyphHandle;
        fromGlyph(glyph: GlyphHandle): FormattableFieldGlyphHandle;
        getFieldDataType(self: FormattableFieldGlyphHandle): FieldDataType;
    }
    export const FormattableFieldGlyphApi: FormattableFieldGlyphApi;

    export interface GlyphApi {
        canSoftBreakAfter(self: GlyphHandle): boolean;
        canSoftBreakBefore(self: GlyphHandle): boolean;
        clone(self: GlyphHandle): GlyphHandle;
        cloneAsGlyph(self: GlyphHandle): GlyphHandle;
        getDescription(self: GlyphHandle, format: StoryIoFormat): string;
        getGlyphType(self: GlyphHandle): GlyphType;
        getHardBreakType(self: GlyphHandle): HardBreakType;
        getSoftBreakType(self: GlyphHandle): SoftBreakType;
        getWordPartType(self: GlyphHandle): WordPartType;
        isAlpha(self: GlyphHandle): boolean;
        isAlphaNumeric(self: GlyphHandle): boolean;
        isCombining(self: GlyphHandle): boolean;
        isConsolidated(self: GlyphHandle): boolean;
        isDeletable(self: GlyphHandle): boolean;
        isHiddenFromOpenType(self: GlyphHandle): boolean;
        isJustificationSpace(self: GlyphHandle): boolean;
        isLowercase(self: GlyphHandle): boolean;
        isMarking(self: GlyphHandle): boolean;
        isMarkup(self: GlyphHandle): boolean;
        isMidWordPunctuation(self: GlyphHandle): boolean;
        isNumeric(self: GlyphHandle): boolean;
        isParagraphBreak(self: GlyphHandle): boolean;
        isSoftBreak(self: GlyphHandle): boolean;
        isStoryTerminator(self: GlyphHandle): boolean;
        isTab(self: GlyphHandle): boolean;
        isTableCellBreak(self: GlyphHandle): boolean;
        isUppercase(self: GlyphHandle): boolean;
        isZeroWidth(self: GlyphHandle): boolean;
        wantsFastFind(self: GlyphHandle): boolean;
    }
    export const GlyphApi: GlyphApi;

    export interface GlyphAttsApi {
        clone(self: GlyphAttsHandle): GlyphAttsHandle;
        create(): GlyphAttsHandle;
        getBrushFill(self: GlyphAttsHandle): FillDescriptorHandle;
        getCapsType(self: GlyphAttsHandle): CapsType;
        getDoubleValue(self: GlyphAttsHandle, att: GlyphAttDoubleType): number;
        getFont(self: GlyphAttsHandle): FontHandle;
        getHighlightFill(self: GlyphAttsHandle): FillDescriptorHandle;
        getIsNoBreak(self: GlyphAttsHandle): boolean;
        getLeadingOverrideType(self: GlyphAttsHandle): LeadingOverrideType;
        getLineStyleDescriptor(self: GlyphAttsHandle): LineStyleDescriptorHandle;
        getOpenTypeLanguageTag(self: GlyphAttsHandle): number;
        getOpenTypeScriptTag(self: GlyphAttsHandle): number;
        getOpticalAlignmentType(self: GlyphAttsHandle): OpticalAlignmentType;
        getPenFill(self: GlyphAttsHandle): FillDescriptorHandle;
        getStrikeoutFill(self: GlyphAttsHandle): FillDescriptorHandle;
        getStrikeoutType(self: GlyphAttsHandle): TypographicLineType;
        getStringValue(self: GlyphAttsHandle, att: GlyphAttStringType): string;
        getSuperSubType(self: GlyphAttsHandle): SuperSubType;
        getTocRoleType(self: GlyphAttsHandle): TocRoleType;
        getTransparency(self: GlyphAttsHandle): FillDescriptorHandle;
        getUnderlineFill(self: GlyphAttsHandle): FillDescriptorHandle;
        getUnderlineType(self: GlyphAttsHandle): TypographicLineType;
        setBrushFill(self: GlyphAttsHandle, fillDescriptorOrNull: FillDescriptorHandle | null): void;
        setCapsType(self: GlyphAttsHandle, type: CapsType): void;
        setDoubleValue(self: GlyphAttsHandle, att: GlyphAttDoubleType, value: number): void;
        setFont(self: GlyphAttsHandle, font: FontHandle): void;
        setHighlightFill(self: GlyphAttsHandle, fillDescriptorOrNull: FillDescriptorHandle | null): void;
        setIsNoBreak(self: GlyphAttsHandle, isNoBreak: boolean): void;
        setLeadingOverrideType(self: GlyphAttsHandle, type: LeadingOverrideType): void;
        setLineStyleDescriptor(self: GlyphAttsHandle, lineStyleDescriptor: LineStyleDescriptorHandle): void;
        setOpenTypeLanguageTag(self: GlyphAttsHandle, tag: number): void;
        setOpenTypeScriptTag(self: GlyphAttsHandle, tag: number): void;
        setOpticalAlignmentType(self: GlyphAttsHandle, type: OpticalAlignmentType): void;
        setPenFill(self: GlyphAttsHandle, fillDescriptorOrNull: FillDescriptorHandle | null): void;
        setStrikeoutFill(self: GlyphAttsHandle, fillDescriptorOrNull: FillDescriptorHandle | null): void;
        setStrikeoutType(self: GlyphAttsHandle, type: TypographicLineType): void;
        setStringValue(self: GlyphAttsHandle, att: GlyphAttStringType, value: string): void;
        setSuperSubType(self: GlyphAttsHandle, type: SuperSubType): void;
        setTocRoleType(self: GlyphAttsHandle, type: TocRoleType): void;
        setTransparency(self: GlyphAttsHandle, fillDescriptorOrNull: FillDescriptorHandle | null): void;
        setUnderlineFill(self: GlyphAttsHandle, fillDescriptorOrNull: FillDescriptorHandle | null): void;
        setUnderlineType(self: GlyphAttsHandle, type: TypographicLineType): void;
    }
    export const GlyphAttsApi: GlyphAttsApi;

    export interface GlyphIndexGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: GlyphIndexGlyphHandle): GlyphIndexGlyphHandle;
        cloneAsGlyphIndexGlyph(self: GlyphIndexGlyphHandle): GlyphIndexGlyphHandle;
        fromGlyph(glyph: GlyphHandle): GlyphIndexGlyphHandle;
        getIndex(self: GlyphIndexGlyphHandle): number;
    }
    export const GlyphIndexGlyphApi: GlyphIndexGlyphApi;

    export interface HardBreakGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: HardBreakGlyphHandle): HardBreakGlyphHandle;
        cloneAsHardBreakGlyph(self: HardBreakGlyphHandle): HardBreakGlyphHandle;
        fromGlyph(glyph: GlyphHandle): HardBreakGlyphHandle;
    }
    export const HardBreakGlyphApi: HardBreakGlyphApi;

    export interface IndentToHereGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: IndentToHereGlyphHandle): IndentToHereGlyphHandle;
        cloneAsIndentToHereGlyph(self: IndentToHereGlyphHandle): IndentToHereGlyphHandle;
        fromGlyph(glyph: GlyphHandle): IndentToHereGlyphHandle;
    }
    export const IndentToHereGlyphApi: IndentToHereGlyphApi;

    export interface IndexMarkGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: IndexMarkGlyphHandle): IndexMarkGlyphHandle;
        cloneAsIndexMarkGlyph(self: IndexMarkGlyphHandle): IndexMarkGlyphHandle;
        fromGlyph(glyph: GlyphHandle): IndexMarkGlyphHandle;
        getGlyphStyle(self: IndexMarkGlyphHandle): string;
    }
    export const IndexMarkGlyphApi: IndexMarkGlyphApi;

    export interface ListNumberGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: ListNumberGlyphHandle): ListNumberGlyphHandle;
        cloneAsListNumberGlyph(self: ListNumberGlyphHandle): ListNumberGlyphHandle;
        fromGlyph(glyph: GlyphHandle): ListNumberGlyphHandle;
        getLevel(self: ListNumberGlyphHandle): number;
    }
    export const ListNumberGlyphApi: ListNumberGlyphApi;

    export interface NoteNumberGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: NoteNumberGlyphHandle): NoteNumberGlyphHandle;
        cloneAsNoteNumberGlyph(self: NoteNumberGlyphHandle): NoteNumberGlyphHandle;
        fromGlyph(glyph: GlyphHandle): NoteNumberGlyphHandle;
    }
    export const NoteNumberGlyphApi: NoteNumberGlyphApi;

    export interface PageNumberGlyphApi extends Omit<FieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: PageNumberGlyphHandle): PageNumberGlyphHandle;
        cloneAsPageNumberGlyph(self: PageNumberGlyphHandle): PageNumberGlyphHandle;
        fromGlyph(glyph: GlyphHandle): PageNumberGlyphHandle;
        getPageNumberType(self: PageNumberGlyphHandle): PageNumberType;
    }
    export const PageNumberGlyphApi: PageNumberGlyphApi;

    export interface ParagraphAttsApi {
        clone(self: ParagraphAttsHandle): ParagraphAttsHandle;
        create(): ParagraphAttsHandle;
        getAlignToBaselineGrid(self: ParagraphAttsHandle): boolean;
        getAlignXType(self: ParagraphAttsHandle): ParagraphAlignXType;
        getDoubleValue(self: ParagraphAttsHandle, att: ParagraphAttDoubleType): number;
        getHyphenateMinLength(self: ParagraphAttsHandle): number;
        getHyphenateMinPrefix(self: ParagraphAttsHandle): number;
        getHyphenateMinSuffix(self: ParagraphAttsHandle): number;
        getIsAutoHyphenate(self: ParagraphAttsHandle): boolean;
        getIsBookEndnotes(self: ParagraphAttsHandle): boolean;
        getIsIndex(self: ParagraphAttsHandle): boolean;
        getIsKeepTogether(self: ParagraphAttsHandle): boolean;
        getIsKeepWithPrevious(self: ParagraphAttsHandle): boolean;
        getIsPreventOrphans(self: ParagraphAttsHandle): boolean;
        getIsPreventWidows(self: ParagraphAttsHandle): boolean;
        getIsSumBeforeAndAfterSpace(self: ParagraphAttsHandle): boolean;
        getKeepWithNext(self: ParagraphAttsHandle): number;
        getLeadingType(self: ParagraphAttsHandle): ParagraphLeadingType;
        getLineBreakModeType(self: ParagraphAttsHandle): ParagraphLineBreakModeType;
        getMaxConsecutiveHyphens(self: ParagraphAttsHandle): number;
        getPDFExportTagType(self: ParagraphAttsHandle): ParagraphPDFExportTagType;
        getStartAtHardBreakType(self: ParagraphAttsHandle): ParagraphStartAtHardBreakType;
        getStringValue(self: ParagraphAttsHandle, att: ParagraphAttStringType): string;
        getUseModernLeading(self: ParagraphAttsHandle): boolean;
        getUseSpaceBeforeMode(self: ParagraphAttsHandle): ParagraphUseSpaceBeforeMode;
        getUseSpaceBetweenSameStyles(self: ParagraphAttsHandle): boolean;
        setAlignToBaselineGrid(self: ParagraphAttsHandle, value: boolean): void;
        setAlignXType(self: ParagraphAttsHandle, type: ParagraphAlignXType): void;
        setDoubleValue(self: ParagraphAttsHandle, att: ParagraphAttDoubleType, value: number): void;
        setHyphenateMinLength(self: ParagraphAttsHandle, value: number): void;
        setHyphenateMinPrefix(self: ParagraphAttsHandle, value: number): void;
        setHyphenateMinSuffix(self: ParagraphAttsHandle, value: number): void;
        setIsAutoHyphenate(self: ParagraphAttsHandle, value: boolean): void;
        setIsBookEndnotes(self: ParagraphAttsHandle, value: boolean): void;
        setIsIndex(self: ParagraphAttsHandle, value: boolean): void;
        setIsKeepTogether(self: ParagraphAttsHandle, value: boolean): void;
        setIsKeepWithPrevious(self: ParagraphAttsHandle, value: boolean): void;
        setIsPreventOrphans(self: ParagraphAttsHandle, value: boolean): void;
        setIsPreventWidows(self: ParagraphAttsHandle, value: boolean): void;
        setIsSumBeforeAndAfterSpace(self: ParagraphAttsHandle, value: boolean): void;
        setKeepWithNext(self: ParagraphAttsHandle, value: number): void;
        setLeadingType(self: ParagraphAttsHandle, type: ParagraphLeadingType): void;
        setLineBreakModeType(self: ParagraphAttsHandle, type: ParagraphLineBreakModeType): void;
        setMaxConsecutiveHyphens(self: ParagraphAttsHandle, value: number): void;
        setPDFExportTagType(self: ParagraphAttsHandle, type: ParagraphPDFExportTagType): void;
        setStartAtHardBreakType(self: ParagraphAttsHandle, type: ParagraphStartAtHardBreakType): void;
        setStringValue(self: ParagraphAttsHandle, att: ParagraphAttStringType, value: string): void;
        setUseModernLeading(self: ParagraphAttsHandle, value: boolean): void;
        setUseSpaceBeforeMode(self: ParagraphAttsHandle, mode: ParagraphUseSpaceBeforeMode): void;
        setUseSpaceBetweenSameStyles(self: ParagraphAttsHandle, value: boolean): void;
    }
    export const ParagraphAttsApi: ParagraphAttsApi;

    export interface PinGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: PinGlyphHandle): PinGlyphHandle;
        cloneAsPinGlyph(self: PinGlyphHandle): PinGlyphHandle;
        fromGlyph(glyph: GlyphHandle): PinGlyphHandle;
        getNotePosition(self: PinGlyphHandle): NotePosition;
        getNoteType(self: PinGlyphHandle): NoteType;
        isInline(self: PinGlyphHandle): boolean;
        isNote(self: PinGlyphHandle): boolean;
    }
    export const PinGlyphApi: PinGlyphApi;

    export interface RangenoteBodyGlyphApi extends Omit<FieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: RangenoteBodyGlyphHandle): RangenoteBodyGlyphHandle;
        cloneAsRangenoteBodyGlyph(self: RangenoteBodyGlyphHandle): RangenoteBodyGlyphHandle;
        fromGlyph(glyph: GlyphHandle): RangenoteBodyGlyphHandle;
        isLive(self: RangenoteBodyGlyphHandle): boolean;
    }
    export const RangenoteBodyGlyphApi: RangenoteBodyGlyphApi;

    export interface RangenoteEndGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: RangenoteEndGlyphHandle): RangenoteEndGlyphHandle;
        cloneAsRangenoteEndGlyph(self: RangenoteEndGlyphHandle): RangenoteEndGlyphHandle;
        fromGlyph(glyph: GlyphHandle): RangenoteEndGlyphHandle;
        isLive(self: RangenoteEndGlyphHandle): boolean;
    }
    export const RangenoteEndGlyphApi: RangenoteEndGlyphApi;

    export interface RangenoteReferenceGlyphApi extends Omit<FieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: RangenoteReferenceGlyphHandle): RangenoteReferenceGlyphHandle;
        cloneAsRangenoteReferenceGlyph(self: RangenoteReferenceGlyphHandle): RangenoteReferenceGlyphHandle;
        fromGlyph(glyph: GlyphHandle): RangenoteReferenceGlyphHandle;
        getNotePosition(self: RangenoteReferenceGlyphHandle): NotePosition;
        getNoteType(self: RangenoteReferenceGlyphHandle): NoteType;
    }
    export const RangenoteReferenceGlyphApi: RangenoteReferenceGlyphApi;

    export interface RightIndentTabGlyphApi extends Omit<GlyphApi, "clone"> {
        clone(self: RightIndentTabGlyphHandle): RightIndentTabGlyphHandle;
        cloneAsRightIndentTabGlyph(self: RightIndentTabGlyphHandle): RightIndentTabGlyphHandle;
        fromGlyph(glyph: GlyphHandle): RightIndentTabGlyphHandle;
    }
    export const RightIndentTabGlyphApi: RightIndentTabGlyphApi;

    export interface RunningHeaderGlyphApi extends Omit<FormattableFieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: RunningHeaderGlyphHandle): RunningHeaderGlyphHandle;
        cloneAsRunningHeaderGlyph(self: RunningHeaderGlyphHandle): RunningHeaderGlyphHandle;
        fromGlyph(glyph: GlyphHandle): RunningHeaderGlyphHandle;
    }
    export const RunningHeaderGlyphApi: RunningHeaderGlyphApi;

    export interface SectionNameGlyphApi extends Omit<FieldGlyphApi, "clone" | "fromGlyph"> {
        clone(self: SectionNameGlyphHandle): SectionNameGlyphHandle;
        cloneAsSectionNameGlyph(self: SectionNameGlyphHandle): SectionNameGlyphHandle;
        fromGlyph(glyph: GlyphHandle): SectionNameGlyphHandle;
    }
    export const SectionNameGlyphApi: SectionNameGlyphApi;

    export interface StoryApi {
        containsBookEndnotes(self: StoryHandle): boolean;
        containsIndex(self: StoryHandle): boolean;
        containsToc(self: StoryHandle): boolean;
        findParagraphBreak(self: StoryHandle, startPos: number, maxNum: number): number;
        findWordBegin(self: StoryHandle, startPos: number, maxNum: number): number;
        findWordEnd(self: StoryHandle, startPos: number, maxNum: number): number;
        findWordPart(self: StoryHandle, startPos: number, maxNum: number): number;
        getGlyph(self: StoryHandle, pos: number): GlyphHandle;
        getGlyphAtts(self: StoryHandle, pos: number): GlyphAttsHandle;
        getGlyphAttsRunEnd(self: StoryHandle, pos: number, maxPos: number): number;
        getGlyphType(self: StoryHandle, pos: number): GlyphType;
        getHardBreakType(self: StoryHandle, pos: number): HardBreakType;
        getLength(self: StoryHandle): number;
        getParagraphAtts(self: StoryHandle, pos: number): ParagraphAttsHandle;
        getParagraphAttsRunEnd(self: StoryHandle, pos: number, maxPos: number): number;
        getSoftBreakType(self: StoryHandle, pos: number): SoftBreakType;
        getText(self: StoryHandle, storyPos: number, maxNum: number, format: StoryIoFormat): string;
        getWordPartType(self: StoryHandle, pos: number): WordPartType;
        isCellBegin(self: StoryHandle, pos: number): boolean;
        isCellEnd(self: StoryHandle, pos: number): boolean;
        isEmpty(self: StoryHandle): boolean;
        isParagraphBreak(self: StoryHandle, pos: number): boolean;
        isRangenoteBodyStory(self: StoryHandle): boolean;
        isTable(self: StoryHandle): boolean;
        isWordBegin(self: StoryHandle, pos: number): boolean;
        isWordEnd(self: StoryHandle, pos: number): boolean;
        isWordPart(self: StoryHandle, pos: number): boolean;
        rFindParagraphBreak(self: StoryHandle, startPos: number, maxNum: number): number;
        rFindWordBegin(self: StoryHandle, startPos: number, maxNum: number): number;
        rFindWordEnd(self: StoryHandle, startPos: number, maxNum: number): number;
        rFindWordPart(self: StoryHandle, startPos: number, maxNum: number): number;
        usesGlobalNumbering(self: StoryHandle): boolean;
    }
    export const StoryApi: StoryApi;

    export interface StoryBuilderApi {
        addParagraphBreak(self: StoryBuilderHandle): void;
        addText(self: StoryBuilderHandle, utf8Text: string): void;
        applyGlyphDelta(self: StoryBuilderHandle, delta: StoryDeltaHandle): void;
        applyParagraphDelta(self: StoryBuilderHandle, delta: StoryDeltaHandle): void;
        clearText(self: StoryBuilderHandle): void;
        create(): StoryBuilderHandle;
        getGlyphAtts(self: StoryBuilderHandle): GlyphAttsHandle;
        getParagraphAtts(self: StoryBuilderHandle): ParagraphAttsHandle;
        setGlyphAtts(self: StoryBuilderHandle, glyphAtts: GlyphAttsHandle): void;
        setParagraphAtts(self: StoryBuilderHandle, paragraphAtts: ParagraphAttsHandle): void;
        setToArtisticTextDefaultStyle(self: StoryBuilderHandle, dpi: number, format: RasterFormat): void;
        setToFrameTextDefaultStyle(self: StoryBuilderHandle, dpi: number, format: RasterFormat): void;
    }
    export const StoryBuilderApi: StoryBuilderApi;

    export interface StoryDeltaApi {
        createAlignToBaselineGridDelta(value: boolean): StoryDeltaHandle;
        createAlignXDelta(type: ParagraphAlignXType): StoryDeltaHandle;
        createBrushFillDelta(fillDescriptorOrNull: FillDescriptorHandle | null): StoryDeltaHandle;
        createCapsTypeDelta(type: CapsType): StoryDeltaHandle;
        createCompositeDelta(deltas: StoryDeltaHandle[]): StoryDeltaHandle;
        createFamilyNameDelta(familyName: string): StoryDeltaHandle;
        createFontDelta(fields: FontField, font: FontHandle): StoryDeltaHandle;
        createGlyphDoubleDelta(key: GlyphAttDoubleType, value: number): StoryDeltaHandle;
        createGlyphLineStyleDescriptorDelta(lineStyleDescriptor: LineStyleDescriptorHandle): StoryDeltaHandle;
        createGlyphStringDelta(key: GlyphAttStringType, value: string): StoryDeltaHandle;
        createHighlightFillDelta(fillDescriptorOrNull: FillDescriptorHandle | null): StoryDeltaHandle;
        createHyphenateMinLengthDelta(value: number): StoryDeltaHandle;
        createHyphenateMinPrefixDelta(value: number): StoryDeltaHandle;
        createHyphenateMinSuffixDelta(value: number): StoryDeltaHandle;
        createIsAutoHyphenateDelta(value: boolean): StoryDeltaHandle;
        createIsKeepTogetherDelta(value: boolean): StoryDeltaHandle;
        createIsKeepWithPreviousDelta(value: boolean): StoryDeltaHandle;
        createIsNoBreakDelta(isNoBreak: boolean): StoryDeltaHandle;
        createIsPreventOrphansDelta(value: boolean): StoryDeltaHandle;
        createIsPreventWidowsDelta(value: boolean): StoryDeltaHandle;
        createIsSumBeforeAndAfterSpaceDelta(value: boolean): StoryDeltaHandle;
        createItalicDelta(italic: boolean): StoryDeltaHandle;
        createKeepWithNextDelta(value: number): StoryDeltaHandle;
        createLeadingOverrideTypeDelta(type: LeadingOverrideType): StoryDeltaHandle;
        createLeadingTypeDelta(type: ParagraphLeadingType): StoryDeltaHandle;
        createLeftIndentDelta(value: number): StoryDeltaHandle;
        createLineBreakModeDelta(mode: ParagraphLineBreakModeType): StoryDeltaHandle;
        createMaxConsecutiveHyphensDelta(value: number): StoryDeltaHandle;
        createOpenTypeLanguageTagDelta(tag: number): StoryDeltaHandle;
        createOpenTypeScriptTagDelta(tag: number): StoryDeltaHandle;
        createOpticalAlignmentTypeDelta(type: OpticalAlignmentType): StoryDeltaHandle;
        createPDFExportTagDelta(type: ParagraphPDFExportTagType): StoryDeltaHandle;
        createParagraphDoubleDelta(key: ParagraphAttDoubleType, value: number): StoryDeltaHandle;
        createParagraphStringDelta(key: ParagraphAttStringType, value: string): StoryDeltaHandle;
        createPenFillDelta(fillDescriptorOrNull: FillDescriptorHandle | null): StoryDeltaHandle;
        createPostscriptNameDelta(postscriptName: string): StoryDeltaHandle;
        createRightIndentDelta(value: number): StoryDeltaHandle;
        createSetAttsDelta(glyphAttsOrNull: GlyphAttsHandle | null, paragraphAttsOrNull: ParagraphAttsHandle | null): StoryDeltaHandle;
        createStartAtHardBreakDelta(type: ParagraphStartAtHardBreakType): StoryDeltaHandle;
        createStrikeoutFillDelta(fillDescriptorOrNull: FillDescriptorHandle | null): StoryDeltaHandle;
        createStrikeoutTypeDelta(type: TypographicLineType): StoryDeltaHandle;
        createSuperSubTypeDelta(type: SuperSubType): StoryDeltaHandle;
        createTocRoleTypeDelta(type: TocRoleType): StoryDeltaHandle;
        createTransparencyDelta(fillDescriptorOrNull: FillDescriptorHandle | null): StoryDeltaHandle;
        createUnderlineFillDelta(fillDescriptorOrNull: FillDescriptorHandle | null): StoryDeltaHandle;
        createUnderlineTypeDelta(type: TypographicLineType): StoryDeltaHandle;
        createUseModernLeadingDelta(value: boolean): StoryDeltaHandle;
        createUseSpaceBeforeModeDelta(mode: ParagraphUseSpaceBeforeMode): StoryDeltaHandle;
        createUseSpaceBetweenSameStylesDelta(value: boolean): StoryDeltaHandle;
        createWeightDelta(weight: number): StoryDeltaHandle;
        createWidthDelta(width: FontWidth): StoryDeltaHandle;
    }
    export const StoryDeltaApi: StoryDeltaApi;

    export interface StoryRangeApi {
        getCount(range: StoryRange): number;
        getReversed(range: StoryRange): StoryRange;
        isBackwards(range: StoryRange): boolean;
        isEmpty(range: StoryRange): boolean;
        isForwards(range: StoryRange): boolean;
    }
    export const StoryRangeApi: StoryRangeApi;

}
