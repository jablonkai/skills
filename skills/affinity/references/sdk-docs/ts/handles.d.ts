// Type declarations for the Affinity JavaScript SDK.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. Re-run the script when the SDK changes.
//
// Layout
//  - Handles are opaque values returned by the SDK. They are never required
//    or constructed from JavaScript, so they are declared once, globally, at
//    the top of the file. Each handle interface has one read-only marker
//    property named after itself. The marker never exists at runtime; it only
//    makes handle types distinct to the compiler. A handle with a "base" in
//    handles.json `extends` that base, so it also carries the base's marker
//    and is accepted wherever the base is expected.
//  - Everything else is a runtime export of an "affinity:<module>" module,
//    so it is declared inside the matching `declare module` block. This
//    makes both of these type-check:
//        const { PageBoxInterfaceApi } = require("affinity:dom");
//        import { PageBoxInterfaceApi } from "affinity:dom";
//    Types that live in another module are imported at the top of the block.
//  - Classes are `class` declarations: one field per variable, then any
//    methods. Constructors are not declared yet; they will be added once
//    the SDK description includes them. A class marked "boundOnly" (its
//    inputs must be real instances, not just objects of the same shape) gets
//    a `#private;` member, which makes TypeScript compare it nominally.
//  - Enums are `enum` declarations listing the item names only.
//  - APIs are an `interface` with one method per API method, plus a `const`
//    of that type, which is the object scripts actually call. An API with a
//    "base" in its JSON `extends` that base API's interface, so the inherited
//    methods are available on it. A method the derived API declares itself
//    replaces the inherited one, exactly as on the JavaScript prototype
//    chain, so such names are removed from the base with `Omit` first.
//    Methods with no return value return `void`.
//  - Union types (JSON "A|B") are written `A | B`.
//  - Parameters whose name ends in "OrNull" also accept `null`.
//  - Callback parameters are inline function types, such as
//    `(node: NodeHandle) => EnumerationResult`: the arguments the SDK passes
//    to the function, and what it should return. Asynchronous callbacks are
//    Node.js style, `(err: Error | null, result: XHandle | null) => void`.
//    A callback whose signature the SDK description doesn't give is the
//    built-in `Function`.
//  - The declarations are a set of files: this one holds the global handles,
//    each module has a <module>.d.ts, and a module too big for one file has
//    its enums and classes in <module>.d.ts and each API in <module>/<Api>.d.ts.
//    Blocks of the same `declare module` merge, so load the files together.

// ---------------------------------------------------------------------------
// Handles
// ---------------------------------------------------------------------------

