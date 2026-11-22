// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", its enums and classes (the APIs are in dom/).
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    import { Point } from "affinity:geometry";

    export enum AddNoiseType {
        Gaussian,
        Uniform,
    }

    export enum AntialiasingMode {
        Inherit,
        ForceOn,
        ForceOff,
    }

    export enum BaselineGridRelativeTo {
        TopOfSpread,
        TopOfPage,
        TopMargin,
        TopOfArtboard,
        TopArtboardMargin,
        TopOfFrame,
        TopInset,
    }

    export enum BloomMethod {
        Contrast,
        Bright,
    }

    export enum CompoundOperation {
        Union,
        Intersect,
        Subtract,
        Xor,
    }

    export enum ConstraintType {
        NotSizable,
        FixedMinX,
        ScaleWidth,
        FixedMaxX,
        FixedMinY,
        ScaleHeight,
        FixedMaxY,
        FixedAspectMin,
        FixedAspectMax,
        ForceAspectMin,
        ForceAspectMax,
        StretchToFit,
        NoScale,
        Default,
    }

    export enum ContentType {
        Main,
        Frame,
        Cell,
    }

    export enum DepthOfFieldMode {
        Elliptical,
        TiltShift,
    }

    export enum DevelopDetailRefinementMethod {
        UnsharpMask,
        HighPass,
        MultiBand,
    }

    export enum DevelopInvertMethod {
        InfraredRB,
        InfraredRGB,
        Negative,
    }

    export enum DevelopToneCurveMethod {
        Standard,
        Compressed,
        Natural,
        HighContrast,
        Log,
    }

    export enum DocumentLoadMode {
        Application,
        Spreads,
        Artboards,
    }

    export enum ExportScalePreset {
        Standard,
        Mult2x,
        Mult3x,
        Width100,
        Height50,
        Square64,
        Square64Mult2x,
        Width32Height32,
    }

    export enum ExportScaleSizeType {
        None,
        Width,
        Height,
        Square,
        WidthHeight,
    }

    export enum FileType {
        JPEG,
        PNG,
        TIFF,
        WEBP,
        HDPhoto,
        RAW,
        GIF,
        JPEG2000,
        BMP,
        TGA,
        OpenEXR,
        HDR,
        Unknown,
        Affinity,
        HEIF,
        FITS,
        Plugin,
    }

    export enum HalftoneDotType {
        Cosine,
        Round,
        Line,
    }

    export enum HalftoneScreenType {
        Mono,
        Colour,
        Line,
        Circular,
    }

    export enum ImagePlacement {
        Embedded,
        Linked,
    }

    export enum LoadDwgLayoutSelection {
        AllPages,
        Model,
        Single,
    }

    export enum NodeChildType {
        Main,
        Enclosure,
        MasterSpread,
        WrapShape,
        StoryPin,
    }

    export enum NodeMoveType {
        Before,
        After,
        Inside,
    }

    export enum PackageResourcesPolicy {
        None,
        IncludeImages,
        IncludeTexts,
        IncludeCSS,
        IncludeUnrestrictedFonts,
        IncludeRestrictedFonts,
    }

    export enum PageBoundingBoxType {
        MediaBox,
        CropBox,
        TrimBox,
        ArtBox,
        BleedBox,
        MinimumContent,
        MinimumVisibleContent,
        MaximumContent,
        MaximumVisibleContent,
    }

    export enum PredefinedTagKey {
        AltTextTag,
        AltTextSource,
        ExtDescTag,
        ExtDescSource,
        ScriptLabel,
    }

    export enum RasterFillMode {
        Colour,
        Foreground,
        Background,
        Inpainting,
        History,
    }

    export enum RasterFloodFillSamplingSource {
        CurrentLayer,
        CurrentLayerAndBelow,
        LayersBeneath,
    }

    export enum RasterSelectionLogicalOperation {
        New,
        Add,
        Subtract,
        Intersect,
    }

    export enum RasterSelectionOutlineAlignment {
        Outside,
        Centre,
        Inside,
    }

    export enum SamplingSource {
        CurrentLayer,
        AllLayers,
    }

    export enum SelectiveColour {
        Reds,
        Yellows,
        Greens,
        Cyans,
        Blues,
        Magentas,
        Whites,
        Neutrals,
        Blacks,
    }

    export enum ShadowsHighlightsVersion {
        Default,
        V16,
    }

    export enum SpatialAnchor {
        None,
        TopLeft,
        CentreLeft,
        BottomLeft,
        TopCentre,
        Centre,
        BottomCentre,
        TopRight,
        CentreRight,
        BottomRight,
        FocalPoint,
    }

    export enum SubSelectionType {
        CurveEdge,
        CurveNode,
        Text,
        Table,
        ExportFormat,
        Fill,
        LineFill,
        Transparency,
        FillMesh,
        LineFillMesh,
        TransparencyMesh,
        GeometryModifier,
        FillDiffusion,
    }

    export enum TableEdgeSelector {
        None,
        Left,
        Right,
        InnerColumns,
        Top,
        Bottom,
        InnerRows,
        OuterRows,
        Rows,
        OuterColumns,
        Columns,
        Inner,
        Border,
        All,
    }

    export enum TextDefaultType {
        Art,
        Frame,
        Unknown,
        Measurement,
    }

    export enum TextFlowOverflowState {
        Unknown,
        None,
        Safe,
        Warn,
    }

    export enum TonalRangeType {
        Shadows,
        Midtones,
        Highlights,
    }

    export enum ToneCompressionMethod {
        Basic,
        Natural,
        Bright,
        Contrast,
        Filmic,
        Punchy,
        PBRNeutral,
        Log,
    }

    export enum ToneStretchMethod {
        Basic,
        Arcsinh,
        Logarithmic,
        Structural,
        ColourPreserving,
    }

    export enum VisibilityMode {
        Main,
        Export,
    }

    export class ColourBalanceValues {
        cyanRed: number;
        magentaGreen: number;
        yellowBlue: number;
    }

    export class CurveEdgeSubSelectionItem {
        curveID: number;
        edgeID: number;
    }

    export class CurveNodeSubSelectionItem {
        curveID: number;
        nodeID: number;
    }

    export class DocumentLoadResult {
        document: DocumentHandle;
        description: string;
    }

    export class EllipticalDepthOfFieldParameters {
        position: Point;
        radiusX: number;
        radiusY: number;
        inFocus: number;
        rotation: number;
    }

    export class FieldBlurItemParameters {
        position: Point;
        level: number;
        power: number;
    }

    export class FocalPoint {
        point: Point;
        isValid: boolean;
    }

    export class HSLShiftAdjustmentChannelParameters {
        hueShift: number;
        saturationShift: number;
        luminosityShift: number;
    }

    export class HSLShiftAdjustmentColourRange {
        rampUpBegin: number;
        rampUpEnd: number;
        rampDownBegin: number;
        rampDownEnd: number;
    }

    export class LTRB {
        left: number;
        top: number;
        right: number;
        bottom: number;
    }

    export class LevelsAdjustmentChannelParameters {
        blackLevel: number;
        whiteLevel: number;
        gamma: number;
        outputBlackLevel: number;
        outputWhiteLevel: number;
    }

    export class LineDescriptors {
        fill: FillDescriptorHandle;
        lineStyle: LineStyleDescriptorHandle;
    }

    export class MeshSubSelectionItem {
        x: number;
        y: number;
    }

    export class PageOriginDelta {
        x: number;
        y: number;
    }

    export class SelectiveColourWeights {
        cyanWeight: number;
        magentaWeight: number;
        yellowWeight: number;
        blackWeight: number;
    }

    export class TiltShiftDepthOfFieldParameters {
        position: Point;
        top: number;
        bottom: number;
        inFocusTop: number;
        inFocusBottom: number;
        rotation: number;
    }

}
