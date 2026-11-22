// Type declarations for the Affinity JavaScript SDK: module "affinity:commands".
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:commands" {

    import { ColourSpaceType } from "affinity:colours";
    import { BlendMode, EnumerationResult, UnitType } from "affinity:common";
    import { AntialiasingMode, ContentType, CurveNodeSubSelectionItem, NodeChildType, NodeMoveType, PageBoundingBoxType, PredefinedTagKey, RasterFillMode, RasterFloodFillSamplingSource, RasterSelectionLogicalOperation, RasterSelectionOutlineAlignment, SamplingSource, SpatialAnchor, VisibilityMode } from "affinity:dom";
    import { FillMask } from "affinity:fills";
    import { CurveNodeStyle, Point, Rectangle, ShapeBoolParam, ShapeEnumParam, ShapeFloatParam, ShapeIntParam, Transform, WindingOrder } from "affinity:geometry";
    import { BevelEmbossType, StrokeFillType } from "affinity:layereffects";
    import { LineStyleMask, StrokeAlignment } from "affinity:linestyles";
    import { RasterFormat } from "affinity:raster";

    export enum GroupTransformAnchor {
        LogicalEdge,
        Spread,
        SpreadMargins,
        FirstSelected,
        LastSelected,
        Page,
        PageMargins,
    }

    export enum GroupTransformOrder {
        Min,
        Mid,
        Max,
    }

    export enum GroupTransformType {
        None,
        Min,
        Mid,
        Max,
        DistributeMin,
        DistributeMid,
        DistributeMax,
        Space,
        Reorder,
        SpaceKeyObject,
    }

    export enum InsertionMode {
        Default,
        Inside_AtBack,
        Inside_AtFront,
        Behind,
        Top,
    }

    export enum LineCommandDefaultsMode {
        None,
        Line,
        Brush,
        ArtText,
        FrameText,
    }

    export enum PageInsertMode {
        DocumentFlow,
        ExtendSpread,
        CreateSpread,
    }

    export class GroupTransformData {
        type: GroupTransformType;
        anchor: GroupTransformAnchor;
        order: GroupTransformOrder;
        spacing: number;
        isAutoSpacing: boolean;
        reorderSpaces: boolean;
    }

    export interface AddChildNodesCommandBuilderApi {
        addAddNoiseFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: AddNoiseFilterRasterNodeDefinitionHandle): void;
        addBilateralBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, bilateralBlurFilterRasterNodeDefinition: BilateralBlurFilterRasterNodeDefinitionHandle): void;
        addBlackAndWhiteAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: BlackAndWhiteAdjustmentRasterNodeDefinitionHandle): void;
        addBloomFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: BloomFilterRasterNodeDefinitionHandle): void;
        addBoxBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, boxBlurFilterRasterNodeDefinition: BoxBlurFilterRasterNodeDefinitionHandle): void;
        addBrightnessContrastAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: BrightnessContrastAdjustmentRasterNodeDefinitionHandle): void;
        addClarityFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: ClarityFilterRasterNodeDefinitionHandle): void;
        addColourBalanceAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: ColourBalanceAdjustmentRasterNodeDefinitionHandle): void;
        addContainerNode(self: AddChildNodesCommandBuilderHandle, containerNodeDefinition: ContainerNodeDefinitionHandle): void;
        addCurvesAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, curvesAdjustmentRasterNodeDefinition: CurvesAdjustmentRasterNodeDefinitionHandle): void;
        addDefringeFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: DefringeFilterRasterNodeDefinitionHandle): void;
        addDenoiseFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: DenoiseFilterRasterNodeDefinitionHandle): void;
        addDepthOfFieldFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: DepthOfFieldFilterRasterNodeDefinitionHandle): void;
        addDiffuseFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: DiffuseFilterRasterNodeDefinitionHandle): void;
        addDiffuseGlowFilterRasterNode(self: AddChildNodesCommandBuilderHandle, diffuseGlowFilterRasterNodeDefinition: DiffuseGlowFilterRasterNodeDefinitionHandle): void;
        addDustAndScratchFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: DustAndScratchFilterRasterNodeDefinitionHandle): void;
        addExposureAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, exposureAdjustmentRasterNodeDefinition: ExposureAdjustmentRasterNodeDefinitionHandle): void;
        addFieldBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, fieldBlurFilterRasterNodeDefinition: FieldBlurFilterRasterNodeDefinitionHandle): void;
        addGaussianBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, gaussianBlurFilterRasterNodeDefinition: GaussianBlurFilterRasterNodeDefinitionHandle): void;
        addHSLShiftAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: HSLShiftAdjustmentRasterNodeDefinitionHandle): void;
        addHalftoneFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: HalftoneFilterRasterNodeDefinitionHandle): void;
        addHighPassFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: HighPassFilterRasterNodeDefinitionHandle): void;
        addImageNode(self: AddChildNodesCommandBuilderHandle, imageNodeDefinition: ImageNodeDefinitionHandle): void;
        addInvertAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: InvertAdjustmentRasterNodeDefinitionHandle): void;
        addLensBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, lensBlurFilterRasterNodeDefinition: LensBlurFilterRasterNodeDefinitionHandle): void;
        addLevelsAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, levelsAdjustmentRasterNodeDefinition: LevelsAdjustmentRasterNodeDefinitionHandle): void;
        addMaskRasterNode(self: AddChildNodesCommandBuilderHandle, maskRasterNodeDefinition: MaskRasterNodeDefinitionHandle): void;
        addMaximumBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, maximumBlurFilterRasterNodeDefinition: MaximumBlurFilterRasterNodeDefinitionHandle): void;
        addMeasurementNode(self: AddChildNodesCommandBuilderHandle, measurementNodeDefinition: MeasurementNodeDefinitionHandle): void;
        addMedianBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, medianBlurFilterRasterNodeDefinition: MedianBlurFilterRasterNodeDefinitionHandle): void;
        addMinimumBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, minimumBlurFilterRasterNodeDefinition: MinimumBlurFilterRasterNodeDefinitionHandle): void;
        addMotionBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, motionBlurFilterRasterNodeDefinition: MotionBlurFilterRasterNodeDefinitionHandle): void;
        addNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: NodeDefinitionHandle): void;
        addNormalsAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: NormalsAdjustmentRasterNodeDefinitionHandle): void;
        addPatternRasterNode(self: AddChildNodesCommandBuilderHandle, patternRasterNodeDefinition: PatternRasterNodeDefinitionHandle): void;
        addPinchPunchFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: PinchPunchFilterRasterNodeDefinitionHandle): void;
        addPixelateFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: PixelateFilterRasterNodeDefinitionHandle): void;
        addPolyCurveNode(self: AddChildNodesCommandBuilderHandle, polyCurveNodeDefinition: PolyCurveNodeDefinitionHandle): void;
        addPosteriseAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: PosteriseAdjustmentRasterNodeDefinitionHandle): void;
        addRadialBlurFilterRasterNode(self: AddChildNodesCommandBuilderHandle, radialBlurFilterRasterNodeDefinition: RadialBlurFilterRasterNodeDefinitionHandle): void;
        addRasterNode(self: AddChildNodesCommandBuilderHandle, rasterNodeDefinition: RasterNodeDefinitionHandle): void;
        addRecolourAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: RecolourAdjustmentRasterNodeDefinitionHandle): void;
        addRippleFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: RippleFilterRasterNodeDefinitionHandle): void;
        addSelectiveColourAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: SelectiveColourAdjustmentRasterNodeDefinitionHandle): void;
        addShadowsHighlightsFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: ShadowsHighlightsFilterRasterNodeDefinitionHandle): void;
        addShapeNode(self: AddChildNodesCommandBuilderHandle, shapeNodeDefinition: ShapeNodeDefinitionHandle): void;
        addSphericalFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: SphericalFilterRasterNodeDefinitionHandle): void;
        addSplitToningAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: SplitToningAdjustmentRasterNodeDefinitionHandle): void;
        addTableTextNode(self: AddChildNodesCommandBuilderHandle, tableTextNodeDefinition: TableTextNodeDefinitionHandle): void;
        addThresholdAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: ThresholdAdjustmentRasterNodeDefinitionHandle): void;
        addToneCompressionAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, toneCompressionAdjustmentRasterNodeDefinition: ToneCompressionAdjustmentRasterNodeDefinitionHandle): void;
        addToneStretchAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, toneStretchAdjustmentRasterNodeDefinition: ToneStretchAdjustmentRasterNodeDefinitionHandle): void;
        addTwirlFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: TwirlFilterRasterNodeDefinitionHandle): void;
        addUnsharpMaskFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: UnsharpMaskFilterRasterNodeDefinitionHandle): void;
        addVibranceAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: VibranceAdjustmentRasterNodeDefinitionHandle): void;
        addVignetteFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: VignetteFilterRasterNodeDefinitionHandle): void;
        addVoronoiFilterRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: VoronoiFilterRasterNodeDefinitionHandle): void;
        addWhiteBalanceAdjustmentRasterNode(self: AddChildNodesCommandBuilderHandle, nodeDefinition: WhiteBalanceAdjustmentRasterNodeDefinitionHandle): void;
        clearInsertionTarget(self: AddChildNodesCommandBuilderHandle): void;
        clearInsertionTargetSelection(self: AddChildNodesCommandBuilderHandle): void;
        clearNodes(self: AddChildNodesCommandBuilderHandle): void;
        create(): AddChildNodesCommandBuilderHandle;
        createCommand(self: AddChildNodesCommandBuilderHandle, andSelect: boolean, childType: NodeChildType): DocumentCommandHandle;
        createCommandAndReset(self: AddChildNodesCommandBuilderHandle, andSelect: boolean, childType: NodeChildType): DocumentCommandHandle;
        setAppendCurrentSelection(self: AddChildNodesCommandBuilderHandle, appendCurrentSelection: boolean): void;
        setAutoName(self: AddChildNodesCommandBuilderHandle, autoName: boolean): void;
        setClearCurrentSelection(self: AddChildNodesCommandBuilderHandle, clearCurrentSelection: boolean): void;
        setForcePixelAlignment(self: AddChildNodesCommandBuilderHandle, forcePixelAlignment: boolean): void;
        setInsertionMode(self: AddChildNodesCommandBuilderHandle, mode: InsertionMode): void;
        setInsertionTarget(self: AddChildNodesCommandBuilderHandle, targetNode: NodeHandle): void;
        setInsertionTargetSelection(self: AddChildNodesCommandBuilderHandle, targetSelection: SelectionHandle): void;
    }
    export const AddChildNodesCommandBuilderApi: AddChildNodesCommandBuilderApi;

    export interface CommandApi {
        areEqual(self: CommandHandle, other: CommandHandle): void;
        getDescription(self: CommandHandle): string;
    }
    export const CommandApi: CommandApi;

    export interface CompoundCommandBuilderApi {
        addCommand(self: CompoundCommandBuilderHandle, documentCommand: DocumentCommandHandle, useAsDescription: boolean): void;
        clear(self: CompoundCommandBuilderHandle): void;
        create(): CompoundCommandBuilderHandle;
        createCommand(self: CompoundCommandBuilderHandle): DocumentCommandHandle;
    }
    export const CompoundCommandBuilderApi: CompoundCommandBuilderApi;

    export interface DocumentCommandApi extends CommandApi {
        createAddArtboardCommand(artboardDefinition: NodeDefinitionHandle, copyProperties: boolean, copyGuides: boolean): DocumentCommandHandle;
        createAddCurveCommand(curvesInterface: CurvesInterfaceHandle, curve: CurveHandle, select: boolean, preserveExistingSubSelection: boolean): DocumentCommandHandle;
        createAddCurveNodeCommand(curvesInterface: CurvesInterfaceHandle, curveHandle: CurveNodeSubSelectionItem, parametricDistance: number): DocumentCommandHandle;
        createAddDocumentSnapshotCommand(description: string): DocumentCommandHandle;
        createAddEmptyMaskCommand(selectionOrNull: SelectionHandle | null, andSelect: boolean, childType: NodeChildType): DocumentCommandHandle;
        createAddGuideCommand(horizontal: boolean, dPixels96: number): DocumentCommandHandle;
        createAddMaskCommand(selectionOrNull: SelectionHandle | null, andSelect: boolean, childType: NodeChildType): DocumentCommandHandle;
        createAddMasterPagesCommand(insertAfterMasterSpreadIndex: number, masterSpreadCount: number, pageCount: number): DocumentCommandHandle;
        createAddNoiseFilterCommand(selectionOrNull: SelectionHandle | null, parameters: AddNoiseFilterParametersHandle): DocumentCommandHandle;
        createAddPagesCommand(firstPageIndex: number, insertAfter: boolean, pageCount: number, masterSpreadIndex: number, insertMode: PageInsertMode): DocumentCommandHandle;
        createAddShapeCommand(shape: ShapeHandle, rectangle: Rectangle): DocumentCommandHandle;
        createBilateralBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: BilateralBlurFilterParametersHandle): DocumentCommandHandle;
        createBloomFilterCommand(selectionOrNull: SelectionHandle | null, parameters: BloomFilterParametersHandle): DocumentCommandHandle;
        createBoolOpIntersectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createBoolOpSubtractCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createBoolOpUnionCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createBoolOpXorCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createBoxBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: BoxBlurFilterParametersHandle): DocumentCommandHandle;
        createBreakCurvesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createClarityFilterCommand(selectionOrNull: SelectionHandle | null, parameters: ClarityFilterParametersHandle): DocumentCommandHandle;
        createClearMacroCommand(): DocumentCommandHandle;
        createClearPreviewsCommand(): DocumentCommandHandle;
        createColouriseCommand(): DocumentCommandHandle;
        createConvertDocumentFormatCommand(format: RasterFormat): DocumentCommandHandle;
        createConvertToCurvesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createCycleAlternateFuturesCommand(index: number): DocumentCommandHandle;
        createDecomposeLayerCommand(): DocumentCommandHandle;
        createDefringeFilterCommand(selectionOrNull: SelectionHandle | null, parameters: DefringeFilterParametersHandle): DocumentCommandHandle;
        createDeleteCurveNodesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createDeleteDocumentSnapshotCommand(snapshot: DocumentSnapshotHandle): DocumentCommandHandle;
        createDeleteMasterPagesCommand(firstMasterSpreadIndex: number, masterSpreadCount: number): DocumentCommandHandle;
        createDeleteNodesCommand(selectionOrNull: SelectionHandle | null, ignoreRasterSelection: boolean): DocumentCommandHandle;
        createDeletePagesCommand(firstPageIndex: number, pageCount: number): DocumentCommandHandle;
        createDenoiseFilterCommand(selectionOrNull: SelectionHandle | null, parameters: DenoiseFilterParametersHandle): DocumentCommandHandle;
        createDepthOfFieldFilterCommand(selectionOrNull: SelectionHandle | null, parameters: DepthOfFieldFilterParametersHandle): DocumentCommandHandle;
        createDetectDepthCommand(): DocumentCommandHandle;
        createDiffuseFilterCommand(selectionOrNull: SelectionHandle | null, parameters: DiffuseFilterParametersHandle): DocumentCommandHandle;
        createDiffuseGlowFilterCommand(selectionOrNull: SelectionHandle | null, parameters: DiffuseGlowFilterParametersHandle): DocumentCommandHandle;
        createDivideShapesCommand(selectionOrNull: SelectionHandle | null, retainAllParts: boolean): DocumentCommandHandle;
        createDuplicateBevelEmbossLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createDuplicateColourOverlayLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createDuplicateGaussianBlurLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createDuplicateGradientOverlayLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createDuplicateInnerGlowLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createDuplicateInnerShadowLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createDuplicateOuterGlowLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createDuplicateOuterShadowLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createDuplicateOutlineLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createDuplicatePhongBevelLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createDustAndScratchFilterCommand(selectionOrNull: SelectionHandle | null, parameters: DustAndScratchFilterParametersHandle): DocumentCommandHandle;
        createExportMacroCommand(macroPath: string): DocumentCommandHandle;
        createFeatherRasterSelectionCommand(radius: number): DocumentCommandHandle;
        createFieldBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: FieldBlurFilterParametersHandle): DocumentCommandHandle;
        createFlattenCommand(): DocumentCommandHandle;
        createFlipCanvasCommand(isHorizontal: boolean): DocumentCommandHandle;
        createFormatTextCommand(selectionOrNull: SelectionHandle | null, delta: StoryDeltaHandle): DocumentCommandHandle;
        createGaussianBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: GaussianBlurFilterParametersHandle): DocumentCommandHandle;
        createGenerateImageCommand(prompt: string): DocumentCommandHandle;
        createGenerativeEditImageCommand(prompt: string): DocumentCommandHandle;
        createGenerativeUpscaleCommand(selectionOrNull: SelectionHandle | null, scale: number): DocumentCommandHandle;
        createGroupNodesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createGroupTransformCommand(selectionOrNull: SelectionHandle | null, xDataOrNull: GroupTransformData | null, yDataOrNull: GroupTransformData | null): DocumentCommandHandle;
        createGrowShrinkRasterSelectionCommand(radius: number, circular: boolean): DocumentCommandHandle;
        createHalftoneFilterCommand(selectionOrNull: SelectionHandle | null, parameters: HalftoneFilterParametersHandle): DocumentCommandHandle;
        createHighPassFilterCommand(selectionOrNull: SelectionHandle | null, parameters: HighPassFilterParametersHandle): DocumentCommandHandle;
        createImageTraceCommand(selectionOrNull: SelectionHandle | null, edgeThreshold: number, curveFittingTolerance: number): DocumentCommandHandle;
        createImportMacroCommand(macroPath: string): DocumentCommandHandle;
        createInsertGlyphCommand(selectionOrNull: SelectionHandle | null, glyph: GlyphHandle): DocumentCommandHandle;
        createJoinCurvesCommand(selectionOrNull: SelectionHandle | null, isJoinStraight: boolean): DocumentCommandHandle;
        createKnifeCutCommand(cutCurve: CurveHandle, selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createLayerTo3DModelCommand(): DocumentCommandHandle;
        createLensBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: LensBlurFilterParametersHandle): DocumentCommandHandle;
        createLinkTextFrameCommand(srcNode: TextNodeHandle, destNode: TextNodeHandle): DocumentCommandHandle;
        createLiveStackGroupNodesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createLiveToneBlendGroupNodesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createMaximumBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: MaximumBlurFilterParametersHandle): DocumentCommandHandle;
        createMedianBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: MedianBlurFilterParametersHandle): DocumentCommandHandle;
        createMergeCurvesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createMergeDownCommand(): DocumentCommandHandle;
        createMergeSelectedCommand(): DocumentCommandHandle;
        createMergeVisibleCommand(): DocumentCommandHandle;
        createMinimumBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: MinimumBlurFilterParametersHandle): DocumentCommandHandle;
        createMixedLightCorrectionCommand(selectionOrNull: SelectionHandle | null, strength: number, preserveWhiteBalance: boolean, temperature: number): DocumentCommandHandle;
        createMotionBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: MotionBlurFilterParametersHandle): DocumentCommandHandle;
        createMoveColourOverlayLayerEffectCommand(selectionOrNull: SelectionHandle | null, fromIndex: number, toIndex: number): DocumentCommandHandle;
        createMoveGradientOverlayLayerEffectCommand(selectionOrNull: SelectionHandle | null, fromIndex: number, toIndex: number): DocumentCommandHandle;
        createMoveGuideCommand(horizontal: boolean, nIndex: number, dNewPixels96: number): DocumentCommandHandle;
        createMoveInnerShadowLayerEffectCommand(selectionOrNull: SelectionHandle | null, fromIndex: number, toIndex: number): DocumentCommandHandle;
        createMoveMappedNodesCommand(selectionOrNull: SelectionHandle | null, fromNodes: NodeHandle[], toNodes: NodeHandle[], nodeMoveType: NodeMoveType): DocumentCommandHandle;
        createMoveNodesCommand(selectionOrNull: SelectionHandle | null, toNode: NodeHandle, nodeMoveType: NodeMoveType, childType: NodeChildType): DocumentCommandHandle;
        createMoveOuterShadowLayerEffectCommand(selectionOrNull: SelectionHandle | null, fromIndex: number, toIndex: number): DocumentCommandHandle;
        createMoveOutlineLayerEffectCommand(selectionOrNull: SelectionHandle | null, fromIndex: number, toIndex: number): DocumentCommandHandle;
        createOutlineRasterSelectionCommand(radius: number, alignment: RasterSelectionOutlineAlignment, circular: boolean): DocumentCommandHandle;
        createPinchPunchFilterCommand(selectionOrNull: SelectionHandle | null, parameters: PinchPunchFilterParametersHandle): DocumentCommandHandle;
        createPixelateFilterCommand(selectionOrNull: SelectionHandle | null, parameters: PixelateFilterParametersHandle): DocumentCommandHandle;
        createPopulatePictureFrameCommand(contentNode: NodeHandle, selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRadialBlurFilterCommand(selectionOrNull: SelectionHandle | null, parameters: RadialBlurFilterParametersHandle): DocumentCommandHandle;
        createRasterAutoColoursCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasterAutoContrastCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasterAutoLevelsCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasterAutoWhiteBalanceCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasterDeselectCommand(): DocumentCommandHandle;
        createRasterEdgeDetectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasterFillCommand(selectionOrNull: SelectionHandle | null, mode: RasterFillMode, colourOrNull: ColourHandle | null, opacity: number, blendMode: BlendMode): DocumentCommandHandle;
        createRasterFloodFillCommand(selectionOrNull: SelectionHandle | null, point: Point, tolerance: number, isContiguous: boolean, antialias: boolean, samplingSource: RasterFloodFillSamplingSource, blendMode: BlendMode, colourOrNull: ColourHandle | null): DocumentCommandHandle;
        createRasterFloodSelectCommand(point: Point, tolerance: number, isContiguous: boolean, antialias: boolean, operation: RasterSelectionLogicalOperation, samplingSource: SamplingSource): DocumentCommandHandle;
        createRasterHorizontalEdgeDetectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasterInvertSelectionCommand(): DocumentCommandHandle;
        createRasterMLDenoiseCommand(selectionOrNull: SelectionHandle | null, lumaStrength: number, chromaStrength: number): DocumentCommandHandle;
        createRasterMotionBlurReductionCommand(selectionOrNull: SelectionHandle | null, strength: number): DocumentCommandHandle;
        createRasterPolarToRectangularCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasterRectangularToPolarCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasterReselectCommand(): DocumentCommandHandle;
        createRasterSDRToHDRCommand(selectionOrNull: SelectionHandle | null, strength: number): DocumentCommandHandle;
        createRasterSelectAllCommand(): DocumentCommandHandle;
        createRasterSelectBluesCommand(): DocumentCommandHandle;
        createRasterSelectGreensCommand(): DocumentCommandHandle;
        createRasterSelectHighlightsCommand(): DocumentCommandHandle;
        createRasterSelectMidtonesCommand(): DocumentCommandHandle;
        createRasterSelectOpaqueCommand(): DocumentCommandHandle;
        createRasterSelectPartiallyTransparentCommand(): DocumentCommandHandle;
        createRasterSelectRedsCommand(): DocumentCommandHandle;
        createRasterSelectShadowsCommand(): DocumentCommandHandle;
        createRasterSelectTransparentCommand(): DocumentCommandHandle;
        createRasterVerticalEdgeDetectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRasteriseObjectsCommand(selectionOrNull: SelectionHandle | null, rasteriseContentsOnly: boolean, clipToSpread: boolean): DocumentCommandHandle;
        createRedoCommand(): DocumentCommandHandle;
        createRemoveAllLayerEffectsCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRemoveBackgroundCommand(): DocumentCommandHandle;
        createRemoveBevelEmbossLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRemoveColourOverlayLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createRemoveGaussianBlurLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRemoveGradientOverlayLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createRemoveGuideCommand(horizontal: boolean, nIndex: number): DocumentCommandHandle;
        createRemoveInnerGlowLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRemoveInnerShadowLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createRemoveOuterGlowLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRemoveOuterShadowLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createRemoveOutlineLayerEffectCommand(selectionOrNull: SelectionHandle | null, index: number): DocumentCommandHandle;
        createRemovePhongBevelLayerEffectCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createReplaceBitmapCommand(selectionOrNull: SelectionHandle | null, bitmap: RasterObjectHandle): DocumentCommandHandle;
        createReplayMacroCommand(): DocumentCommandHandle;
        createRestoreDocumentSnapshotCommand(snapshot: DocumentSnapshotHandle): DocumentCommandHandle;
        createReverseCurvesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createRippleFilterCommand(selectionOrNull: SelectionHandle | null, parameters: RippleFilterParametersHandle): DocumentCommandHandle;
        createScissorCutCommand(node: NodeHandle, polyCurveIndex: number, curveIndex: number, isParametric: boolean, distance: number): DocumentCommandHandle;
        createSelectAllCommand(selectOnCurrentLayerOnly: boolean): DocumentCommandHandle;
        createSelectSubjectCommand(): DocumentCommandHandle;
        createSeparateCurvesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createSetAddNoiseFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: AddNoiseFilterParametersHandle): DocumentCommandHandle;
        createSetAllLayerEffectsScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean): DocumentCommandHandle;
        createSetAntialiasingModeCommand(selectionOrNull: SelectionHandle | null, antialiasingMode: AntialiasingMode): DocumentCommandHandle;
        createSetArtboardBaselineGridCommand(selectionOrNull: SelectionHandle | null, baselineGridOptions: BaselineGridOptionsHandle): DocumentCommandHandle;
        createSetArtboardDocumentPropertiesCommand(artboardInterface: ArtboardInterfaceHandle, artboardDocumentProperties: ArtboardDocumentPropertiesHandle): DocumentCommandHandle;
        createSetArtboardEnabledCommand(selectionOrNull: SelectionHandle | null, isEnabled: boolean): DocumentCommandHandle;
        createSetArtboardSizeWithAnchorCommand(artboardInterface: ArtboardInterfaceHandle, width: number, height: number, anchor: SpatialAnchor): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectAzimuthCommand(selectionOrNull: SelectionHandle | null, azimuth: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: BevelEmbossLayerEffectHandle): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectDepthCommand(selectionOrNull: SelectionHandle | null, depth: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectDirectionCommand(selectionOrNull: SelectionHandle | null, azimuth: number, elevation: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectElevationCommand(selectionOrNull: SelectionHandle | null, elevation: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectHighlightBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectHighlightColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectHighlightOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectInvertedCommand(selectionOrNull: SelectionHandle | null, inverted: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectLinkDepthCommand(selectionOrNull: SelectionHandle | null, linkDepth: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectRadiusCommand(selectionOrNull: SelectionHandle | null, radius: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectShadowBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectShadowColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectShadowOpacityCommand(selectionOrNull: SelectionHandle | null, shadowOpacity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectSoftenCommand(selectionOrNull: SelectionHandle | null, soften: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBevelEmbossLayerEffectTypeCommand(selectionOrNull: SelectionHandle | null, bevelType: BevelEmbossType, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetBilateralBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: BilateralBlurFilterParametersHandle): DocumentCommandHandle;
        createSetBlackAndWhiteAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: BlackAndWhiteAdjustmentParametersHandle): DocumentCommandHandle;
        createSetBlendGammaCommand(selectionOrNull: SelectionHandle | null, gamma: number): DocumentCommandHandle;
        createSetBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, setPassthrough: boolean): DocumentCommandHandle;
        createSetBlendRangesCommand(selectionOrNull: SelectionHandle | null, blendOptions: BlendOptionsHandle): DocumentCommandHandle;
        createSetBloomFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: BloomFilterParametersHandle): DocumentCommandHandle;
        createSetBoxBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: BoxBlurFilterParametersHandle): DocumentCommandHandle;
        createSetBrightnessContrastAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: BrightnessContrastAdjustmentParametersHandle): DocumentCommandHandle;
        createSetBrushFillCommand(selectionOrNull: SelectionHandle | null, fillDescriptorOrNull: FillDescriptorHandle | null, contentType: ContentType, fillMask: FillMask, copyTransform: boolean, useTextSelection: boolean, maintainBlendMode: boolean, restoreAspectRatio: boolean): DocumentCommandHandle;
        createSetBrushFillIsAnchoredToSpreadCommand(selectionOrNull: SelectionHandle | null, isAnchoredToSpread: boolean, contentType: ContentType, useTextSelection: boolean, applyToAllFills: boolean): DocumentCommandHandle;
        createSetBrushFillOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, contentType: ContentType, useTextSelection: boolean): DocumentCommandHandle;
        createSetClarityFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: ClarityFilterParametersHandle): DocumentCommandHandle;
        createSetColourBalanceAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: ColourBalanceAdjustmentParametersHandle): DocumentCommandHandle;
        createSetColourOverlayLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetColourOverlayLayerEffectColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetColourOverlayLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: ColourOverlayLayerEffectHandle, index: number): DocumentCommandHandle;
        createSetColourOverlayLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean, index: number): DocumentCommandHandle;
        createSetColourOverlayLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetColourOverlayLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetCurrentSnapshotCommand(snapshot: DocumentSnapshotHandle): DocumentCommandHandle;
        createSetCurrentSnapshotFromHistoryItemCommand(historyItem: DocumentHistoryItemHandle): DocumentCommandHandle;
        createSetCurrentSpreadCommand(spreadNode: SpreadNodeHandle): DocumentCommandHandle;
        createSetCurveNodeStyleCommand(selectionOrNull: SelectionHandle | null, style: CurveNodeStyle): DocumentCommandHandle;
        createSetCurvesAdjustmentColourSpaceCommand(selectionOrNull: SelectionHandle | null, colourSpace: ColourSpaceType): DocumentCommandHandle;
        createSetCurvesAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: CurvesAdjustmentParametersHandle): DocumentCommandHandle;
        createSetCurvesCommand(curvesInterface: CurvesInterfaceHandle, polyCurve: PolyCurveHandle): DocumentCommandHandle;
        createSetDefringeFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: DefringeFilterParametersHandle): DocumentCommandHandle;
        createSetDenoiseFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: DenoiseFilterParametersHandle): DocumentCommandHandle;
        createSetDepthOfFieldFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: DepthOfFieldFilterParametersHandle): DocumentCommandHandle;
        createSetDescriptionCommand(selectionOrNull: SelectionHandle | null, description: string): DocumentCommandHandle;
        createSetDevelopParametersCommand(selectionOrNull: SelectionHandle | null, parameters: DevelopParametersHandle): DocumentCommandHandle;
        createSetDiffuseFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: DiffuseFilterParametersHandle): DocumentCommandHandle;
        createSetDiffuseGlowFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: DiffuseGlowFilterParametersHandle): DocumentCommandHandle;
        createSetDocumentBaselineGridCommand(baselineGridOptions: BaselineGridOptionsHandle): DocumentCommandHandle;
        createSetDocumentPropertiesCommand(documentProperties: DocumentPropertiesHandle): DocumentCommandHandle;
        createSetDocumentUnitsCommand(units: UnitType): DocumentCommandHandle;
        createSetDustAndScratchFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: DustAndScratchFilterParametersHandle): DocumentCommandHandle;
        createSetEditableCommand(selectionOrNull: SelectionHandle | null, isEditable: boolean): DocumentCommandHandle;
        createSetEmbeddedDocumentAllLayersVisibilityCommand(selectionOrNull: SelectionHandle | null, isVisible: boolean[]): DocumentCommandHandle;
        createSetEmbeddedDocumentLayerVisibilityCommand(selectionOrNull: SelectionHandle | null, layer: number, isVisible: boolean): DocumentCommandHandle;
        createSetEmbeddedDocumentPDFPassthroughCommand(selectionOrNull: SelectionHandle | null, isSet: boolean): DocumentCommandHandle;
        createSetEmbeddedDocumentPageBoundingBoxTypeCommand(selectionOrNull: SelectionHandle | null, pageBoundingBoxType: PageBoundingBoxType): DocumentCommandHandle;
        createSetEmbeddedDocumentSelectedArtboardIDCommand(selectionOrNull: SelectionHandle | null, artboardID: string): DocumentCommandHandle;
        createSetEmbeddedDocumentSelectedSpreadIDCommand(selectionOrNull: SelectionHandle | null, spreadID: string): DocumentCommandHandle;
        createSetExportConfigCommand(selectionOrNull: SelectionHandle | null, exportConfig: ExportConfigHandle): DocumentCommandHandle;
        createSetExposureAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: ExposureAdjustmentParametersHandle): DocumentCommandHandle;
        createSetFieldBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: FieldBlurFilterParametersHandle): DocumentCommandHandle;
        createSetGaussianBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: GaussianBlurFilterParametersHandle): DocumentCommandHandle;
        createSetGaussianBlurLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGaussianBlurLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: GaussianBlurLayerEffectHandle): DocumentCommandHandle;
        createSetGaussianBlurLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean): DocumentCommandHandle;
        createSetGaussianBlurLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGaussianBlurLayerEffectPreserveAlphaCommand(selectionOrNull: SelectionHandle | null, preserveAlpha: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGaussianBlurLayerEffectRadiusCommand(selectionOrNull: SelectionHandle | null, radius: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGaussianBlurLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGradientOverlayLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGradientOverlayLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: GradientOverlayLayerEffectHandle, index: number): DocumentCommandHandle;
        createSetGradientOverlayLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean, index: number): DocumentCommandHandle;
        createSetGradientOverlayLayerEffectFillCommand(selectionOrNull: SelectionHandle | null, gradientFill: GradientFillHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGradientOverlayLayerEffectFillTransformCommand(selectionOrNull: SelectionHandle | null, transform: Transform, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGradientOverlayLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGradientOverlayLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetGuidesColourCommand(colour: ColourHandle): DocumentCommandHandle;
        createSetHSLShiftAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: HSLShiftAdjustmentParametersHandle): DocumentCommandHandle;
        createSetHalftoneFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: HalftoneFilterParametersHandle): DocumentCommandHandle;
        createSetHighPassFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: HighPassFilterParametersHandle): DocumentCommandHandle;
        createSetHistoryIndexCommand(index: number): DocumentCommandHandle;
        createSetInnerGlowLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerGlowLayerEffectColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerGlowLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: InnerGlowLayerEffectHandle): DocumentCommandHandle;
        createSetInnerGlowLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean): DocumentCommandHandle;
        createSetInnerGlowLayerEffectIntensityCommand(selectionOrNull: SelectionHandle | null, intensity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerGlowLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerGlowLayerEffectRadiusCommand(selectionOrNull: SelectionHandle | null, radius: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerGlowLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerShadowLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerShadowLayerEffectColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerShadowLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: InnerShadowLayerEffectHandle, index: number): DocumentCommandHandle;
        createSetInnerShadowLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean, index: number): DocumentCommandHandle;
        createSetInnerShadowLayerEffectIntensityCommand(selectionOrNull: SelectionHandle | null, intensity: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerShadowLayerEffectOffsetAngleCommand(selectionOrNull: SelectionHandle | null, offset: number, angle: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerShadowLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerShadowLayerEffectRadiusCommand(selectionOrNull: SelectionHandle | null, radius: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetInnerShadowLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetLensBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: LensBlurFilterParametersHandle): DocumentCommandHandle;
        createSetLevelsAdjustmentColourSpaceCommand(selectionOrNull: SelectionHandle | null, colourSpace: ColourSpaceType): DocumentCommandHandle;
        createSetLevelsAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: LevelsAdjustmentParametersHandle): DocumentCommandHandle;
        createSetLineFillOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, contentType: ContentType, useTextSelection: boolean): DocumentCommandHandle;
        createSetLineStyleCommand(selectionOrNull: SelectionHandle | null, lineStyle: LineStyleHandle, lineStyleMask: LineStyleMask, contentType: ContentType, useTextSelection: boolean, defaultsMode: LineCommandDefaultsMode): DocumentCommandHandle;
        createSetLineStyleDescriptorCommand(selectionOrNull: SelectionHandle | null, lineStyleDescriptor: LineStyleDescriptorHandle, lineStyleMask: LineStyleMask, contentType: ContentType, useTextSelection: boolean, defaultsMode: LineCommandDefaultsMode): DocumentCommandHandle;
        createSetMaximumBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: MaximumBlurFilterParametersHandle): DocumentCommandHandle;
        createSetMeasurementAnnotationOffsetCommand(node: MeasurementNodeHandle, offset: number): DocumentCommandHandle;
        createSetMeasurementPrecisionCommand(useDocumentPrecision: boolean, decimalPlaces: number): DocumentCommandHandle;
        createSetMeasurementShowEndpointMarkersCommand(show: boolean): DocumentCommandHandle;
        createSetMeasurementUnitsCommand(units: UnitType): DocumentCommandHandle;
        createSetMedianBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: MedianBlurFilterParametersHandle): DocumentCommandHandle;
        createSetMinimumBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: MinimumBlurFilterParametersHandle): DocumentCommandHandle;
        createSetMotionBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: MotionBlurFilterParametersHandle): DocumentCommandHandle;
        createSetNormalsAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: NormalsAdjustmentParametersHandle): DocumentCommandHandle;
        createSetOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number): DocumentCommandHandle;
        createSetOuterGlowLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterGlowLayerEffectColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterGlowLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: OuterGlowLayerEffectHandle): DocumentCommandHandle;
        createSetOuterGlowLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean): DocumentCommandHandle;
        createSetOuterGlowLayerEffectIntensityCommand(selectionOrNull: SelectionHandle | null, intensity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterGlowLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterGlowLayerEffectRadiusCommand(selectionOrNull: SelectionHandle | null, radius: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterGlowLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterShadowLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterShadowLayerEffectColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterShadowLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: OuterShadowLayerEffectHandle, index: number): DocumentCommandHandle;
        createSetOuterShadowLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean, index: number): DocumentCommandHandle;
        createSetOuterShadowLayerEffectIntensityCommand(selectionOrNull: SelectionHandle | null, intensity: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterShadowLayerEffectKnocksOutCommand(selectionOrNull: SelectionHandle | null, knocksOut: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterShadowLayerEffectOffsetAngleCommand(selectionOrNull: SelectionHandle | null, offset: number, angle: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterShadowLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterShadowLayerEffectRadiusCommand(selectionOrNull: SelectionHandle | null, radius: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOuterShadowLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectAlignmentCommand(selectionOrNull: SelectionHandle | null, alignment: StrokeAlignment, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectBlendModeCommand(selectionOrNull: SelectionHandle | null, blendMode: BlendMode, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: OutlineLayerEffectHandle, index: number): DocumentCommandHandle;
        createSetOutlineLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean, index: number): DocumentCommandHandle;
        createSetOutlineLayerEffectFillCommand(selectionOrNull: SelectionHandle | null, gradientFill: GradientFillHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectFillTransformCommand(selectionOrNull: SelectionHandle | null, fillDescriptor: FillDescriptorHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectFillTypeCommand(selectionOrNull: SelectionHandle | null, fillType: StrokeFillType, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectRadiusCommand(selectionOrNull: SelectionHandle | null, radius: number, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetOutlineLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, index: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPageDocumentPropertiesCommand(spreadNode: SpreadNodeHandle, page: number, pageDocumentProperties: PageDocumentPropertiesHandle): DocumentCommandHandle;
        createSetPenFillCommand(selectionOrNull: SelectionHandle | null, fillDescriptorOrNull: FillDescriptorHandle | null, contentType: ContentType, fillMask: FillMask, copyTransform: boolean, useTextSelection: boolean, maintainBlendMode: boolean, restoreAspectRatio: boolean): DocumentCommandHandle;
        createSetPenFillIsAnchoredToSpreadCommand(selectionOrNull: SelectionHandle | null, isAnchoredToSpread: boolean, contentType: ContentType, useTextSelection: boolean, applyToAllFills: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectAmbientColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectAmbientCommand(selectionOrNull: SelectionHandle | null, ambient: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectCommand(selectionOrNull: SelectionHandle | null, layerEffect: PhongBevelLayerEffectHandle): DocumentCommandHandle;
        createSetPhongBevelLayerEffectDepthCommand(selectionOrNull: SelectionHandle | null, depth: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectDiffuseCommand(selectionOrNull: SelectionHandle | null, diffuse: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectEnabledCommand(selectionOrNull: SelectionHandle | null, enabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectLightsCommand(selectionOrNull: SelectionHandle | null, lights: PointLightHandle[], enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectLinkDepthCommand(selectionOrNull: SelectionHandle | null, linkDepth: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectOpacityCommand(selectionOrNull: SelectionHandle | null, opacity: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectRadiusCommand(selectionOrNull: SelectionHandle | null, radius: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectScaleWithObjectCommand(selectionOrNull: SelectionHandle | null, scaleWithObject: boolean, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectShininessCommand(selectionOrNull: SelectionHandle | null, shininess: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectSoftenCommand(selectionOrNull: SelectionHandle | null, soften: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectSpecularColourCommand(selectionOrNull: SelectionHandle | null, colour: ColourHandle, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPhongBevelLayerEffectSpecularCommand(selectionOrNull: SelectionHandle | null, specular: number, enableIfDisabled: boolean): DocumentCommandHandle;
        createSetPinchPunchFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: PinchPunchFilterParametersHandle): DocumentCommandHandle;
        createSetPixelateFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: PixelateFilterParametersHandle): DocumentCommandHandle;
        createSetPosteriseAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: PosteriseAdjustmentParametersHandle): DocumentCommandHandle;
        createSetRadialBlurFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: RadialBlurFilterParametersHandle): DocumentCommandHandle;
        createSetRasterSelectionFromObjectCommand(nodeOrNull: NodeHandle | null, useIntensity: boolean, operation: RasterSelectionLogicalOperation): DocumentCommandHandle;
        createSetRasterSelectionFromPolygonCommand(polygon: PolygonHandle, operation: RasterSelectionLogicalOperation, isAntialias: boolean, featherRadius: number): DocumentCommandHandle;
        createSetRecolourAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: RecolourAdjustmentParametersHandle): DocumentCommandHandle;
        createSetRippleFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: RippleFilterParametersHandle): DocumentCommandHandle;
        createSetSelectionCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createSetSelectiveColourAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: SelectiveColourAdjustmentParametersHandle): DocumentCommandHandle;
        createSetShadowsHighlightsAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: ShadowsHighlightsAdjustmentParametersHandle): DocumentCommandHandle;
        createSetShadowsHighlightsFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: ShadowsHighlightsFilterParametersHandle): DocumentCommandHandle;
        createSetShapeBoolParamCommand(selectionOrNull: SelectionHandle | null, key: ShapeBoolParam, value: boolean): DocumentCommandHandle;
        createSetShapeCommand(selectionOrNull: SelectionHandle | null, shape: ShapeHandle, onlyReplaceLikeShapes: boolean): DocumentCommandHandle;
        createSetShapeEnumParamCommand(selectionOrNull: SelectionHandle | null, key: ShapeEnumParam, value: number): DocumentCommandHandle;
        createSetShapeFloatParamCommand(selectionOrNull: SelectionHandle | null, key: ShapeFloatParam, value: number, isConstrained: boolean, isSymmetrical: boolean): DocumentCommandHandle;
        createSetShapeIntParamCommand(selectionOrNull: SelectionHandle | null, key: ShapeIntParam, value: number): DocumentCommandHandle;
        createSetSphericalFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: SphericalFilterParametersHandle): DocumentCommandHandle;
        createSetSplitToningAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: SplitToningAdjustmentParametersHandle): DocumentCommandHandle;
        createSetSpreadDocumentPropertiesCommand(spreadNode: SpreadNodeHandle, spreadDocumentProperties: SpreadDocumentPropertiesHandle): DocumentCommandHandle;
        createSetSpreadSizeWithAnchorCommand(spreadNode: SpreadNodeHandle, width: number, height: number, anchor: SpatialAnchor): DocumentCommandHandle;
        createSetStrokeAlignmentCommand(selectionOrNull: SelectionHandle | null, strokeAlignment: StrokeAlignment, contentType: ContentType, useTextSelection: boolean, defaultsMode: LineCommandDefaultsMode): DocumentCommandHandle;
        createSetTagColourCommand(selectionOrNull: SelectionHandle | null, colourOrNull: ColourHandle | null): DocumentCommandHandle;
        createSetTagValueForKeyCommand(selectionOrNull: SelectionHandle | null, tagKey: string, tagValue: string): DocumentCommandHandle;
        createSetTagValueForPredefinedKeyCommand(selectionOrNull: SelectionHandle | null, key: PredefinedTagKey, tagValue: string): DocumentCommandHandle;
        createSetTextCommand(selectionOrNull: SelectionHandle | null, text: string): DocumentCommandHandle;
        createSetTextFrameBaselineGridCommand(selectionOrNull: SelectionHandle | null, baselineGridOptions: BaselineGridOptionsHandle): DocumentCommandHandle;
        createSetTextFrameHideOverflowCommand(selectionOrNull: SelectionHandle | null, hideOverflow: boolean): DocumentCommandHandle;
        createSetTextFrameIgnoreBaselineGridCommand(selectionOrNull: SelectionHandle | null, ignoreBaselineGrid: boolean): DocumentCommandHandle;
        createSetTextFrameIgnoreTextWrapsCommand(selectionOrNull: SelectionHandle | null, ignoreTextWraps: boolean): DocumentCommandHandle;
        createSetThresholdAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: ThresholdAdjustmentParametersHandle): DocumentCommandHandle;
        createSetToneCompressionAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: ToneCompressionAdjustmentParametersHandle): DocumentCommandHandle;
        createSetToneStretchAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: ToneStretchAdjustmentParametersHandle): DocumentCommandHandle;
        createSetTransparencyFillCommand(selectionOrNull: SelectionHandle | null, fillDescriptorOrNull: FillDescriptorHandle | null, contentType: ContentType, fillMask: FillMask, copyTransform: boolean, useTextSelection: boolean, maintainBlendMode: boolean, restoreAspectRatio: boolean): DocumentCommandHandle;
        createSetTransparencyFillIsAnchoredToSpreadCommand(selectionOrNull: SelectionHandle | null, isAnchoredToSpread: boolean, contentType: ContentType, useTextSelection: boolean, applyToAllFills: boolean): DocumentCommandHandle;
        createSetTwirlFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: TwirlFilterParametersHandle): DocumentCommandHandle;
        createSetUnsharpMaskFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: UnsharpMaskFilterParametersHandle): DocumentCommandHandle;
        createSetVibranceAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: VibranceAdjustmentParametersHandle): DocumentCommandHandle;
        createSetVignetteFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: VignetteFilterParametersHandle): DocumentCommandHandle;
        createSetVisibilityCommand(selectionOrNull: SelectionHandle | null, mode: VisibilityMode, isVisible: boolean): DocumentCommandHandle;
        createSetVoronoiFilterParametersCommand(selectionOrNull: SelectionHandle | null, parameters: VoronoiFilterParametersHandle): DocumentCommandHandle;
        createSetWhiteBalanceAdjustmentParametersCommand(selectionOrNull: SelectionHandle | null, parameters: WhiteBalanceAdjustmentParametersHandle): DocumentCommandHandle;
        createSetWindingModeCommand(selectionOrNull: SelectionHandle | null, windingOrder: WindingOrder): DocumentCommandHandle;
        createShadowsHighlightsFilterCommand(selectionOrNull: SelectionHandle | null, parameters: ShadowsHighlightsFilterParametersHandle): DocumentCommandHandle;
        createShowAllCommand(): DocumentCommandHandle;
        createSmoothCurvesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createSmoothRasterSelectionCommand(radius: number): DocumentCommandHandle;
        createSphericalFilterCommand(selectionOrNull: SelectionHandle | null, parameters: SphericalFilterParametersHandle): DocumentCommandHandle;
        createSplitCurveCommand(selectionOrNull: SelectionHandle | null, parametricDistance: number): DocumentCommandHandle;
        createStartRecordingMacroCommand(): DocumentCommandHandle;
        createStopRecordingMacroCommand(): DocumentCommandHandle;
        createTransformCommand(selectionOrNull: SelectionHandle | null, transform: Transform, isMergeable: boolean, cloneRaster: boolean, correctChildren: boolean, duplicateNodes: boolean): DocumentCommandHandle;
        createTwirlFilterCommand(selectionOrNull: SelectionHandle | null, parameters: TwirlFilterParametersHandle): DocumentCommandHandle;
        createUndoCommand(): DocumentCommandHandle;
        createUngroupAllNodesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createUngroupNodesCommand(selectionOrNull: SelectionHandle | null): DocumentCommandHandle;
        createUnlinkTextFrameCommand(node: TextNodeHandle): DocumentCommandHandle;
        createUnlockAllCommand(): DocumentCommandHandle;
        createUnsharpMaskFilterCommand(selectionOrNull: SelectionHandle | null, parameters: UnsharpMaskFilterParametersHandle): DocumentCommandHandle;
        createVignetteFilterCommand(selectionOrNull: SelectionHandle | null, parameters: VignetteFilterParametersHandle): DocumentCommandHandle;
        createVoronoiFilterCommand(selectionOrNull: SelectionHandle | null, parameters: VoronoiFilterParametersHandle): DocumentCommandHandle;
        enumerateNewNodes(self: DocumentCommandHandle, callback: (node: NodeHandle) => EnumerationResult): void;
    }
    export const DocumentCommandApi: DocumentCommandApi;

    export interface SetHatchFillAttributesCommandBuilderApi {
        clone(self: SetHatchFillAttributesCommandBuilderHandle): SetHatchFillAttributesCommandBuilderHandle;
        create(): SetHatchFillAttributesCommandBuilderHandle;
        createBrushFillCommand(self: SetHatchFillAttributesCommandBuilderHandle, contentType: ContentType, bUseTextSelection: boolean, selectionOrNull: SelectionHandle | null, bApplyToAllFills: boolean): DocumentCommandHandle;
        createPenFillCommand(self: SetHatchFillAttributesCommandBuilderHandle, contentType: ContentType, bUseTextSelection: boolean, selectionOrNull: SelectionHandle | null, bApplyToAllFills: boolean): DocumentCommandHandle;
        createTransparencyFillCommand(self: SetHatchFillAttributesCommandBuilderHandle, contentType: ContentType, bUseTextSelection: boolean, selectionOrNull: SelectionHandle | null, bApplyToAllFills: boolean): DocumentCommandHandle;
        reset(self: SetHatchFillAttributesCommandBuilderHandle): void;
        setBrushColour(self: SetHatchFillAttributesCommandBuilderHandle, brushColourOrNull: ColourHandle | null): void;
        setFixScale(self: SetHatchFillAttributesCommandBuilderHandle, fixScale: boolean): void;
        setLineWeight(self: SetHatchFillAttributesCommandBuilderHandle, lineWeight: number): void;
        setPattern(self: SetHatchFillAttributesCommandBuilderHandle, pattern: HatchPatternHandle): void;
        setPenColour(self: SetHatchFillAttributesCommandBuilderHandle, penColourOrNull: ColourHandle | null): void;
        setRotation(self: SetHatchFillAttributesCommandBuilderHandle, rotationRads: number): void;
        setScale(self: SetHatchFillAttributesCommandBuilderHandle, scale: number): void;
        setUseCurrentItemOriginForRelativeTransform(self: SetHatchFillAttributesCommandBuilderHandle, useCurrentItemOriginForRelativeTransform: boolean): void;
        setUseRelativeTransform(self: SetHatchFillAttributesCommandBuilderHandle, useRelativeTransform: boolean): void;
    }
    export const SetHatchFillAttributesCommandBuilderApi: SetHatchFillAttributesCommandBuilderApi;

}
