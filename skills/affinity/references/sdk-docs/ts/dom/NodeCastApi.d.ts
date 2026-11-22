// Type declarations for the Affinity JavaScript SDK: module "affinity:dom", NodeCastApi.
//
// GENERATED FILE - do not edit. Produced by util/GenerateDTS.py from the SDK
// description in output/json-js. See handles.d.ts for the layout.

declare module "affinity:dom" {

    export interface NodeCastApi {
        create(): NodeCastHandle;
        exec(self: NodeCastHandle, node: NodeHandle): void;
        setAddNoiseFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: AddNoiseFilterRasterNodeHandle) => void): void;
        setAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: AdjustmentRasterNodeHandle) => void): void;
        setArtTextNodeHandler(self: NodeCastHandle, handler: (node: ArtTextNodeHandle) => void): void;
        setBilateralBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: BilateralBlurFilterRasterNodeHandle) => void): void;
        setBlackAndWhiteAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: BlackAndWhiteAdjustmentRasterNodeHandle) => void): void;
        setBloomFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: BloomFilterRasterNodeHandle) => void): void;
        setBoxBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: BoxBlurFilterRasterNodeHandle) => void): void;
        setBrightnessContrastAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: BrightnessContrastAdjustmentRasterNodeHandle) => void): void;
        setClarityFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: ClarityFilterRasterNodeHandle) => void): void;
        setColourBalanceAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: ColourBalanceAdjustmentRasterNodeHandle) => void): void;
        setColouredLogicalNodeHandler(self: NodeCastHandle, handler: (node: ColouredLogicalNodeHandle) => void): void;
        setContainerNodeHandler(self: NodeCastHandle, handler: (node: ContainerNodeHandle) => void): void;
        setCurvePathTextNodeHandler(self: NodeCastHandle, handler: (node: CurvePathTextNodeHandle) => void): void;
        setCurvesAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: CurvesAdjustmentRasterNodeHandle) => void): void;
        setDefringeFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: DefringeFilterRasterNodeHandle) => void): void;
        setDenoiseFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: DenoiseFilterRasterNodeHandle) => void): void;
        setDepthOfFieldFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: DepthOfFieldFilterRasterNodeHandle) => void): void;
        setDevelopNodeHandler(self: NodeCastHandle, handler: (node: DevelopNodeHandle) => void): void;
        setDiffuseFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: DiffuseFilterRasterNodeHandle) => void): void;
        setDiffuseGlowFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: DiffuseGlowFilterRasterNodeHandle) => void): void;
        setDocumentNodeHandler(self: NodeCastHandle, handler: (node: DocumentNodeHandle) => void): void;
        setDustAndScratchFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: DustAndScratchFilterRasterNodeHandle) => void): void;
        setEmbeddedDocumentNodeHandler(self: NodeCastHandle, handler: (node: EmbeddedDocumentNodeHandle) => void): void;
        setEnclosureRasterNodeHandler(self: NodeCastHandle, handler: (node: EnclosureRasterNodeHandle) => void): void;
        setExposureAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: ExposureAdjustmentRasterNodeHandle) => void): void;
        setFieldBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: FieldBlurFilterRasterNodeHandle) => void): void;
        setFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: FilterRasterNodeHandle) => void): void;
        setFrameTextNodeHandler(self: NodeCastHandle, handler: (node: FrameTextNodeHandle) => void): void;
        setGaussianBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: GaussianBlurFilterRasterNodeHandle) => void): void;
        setGroupNodeHandler(self: NodeCastHandle, handler: (node: GroupNodeHandle) => void): void;
        setHSLShiftAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: HSLShiftAdjustmentRasterNodeHandle) => void): void;
        setHalftoneFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: HalftoneFilterRasterNodeHandle) => void): void;
        setHighPassFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: HighPassFilterRasterNodeHandle) => void): void;
        setImageNodeHandler(self: NodeCastHandle, handler: (node: ImageNodeHandle) => void): void;
        setInvertAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: InvertAdjustmentRasterNodeHandle) => void): void;
        setLensBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: LensBlurFilterRasterNodeHandle) => void): void;
        setLevelsAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: LevelsAdjustmentRasterNodeHandle) => void): void;
        setLogicalNodeHandler(self: NodeCastHandle, handler: (node: LogicalNodeHandle) => void): void;
        setMaskRasterNodeHandler(self: NodeCastHandle, handler: (node: MaskRasterNodeHandle) => void): void;
        setMaximumBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: MaximumBlurFilterRasterNodeHandle) => void): void;
        setMeasurementNodeHandler(self: NodeCastHandle, handler: (node: MeasurementNodeHandle) => void): void;
        setMedianBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: MedianBlurFilterRasterNodeHandle) => void): void;
        setMinimumBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: MinimumBlurFilterRasterNodeHandle) => void): void;
        setMotionBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: MotionBlurFilterRasterNodeHandle) => void): void;
        setNodeHandler(self: NodeCastHandle, handler: (node: NodeHandle) => void): void;
        setNormalsAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: NormalsAdjustmentRasterNodeHandle) => void): void;
        setPatternRasterNodeHandler(self: NodeCastHandle, handler: (node: PatternRasterNodeHandle) => void): void;
        setPhysicalNodeHandler(self: NodeCastHandle, handler: (node: PhysicalNodeHandle) => void): void;
        setPinchPunchFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: PinchPunchFilterRasterNodeHandle) => void): void;
        setPixelateFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: PixelateFilterRasterNodeHandle) => void): void;
        setPolyCurveNodeHandler(self: NodeCastHandle, handler: (node: PolyCurveNodeHandle) => void): void;
        setPolyCurveTextNodeHandler(self: NodeCastHandle, handler: (node: PolyCurveTextNodeHandle) => void): void;
        setPosteriseAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: PosteriseAdjustmentRasterNodeHandle) => void): void;
        setRadialBlurFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: RadialBlurFilterRasterNodeHandle) => void): void;
        setRasterNodeHandler(self: NodeCastHandle, handler: (node: RasterNodeHandle) => void): void;
        setRecolourAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: RecolourAdjustmentRasterNodeHandle) => void): void;
        setRippleFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: RippleFilterRasterNodeHandle) => void): void;
        setSelectiveColourAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: SelectiveColourAdjustmentRasterNodeHandle) => void): void;
        setShadowsHighlightsAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: ShadowsHighlightsAdjustmentRasterNodeHandle) => void): void;
        setShadowsHighlightsFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: ShadowsHighlightsFilterRasterNodeHandle) => void): void;
        setShapeNodeHandler(self: NodeCastHandle, handler: (node: ShapeNodeHandle) => void): void;
        setShapePathTextNodeHandler(self: NodeCastHandle, handler: (node: ShapePathTextNodeHandle) => void): void;
        setShapeTextNodeHandler(self: NodeCastHandle, handler: (node: ShapeTextNodeHandle) => void): void;
        setSphericalFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: SphericalFilterRasterNodeHandle) => void): void;
        setSplitToningAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: SplitToningAdjustmentRasterNodeHandle) => void): void;
        setSpreadNodeHandler(self: NodeCastHandle, handler: (node: SpreadNodeHandle) => void): void;
        setTableTextNodeHandler(self: NodeCastHandle, handler: (node: TableTextNodeHandle) => void): void;
        setTextNodeHandler(self: NodeCastHandle, handler: (node: TextNodeHandle) => void): void;
        setThresholdAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: ThresholdAdjustmentRasterNodeHandle) => void): void;
        setToneCompressionAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: ToneCompressionAdjustmentRasterNodeHandle) => void): void;
        setToneStretchAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: ToneStretchAdjustmentRasterNodeHandle) => void): void;
        setTwirlFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: TwirlFilterRasterNodeHandle) => void): void;
        setUnsharpMaskFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: UnsharpMaskFilterRasterNodeHandle) => void): void;
        setVectorNodeHandler(self: NodeCastHandle, handler: (node: VectorNodeHandle) => void): void;
        setVibranceAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: VibranceAdjustmentRasterNodeHandle) => void): void;
        setVignetteFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: VignetteFilterRasterNodeHandle) => void): void;
        setVoronoiFilterRasterNodeHandler(self: NodeCastHandle, handler: (node: VoronoiFilterRasterNodeHandle) => void): void;
        setWhiteBalanceAdjustmentRasterNodeHandler(self: NodeCastHandle, handler: (node: WhiteBalanceAdjustmentRasterNodeHandle) => void): void;
    }
    export const NodeCastApi: NodeCastApi;

}