interface AddChildNodesCommandBuilderHandle { readonly __AddChildNodesCommandBuilderHandle: true; }
interface AddNoiseFilterParametersHandle { readonly __AddNoiseFilterParametersHandle: true; }
interface AddNoiseFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __AddNoiseFilterRasterNodeDefinitionHandle: true; }
interface AddNoiseFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __AddNoiseFilterRasterNodeHandle: true; }
interface AdjustmentRasterNodeDefinitionHandle extends EnclosureRasterNodeDefinitionHandle { readonly __AdjustmentRasterNodeDefinitionHandle: true; }
interface AdjustmentRasterNodeHandle extends EnclosureRasterNodeHandle { readonly __AdjustmentRasterNodeHandle: true; }
interface AnchorGlyphHandle extends GlyphHandle { readonly __AnchorGlyphHandle: true; }
interface ArrowHeadHandle { readonly __ArrowHeadHandle: true; }
interface ArtTextNodeDefinitionHandle extends TextNodeDefinitionHandle { readonly __ArtTextNodeDefinitionHandle: true; }
interface ArtTextNodeHandle extends TextNodeHandle { readonly __ArtTextNodeHandle: true; }
interface ArtboardDocumentPropertiesHandle { readonly __ArtboardDocumentPropertiesHandle: true; }
interface ArtboardInterfaceHandle { readonly __ArtboardInterfaceHandle: true; }
interface ArtboardPropertiesHandle { readonly __ArtboardPropertiesHandle: true; }
interface BaseBoxInterfaceHandle { readonly __BaseBoxInterfaceHandle: true; }
interface BaselineGridInterfaceHandle { readonly __BaselineGridInterfaceHandle: true; }
interface BaselineGridOptionsHandle { readonly __BaselineGridOptionsHandle: true; }
interface BevelEmbossLayerEffectHandle extends LayerEffectHandle { readonly __BevelEmbossLayerEffectHandle: true; }
interface BilateralBlurFilterParametersHandle { readonly __BilateralBlurFilterParametersHandle: true; }
interface BilateralBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __BilateralBlurFilterRasterNodeDefinitionHandle: true; }
interface BilateralBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __BilateralBlurFilterRasterNodeHandle: true; }
interface BitmapFillHandle extends FillHandle { readonly __BitmapFillHandle: true; }
interface BlackAndWhiteAdjustmentParametersHandle { readonly __BlackAndWhiteAdjustmentParametersHandle: true; }
interface BlackAndWhiteAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __BlackAndWhiteAdjustmentRasterNodeDefinitionHandle: true; }
interface BlackAndWhiteAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __BlackAndWhiteAdjustmentRasterNodeHandle: true; }
interface BlendModeInterfaceHandle { readonly __BlendModeInterfaceHandle: true; }
interface BlendOptionsHandle { readonly __BlendOptionsHandle: true; }
interface BloomFilterParametersHandle { readonly __BloomFilterParametersHandle: true; }
interface BloomFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __BloomFilterRasterNodeDefinitionHandle: true; }
interface BloomFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __BloomFilterRasterNodeHandle: true; }
interface BoxBlurFilterParametersHandle { readonly __BoxBlurFilterParametersHandle: true; }
interface BoxBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __BoxBlurFilterRasterNodeDefinitionHandle: true; }
interface BoxBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __BoxBlurFilterRasterNodeHandle: true; }
interface BrightnessContrastAdjustmentParametersHandle { readonly __BrightnessContrastAdjustmentParametersHandle: true; }
interface BrightnessContrastAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __BrightnessContrastAdjustmentRasterNodeDefinitionHandle: true; }
interface BrightnessContrastAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __BrightnessContrastAdjustmentRasterNodeHandle: true; }
interface BrushDynamicHandle { readonly __BrushDynamicHandle: true; }
interface BrushFillInterfaceHandle { readonly __BrushFillInterfaceHandle: true; }
interface BufferHandle { readonly __BufferHandle: true; }
interface CapturedDateTimeGlyphHandle extends FormattableFieldGlyphHandle { readonly __CapturedDateTimeGlyphHandle: true; }
interface CharGlyphHandle extends GlyphHandle { readonly __CharGlyphHandle: true; }
interface ClarityFilterParametersHandle { readonly __ClarityFilterParametersHandle: true; }
interface ClarityFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __ClarityFilterRasterNodeDefinitionHandle: true; }
interface ClarityFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __ClarityFilterRasterNodeHandle: true; }
interface ColourBalanceAdjustmentParametersHandle { readonly __ColourBalanceAdjustmentParametersHandle: true; }
interface ColourBalanceAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __ColourBalanceAdjustmentRasterNodeDefinitionHandle: true; }
interface ColourBalanceAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __ColourBalanceAdjustmentRasterNodeHandle: true; }
interface ColourHandle { readonly __ColourHandle: true; }
interface ColourMeshHandle extends MeshHandle { readonly __ColourMeshHandle: true; }
interface ColourOverlayLayerEffectHandle extends LayerEffectHandle { readonly __ColourOverlayLayerEffectHandle: true; }
interface ColourProfileHandle { readonly __ColourProfileHandle: true; }
interface ColourProfileSetHandle { readonly __ColourProfileSetHandle: true; }
interface ColouredLogicalNodeDefinitionHandle extends LogicalNodeDefinitionHandle { readonly __ColouredLogicalNodeDefinitionHandle: true; }
interface ColouredLogicalNodeHandle extends LogicalNodeHandle { readonly __ColouredLogicalNodeHandle: true; }
interface CommandHandle { readonly __CommandHandle: true; }
interface CompoundCommandBuilderHandle { readonly __CompoundCommandBuilderHandle: true; }
interface CompoundOperationInterfaceHandle { readonly __CompoundOperationInterfaceHandle: true; }
interface ConfigurationItemHandle { readonly __ConfigurationItemHandle: true; }
interface ContainerNodeDefinitionHandle extends ColouredLogicalNodeDefinitionHandle { readonly __ContainerNodeDefinitionHandle: true; }
interface ContainerNodeHandle extends ColouredLogicalNodeHandle { readonly __ContainerNodeHandle: true; }
interface CrossReferenceGlyphHandle extends FieldGlyphHandle { readonly __CrossReferenceGlyphHandle: true; }
interface CrossReferenceSubGlyphHandle extends GlyphHandle { readonly __CrossReferenceSubGlyphHandle: true; }
interface CurveBuilderHandle { readonly __CurveBuilderHandle: true; }
interface CurveEdgeSubSelectionHandle extends SubSelectionHandle { readonly __CurveEdgeSubSelectionHandle: true; }
interface CurveHandle { readonly __CurveHandle: true; }
interface CurveNodeSubSelectionHandle extends SubSelectionHandle { readonly __CurveNodeSubSelectionHandle: true; }
interface CurvePathTextNodeDefinitionHandle extends TextNodeDefinitionHandle { readonly __CurvePathTextNodeDefinitionHandle: true; }
interface CurvePathTextNodeHandle extends TextNodeHandle { readonly __CurvePathTextNodeHandle: true; }
interface CurvesAdjustmentParametersHandle { readonly __CurvesAdjustmentParametersHandle: true; }
interface CurvesAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __CurvesAdjustmentRasterNodeDefinitionHandle: true; }
interface CurvesAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __CurvesAdjustmentRasterNodeHandle: true; }
interface CurvesInterfaceHandle { readonly __CurvesInterfaceHandle: true; }
interface CustomFieldGlyphHandle extends FormattableFieldGlyphHandle { readonly __CustomFieldGlyphHandle: true; }
interface DataMergeFieldGlyphHandle extends DataMergeGlyphHandle { readonly __DataMergeFieldGlyphHandle: true; }
interface DataMergeGlyphHandle extends FormattableFieldGlyphHandle { readonly __DataMergeGlyphHandle: true; }
interface DataMergeSourceGlyphHandle extends DataMergeGlyphHandle { readonly __DataMergeSourceGlyphHandle: true; }
interface DefringeFilterParametersHandle { readonly __DefringeFilterParametersHandle: true; }
interface DefringeFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __DefringeFilterRasterNodeDefinitionHandle: true; }
interface DefringeFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __DefringeFilterRasterNodeHandle: true; }
interface DenoiseFilterParametersHandle { readonly __DenoiseFilterParametersHandle: true; }
interface DenoiseFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __DenoiseFilterRasterNodeDefinitionHandle: true; }
interface DenoiseFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __DenoiseFilterRasterNodeHandle: true; }
interface DepthOfFieldFilterParametersHandle { readonly __DepthOfFieldFilterParametersHandle: true; }
interface DepthOfFieldFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __DepthOfFieldFilterRasterNodeDefinitionHandle: true; }
interface DepthOfFieldFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __DepthOfFieldFilterRasterNodeHandle: true; }
interface DescriptionInterfaceHandle { readonly __DescriptionInterfaceHandle: true; }
interface DevelopNodeHandle extends PhysicalNodeHandle { readonly __DevelopNodeHandle: true; }
interface DevelopParametersHandle { readonly __DevelopParametersHandle: true; }
interface DialogBoolControlHandle extends DialogControlHandle { readonly __DialogBoolControlHandle: true; }
interface DialogButtonHandle extends DialogControlHandle { readonly __DialogButtonHandle: true; }
interface DialogButtonSetHandle extends DialogEnumControlHandle { readonly __DialogButtonSetHandle: true; }
interface DialogCheckBoxHandle extends DialogBoolControlHandle { readonly __DialogCheckBoxHandle: true; }
interface DialogColourPickerHandle extends DialogControlHandle { readonly __DialogColourPickerHandle: true; }
interface DialogColumnHandle extends DialogItemHandle { readonly __DialogColumnHandle: true; }
interface DialogColumnStackHandle extends DialogItemHandle { readonly __DialogColumnStackHandle: true; }
interface DialogComboBoxHandle extends DialogEnumControlHandle { readonly __DialogComboBoxHandle: true; }
interface DialogControlHandle extends DialogItemHandle { readonly __DialogControlHandle: true; }
interface DialogEnumControlHandle extends DialogControlHandle { readonly __DialogEnumControlHandle: true; }
interface DialogFillEditorHandle extends DialogControlHandle { readonly __DialogFillEditorHandle: true; }
interface DialogFontPickerHandle extends DialogControlHandle { readonly __DialogFontPickerHandle: true; }
interface DialogGroupHandle extends DialogItemHandle { readonly __DialogGroupHandle: true; }
interface DialogHandle { readonly __DialogHandle: true; }
interface DialogItemHandle { readonly __DialogItemHandle: true; }
interface DialogRadioGroupHandle extends DialogEnumControlHandle { readonly __DialogRadioGroupHandle: true; }
interface DialogSpatialAnchorHandle extends DialogControlHandle { readonly __DialogSpatialAnchorHandle: true; }
interface DialogStaticTextHandle extends DialogTextControlHandle { readonly __DialogStaticTextHandle: true; }
interface DialogStrokeEditorHandle extends DialogControlHandle { readonly __DialogStrokeEditorHandle: true; }
interface DialogSwitchHandle extends DialogBoolControlHandle { readonly __DialogSwitchHandle: true; }
interface DialogTextBoxHandle extends DialogTextControlHandle { readonly __DialogTextBoxHandle: true; }
interface DialogTextControlHandle extends DialogControlHandle { readonly __DialogTextControlHandle: true; }
interface DialogUnitValueEditorHandle extends DialogControlHandle { readonly __DialogUnitValueEditorHandle: true; }
interface DiffuseFilterParametersHandle { readonly __DiffuseFilterParametersHandle: true; }
interface DiffuseFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __DiffuseFilterRasterNodeDefinitionHandle: true; }
interface DiffuseFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __DiffuseFilterRasterNodeHandle: true; }
interface DiffuseGlowFilterParametersHandle { readonly __DiffuseGlowFilterParametersHandle: true; }
interface DiffuseGlowFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __DiffuseGlowFilterRasterNodeDefinitionHandle: true; }
interface DiffuseGlowFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __DiffuseGlowFilterRasterNodeHandle: true; }
interface DiffusionCurveSetHandle { readonly __DiffusionCurveSetHandle: true; }
interface DiffusionFillHandle extends FillHandle { readonly __DiffusionFillHandle: true; }
interface DirectoryIteratorHandle { readonly __DirectoryIteratorHandle: true; }
interface DocumentCommandHandle extends CommandHandle { readonly __DocumentCommandHandle: true; }
interface DocumentExportRecordHandle { readonly __DocumentExportRecordHandle: true; }
interface DocumentExportRecordsHandle { readonly __DocumentExportRecordsHandle: true; }
interface DocumentFieldGlyphHandle extends FormattableFieldGlyphHandle { readonly __DocumentFieldGlyphHandle: true; }
interface DocumentHandle { readonly __DocumentHandle: true; }
interface DocumentHistoryHandle { readonly __DocumentHistoryHandle: true; }
interface DocumentHistoryItemHandle { readonly __DocumentHistoryItemHandle: true; }
interface DocumentNodeHandle extends LogicalNodeHandle { readonly __DocumentNodeHandle: true; }
interface DocumentPresetHandle { readonly __DocumentPresetHandle: true; }
interface DocumentPropertiesHandle { readonly __DocumentPropertiesHandle: true; }
interface DocumentSnapshotHandle { readonly __DocumentSnapshotHandle: true; }
interface DocumentViewHandle { readonly __DocumentViewHandle: true; }
interface DrawingScaleHandle { readonly __DrawingScaleHandle: true; }
interface DustAndScratchFilterParametersHandle { readonly __DustAndScratchFilterParametersHandle: true; }
interface DustAndScratchFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __DustAndScratchFilterRasterNodeDefinitionHandle: true; }
interface DustAndScratchFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __DustAndScratchFilterRasterNodeHandle: true; }
interface EditabilityInterfaceHandle { readonly __EditabilityInterfaceHandle: true; }
interface EmbeddedDocumentNodeHandle extends PhysicalNodeHandle { readonly __EmbeddedDocumentNodeHandle: true; }
interface EnclosureRasterNodeDefinitionHandle extends RasterNodeDefinitionHandle { readonly __EnclosureRasterNodeDefinitionHandle: true; }
interface EnclosureRasterNodeHandle extends RasterNodeHandle { readonly __EnclosureRasterNodeHandle: true; }
interface ExportConfigHandle { readonly __ExportConfigHandle: true; }
interface ExportFormatHandle { readonly __ExportFormatHandle: true; }
interface ExportScaleHandle { readonly __ExportScaleHandle: true; }
interface ExportSizeHandle { readonly __ExportSizeHandle: true; }
interface ExportableInterfaceHandle { readonly __ExportableInterfaceHandle: true; }
interface ExposureAdjustmentParametersHandle { readonly __ExposureAdjustmentParametersHandle: true; }
interface ExposureAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __ExposureAdjustmentRasterNodeDefinitionHandle: true; }
interface ExposureAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __ExposureAdjustmentRasterNodeHandle: true; }
interface FieldBlurFilterParametersHandle { readonly __FieldBlurFilterParametersHandle: true; }
interface FieldBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __FieldBlurFilterRasterNodeDefinitionHandle: true; }
interface FieldBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __FieldBlurFilterRasterNodeHandle: true; }
interface FieldGlyphHandle extends GlyphHandle { readonly __FieldGlyphHandle: true; }
interface FileExportAreaHandle { readonly __FileExportAreaHandle: true; }
interface FileExportOptionsHandle { readonly __FileExportOptionsHandle: true; }
interface FileHandle { readonly __FileHandle: true; }
interface FileStatusHandle { readonly __FileStatusHandle: true; }
interface FillDescriptorHandle { readonly __FillDescriptorHandle: true; }
interface FillHandle { readonly __FillHandle: true; }
interface FillMeshSubSelectionHandle extends SubSelectionHandle { readonly __FillMeshSubSelectionHandle: true; }
interface FillSubSelectionHandle extends SubSelectionHandle { readonly __FillSubSelectionHandle: true; }
interface FillerTextGlyphHandle extends FieldGlyphHandle { readonly __FillerTextGlyphHandle: true; }
interface FilterRasterNodeDefinitionHandle extends EnclosureRasterNodeDefinitionHandle { readonly __FilterRasterNodeDefinitionHandle: true; }
interface FilterRasterNodeHandle extends EnclosureRasterNodeHandle { readonly __FilterRasterNodeHandle: true; }
interface FontCollectionHandle { readonly __FontCollectionHandle: true; }
interface FontFamilyHandle { readonly __FontFamilyHandle: true; }
interface FontHandle { readonly __FontHandle: true; }
interface FormattableFieldGlyphHandle extends FieldGlyphHandle { readonly __FormattableFieldGlyphHandle: true; }
interface FrameTextNodeDefinitionHandle extends TextNodeDefinitionHandle { readonly __FrameTextNodeDefinitionHandle: true; }
interface FrameTextNodeHandle extends TextNodeHandle { readonly __FrameTextNodeHandle: true; }
interface GaussianBlurFilterParametersHandle { readonly __GaussianBlurFilterParametersHandle: true; }
interface GaussianBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __GaussianBlurFilterRasterNodeDefinitionHandle: true; }
interface GaussianBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __GaussianBlurFilterRasterNodeHandle: true; }
interface GaussianBlurLayerEffectHandle extends LayerEffectHandle { readonly __GaussianBlurLayerEffectHandle: true; }
interface GlyphAttsHandle { readonly __GlyphAttsHandle: true; }
interface GlyphHandle { readonly __GlyphHandle: true; }
interface GlyphIndexGlyphHandle extends GlyphHandle { readonly __GlyphIndexGlyphHandle: true; }
interface GradientFillHandle extends FillHandle { readonly __GradientFillHandle: true; }
interface GradientHandle { readonly __GradientHandle: true; }
interface GradientOverlayLayerEffectHandle extends LayerEffectHandle { readonly __GradientOverlayLayerEffectHandle: true; }
interface GroupNodeHandle extends LogicalNodeHandle { readonly __GroupNodeHandle: true; }
interface HSLShiftAdjustmentParametersHandle { readonly __HSLShiftAdjustmentParametersHandle: true; }
interface HSLShiftAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __HSLShiftAdjustmentRasterNodeDefinitionHandle: true; }
interface HSLShiftAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __HSLShiftAdjustmentRasterNodeHandle: true; }
interface HalftoneFilterParametersHandle { readonly __HalftoneFilterParametersHandle: true; }
interface HalftoneFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __HalftoneFilterRasterNodeDefinitionHandle: true; }
interface HalftoneFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __HalftoneFilterRasterNodeHandle: true; }
interface HardBreakGlyphHandle extends GlyphHandle { readonly __HardBreakGlyphHandle: true; }
interface HatchFillHandle extends FillHandle { readonly __HatchFillHandle: true; }
interface HatchLineHandle { readonly __HatchLineHandle: true; }
interface HatchPatternHandle { readonly __HatchPatternHandle: true; }
interface HighPassFilterParametersHandle { readonly __HighPassFilterParametersHandle: true; }
interface HighPassFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __HighPassFilterRasterNodeDefinitionHandle: true; }
interface HighPassFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __HighPassFilterRasterNodeHandle: true; }
interface HttpRequestHandle { readonly __HttpRequestHandle: true; }
interface HttpResponseHandle { readonly __HttpResponseHandle: true; }
interface ImageNodeDefinitionHandle extends VectorNodeDefinitionHandle { readonly __ImageNodeDefinitionHandle: true; }
interface ImageNodeHandle extends VectorNodeHandle { readonly __ImageNodeHandle: true; }
interface ImageResourceInterfaceHandle { readonly __ImageResourceInterfaceHandle: true; }
interface IndentToHereGlyphHandle extends GlyphHandle { readonly __IndentToHereGlyphHandle: true; }
interface IndexMarkGlyphHandle extends GlyphHandle { readonly __IndexMarkGlyphHandle: true; }
interface InnerGlowLayerEffectHandle extends LayerEffectHandle { readonly __InnerGlowLayerEffectHandle: true; }
interface InnerShadowLayerEffectHandle extends LayerEffectHandle { readonly __InnerShadowLayerEffectHandle: true; }
interface InvertAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __InvertAdjustmentRasterNodeDefinitionHandle: true; }
interface InvertAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __InvertAdjustmentRasterNodeHandle: true; }
interface LayerEffectHandle { readonly __LayerEffectHandle: true; }
interface LayerEffectsInterfaceHandle { readonly __LayerEffectsInterfaceHandle: true; }
interface LensBlurFilterParametersHandle { readonly __LensBlurFilterParametersHandle: true; }
interface LensBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __LensBlurFilterRasterNodeDefinitionHandle: true; }
interface LensBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __LensBlurFilterRasterNodeHandle: true; }
interface LevelsAdjustmentParametersHandle { readonly __LevelsAdjustmentParametersHandle: true; }
interface LevelsAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __LevelsAdjustmentRasterNodeDefinitionHandle: true; }
interface LevelsAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __LevelsAdjustmentRasterNodeHandle: true; }
interface LineFillMeshSubSelectionHandle extends SubSelectionHandle { readonly __LineFillMeshSubSelectionHandle: true; }
interface LineFillSubSelectionHandle extends SubSelectionHandle { readonly __LineFillSubSelectionHandle: true; }
interface LineStyleDescriptorHandle { readonly __LineStyleDescriptorHandle: true; }
interface LineStyleHandle { readonly __LineStyleHandle: true; }
interface LineStyleInterfaceHandle { readonly __LineStyleInterfaceHandle: true; }
interface ListNumberGlyphHandle extends GlyphHandle { readonly __ListNumberGlyphHandle: true; }
interface LoadDocumentOptionsHandle { readonly __LoadDocumentOptionsHandle: true; }
interface LoadDwgOptionsHandle extends LoadDocumentOptionsHandle { readonly __LoadDwgOptionsHandle: true; }
interface LocaleHandle { readonly __LocaleHandle: true; }
interface LogFileHandle { readonly __LogFileHandle: true; }
interface LogicalNodeDefinitionHandle extends NodeDefinitionHandle { readonly __LogicalNodeDefinitionHandle: true; }
interface LogicalNodeHandle extends NodeHandle { readonly __LogicalNodeHandle: true; }
interface MarginsInterfaceHandle { readonly __MarginsInterfaceHandle: true; }
interface MaskRasterNodeDefinitionHandle { readonly __MaskRasterNodeDefinitionHandle: true; }
interface MaskRasterNodeHandle extends EnclosureRasterNodeHandle { readonly __MaskRasterNodeHandle: true; }
interface MaximumBlurFilterParametersHandle { readonly __MaximumBlurFilterParametersHandle: true; }
interface MaximumBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __MaximumBlurFilterRasterNodeDefinitionHandle: true; }
interface MaximumBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __MaximumBlurFilterRasterNodeHandle: true; }
interface MeasurementNodeDefinitionHandle extends VectorNodeDefinitionHandle { readonly __MeasurementNodeDefinitionHandle: true; }
interface MeasurementNodeHandle extends VectorNodeHandle { readonly __MeasurementNodeHandle: true; }
interface MedianBlurFilterParametersHandle { readonly __MedianBlurFilterParametersHandle: true; }
interface MedianBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __MedianBlurFilterRasterNodeDefinitionHandle: true; }
interface MedianBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __MedianBlurFilterRasterNodeHandle: true; }
interface MeshFillHandle extends FillHandle { readonly __MeshFillHandle: true; }
interface MeshHandle { readonly __MeshHandle: true; }
interface MinimumBlurFilterParametersHandle { readonly __MinimumBlurFilterParametersHandle: true; }
interface MinimumBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __MinimumBlurFilterRasterNodeDefinitionHandle: true; }
interface MinimumBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __MinimumBlurFilterRasterNodeHandle: true; }
interface MotionBlurFilterParametersHandle { readonly __MotionBlurFilterParametersHandle: true; }
interface MotionBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __MotionBlurFilterRasterNodeDefinitionHandle: true; }
interface MotionBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __MotionBlurFilterRasterNodeHandle: true; }
interface NewDocumentOptionsHandle { readonly __NewDocumentOptionsHandle: true; }
interface NoFillHandle extends FillHandle { readonly __NoFillHandle: true; }
interface NodeCastHandle { readonly __NodeCastHandle: true; }
interface NodeDefinitionHandle { readonly __NodeDefinitionHandle: true; }
interface NodeHandle extends SelectableHandle { readonly __NodeHandle: true; }
interface NodeRenderingEngineOptionsHandle { readonly __NodeRenderingEngineOptionsHandle: true; }
interface NormalsAdjustmentParametersHandle { readonly __NormalsAdjustmentParametersHandle: true; }
interface NormalsAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __NormalsAdjustmentRasterNodeDefinitionHandle: true; }
interface NormalsAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __NormalsAdjustmentRasterNodeHandle: true; }
interface NoteNumberGlyphHandle extends GlyphHandle { readonly __NoteNumberGlyphHandle: true; }
interface OuterGlowLayerEffectHandle extends LayerEffectHandle { readonly __OuterGlowLayerEffectHandle: true; }
interface OuterShadowLayerEffectHandle extends LayerEffectHandle { readonly __OuterShadowLayerEffectHandle: true; }
interface OutlineLayerEffectHandle extends LayerEffectHandle { readonly __OutlineLayerEffectHandle: true; }
interface PageBoxInterfaceHandle { readonly __PageBoxInterfaceHandle: true; }
interface PageDocumentPropertiesHandle { readonly __PageDocumentPropertiesHandle: true; }
interface PageNumberGlyphHandle extends FieldGlyphHandle { readonly __PageNumberGlyphHandle: true; }
interface PanoseHandle { readonly __PanoseHandle: true; }
interface ParagraphAttsHandle { readonly __ParagraphAttsHandle: true; }
interface PathBrushHandle { readonly __PathBrushHandle: true; }
interface PatternRasterNodeDefinitionHandle extends RasterNodeDefinitionHandle { readonly __PatternRasterNodeDefinitionHandle: true; }
interface PatternRasterNodeHandle extends RasterNodeHandle { readonly __PatternRasterNodeHandle: true; }
interface PhongBevelLayerEffectHandle extends LayerEffectHandle { readonly __PhongBevelLayerEffectHandle: true; }
interface PhysicalNodeDefinitionHandle extends NodeDefinitionHandle { readonly __PhysicalNodeDefinitionHandle: true; }
interface PhysicalNodeHandle extends NodeHandle { readonly __PhysicalNodeHandle: true; }
interface PhysicalRootInterfaceHandle { readonly __PhysicalRootInterfaceHandle: true; }
interface PhysicalRootPropertiesInterfaceHandle { readonly __PhysicalRootPropertiesInterfaceHandle: true; }
interface PictureFrameInterfaceHandle { readonly __PictureFrameInterfaceHandle: true; }
interface PinGlyphHandle extends GlyphHandle { readonly __PinGlyphHandle: true; }
interface PinchPunchFilterParametersHandle { readonly __PinchPunchFilterParametersHandle: true; }
interface PinchPunchFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __PinchPunchFilterRasterNodeDefinitionHandle: true; }
interface PinchPunchFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __PinchPunchFilterRasterNodeHandle: true; }
interface PixelReaderCMYKA8Handle { readonly __PixelReaderCMYKA8Handle: true; }
interface PixelReaderIA16Handle { readonly __PixelReaderIA16Handle: true; }
interface PixelReaderIA8Handle { readonly __PixelReaderIA8Handle: true; }
interface PixelReaderLABA16Handle { readonly __PixelReaderLABA16Handle: true; }
interface PixelReaderM16Handle { readonly __PixelReaderM16Handle: true; }
interface PixelReaderM8Handle { readonly __PixelReaderM8Handle: true; }
interface PixelReaderMfHandle { readonly __PixelReaderMfHandle: true; }
interface PixelReaderRGBA16Handle { readonly __PixelReaderRGBA16Handle: true; }
interface PixelReaderRGBA8Handle { readonly __PixelReaderRGBA8Handle: true; }
interface PixelReaderRGBAufHandle { readonly __PixelReaderRGBAufHandle: true; }
interface PixelReaderWriterCMYKA8Handle { readonly __PixelReaderWriterCMYKA8Handle: true; }
interface PixelReaderWriterIA16Handle { readonly __PixelReaderWriterIA16Handle: true; }
interface PixelReaderWriterIA8Handle { readonly __PixelReaderWriterIA8Handle: true; }
interface PixelReaderWriterLABA16Handle { readonly __PixelReaderWriterLABA16Handle: true; }
interface PixelReaderWriterM16Handle { readonly __PixelReaderWriterM16Handle: true; }
interface PixelReaderWriterM8Handle { readonly __PixelReaderWriterM8Handle: true; }
interface PixelReaderWriterMfHandle { readonly __PixelReaderWriterMfHandle: true; }
interface PixelReaderWriterRGBA16Handle { readonly __PixelReaderWriterRGBA16Handle: true; }
interface PixelReaderWriterRGBA8Handle { readonly __PixelReaderWriterRGBA8Handle: true; }
interface PixelReaderWriterRGBAufHandle { readonly __PixelReaderWriterRGBAufHandle: true; }
interface PixelateFilterParametersHandle { readonly __PixelateFilterParametersHandle: true; }
interface PixelateFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __PixelateFilterRasterNodeDefinitionHandle: true; }
interface PixelateFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __PixelateFilterRasterNodeHandle: true; }
interface PointLightHandle { readonly __PointLightHandle: true; }
interface PolyCurveHandle { readonly __PolyCurveHandle: true; }
interface PolyCurveNodeDefinitionHandle extends VectorNodeDefinitionHandle { readonly __PolyCurveNodeDefinitionHandle: true; }
interface PolyCurveNodeHandle extends VectorNodeHandle { readonly __PolyCurveNodeHandle: true; }
interface PolyCurveTextNodeDefinitionHandle extends TextNodeDefinitionHandle { readonly __PolyCurveTextNodeDefinitionHandle: true; }
interface PolyCurveTextNodeHandle extends TextNodeHandle { readonly __PolyCurveTextNodeHandle: true; }
interface PolyPolyCurveHandle { readonly __PolyPolyCurveHandle: true; }
interface PolygonHandle { readonly __PolygonHandle: true; }
interface PosteriseAdjustmentParametersHandle { readonly __PosteriseAdjustmentParametersHandle: true; }
interface PosteriseAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __PosteriseAdjustmentRasterNodeDefinitionHandle: true; }
interface PosteriseAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __PosteriseAdjustmentRasterNodeHandle: true; }
interface QRPayloadDataMergeHandle extends QRPayloadHandle { readonly __QRPayloadDataMergeHandle: true; }
interface QRPayloadEmailHandle extends QRPayloadHandle { readonly __QRPayloadEmailHandle: true; }
interface QRPayloadFaceTimeHandle extends QRPayloadHandle { readonly __QRPayloadFaceTimeHandle: true; }
interface QRPayloadHandle { readonly __QRPayloadHandle: true; }
interface QRPayloadLocationHandle extends QRPayloadHandle { readonly __QRPayloadLocationHandle: true; }
interface QRPayloadPhoneHandle extends QRPayloadHandle { readonly __QRPayloadPhoneHandle: true; }
interface QRPayloadSMSHandle extends QRPayloadHandle { readonly __QRPayloadSMSHandle: true; }
interface QRPayloadTextHandle extends QRPayloadHandle { readonly __QRPayloadTextHandle: true; }
interface QRPayloadURLHandle extends QRPayloadHandle { readonly __QRPayloadURLHandle: true; }
interface QRPayloadVCardHandle extends QRPayloadHandle { readonly __QRPayloadVCardHandle: true; }
interface QRPayloadWhatsAppHandle extends QRPayloadHandle { readonly __QRPayloadWhatsAppHandle: true; }
interface QRPayloadWifiHandle extends QRPayloadHandle { readonly __QRPayloadWifiHandle: true; }
interface RadialBlurFilterParametersHandle { readonly __RadialBlurFilterParametersHandle: true; }
interface RadialBlurFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __RadialBlurFilterRasterNodeDefinitionHandle: true; }
interface RadialBlurFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __RadialBlurFilterRasterNodeHandle: true; }
interface RangenoteBodyGlyphHandle extends FieldGlyphHandle { readonly __RangenoteBodyGlyphHandle: true; }
interface RangenoteEndGlyphHandle extends GlyphHandle { readonly __RangenoteEndGlyphHandle: true; }
interface RangenoteReferenceGlyphHandle extends FieldGlyphHandle { readonly __RangenoteReferenceGlyphHandle: true; }
interface RasterBrushHandle { readonly __RasterBrushHandle: true; }
interface RasterInterfaceHandle { readonly __RasterInterfaceHandle: true; }
interface RasterNodeDefinitionHandle extends PhysicalNodeDefinitionHandle { readonly __RasterNodeDefinitionHandle: true; }
interface RasterNodeHandle extends PhysicalNodeHandle { readonly __RasterNodeHandle: true; }
interface RasterObjectHandle { readonly __RasterObjectHandle: true; }
interface RasterSelectionHandle { readonly __RasterSelectionHandle: true; }
interface RecolourAdjustmentParametersHandle { readonly __RecolourAdjustmentParametersHandle: true; }
interface RecolourAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __RecolourAdjustmentRasterNodeDefinitionHandle: true; }
interface RecolourAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __RecolourAdjustmentRasterNodeHandle: true; }
interface RefControlHandle { readonly __RefControlHandle: true; }
interface ResourceBundleHandle { readonly __ResourceBundleHandle: true; }
interface ResourceHandle { readonly __ResourceHandle: true; }
interface ResourceIteratorHandle { readonly __ResourceIteratorHandle: true; }
interface RightIndentTabGlyphHandle extends GlyphHandle { readonly __RightIndentTabGlyphHandle: true; }
interface RippleFilterParametersHandle { readonly __RippleFilterParametersHandle: true; }
interface RippleFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __RippleFilterRasterNodeDefinitionHandle: true; }
interface RippleFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __RippleFilterRasterNodeHandle: true; }
interface RunningHeaderGlyphHandle extends FormattableFieldGlyphHandle { readonly __RunningHeaderGlyphHandle: true; }
interface SectionNameGlyphHandle extends FieldGlyphHandle { readonly __SectionNameGlyphHandle: true; }
interface SelectableHandle { readonly __SelectableHandle: true; }
interface SelectionHandle { readonly __SelectionHandle: true; }
interface SelectionItemHandle { readonly __SelectionItemHandle: true; }
interface SelectiveColourAdjustmentParametersHandle { readonly __SelectiveColourAdjustmentParametersHandle: true; }
interface SelectiveColourAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __SelectiveColourAdjustmentRasterNodeDefinitionHandle: true; }
interface SelectiveColourAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __SelectiveColourAdjustmentRasterNodeHandle: true; }
interface SetHatchFillAttributesCommandBuilderHandle { readonly __SetHatchFillAttributesCommandBuilderHandle: true; }
interface ShadowsHighlightsAdjustmentParametersHandle { readonly __ShadowsHighlightsAdjustmentParametersHandle: true; }
interface ShadowsHighlightsAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __ShadowsHighlightsAdjustmentRasterNodeDefinitionHandle: true; }
interface ShadowsHighlightsAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __ShadowsHighlightsAdjustmentRasterNodeHandle: true; }
interface ShadowsHighlightsFilterParametersHandle { readonly __ShadowsHighlightsFilterParametersHandle: true; }
interface ShadowsHighlightsFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __ShadowsHighlightsFilterRasterNodeDefinitionHandle: true; }
interface ShadowsHighlightsFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __ShadowsHighlightsFilterRasterNodeHandle: true; }
interface ShapeArrowHandle extends ShapeHandle { readonly __ShapeArrowHandle: true; }
interface ShapeCalloutEllipseHandle extends ShapeHandle { readonly __ShapeCalloutEllipseHandle: true; }
interface ShapeCalloutRectangleHandle extends ShapeHandle { readonly __ShapeCalloutRectangleHandle: true; }
interface ShapeCat2Handle extends ShapeHandle { readonly __ShapeCat2Handle: true; }
interface ShapeCat3Handle extends ShapeHandle { readonly __ShapeCat3Handle: true; }
interface ShapeCat4Handle extends ShapeHandle { readonly __ShapeCat4Handle: true; }
interface ShapeCatHandle extends ShapeHandle { readonly __ShapeCatHandle: true; }
interface ShapeCloudHandle extends ShapeHandle { readonly __ShapeCloudHandle: true; }
interface ShapeCogHandle extends ShapeHandle { readonly __ShapeCogHandle: true; }
interface ShapeCrescentHandle extends ShapeHandle { readonly __ShapeCrescentHandle: true; }
interface ShapeDiamondHandle extends ShapeHandle { readonly __ShapeDiamondHandle: true; }
interface ShapeDoubleStarHandle extends ShapeHandle { readonly __ShapeDoubleStarHandle: true; }
interface ShapeEllipseHandle extends ShapeHandle { readonly __ShapeEllipseHandle: true; }
interface ShapeHandle { readonly __ShapeHandle: true; }
interface ShapeHeartHandle extends ShapeHandle { readonly __ShapeHeartHandle: true; }
interface ShapeInterfaceHandle { readonly __ShapeInterfaceHandle: true; }
interface ShapeNodeDefinitionHandle extends VectorNodeDefinitionHandle { readonly __ShapeNodeDefinitionHandle: true; }
interface ShapeNodeHandle extends VectorNodeHandle { readonly __ShapeNodeHandle: true; }
interface ShapePathTextNodeDefinitionHandle extends TextNodeDefinitionHandle { readonly __ShapePathTextNodeDefinitionHandle: true; }
interface ShapePathTextNodeHandle extends TextNodeHandle { readonly __ShapePathTextNodeHandle: true; }
interface ShapePieHandle extends ShapeHandle { readonly __ShapePieHandle: true; }
interface ShapePolygonHandle extends ShapeHandle { readonly __ShapePolygonHandle: true; }
interface ShapeQRCodeHandle extends ShapeHandle { readonly __ShapeQRCodeHandle: true; }
interface ShapeRectangleHandle extends ShapeHandle { readonly __ShapeRectangleHandle: true; }
interface ShapeSegmentHandle extends ShapeHandle { readonly __ShapeSegmentHandle: true; }
interface ShapeSpiralHandle extends ShapeHandle { readonly __ShapeSpiralHandle: true; }
interface ShapeSquareStarHandle extends ShapeHandle { readonly __ShapeSquareStarHandle: true; }
interface ShapeStarHandle extends ShapeHandle { readonly __ShapeStarHandle: true; }
interface ShapeTearHandle extends ShapeHandle { readonly __ShapeTearHandle: true; }
interface ShapeTextNodeDefinitionHandle extends TextNodeDefinitionHandle { readonly __ShapeTextNodeDefinitionHandle: true; }
interface ShapeTextNodeHandle extends TextNodeHandle { readonly __ShapeTextNodeHandle: true; }
interface ShapeTrapezoidHandle extends ShapeHandle { readonly __ShapeTrapezoidHandle: true; }
interface ShapeTriangleHandle extends ShapeHandle { readonly __ShapeTriangleHandle: true; }
interface SolidFillHandle extends FillHandle { readonly __SolidFillHandle: true; }
interface SphericalFilterParametersHandle { readonly __SphericalFilterParametersHandle: true; }
interface SphericalFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __SphericalFilterRasterNodeDefinitionHandle: true; }
interface SphericalFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __SphericalFilterRasterNodeHandle: true; }
interface SplineHandle { readonly __SplineHandle: true; }
interface SplitToningAdjustmentParametersHandle { readonly __SplitToningAdjustmentParametersHandle: true; }
interface SplitToningAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __SplitToningAdjustmentRasterNodeDefinitionHandle: true; }
interface SplitToningAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __SplitToningAdjustmentRasterNodeHandle: true; }
interface SpreadDocumentPropertiesHandle extends ArtboardDocumentPropertiesHandle { readonly __SpreadDocumentPropertiesHandle: true; }
interface SpreadNodeHandle extends PhysicalNodeHandle { readonly __SpreadNodeHandle: true; }
interface StoryBuilderHandle { readonly __StoryBuilderHandle: true; }
interface StoryDeltaHandle { readonly __StoryDeltaHandle: true; }
interface StoryHandle { readonly __StoryHandle: true; }
interface StoryInterfaceHandle { readonly __StoryInterfaceHandle: true; }
interface SubSelectionHandle { readonly __SubSelectionHandle: true; }
interface TableSubSelectionHandle extends SubSelectionHandle { readonly __TableSubSelectionHandle: true; }
interface TableTextNodeDefinitionHandle extends TextNodeDefinitionHandle { readonly __TableTextNodeDefinitionHandle: true; }
interface TableTextNodeHandle extends TextNodeHandle { readonly __TableTextNodeHandle: true; }
interface TagInterfaceHandle { readonly __TagInterfaceHandle: true; }
interface TextFlowHandle { readonly __TextFlowHandle: true; }
interface TextFlowOverflowInfoHandle { readonly __TextFlowOverflowInfoHandle: true; }
interface TextFrameInterfaceHandle { readonly __TextFrameInterfaceHandle: true; }
interface TextNodeDefinitionHandle extends PhysicalNodeDefinitionHandle { readonly __TextNodeDefinitionHandle: true; }
interface TextNodeHandle extends PhysicalNodeHandle { readonly __TextNodeHandle: true; }
interface TextSelectionHandle extends SubSelectionHandle { readonly __TextSelectionHandle: true; }
interface TextVisibilityOptionsHandle { readonly __TextVisibilityOptionsHandle: true; }
interface ThresholdAdjustmentParametersHandle { readonly __ThresholdAdjustmentParametersHandle: true; }
interface ThresholdAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __ThresholdAdjustmentRasterNodeDefinitionHandle: true; }
interface ThresholdAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __ThresholdAdjustmentRasterNodeHandle: true; }
interface TimerHandle { readonly __TimerHandle: true; }
interface ToneCompressionAdjustmentParametersHandle { readonly __ToneCompressionAdjustmentParametersHandle: true; }
interface ToneCompressionAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __ToneCompressionAdjustmentRasterNodeDefinitionHandle: true; }
interface ToneCompressionAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __ToneCompressionAdjustmentRasterNodeHandle: true; }
interface ToneStretchAdjustmentParametersHandle { readonly __ToneStretchAdjustmentParametersHandle: true; }
interface ToneStretchAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __ToneStretchAdjustmentRasterNodeDefinitionHandle: true; }
interface ToneStretchAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __ToneStretchAdjustmentRasterNodeHandle: true; }
interface TransformInterfaceHandle { readonly __TransformInterfaceHandle: true; }
interface TransparencyInterfaceHandle { readonly __TransparencyInterfaceHandle: true; }
interface TransparencyMeshSubSelectionHandle extends SubSelectionHandle { readonly __TransparencyMeshSubSelectionHandle: true; }
interface TransparencySubSelectionHandle extends SubSelectionHandle { readonly __TransparencySubSelectionHandle: true; }
interface TwirlFilterParametersHandle { readonly __TwirlFilterParametersHandle: true; }
interface TwirlFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __TwirlFilterRasterNodeDefinitionHandle: true; }
interface TwirlFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __TwirlFilterRasterNodeHandle: true; }
interface UnitValueConverterHandle { readonly __UnitValueConverterHandle: true; }
interface UnsharpMaskFilterParametersHandle { readonly __UnsharpMaskFilterParametersHandle: true; }
interface UnsharpMaskFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __UnsharpMaskFilterRasterNodeDefinitionHandle: true; }
interface UnsharpMaskFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __UnsharpMaskFilterRasterNodeHandle: true; }
interface VectorNodeDefinitionHandle extends PhysicalNodeDefinitionHandle { readonly __VectorNodeDefinitionHandle: true; }
interface VectorNodeHandle extends PhysicalNodeHandle { readonly __VectorNodeHandle: true; }
interface VibranceAdjustmentParametersHandle { readonly __VibranceAdjustmentParametersHandle: true; }
interface VibranceAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __VibranceAdjustmentRasterNodeDefinitionHandle: true; }
interface VibranceAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __VibranceAdjustmentRasterNodeHandle: true; }
interface VignetteFilterParametersHandle { readonly __VignetteFilterParametersHandle: true; }
interface VignetteFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __VignetteFilterRasterNodeDefinitionHandle: true; }
interface VignetteFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __VignetteFilterRasterNodeHandle: true; }
interface VisibilityInterfaceHandle { readonly __VisibilityInterfaceHandle: true; }
interface VisibilityTestOptionsHandle { readonly __VisibilityTestOptionsHandle: true; }
interface VoronoiFilterParametersHandle { readonly __VoronoiFilterParametersHandle: true; }
interface VoronoiFilterRasterNodeDefinitionHandle extends FilterRasterNodeDefinitionHandle { readonly __VoronoiFilterRasterNodeDefinitionHandle: true; }
interface VoronoiFilterRasterNodeHandle extends FilterRasterNodeHandle { readonly __VoronoiFilterRasterNodeHandle: true; }
interface WhiteBalanceAdjustmentParametersHandle { readonly __WhiteBalanceAdjustmentParametersHandle: true; }
interface WhiteBalanceAdjustmentRasterNodeDefinitionHandle extends AdjustmentRasterNodeDefinitionHandle { readonly __WhiteBalanceAdjustmentRasterNodeDefinitionHandle: true; }
interface WhiteBalanceAdjustmentRasterNodeHandle extends AdjustmentRasterNodeHandle { readonly __WhiteBalanceAdjustmentRasterNodeHandle: true; }

// ---------------------------------------------------------------------------
// Not assigned to any module in modules.json, so declared globally
// ---------------------------------------------------------------------------

declare enum RasterBrushSubSyncMode {
    CurrentNozzle,
    PreviousNozzle,
    WholeStroke,
}

declare enum TaskCallbackReason {
    Execute,
    Destroy,
}

declare class UnitTypePower {
    type: import("affinity:common").UnitType;
    power: number;
}

