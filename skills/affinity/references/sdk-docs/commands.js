'use strict';

const { ColourSpaceType } = require('affinity:colours');
const {
    AddChildNodesCommandBuilderApi,
    CommandApi,
    CompoundCommandBuilderApi,
    DocumentCommandApi,
    GroupTransformAnchor,
    GroupTransformData,
    GroupTransformOrder,
    GroupTransformType,
    InsertionMode,
    LineCommandDefaultsMode,
    SetHatchFillAttributesCommandBuilderApi
} = require('affinity:commands');
const { BlendMode, EnumerationResult, UnitType } = require('affinity:common');
const { AntialiasingMode, ContentType, NodeChildType, NodeMoveType, PageBoundingBoxType, PredefinedTagKey, RasterSelectionLogicalOperation, RasterSelectionOutlineAlignment, SpatialAnchor, VisibilityMode } = require('affinity:dom');
const { FillMask } = require('affinity:fills');
const { CurveNodeStyle, ShapeBoolParam, ShapeEnumParam, ShapeFloatParam, ShapeIntParam, WindingOrder } = require('affinity:geometry');
const { BevelEmbossType, StrokeFillType } = require('affinity:layereffects');
const { LineStyleMask, StrokeAlignment } = require('affinity:linestyles');
const { RasterFormat } = require('affinity:raster');
const { Colour } = require('./colours.js');
const { DocumentProperties } = require('./documentproperties.js');
const { FillDescriptor, SolidFill } = require('./fills.js');
const { Transform } = require('./geometry.js');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require("./nodes.js");

class Command extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Command';
    }

    get description() {
        return CommandApi.getDescription(this.handle);
    }
}

class DocumentCommand extends HandleObject {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'DocumentCommand';
    }
    
    get description() {
        return CommandApi.getDescription(this.handle);
    }

    enumerateNewNodes(callback) {
        if (typeof callback === 'function') {
            function wrapped(nodeHandle) {
                return callback(NodesModule.createTypedNode(nodeHandle));
            }
            return DocumentCommandApi.enumerateNewNodes(this.handle, wrapped);
        }
        return DocumentCommandApi.enumerateNewNodes(this.handle, callback);
    }

    get newNodes() {
        const res = [];
        this.enumerateNewNodes(node => {
            res.push(node);
            return EnumerationResult.Continue;
        });
        return res;
    }

    static createSetSelection(selection) {
        return new DocumentCommand(DocumentCommandApi.createSetSelectionCommand(selection?.handle));
    }
    
    static createDeleteSelection(selection, ignoreRasterSelection) {
        return new DocumentCommand(DocumentCommandApi.createDeleteNodesCommand(selection?.handle, ignoreRasterSelection));
    }
    
    static createHideSelection(selection) {
        return new DocumentCommand(DocumentCommandApi.createSetVisibilityCommand(selection?.handle, VisibilityMode.Main, false));
    }
    
    static createTransform(selection, xf, options) {
        if (!xf)
            xf = new Transform();
        return new DocumentCommand(DocumentCommandApi.createTransformCommand(
            selection?.handle,
            xf,
            options?.mergeable,
            options?.cloneRaster,
            options?.correctChildren,
            options?.duplicateNodes)
        );
    }

    static createSetBrushFill(selection, fillDescriptorOrColour, options) {
        if (fillDescriptorOrColour instanceof Colour || fillDescriptorOrColour instanceof SolidFill)
            fillDescriptorOrColour = FillDescriptor.createSolid(fillDescriptorOrColour);
        return new DocumentCommand(DocumentCommandApi.createSetBrushFillCommand(
            selection?.handle,
            fillDescriptorOrColour?.handle,
            options?.contentType ?? ContentType.Main,
            options?.fillMask ?? FillMask.All,
            options?.copyTransform ?? true,
            options?.useTextSelection,
            options?.maintainBlendMode,
            options?.restoreAspectRatio)
        );
    }

    static createSetPenFill(selection, fillDescriptorOrColour, options) {
        if (fillDescriptorOrColour instanceof Colour || fillDescriptorOrColour instanceof SolidFill)
            fillDescriptorOrColour = FillDescriptor.createSolid(fillDescriptorOrColour);
        return new DocumentCommand(DocumentCommandApi.createSetPenFillCommand(
            selection?.handle,
            fillDescriptorOrColour?.handle,
            options?.contentType ?? ContentType.Main,
            options?.fillMask ?? FillMask.All,
            options?.copyTransform ?? true,
            options?.useTextSelection,
            options?.maintainBlendMode,
            options?.restoreAspectRatio)
        );
    }

    static createSetTransparencyFill(selection, fillDescriptor, options) {
        return new DocumentCommand(DocumentCommandApi.createSetTransparencyFillCommand(
            selection?.handle,
            fillDescriptor?.handle,
            options?.contentType ?? ContentType.Main,
            options?.fillMask ?? FillMask.All,
            options?.copyTransform ?? true,
            options?.useTextSelection,
            options?.maintainBlendMode,
            options?.restoreAspectRatio)
        );
    }

    static createSetVisibility(selection, visible, options) {
        return new DocumentCommand(DocumentCommandApi.createSetVisibilityCommand(
            selection?.handle,
            options?.visibilityMode ?? VisibilityMode.Main,
            visible)
        );
    }

    static createSetLineStyle(selection, lineStyle, options) {
        return new DocumentCommand(DocumentCommandApi.createSetLineStyleCommand(
            selection?.handle,
            lineStyle.handle,
            options?.lineStyleMask,
            options?.contentType,
            options?.useTextSelection,
            options?.defaultsMode)
        );
    }

    static createSetLineStyleDescriptor(selection, lineStyleDescriptor, options) {
        return new DocumentCommand(DocumentCommandApi.createSetLineStyleDescriptorCommand(
            selection?.handle,
            lineStyleDescriptor.handle,
            options?.lineStyleMask,
            options?.contentType,
            options?.useTextSelection,
            options?.defaultsMode)
        );
    }

    static createSetStrokeAlignment(selection, strokeAlignment, options) {
        return new DocumentCommand(DocumentCommandApi.createSetStrokeAlignmentCommand(
            selection?.handle,
            strokeAlignment,
            options?.contentType,
            options?.useTextSelection,
            options?.defaultsMode)
        );
    }
    
    static createMoveNodes(selection, target, moveType, childListType) {
        return new DocumentCommand(DocumentCommandApi.createMoveNodesCommand(
            selection?.handle, 
            target.handle,
            moveType,
            childListType)
        );
    }

    static createMoveMappedNodes(selection, sources, targets, moveType) {
        return new DocumentCommand(DocumentCommandApi.createMoveMappedNodesCommand(
            selection?.handle, 
            sources.map(node => node.handle), 
            targets.map(node => node.handle),
            moveType)
        );
    }

    static createUndo() {
        return new DocumentCommand(DocumentCommandApi.createUndoCommand());
    }

    static createRedo() {
        return new DocumentCommand(DocumentCommandApi.createRedoCommand());
    }

    static createSetHistoryIndex(index) {
        return new DocumentCommand(DocumentCommandApi.createSetHistoryIndexCommand(index));
    }

    static createCycleAlternateFutures(index) {
        return new DocumentCommand(DocumentCommandApi.createCycleAlternateFuturesCommand(index));
    }

    static createSetShape(selection, shape, options) {
        return new DocumentCommand(DocumentCommandApi.createSetShapeCommand(selection?.handle, shape.handle, options?.allowReplaceLikeShapes));
    }

    static createSetShapeFloatParam(selection, key, value, options) {
        return new DocumentCommand(DocumentCommandApi.createSetShapeFloatParamCommand(selection?.handle, key, value, options?.constrained, options?.symmetrical));
    }

    static createSetShapeIntParam(selection, key, value) {
        return new DocumentCommand(DocumentCommandApi.createSetShapeIntParamCommand(selection?.handle, key, value));
    }

    static createSetShapeBoolParam(selection, key, value) {
        return new DocumentCommand(DocumentCommandApi.createSetShapeBoolParamCommand(selection?.handle, key, value));
    }

    static createSetShapeEnumParam(selection, key, value) {
        return new DocumentCommand(DocumentCommandApi.createSetShapeEnumParamCommand(selection?.handle, key, value));
    }

    static createShowAll() {
        return new DocumentCommand(DocumentCommandApi.createShowAllCommand());
    }

    static createSelectAll(selectOnCurrentLayerOnly) {
        return new DocumentCommand(DocumentCommandApi.createSelectAllCommand(selectOnCurrentLayerOnly));
    }

    static createSetText(selection, text) {
        return new DocumentCommand(DocumentCommandApi.createSetTextCommand(selection?.handle, text));
    }

    static createInsertGlyph(selection, glyph) {
        return new DocumentCommand(DocumentCommandApi.createInsertGlyphCommand(selection?.handle, glyph.handle));
    }

    static createFormatText(selection, delta) {
        return new DocumentCommand(DocumentCommandApi.createFormatTextCommand(selection?.handle, delta.handle));
    }

    static createSetTagColour(selection, colour) {
        return new DocumentCommand(DocumentCommandApi.createSetTagColourCommand(selection?.handle, colour.handle));
    }

    static createSetCurveNodeStyle(selection, style) {
        return new DocumentCommand(DocumentCommandApi.createSetCurveNodeStyleCommand(selection?.handle, style));
    }

    static createDeleteCurveNodes(selection) {
        return new DocumentCommand(DocumentCommandApi.createDeleteCurveNodesCommand(selection?.handle));
    }

    static createAddCurveNode(curvesInterface, curveHandle, parametricDistance) {
        return new DocumentCommand(DocumentCommandApi.createAddCurveNodeCommand(curvesInterface.handle, curveHandle, parametricDistance));
    }

    static createAddCurve(curvesInterface, curve, select, preserveExistingSubSelection) {
        return new DocumentCommand(DocumentCommandApi.createAddCurveCommand(curvesInterface.handle, curve.handle, select, preserveExistingSubSelection));
    }

    static createSetDescription(selection, description) {
        return new DocumentCommand(DocumentCommandApi.createSetDescriptionCommand(selection?.handle, description));
    }
    
    
    static createSetEmbeddedDocumentLayerVisibility(selection, layer, visibility) {
        return new DocumentCommand(DocumentCommandApi.createSetEmbeddedDocumentLayerVisibilityCommand(selection?.handle, layer, visibility));
    }
    
    static createSetEmbeddedDocumentAllLayersVisibility(selection, visibilities) {
        return new DocumentCommand(DocumentCommandApi.createSetEmbeddedDocumentAllLayersVisibilityCommand(selection?.handle, visibilities));
    }
    
    static createSetEmbeddedDocumentSelectedArtboardID(selection, artboardID) {
        return new DocumentCommand(DocumentCommandApi.createSetEmbeddedDocumentSelectedArtboardIDCommand(selection?.handle, artboardID));
    }
    
    static createSetEmbeddedDocumentSelectedSpreadID(selection, spreadID) {
        return new DocumentCommand(DocumentCommandApi.createSetEmbeddedDocumentSelectedSpreadIDCommand(selection?.handle, spreadID));
    }
    
    static createSetEmbeddedDocumentPageBoundingBoxType(selection, pageBoundingBoxType) {
        return new DocumentCommand(DocumentCommandApi.createSetEmbeddedDocumentPageBoundingBoxTypeCommand(selection?.handle, pageBoundingBoxType));
    }
    
    static createSetEmbeddedDocumentPDFPassthrough(selection, isPDFPassthrough) {
        return new DocumentCommand(DocumentCommandApi.createSetEmbeddedDocumentPDFPassthroughCommand(selection?.handle, isPDFPassthrough));
    }

    static createKnifeCut(cutCurve, selection) {
        return new DocumentCommand(DocumentCommandApi.createKnifeCutCommand(cutCurve.handle, selection?.handle));
    }

    static createScissorCut(node, polyCurveIndex, curveIndex, isParametric, distance) {
        return new DocumentCommand(DocumentCommandApi.createScissorCutCommand(node.handle, polyCurveIndex, curveIndex, isParametric, distance));
    }

    static createSplitCurve(selection, parametricDistance) {
        return new DocumentCommand(DocumentCommandApi.createSplitCurveCommand(selection?.handle, parametricDistance));
    }
    
    static createImportMacro(path) {
        return new DocumentCommand(DocumentCommandApi.createImportMacroCommand(path));
    }
    
    static createExportMacro(path) {
        return new DocumentCommand(DocumentCommandApi.createExportMacroCommand(path));
    }
    
    static createGenerateImage(prompt) {
        return new DocumentCommand(DocumentCommandApi.createGenerateImageCommand(prompt));
    }
    
    static createDetectDepth() {
        return new DocumentCommand(DocumentCommandApi.createDetectDepthCommand());
    }
    
    static createColourise() {
        return new DocumentCommand(DocumentCommandApi.createColouriseCommand());
    }
    
    static createGenerativeEditImage(prompt) {
        return new DocumentCommand(DocumentCommandApi.createGenerativeEditImageCommand(prompt));
    }
    
    static createReplayMacro() {
        return new DocumentCommand(DocumentCommandApi.createReplayMacroCommand());
    }
    
    static createClearMacro() {
        return new DocumentCommand(DocumentCommandApi.createClearMacroCommand());
    }
    
    static createStartRecordingMacro() {
        return new DocumentCommand(DocumentCommandApi.createStartRecordingMacroCommand());
    }
    
    static createStopRecordingMacro() {
        return new DocumentCommand(DocumentCommandApi.createStopRecordingMacroCommand());
    }
    
    static createRemoveBackground() {
        return new DocumentCommand(DocumentCommandApi.createRemoveBackgroundCommand());
    }
    
    static createSelectSubject() {
        return new DocumentCommand(DocumentCommandApi.createSelectSubjectCommand());
    }

    static createSetEditable(selection, editable) {
        return new DocumentCommand(DocumentCommandApi.createSetEditableCommand(selection?.handle, editable));
    }

    static createSetArtboardEnabled(selection, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetArtboardEnabledCommand(selection?.handle, enabled));
    }

    static createSetDocumentUnits(units) {
        return new DocumentCommand(DocumentCommandApi.createSetDocumentUnitsCommand(units));
    }

    static createAddGuide(horizontal, at) {
        return new DocumentCommand(DocumentCommandApi.createAddGuideCommand(horizontal, at));
    }

    static createAddHorizontalGuide(pixels) {
        return DocumentCommand.createAddGuide(true, pixels);
    }

    static createAddVerticalGuide(pixels) {
        return DocumentCommand.createAddGuide(false, pixels);
    }

    static createMoveGuide(horizontal, index, newPixels) {
        return new DocumentCommand(DocumentCommandApi.createMoveGuideCommand(horizontal, index, newPixels));
    }

    static createMoveHorizontalGuide(index, newPixels) {
        return DocumentCommand.createMoveGuide(true, index, newPixels);
    }

    static createMoveVerticalGuide(index, newPixels) {
        return DocumentCommand.createMoveGuide(false, index, newPixels);
    }

    static createRemoveGuide(horizontal, index) {
        return new DocumentCommand(DocumentCommandApi.createRemoveGuideCommand(horizontal, index));
    }

    static createRemoveHorizontalGuide(index) {
        return DocumentCommand.createRemoveGuide(true, index);
    }

    static createRemoveVerticalGuide(index) {
        return DocumentCommand.createRemoveGuide(false, index);
    }

    static createSetGuidesColour(colour) {
        return new DocumentCommand(DocumentCommandApi.createSetGuidesColourCommand(colour.handle));
    }

    static createRasteriseObjects(selection, rasteriseContentsOnly, clipToSpread) {
        return new DocumentCommand(DocumentCommandApi.createRasteriseObjectsCommand(selection?.handle, rasteriseContentsOnly, clipToSpread));
    }
    
    static createConvertToCurves(selection) {
        return new DocumentCommand(DocumentCommandApi.createConvertToCurvesCommand(selection?.handle));
    }

    static createSetBrushFillIsAnchoredToSpread(selection, anchoredToSpread, options) {
        return new DocumentCommand(DocumentCommandApi.createSetBrushFillIsAnchoredToSpreadCommand(
            selection?.handle,
            anchoredToSpread,
            options?.contentType,
            options?.useTextSelection,
            options?.applyToAllFills
        ));
    }

    static createSetPenFillIsAnchoredToSpread(selection, anchoredToSpread, options) {
        return new DocumentCommand(DocumentCommandApi.createSetPenFillIsAnchoredToSpreadCommand(
            selection?.handle,
            anchoredToSpread,
            options?.contentType,
            options?.useTextSelection,
            options?.applyToAllFills
        ));
    }

    static createSetTransparencyFillIsAnchoredToSpread(selection, anchoredToSpread, options) {
        return new DocumentCommand(DocumentCommandApi.createSetTransparencyFillIsAnchoredToSpreadCommand(
            selection?.handle,
            anchoredToSpread,
            options?.contentType,
            options?.useTextSelection,
            options?.applyToAllFills
        ));
    }

    static #createHatchFillAttributesCommandBuilder(attr) {
        const builder = SetHatchFillAttributesCommandBuilder.create();
        if (attr.pattern !== undefined)
            builder.pattern = attr.pattern;
        if (attr.penColour !== undefined)
            builder.penColour = attr.penColour;
        if (attr.brushColour !== undefined)
            builder.brushColour = attr.brushColour;
        if (attr.scale !== undefined)
            builder.scale = attr.scale;
        if (attr.rotation !== undefined)
            builder.rotation = attr.rotation;
        if (attr.lineWeight !== undefined)
            builder.lineWeight = attr.lineWeight;
        if (attr.fixScale !== undefined)
            builder.fixScale = attr.fixScale;
        if (attr.useRelativeTransform !== undefined)
            builder.useRelativeTransform = attr.useRelativeTransform;
        if (attr.useCurrentItemOriginForRelativeTransform !== undefined)
            builder.useCurrentItemOriginForRelativeTransform = attr.useCurrentItemOriginForRelativeTransform;
        return builder;
    }
    
    static createSetBrushHatchFillAttributes(selection, attr, options) {
        const builder = DocumentCommand.#createHatchFillAttributesCommandBuilder(attr);
        return builder.createBrushFillCommand(selection,
            options?.contentType ?? ContentType.Main,
            options?.useTextSelection,
            options?.applyToAllFills);
    }

    static createSetPenHatchFillAttributes(attr, selection, options) {
        const builder = DocumentCommand.#createHatchFillAttributesCommandBuilder(attr);
        return builder.createPenFillCommand(selection,
            options?.contentType ?? ContentType.Main,
            options?.useTextSelection,
            options?.applyToAllFills);
    }

    static createSetTransparencyHatchFillAttributes(attr, selection, options) {
        const builder = DocumentCommand.#createHatchFillAttributesCommandBuilder(attr);
        return builder.createTransparencyFillCommand(selection,
            options?.contentType ?? ContentType.Main,
            options?.useTextSelection,
            options?.applyToAllFills);
    }
    
    static createReplaceBitmap(selection, bitmap) {
        return new DocumentCommand(DocumentCommandApi.createReplaceBitmapCommand(selection?.handle, bitmap.handle));
    }

    static createSetCurves(curvesInterface, polyCurve) {
        return new DocumentCommand(DocumentCommandApi.createSetCurvesCommand(curvesInterface.handle, polyCurve.handle));
    }

    static createClearPreviews() {
        return new DocumentCommand(DocumentCommandApi.createClearPreviewsCommand());
    }

    static createFlatten() {
        return new DocumentCommand(DocumentCommandApi.createFlattenCommand());
    }

    static createMergeVisible() {
        return new DocumentCommand(DocumentCommandApi.createMergeVisibleCommand());
    }
    
    static createAddDocumentSnapshot(description) {
        return new DocumentCommand(DocumentCommandApi.createAddDocumentSnapshotCommand(description));
    }

    static createDeleteDocumentSnapshot(snapshot) {
        return new DocumentCommand(DocumentCommandApi.createDeleteDocumentSnapshotCommand(snapshot.handle));
    }

    static createRestoreDocumentSnapshot(snapshot) {
        return new DocumentCommand(DocumentCommandApi.createRestoreDocumentSnapshotCommand(snapshot.handle));
    }

    static createSetCurrentSnapshot(snapshot) {
        return new DocumentCommand(DocumentCommandApi.createSetCurrentSnapshotCommand(snapshot.handle));
    }

    static createSetCurrentSnapshotFromHistoryItem(historyItem) {
        return new DocumentCommand(DocumentCommandApi.createSetCurrentSnapshotFromHistoryItemCommand(historyItem.handle));
    }

    static createSetGaussianBlurFilterParameters(selection, gaussianBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetGaussianBlurFilterParametersCommand(selection?.handle, gaussianBlurParameters));
    }
    
    static createSetBilateralBlurFilterParameters(selection, bilateralBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetBilateralBlurFilterParametersCommand(selection?.handle, bilateralBlurParameters));
    }
    
    static createSetBoxBlurFilterParameters(selection, boxBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetBoxBlurFilterParametersCommand(selection?.handle, boxBlurParameters));
    }
    
    static createSetMedianBlurFilterParameters(selection, medianBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetMedianBlurFilterParametersCommand(selection?.handle, medianBlurParameters));
    }
    
    static createSetDiffuseGlowFilterParameters(selection, diffuseGlowParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetDiffuseGlowFilterParametersCommand(selection?.handle, diffuseGlowParameters));
    }
    
    static createSetFieldBlurFilterParameters(selection, fieldBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetFieldBlurFilterParametersCommand(selection?.handle, fieldBlurParameters.handle));
    }
    
    static createSetDepthOfFieldFilterParameters(selection, depthOfFieldParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetDepthOfFieldFilterParametersCommand(selection?.handle, depthOfFieldParameters.handle));
    }
    
    static createSetLensBlurFilterParameters(selection, lensBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetLensBlurFilterParametersCommand(selection?.handle, lensBlurParameters));
    }
    
    static createSetMaximumBlurFilterParameters(selection, maximumBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetMaximumBlurFilterParametersCommand(selection?.handle, maximumBlurParameters));
    }
    
    static createSetMinimumBlurFilterParameters(selection, minimumBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetMinimumBlurFilterParametersCommand(selection?.handle, minimumBlurParameters));
    }
    
    static createSetMotionBlurFilterParameters(selection, motionBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetMotionBlurFilterParametersCommand(selection?.handle, motionBlurParameters));
    }
    
    static createSetShadowsHighlightsFilterParameters(selection, parameters) {
        return new DocumentCommand(DocumentCommandApi.createSetShadowsHighlightsFilterParametersCommand(selection?.handle, parameters));
    }
    
    static createSetRadialBlurFilterParameters(selection, radialBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetRadialBlurFilterParametersCommand(selection?.handle, radialBlurParameters));
    }
    
    static createSetExposureAdjustmentParameters(selection, exposureAdjustmentParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetExposureAdjustmentParametersCommand(selection?.handle, exposureAdjustmentParameters));
    }
    
    static createSetLevelsAdjustmentParameters(selection, levelsAdjustmentParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetLevelsAdjustmentParametersCommand(selection?.handle, levelsAdjustmentParameters));
    }
    
    static createSetLevelsAdjustmentColourSpace(selection, colourSpace) {
        return new DocumentCommand(DocumentCommandApi.createSetLevelsAdjustmentColourSpaceCommand(selection?.handle, colourSpace));
    }
    
    static createSetBrightnessContrastAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetBrightnessContrastAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetShadowsHighlightsAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetShadowsHighlightsAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetBlackAndWhiteAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetBlackAndWhiteAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetRecolourAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetRecolourAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetPosteriseAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetPosteriseAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetSplitToningAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetSplitToningAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetThresholdAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetThresholdAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetClarityFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetClarityFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetUnsharpMaskFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetUnsharpMaskFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetHighPassFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetHighPassFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetDenoiseFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetDenoiseFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetDiffuseFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetDiffuseFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetDustAndScratchFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetDustAndScratchFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetAddNoiseFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetAddNoiseFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetBloomFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetBloomFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetPixelateFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetPixelateFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetHalftoneFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetHalftoneFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetRippleFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetRippleFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetTwirlFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetTwirlFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetSphericalFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetSphericalFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetPinchPunchFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetPinchPunchFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetWhiteBalanceAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetWhiteBalanceAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetColourBalanceAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetColourBalanceAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetVibranceAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetVibranceAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetNormalsAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetNormalsAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetVignetteFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetVignetteFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetDefringeFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetDefringeFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetVoronoiFilterParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetVoronoiFilterParametersCommand(selection?.handle, params));
    }
    
    static createSetSelectiveColourAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetSelectiveColourAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetHSLShiftAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetHSLShiftAdjustmentParametersCommand(selection?.handle, params.handle));
    }
    
    static createSetCurvesAdjustmentParameters(selection, curvesAdjustmentParameters) {
        return new DocumentCommand(DocumentCommandApi.createSetCurvesAdjustmentParametersCommand(selection?.handle, curvesAdjustmentParameters.handle));
    }
    
    static createSetCurvesAdjustmentColourSpace(selection, colourSpace) {
        return new DocumentCommand(DocumentCommandApi.createSetCurvesAdjustmentColourSpaceCommand(selection?.handle, colourSpace));
    }
    
    static createSetBlendGamma(selection, gamma) {
        return new DocumentCommand(DocumentCommandApi.createSetBlendGammaCommand(selection?.handle, gamma));
    }
    
    static createSetBlendRanges(selection, blendOptions) {
        return new DocumentCommand(DocumentCommandApi.createSetBlendRangesCommand(selection?.handle, blendOptions.handle));
    }
    
    static createSetTagValueForKey(selection, key, value) {
        return new DocumentCommand(DocumentCommandApi.createSetTagValueForKeyCommand(selection?.handle, key, value));
    }
    
    static createSetTagValueForPredefinedKey(selection, predefinedKey, value) {
        return new DocumentCommand(DocumentCommandApi.createSetTagValueForPredefinedKeyCommand(selection?.handle, predefinedKey, value));
    }
    
    static createSetToneCompressionAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetToneCompressionAdjustmentParametersCommand(selection?.handle, params));
    }
    
    static createSetToneStretchAdjustmentParameters(selection, params) {
        return new DocumentCommand(DocumentCommandApi.createSetToneStretchAdjustmentParametersCommand(selection?.handle, params));
    }

    static createRasterSelectAll() {
        return new DocumentCommand(DocumentCommandApi.createRasterSelectAllCommand());
    }

    static createRasterDeselect() {
        return new DocumentCommand(DocumentCommandApi.createRasterDeselectCommand());
    }

    static createRasterInvertSelection() {
        return new DocumentCommand(DocumentCommandApi.createRasterInvertSelectionCommand());
    }

    static createRasterReselect() {
        return new DocumentCommand(DocumentCommandApi.createRasterReselectCommand());
    }

    static createSetRasterSelectionFromPolygon(polygon, operation, isAntialias, featherRadius) {
        return new DocumentCommand(DocumentCommandApi.createSetRasterSelectionFromPolygonCommand(polygon, operation, isAntialias, featherRadius));
    }

    static createSetRasterSelectionFromObject(node, useIntensity, operation) {
        return new DocumentCommand(DocumentCommandApi.createSetRasterSelectionFromObjectCommand(node?.handle, useIntensity, operation));
    }

    /**
    * @deprecated Use createSetRasterSelectionFromPolygon instead.
    */
    static createRasterSelectPolygon(polygon, operation, isAntialias, featherRadius) {
        console.warn("Using deprecated DocumentCommand.createRasterSelectPolygon() function. Use createSetRasterSelectionFromPolygon() instead.");
        return DocumentCommand.createSetRasterSelectionFromPolygon(polygon, operation, isAntialias, featherRadius);
    }

    static createGrowShrinkRasterSelection(radius, circular) {
        return new DocumentCommand(DocumentCommandApi.createGrowShrinkRasterSelectionCommand(radius, circular));
    }
    
    static createFeatherRasterSelection(radius) {
        return new DocumentCommand(DocumentCommandApi.createFeatherRasterSelectionCommand(radius));
    }
    
    static createSmoothRasterSelection(radius) {
        return new DocumentCommand(DocumentCommandApi.createSmoothRasterSelectionCommand(radius));
    }
    
    static createOutlineRasterSelection(radius, alignment, circular) {
        return new DocumentCommand(DocumentCommandApi.createOutlineRasterSelectionCommand(radius, alignment, circular));
    }
    
    static createGaussianBlurFilter(selection, gaussianBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createGaussianBlurFilterCommand(selection?.handle, gaussianBlurParameters));
    }

    static createBoxBlurFilter(selection, boxBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createBoxBlurFilterCommand(selection?.handle, boxBlurParameters));
    }

    static createBilateralBlurFilter(selection, bilateralBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createBilateralBlurFilterCommand(selection?.handle, bilateralBlurParameters));
    }

    static createMedianBlurFilter(selection, medianBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createMedianBlurFilterCommand(selection?.handle, medianBlurParameters));
    }

    static createDiffuseGlowFilter(selection, diffuseGlowParameters) {
        return new DocumentCommand(DocumentCommandApi.createDiffuseGlowFilterCommand(selection?.handle, diffuseGlowParameters));
    }

    static createFieldBlurFilter(selection, fieldBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createFieldBlurFilterCommand(selection?.handle, fieldBlurParameters.handle));
    }

    static createDepthOfFieldFilter(selection, depthOfFieldParameters) {
        return new DocumentCommand(DocumentCommandApi.createDepthOfFieldFilterCommand(selection?.handle, depthOfFieldParameters.handle));
    }

    static createLensBlurFilter(selection, lensBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createLensBlurFilterCommand(selection?.handle, lensBlurParameters));
    }

    static createMaximumBlurFilter(selection, maximumBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createMaximumBlurFilterCommand(selection?.handle, maximumBlurParameters));
    }

    static createMinimumBlurFilter(selection, minimumBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createMinimumBlurFilterCommand(selection?.handle, minimumBlurParameters));
    }

    static createMotionBlurFilter(selection, motionBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createMotionBlurFilterCommand(selection?.handle, motionBlurParameters));
    }

    static createShadowsHighlightsFilter(selection, parameters) {
        return new DocumentCommand(DocumentCommandApi.createShadowsHighlightsFilterCommand(selection?.handle, parameters));
    }

    static createRadialBlurFilter(selection, radialBlurParameters) {
        return new DocumentCommand(DocumentCommandApi.createRadialBlurFilterCommand(selection?.handle, radialBlurParameters));
    }

    static createClarityFilter(selection, clarityFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createClarityFilterCommand(selection?.handle, clarityFilterParameters));
    }

    static createUnsharpMaskFilter(selection, unsharpMaskFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createUnsharpMaskFilterCommand(selection?.handle, unsharpMaskFilterParameters));
    }

    static createHighPassFilter(selection, highPassFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createHighPassFilterCommand(selection?.handle, highPassFilterParameters));
    }

    static createDenoiseFilter(selection, denoiseFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createDenoiseFilterCommand(selection?.handle, denoiseFilterParameters));
    }

    static createDiffuseFilter(selection, diffuseFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createDiffuseFilterCommand(selection?.handle, diffuseFilterParameters));
    }

    static createDustAndScratchFilter(selection, dustAndScratchFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createDustAndScratchFilterCommand(selection?.handle, dustAndScratchFilterParameters));
    }

    static createAddNoiseFilter(selection, addNoiseFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createAddNoiseFilterCommand(selection?.handle, addNoiseFilterParameters));
    }

    static createBloomFilter(selection, bloomFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createBloomFilterCommand(selection?.handle, bloomFilterParameters));
    }
    
    static createPixelateFilter(selection, pixelateFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createPixelateFilterCommand(selection?.handle, pixelateFilterParameters));
    }
    
    static createHalftoneFilter(selection, halftoneFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createHalftoneFilterCommand(selection?.handle, halftoneFilterParameters));
    }

    static createRippleFilter(selection, rippleFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createRippleFilterCommand(selection?.handle, rippleFilterParameters));
    }

    static createTwirlFilter(selection, twirlFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createTwirlFilterCommand(selection?.handle, twirlFilterParameters));
    }

    static createSphericalFilter(selection, sphericalFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createSphericalFilterCommand(selection?.handle, sphericalFilterParameters));
    }

    static createPinchPunchFilter(selection, pinchPunchFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createPinchPunchFilterCommand(selection?.handle, pinchPunchFilterParameters));
    }

    static createVignetteFilter(selection, vignetteFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createVignetteFilterCommand(selection?.handle, vignetteFilterParameters));
    }

    static createDefringeFilter(selection, defringeFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createDefringeFilterCommand(selection?.handle, defringeFilterParameters));
    }

    static createVoronoiFilter(selection, voronoiFilterParameters) {
        return new DocumentCommand(DocumentCommandApi.createVoronoiFilterCommand(selection?.handle, voronoiFilterParameters));
    }

    static createGroupTransform(selection, xDataOrNull, yDataOrNull) {
        return new DocumentCommand(DocumentCommandApi.createGroupTransformCommand(selection?.handle, xDataOrNull, yDataOrNull));
    }
    
    static createConvertDocumentFormat(format) {
        return new DocumentCommand(DocumentCommandApi.createConvertDocumentFormatCommand(format));
    }

    static createSetCurrentSpread(spreadNode) {
        return new DocumentCommand(DocumentCommandApi.createSetCurrentSpreadCommand(spreadNode?.handle));
    }

    static createSetWindingMode(selection, windingOrder) {
        return new DocumentCommand(DocumentCommandApi.createSetWindingModeCommand(selection?.handle, windingOrder));
    }

    static createImageTrace(selection, edgeThreshold, curveFittingTolerance) {
        return new DocumentCommand(DocumentCommandApi.createImageTraceCommand(selection?.handle, edgeThreshold, curveFittingTolerance));
    }

    static createSetBlendMode(selection, blendMode, setPassthrough = false) {
        return new DocumentCommand(DocumentCommandApi.createSetBlendModeCommand(selection?.handle, blendMode, setPassthrough));
    }

    static createSetAntialiasingMode(selection, antialiasingMode) {
        return new DocumentCommand(DocumentCommandApi.createSetAntialiasingModeCommand(selection?.handle, antialiasingMode));
    }

    static createSetDocumentProperties(documentProperties) {
        return new DocumentCommand(DocumentCommandApi.createSetDocumentPropertiesCommand(documentProperties.handle));
    }

    static createSetExportConfig(selection, exportConfig) {
        return new DocumentCommand(DocumentCommandApi.createSetExportConfigCommand(selection?.handle, exportConfig.handle));
    }

    static createSetOpacity(selection, opacity) {
        return new DocumentCommand(DocumentCommandApi.createSetOpacityCommand(selection?.handle, opacity));
    }

    static createSetBrushFillOpacity(selection, opacity, options) {
        return new DocumentCommand(DocumentCommandApi.createSetBrushFillOpacityCommand(
            selection?.handle,
            opacity,
            options?.contentType ?? ContentType.Main,
            options?.useTextSelection
        ));
    }

    static createSetLineFillOpacity(selection, opacity, options) {
        return new DocumentCommand(DocumentCommandApi.createSetLineFillOpacityCommand(
            selection?.handle,
            opacity,
            options?.contentType ?? ContentType.Main,
            options?.useTextSelection
        ));
    }

    static createAddArtboard(artboardDefinition, copyProperties, copyGuides) {
        return new DocumentCommand(DocumentCommandApi.createAddArtboardCommand(artboardDefinition?.handle, copyProperties, copyGuides));
    }

    // LayerEffectCommands
    static createSetAllLayerEffectsScaleWithObject(selection, scaleWithObject) {
        return new DocumentCommand(DocumentCommandApi.createSetAllLayerEffectsScaleWithObjectCommand(selection?.handle, scaleWithObject));
    }

    static createRemoveAllLayerEffects(selection) {
        return new DocumentCommand(DocumentCommandApi.createRemoveAllLayerEffectsCommand(selection?.handle));
    }

    // BevelEmbossLayerEffectCommands
    static createSetBevelEmbossLayerEffectBlendMode(selection, blendMode, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectBlendModeCommand(selection?.handle, blendMode, enableIfDisabled));
    }

    static createDuplicateBevelEmbossLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateBevelEmbossLayerEffectCommand(selection?.handle));
    }

    static createSetBevelEmbossLayerEffectEnabled(selection, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectEnabledCommand(selection?.handle, enabled));
    }

    static createSetBevelEmbossLayerEffectOpacity(selection, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectOpacityCommand(selection?.handle, opacity, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectRadius(selection, radius, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectRadiusCommand(selection?.handle, radius, enableIfDisabled));
    }

    static createRemoveBevelEmbossLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createRemoveBevelEmbossLayerEffectCommand(selection?.handle));
    }

    static createSetBevelEmbossLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectScaleWithObjectCommand(selection?.handle, scaleWithObject, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffect(selection, layerEffect) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectCommand(selection?.handle, layerEffect?.handle));
    }

    static createSetBevelEmbossLayerEffectHighlightColour(selection, colour, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectHighlightColourCommand(selection?.handle, colour?.handle, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectHighlightBlendMode(selection, blendMode, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectHighlightBlendModeCommand(selection?.handle, blendMode, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectHighlightOpacity(selection, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectHighlightOpacityCommand(selection?.handle, opacity, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectShadowColour(selection, colour, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectShadowColourCommand(selection?.handle, colour?.handle, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectDirection(selection, azimuth, elevation, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectDirectionCommand(selection?.handle, azimuth, elevation, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectInverted(selection, inverted, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectInvertedCommand(selection?.handle, inverted, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectLinkDepth(selection, linkDepth, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectLinkDepthCommand(selection?.handle, linkDepth, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectAzimuth(selection, azimuth, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectAzimuthCommand(selection?.handle, azimuth, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectDepth(selection, depth, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectDepthCommand(selection?.handle, depth, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectElevation(selection, elevation, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectElevationCommand(selection?.handle, elevation, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectShadowOpacity(selection, shadowOpacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectShadowOpacityCommand(selection?.handle, shadowOpacity, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectSoften(selection, soften, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectSoftenCommand(selection?.handle, soften, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectShadowBlendMode(selection, blendMode, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectShadowBlendModeCommand(selection?.handle, blendMode, enableIfDisabled));
    }

    static createSetBevelEmbossLayerEffectType(selection, bevelType, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetBevelEmbossLayerEffectTypeCommand(selection?.handle, bevelType, enableIfDisabled));
    }

    // OutlineLayerEffectCommands
    static createSetOutlineLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectBlendModeCommand(selection?.handle, blendMode, index, enableIfDisabled));
    }

    static createDuplicateOutlineLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateOutlineLayerEffectCommand(selection?.handle, index));
    }

    static createSetOutlineLayerEffectEnabled(selection, index, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectEnabledCommand(selection?.handle, index, enabled));
    }

    static createMoveOutlineLayerEffect(selection, fromIndex, toIndex) {
        return new DocumentCommand(DocumentCommandApi.createMoveOutlineLayerEffectCommand(selection?.handle, fromIndex, toIndex));
    }

    static createSetOutlineLayerEffectOpacity(selection, index, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectOpacityCommand(selection?.handle, index, opacity, enableIfDisabled));
    }

    static createSetOutlineLayerEffectRadius(selection, index, radius, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectRadiusCommand(selection?.handle, index, radius, enableIfDisabled));
    }

    static createRemoveOutlineLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createRemoveOutlineLayerEffectCommand(selection?.handle, index));
    }

    static createSetOutlineLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectScaleWithObjectCommand(selection?.handle, index, scaleWithObject, enableIfDisabled));
    }

    static createSetOutlineLayerEffect(selection, layerEffect, index) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectCommand(selection?.handle, layerEffect?.handle, index));
    }

    static createSetOutlineLayerEffectAlignment(selection, alignment, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectAlignmentCommand(selection?.handle, alignment, enableIfDisabled));
    }

    static createSetOutlineLayerEffectColour(selection, colour, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectColourCommand(selection?.handle, colour?.handle, index, enableIfDisabled));
    }

    static createSetOutlineLayerEffectFill(selection, gradientFill, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectFillCommand(selection?.handle, gradientFill?.handle, enableIfDisabled));
    }

    static createSetOutlineLayerEffectFillTransform(selection, fillDescriptor, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectFillTransformCommand(selection?.handle, fillDescriptor?.handle, enableIfDisabled));
    }

    static createSetOutlineLayerEffectFillType(selection, fillType, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOutlineLayerEffectFillTypeCommand(selection?.handle, fillType, enableIfDisabled));
    }

    // PhongBevelLayerEffectCommands
    static createDuplicatePhongBevelLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createDuplicatePhongBevelLayerEffectCommand(selection?.handle));
    }

    static createSetPhongBevelLayerEffectEnabled(selection, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectEnabledCommand(selection?.handle, enabled));
    }

    static createSetPhongBevelLayerEffectOpacity(selection, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectOpacityCommand(selection?.handle, opacity, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectRadius(selection, radius, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectRadiusCommand(selection?.handle, radius, enableIfDisabled));
    }

    static createRemovePhongBevelLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createRemovePhongBevelLayerEffectCommand(selection?.handle));
    }

    static createSetPhongBevelLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectScaleWithObjectCommand(selection?.handle, scaleWithObject, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffect(selection, layerEffect) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectCommand(selection?.handle, layerEffect?.handle));
    }

    static createSetPhongBevelLayerEffectAmbient(selection, ambient, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectAmbientCommand(selection?.handle, ambient, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectAmbientColour(selection, colour, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectAmbientColourCommand(selection?.handle, colour?.handle, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectDepth(selection, depth, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectDepthCommand(selection?.handle, depth, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectDiffuse(selection, diffuse, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectDiffuseCommand(selection?.handle, diffuse, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectLinkDepth(selection, linkDepth, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectLinkDepthCommand(selection?.handle, linkDepth, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectShininess(selection, shininess, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectShininessCommand(selection?.handle, shininess, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectSoften(selection, soften, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectSoftenCommand(selection?.handle, soften, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectSpecular(selection, specular, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectSpecularCommand(selection?.handle, specular, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectSpecularColour(selection, colour, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectSpecularColourCommand(selection?.handle, colour?.handle, enableIfDisabled));
    }

    static createSetPhongBevelLayerEffectLights(selection, lights, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetPhongBevelLayerEffectLightsCommand(selection?.handle, lights?.map(l => l?.handle), enableIfDisabled));
    }

    // InnerShadowLayerEffectCommands
    static createSetInnerShadowLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectBlendModeCommand(selection?.handle, blendMode, index, enableIfDisabled));
    }

    static createDuplicateInnerShadowLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateInnerShadowLayerEffectCommand(selection?.handle, index));
    }

    static createSetInnerShadowLayerEffectEnabled(selection, index, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectEnabledCommand(selection?.handle, index, enabled));
    }

    static createMoveInnerShadowLayerEffect(selection, fromIndex, toIndex) {
        return new DocumentCommand(DocumentCommandApi.createMoveInnerShadowLayerEffectCommand(selection?.handle, fromIndex, toIndex));
    }

    static createSetInnerShadowLayerEffectOpacity(selection, index, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectOpacityCommand(selection?.handle, index, opacity, enableIfDisabled));
    }

    static createSetInnerShadowLayerEffectRadius(selection, index, radius, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectRadiusCommand(selection?.handle, index, radius, enableIfDisabled));
    }

    static createRemoveInnerShadowLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createRemoveInnerShadowLayerEffectCommand(selection?.handle, index));
    }

    static createSetInnerShadowLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectScaleWithObjectCommand(selection?.handle, index, scaleWithObject, enableIfDisabled));
    }

    static createSetInnerShadowLayerEffect(selection, layerEffect, index) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectCommand(selection?.handle, layerEffect?.handle, index));
    }

    static createSetInnerShadowLayerEffectColour(selection, colour, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectColourCommand(selection?.handle, colour?.handle, index, enableIfDisabled));
    }

    static createSetInnerShadowLayerEffectIntensity(selection, index, intensity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectIntensityCommand(selection?.handle, index, intensity, enableIfDisabled));
    }

    static createSetInnerShadowLayerEffectOffsetAngle(selection, offset, angle, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerShadowLayerEffectOffsetAngleCommand(selection?.handle, offset, angle, index, enableIfDisabled));
    }

    // InnerGlowLayerEffectCommands
    static createSetInnerGlowLayerEffectBlendMode(selection, blendMode, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerGlowLayerEffectBlendModeCommand(selection?.handle, blendMode, enableIfDisabled));
    }

    static createDuplicateInnerGlowLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateInnerGlowLayerEffectCommand(selection?.handle));
    }

    static createSetInnerGlowLayerEffectEnabled(selection, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerGlowLayerEffectEnabledCommand(selection?.handle, enabled));
    }

    static createSetInnerGlowLayerEffectOpacity(selection, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerGlowLayerEffectOpacityCommand(selection?.handle, opacity, enableIfDisabled));
    }

    static createSetInnerGlowLayerEffectRadius(selection, radius, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerGlowLayerEffectRadiusCommand(selection?.handle, radius, enableIfDisabled));
    }

    static createRemoveInnerGlowLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createRemoveInnerGlowLayerEffectCommand(selection?.handle));
    }

    static createSetInnerGlowLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerGlowLayerEffectScaleWithObjectCommand(selection?.handle, scaleWithObject, enableIfDisabled));
    }

    static createSetInnerGlowLayerEffect(selection, layerEffect) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerGlowLayerEffectCommand(selection?.handle, layerEffect?.handle));
    }

    static createSetInnerGlowLayerEffectColour(selection, colour, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerGlowLayerEffectColourCommand(selection?.handle, colour?.handle, enableIfDisabled));
    }

    static createSetInnerGlowLayerEffectIntensity(selection, intensity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetInnerGlowLayerEffectIntensityCommand(selection?.handle, intensity, enableIfDisabled));
    }

    // ColourOverlayLayerEffectCommands
    static createSetColourOverlayLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetColourOverlayLayerEffectBlendModeCommand(selection?.handle, blendMode, index, enableIfDisabled));
    }

    static createDuplicateColourOverlayLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateColourOverlayLayerEffectCommand(selection?.handle, index));
    }

    static createSetColourOverlayLayerEffectEnabled(selection, index, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetColourOverlayLayerEffectEnabledCommand(selection?.handle, index, enabled));
    }

    static createMoveColourOverlayLayerEffect(selection, fromIndex, toIndex) {
        return new DocumentCommand(DocumentCommandApi.createMoveColourOverlayLayerEffectCommand(selection?.handle, fromIndex, toIndex));
    }

    static createSetColourOverlayLayerEffectOpacity(selection, index, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetColourOverlayLayerEffectOpacityCommand(selection?.handle, index, opacity, enableIfDisabled));
    }

    static createRemoveColourOverlayLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createRemoveColourOverlayLayerEffectCommand(selection?.handle, index));
    }

    static createSetColourOverlayLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetColourOverlayLayerEffectScaleWithObjectCommand(selection?.handle, index, scaleWithObject, enableIfDisabled));
    }

    static createSetColourOverlayLayerEffect(selection, layerEffect, index) {
        return new DocumentCommand(DocumentCommandApi.createSetColourOverlayLayerEffectCommand(selection?.handle, layerEffect?.handle, index));
    }

    static createSetColourOverlayLayerEffectColour(selection, colour, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetColourOverlayLayerEffectColourCommand(selection?.handle, colour?.handle, index, enableIfDisabled));
    }

    // GradientOverlayLayerEffectCommands
    static createSetGradientOverlayLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGradientOverlayLayerEffectBlendModeCommand(selection?.handle, blendMode, index, enableIfDisabled));
    }

    static createDuplicateGradientOverlayLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateGradientOverlayLayerEffectCommand(selection?.handle, index));
    }

    static createSetGradientOverlayLayerEffectEnabled(selection, index, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGradientOverlayLayerEffectEnabledCommand(selection?.handle, index, enabled));
    }

    static createMoveGradientOverlayLayerEffect(selection, fromIndex, toIndex) {
        return new DocumentCommand(DocumentCommandApi.createMoveGradientOverlayLayerEffectCommand(selection?.handle, fromIndex, toIndex));
    }

    static createSetGradientOverlayLayerEffectOpacity(selection, index, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGradientOverlayLayerEffectOpacityCommand(selection?.handle, index, opacity, enableIfDisabled));
    }

    static createRemoveGradientOverlayLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createRemoveGradientOverlayLayerEffectCommand(selection?.handle, index));
    }

    static createSetGradientOverlayLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGradientOverlayLayerEffectScaleWithObjectCommand(selection?.handle, index, scaleWithObject, enableIfDisabled));
    }

    static createSetGradientOverlayLayerEffect(selection, layerEffect, index) {
        return new DocumentCommand(DocumentCommandApi.createSetGradientOverlayLayerEffectCommand(selection?.handle, layerEffect?.handle, index));
    }

    static createSetGradientOverlayLayerEffectFill(selection, gradientFill, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGradientOverlayLayerEffectFillCommand(selection?.handle, gradientFill?.handle, enableIfDisabled));
    }

    static createSetGradientOverlayLayerEffectFillTransform(selection, transform, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGradientOverlayLayerEffectFillTransformCommand(selection?.handle, transform?.handle, enableIfDisabled));
    }

    // OuterGlowLayerEffectCommands
    static createSetOuterGlowLayerEffectBlendMode(selection, blendMode, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterGlowLayerEffectBlendModeCommand(selection?.handle, blendMode, enableIfDisabled));
    }

    static createDuplicateOuterGlowLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateOuterGlowLayerEffectCommand(selection?.handle));
    }

    static createSetOuterGlowLayerEffectEnabled(selection, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterGlowLayerEffectEnabledCommand(selection?.handle, enabled));
    }

    static createSetOuterGlowLayerEffectOpacity(selection, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterGlowLayerEffectOpacityCommand(selection?.handle, opacity, enableIfDisabled));
    }

    static createSetOuterGlowLayerEffectRadius(selection, radius, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterGlowLayerEffectRadiusCommand(selection?.handle, radius, enableIfDisabled));
    }

    static createRemoveOuterGlowLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createRemoveOuterGlowLayerEffectCommand(selection?.handle));
    }

    static createSetOuterGlowLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterGlowLayerEffectScaleWithObjectCommand(selection?.handle, scaleWithObject, enableIfDisabled));
    }

    static createSetOuterGlowLayerEffect(selection, layerEffect) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterGlowLayerEffectCommand(selection?.handle, layerEffect?.handle));
    }

    static createSetOuterGlowLayerEffectColour(selection, colour, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterGlowLayerEffectColourCommand(selection?.handle, colour?.handle, enableIfDisabled));
    }

    static createSetOuterGlowLayerEffectIntensity(selection, intensity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterGlowLayerEffectIntensityCommand(selection?.handle, intensity, enableIfDisabled));
    }

    // OuterShadowLayerEffectCommands
    static createSetOuterShadowLayerEffectBlendMode(selection, blendMode, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectBlendModeCommand(selection?.handle, blendMode, index, enableIfDisabled));
    }

    static createDuplicateOuterShadowLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateOuterShadowLayerEffectCommand(selection?.handle, index));
    }

    static createSetOuterShadowLayerEffectEnabled(selection, index, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectEnabledCommand(selection?.handle, index, enabled));
    }

    static createMoveOuterShadowLayerEffect(selection, fromIndex, toIndex) {
        return new DocumentCommand(DocumentCommandApi.createMoveOuterShadowLayerEffectCommand(selection?.handle, fromIndex, toIndex));
    }

    static createSetOuterShadowLayerEffectOpacity(selection, index, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectOpacityCommand(selection?.handle, index, opacity, enableIfDisabled));
    }

    static createSetOuterShadowLayerEffectRadius(selection, index, radius, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectRadiusCommand(selection?.handle, index, radius, enableIfDisabled));
    }

    static createRemoveOuterShadowLayerEffect(selection, index) {
        return new DocumentCommand(DocumentCommandApi.createRemoveOuterShadowLayerEffectCommand(selection?.handle, index));
    }

    static createSetOuterShadowLayerEffectScaleWithObject(selection, index, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectScaleWithObjectCommand(selection?.handle, index, scaleWithObject, enableIfDisabled));
    }

    static createSetOuterShadowLayerEffect(selection, layerEffect, index) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectCommand(selection?.handle, layerEffect?.handle, index));
    }

    static createSetOuterShadowLayerEffectColour(selection, colour, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectColourCommand(selection?.handle, colour?.handle, index, enableIfDisabled));
    }

    static createSetOuterShadowLayerEffectIntensity(selection, index, intensity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectIntensityCommand(selection?.handle, index, intensity, enableIfDisabled));
    }

    static createSetOuterShadowLayerEffectKnocksOut(selection, knocksOut, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectKnocksOutCommand(selection?.handle, knocksOut, enableIfDisabled));
    }

    static createSetOuterShadowLayerEffectOffsetAngle(selection, offset, angle, index, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetOuterShadowLayerEffectOffsetAngleCommand(selection?.handle, offset, angle, index, enableIfDisabled));
    }

    // GaussianBlurLayerEffectCommands
    static createSetGaussianBlurLayerEffectBlendMode(selection, blendMode, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGaussianBlurLayerEffectBlendModeCommand(selection?.handle, blendMode, enableIfDisabled));
    }

    static createDuplicateGaussianBlurLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createDuplicateGaussianBlurLayerEffectCommand(selection?.handle));
    }

    static createSetGaussianBlurLayerEffectEnabled(selection, enabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGaussianBlurLayerEffectEnabledCommand(selection?.handle, enabled));
    }

    static createSetGaussianBlurLayerEffectOpacity(selection, opacity, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGaussianBlurLayerEffectOpacityCommand(selection?.handle, opacity, enableIfDisabled));
    }

    static createSetGaussianBlurLayerEffectRadius(selection, radius, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGaussianBlurLayerEffectRadiusCommand(selection?.handle, radius, enableIfDisabled));
    }

    static createRemoveGaussianBlurLayerEffect(selection) {
        return new DocumentCommand(DocumentCommandApi.createRemoveGaussianBlurLayerEffectCommand(selection?.handle));
    }

    static createSetGaussianBlurLayerEffectScaleWithObject(selection, scaleWithObject, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGaussianBlurLayerEffectScaleWithObjectCommand(selection?.handle, scaleWithObject, enableIfDisabled));
    }

    static createSetGaussianBlurLayerEffect(selection, layerEffect) {
        return new DocumentCommand(DocumentCommandApi.createSetGaussianBlurLayerEffectCommand(selection?.handle, layerEffect?.handle));
    }

    static createSetGaussianBlurLayerEffectPreserveAlpha(selection, preserveAlpha, enableIfDisabled) {
        return new DocumentCommand(DocumentCommandApi.createSetGaussianBlurLayerEffectPreserveAlphaCommand(selection?.handle, preserveAlpha, enableIfDisabled));
    }

    static createSetTextFrameIgnoreTextWraps(selection, ignoreTextWraps) {
        return new DocumentCommand(DocumentCommandApi.createSetTextFrameIgnoreTextWrapsCommand(selection?.handle, ignoreTextWraps));
    }

    static createSetTextFrameIgnoreBaselineGrid(selection, ignoreBaselineGrid) {
        return new DocumentCommand(DocumentCommandApi.createSetTextFrameIgnoreBaselineGridCommand(selection?.handle, ignoreBaselineGrid));
    }

    static createSetSpreadSizeWithAnchor(spreadNode, width, height, anchor) {
        return new DocumentCommand(DocumentCommandApi.createSetSpreadSizeWithAnchorCommand(spreadNode.handle, width, height, anchor));
    }

    static createSetArtboardSizeWithAnchor(artboardInterface, width, height, anchor) {
        return new DocumentCommand(DocumentCommandApi.createSetArtboardSizeWithAnchorCommand(artboardInterface.handle, width, height, anchor));
    }

    static createSetSpreadDocumentProperties(spreadNode, spreadDocumentProperties) {
        return new DocumentCommand(DocumentCommandApi.createSetSpreadDocumentPropertiesCommand(spreadNode.handle, spreadDocumentProperties.handle));
    }

    static createSetArtboardDocumentProperties(artboardInterface, artboardDocumentProperties) {
        return new DocumentCommand(DocumentCommandApi.createSetArtboardDocumentPropertiesCommand(artboardInterface.handle, artboardDocumentProperties.handle));
    }
}

/**
* @deprecated Use DocumentCommand instead
*/
class AddNodeCommand extends DocumentCommand {
}


class CompoundCommandBuilder extends HandleObject {
    constructor(handle) {
        super(handle);
    }
    
    clear() {
        CompoundCommandBuilderApi.clear(this.handle);
    }
    
    addCommand(command, useAsDescription) {
        CompoundCommandBuilderApi.addCommand(this.handle, command.handle, useAsDescription);
        return this;
    }
    
    createCommand() {
        return new DocumentCommand(CompoundCommandBuilderApi.createCommand(this.handle));
    }
    
    static create() {
        return new CompoundCommandBuilder(CompoundCommandBuilderApi.create());
    }
}

class AddChildNodesCommandBuilder extends HandleObject {
    constructor(handle) {
        super(handle);
    }
    
    clearNodes() {
        AddChildNodesCommandBuilderApi.clearNodes(this.handle);
    }
    
    clearInsertionTarget() {
        AddChildNodesCommandBuilderApi.clearInsertionTarget(this.handle);
    }
    
    clearInsertionTargetSelection() {
        AddChildNodesCommandBuilderApi.clearInsertionTargetSelection(this.handle);
    }
    
    addNode(nodeDefinition) {
        AddChildNodesCommandBuilderApi.addNode(this.handle, nodeDefinition.handle);
    }
    
    addImageNode(imageNodeDefinition) {
        AddChildNodesCommandBuilderApi.addImageNode(this.handle, imageNodeDefinition.handle);
    }
    
    addShapeNode(shapeNodeDefinition) {
        AddChildNodesCommandBuilderApi.addShapeNode(this.handle, shapeNodeDefinition.handle);
    }
    
    addPolyCurveNode(polyCurveNodeDefinition) {
        AddChildNodesCommandBuilderApi.addPolyCurveNode(this.handle, polyCurveNodeDefinition.handle);
    }
    
    addRasterNode(rasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addRasterNode(this.handle, rasterNodeDefinition.handle);
    }
    
    addPatternRasterNode(patternRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addPatternRasterNode(this.handle, patternRasterNodeDefinition.handle);
    }
    
    addExposureAdjustmentRasterNode(exposureAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addExposureAdjustmentRasterNode(this.handle, exposureAdjustmentRasterNodeDefinition.handle);
    }
    
    addGaussianBlurFilterRasterNode(gaussianBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addGaussianBlurFilterRasterNode(this.handle, gaussianBlurFilterRasterNodeDefinition.handle);
    }

    addBoxBlurFilterRasterNode(boxBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addBoxBlurFilterRasterNode(this.handle, boxBlurFilterRasterNodeDefinition.handle);
    }
    
    addBilateralBlurFilterRasterNode(bilateralBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addBilateralBlurFilterRasterNode(this.handle, bilateralBlurFilterRasterNodeDefinition.handle);
    }
    
    addMedianBlurFilterRasterNode(medianBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addMedianBlurFilterRasterNode(this.handle, medianBlurFilterRasterNodeDefinition.handle);
    }
    
    addFieldBlurFilterRasterNode(fieldBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addFieldBlurFilterRasterNode(this.handle, fieldBlurFilterRasterNodeDefinition.handle);
    }
    
    addDepthOfFieldFilterRasterNode(depthOfFieldFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addDepthOfFieldFilterRasterNode(this.handle, depthOfFieldFilterRasterNodeDefinition.handle);
    }
    
    addDiffuseGlowFilterRasterNode(diffuseGlowFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addDiffuseGlowFilterRasterNode(this.handle, diffuseGlowFilterRasterNodeDefinition.handle);
    }
    
    addLensBlurFilterRasterNode(lensBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addLensBlurFilterRasterNode(this.handle, lensBlurFilterRasterNodeDefinition.handle);
    }
    
    addMaximumBlurFilterRasterNode(maximumBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addMaximumBlurFilterRasterNode(this.handle, maximumBlurFilterRasterNodeDefinition.handle);
    }
    
    addMinimumBlurFilterRasterNode(minimumBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addMinimumBlurFilterRasterNode(this.handle, minimumBlurFilterRasterNodeDefinition.handle);
    }
    
    addMotionBlurFilterRasterNode(motionBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addMotionBlurFilterRasterNode(this.handle, motionBlurFilterRasterNodeDefinition.handle);
    }
    
    addShadowsHighlightsFilterRasterNode(shadowsHighlightsFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addShadowsHighlightsFilterRasterNode(this.handle, shadowsHighlightsFilterRasterNodeDefinition.handle);
    }
    
    addRadialBlurFilterRasterNode(radialBlurFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addRadialBlurFilterRasterNode(this.handle, radialBlurFilterRasterNodeDefinition.handle);
    }
    
    addLevelsAdjustmentRasterNode(levelsAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addLevelsAdjustmentRasterNode(this.handle, levelsAdjustmentRasterNodeDefinition.handle);
    }
    
    addBrightnessContrastAdjustmentRasterNode(brightnessContrastAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addBrightnessContrastAdjustmentRasterNode(this.handle, brightnessContrastAdjustmentRasterNodeDefinition.handle);
    }
    
    addBlackAndWhiteAdjustmentRasterNode(blackAndWhiteAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addBlackAndWhiteAdjustmentRasterNode(this.handle, blackAndWhiteAdjustmentRasterNodeDefinition.handle);
    }
    
    addRecolourAdjustmentRasterNode(recolourAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addRecolourAdjustmentRasterNode(this.handle, recolourAdjustmentRasterNodeDefinition.handle);
    }
    
    addPosteriseAdjustmentRasterNode(posteriseAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addPosteriseAdjustmentRasterNode(this.handle, posteriseAdjustmentRasterNodeDefinition.handle);
    }
    
    addSplitToningAdjustmentRasterNode(splitToningAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addSplitToningAdjustmentRasterNode(this.handle, splitToningAdjustmentRasterNodeDefinition.handle);
    }
    
    addInvertAdjustmentRasterNode(invertAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addInvertAdjustmentRasterNode(this.handle, invertAdjustmentRasterNodeDefinition.handle);
    }
    
    addThresholdAdjustmentRasterNode(thresholdAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addThresholdAdjustmentRasterNode(this.handle, thresholdAdjustmentRasterNodeDefinition.handle);
    }
    
    addClarityFilterRasterNode(clarityFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addClarityFilterRasterNode(this.handle, clarityFilterRasterNodeDefinition.handle);
    }
    
    addUnsharpMaskFilterRasterNode(unsharpMaskFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addUnsharpMaskFilterRasterNode(this.handle, unsharpMaskFilterRasterNodeDefinition.handle);
    }
    
    addHighPassFilterRasterNode(highPassFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addHighPassFilterRasterNode(this.handle, highPassFilterRasterNodeDefinition.handle);
    }
    
    addDenoiseFilterRasterNode(denoiseFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addDenoiseFilterRasterNode(this.handle, denoiseFilterRasterNodeDefinition.handle);
    }
    
    addDiffuseFilterRasterNode(diffuseFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addDiffuseFilterRasterNode(this.handle, diffuseFilterRasterNodeDefinition.handle);
    }
    
    addDustAndScratchFilterRasterNode(dustAndScratchFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addDustAndScratchFilterRasterNode(this.handle, dustAndScratchFilterRasterNodeDefinition.handle);
    }
    
    addAddNoiseFilterRasterNode(addNoiseFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addAddNoiseFilterRasterNode(this.handle, addNoiseFilterRasterNodeDefinition.handle);
    }
    
    addBloomFilterRasterNode(bloomFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addBloomFilterRasterNode(this.handle, bloomFilterRasterNodeDefinition.handle);
    }
    
    addPixelateFilterRasterNode(pixelateFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addPixelateFilterRasterNode(this.handle, pixelateFilterRasterNodeDefinition.handle);
    }
    
    addHalftoneFilterRasterNode(halftoneFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addHalftoneFilterRasterNode(this.handle, halftoneFilterRasterNodeDefinition.handle);
    }
    
    addRippleFilterRasterNode(rippleFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addRippleFilterRasterNode(this.handle, rippleFilterRasterNodeDefinition.handle);
    }
    
    addTwirlFilterRasterNode(twirlFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addTwirlFilterRasterNode(this.handle, twirlFilterRasterNodeDefinition.handle);
    }
    
    addSphericalFilterRasterNode(sphericalFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addSphericalFilterRasterNode(this.handle, sphericalFilterRasterNodeDefinition.handle);
    }
    
    addPinchPunchFilterRasterNode(pinchPunchFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addPinchPunchFilterRasterNode(this.handle, pinchPunchFilterRasterNodeDefinition.handle);
    }
    
    addWhiteBalanceAdjustmentRasterNode(whiteBalanceAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addWhiteBalanceAdjustmentRasterNode(this.handle, whiteBalanceAdjustmentRasterNodeDefinition.handle);
    }
    
    addColourBalanceAdjustmentRasterNode(colourBalanceAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addColourBalanceAdjustmentRasterNode(this.handle, colourBalanceAdjustmentRasterNodeDefinition.handle);
    }
    
    addVibranceAdjustmentRasterNode(vibranceAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addVibranceAdjustmentRasterNode(this.handle, vibranceAdjustmentRasterNodeDefinition.handle);
    }
    
    addNormalsAdjustmentRasterNode(normalsAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addNormalsAdjustmentRasterNode(this.handle, normalsAdjustmentRasterNodeDefinition.handle);
    }
    
    addVignetteFilterRasterNode(vignetteFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addVignetteFilterRasterNode(this.handle, vignetteFilterRasterNodeDefinition.handle);
    }
    
    addDefringeFilterRasterNode(defringeFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addDefringeFilterRasterNode(this.handle, defringeFilterRasterNodeDefinition.handle);
    }
    
    addVoronoiFilterRasterNode(voronoiFilterRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addVoronoiFilterRasterNode(this.handle, voronoiFilterRasterNodeDefinition.handle);
    }
    
    addSelectiveColourAdjustmentRasterNode(selectiveColourAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addSelectiveColourAdjustmentRasterNode(this.handle, selectiveColourAdjustmentRasterNodeDefinition.handle);
    }
    
    addHSLShiftAdjustmentRasterNode(hslShiftAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addHSLShiftAdjustmentRasterNode(this.handle, hslShiftAdjustmentRasterNodeDefinition.handle);
    }
    
    addCurvesAdjustmentRasterNode(curvesAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addCurvesAdjustmentRasterNode(this.handle, curvesAdjustmentRasterNodeDefinition.handle);
    }

    addToneCompressionAdjustmentRasterNode(toneCompressionAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addToneCompressionAdjustmentRasterNode(this.handle, toneCompressionAdjustmentRasterNodeDefinition.handle);
    }
    
    addToneStretchAdjustmentRasterNode(toneStretchAdjustmentRasterNodeDefinition) {
        AddChildNodesCommandBuilderApi.addToneStretchAdjustmentRasterNode(this.handle, toneStretchAdjustmentRasterNodeDefinition.handle);
    }
    
    addContainerNode(containerNodeDefinition) {
        AddChildNodesCommandBuilderApi.addContainerNode(this.handle, containerNodeDefinition.handle);
    }
    
    addTableTextNode(tableTextNodeDefinition) {
        AddChildNodesCommandBuilderApi.addTableTextNode(this.handle, tableTextNodeDefinition.handle);
    }
    
    createCommand(andSelect = true, childListType = NodeChildType.Main) {
        return new DocumentCommand(AddChildNodesCommandBuilderApi.createCommand(this.handle, andSelect, childListType));
    }
    
    createCommandAndReset(andSelect = true, childListType = NodeChildType.Main) {
        return new DocumentCommand(AddChildNodesCommandBuilderApi.createCommandAndReset(this.handle, andSelect, childListType));
    }
    
    set autoName(isAutoName) {
        AddChildNodesCommandBuilderApi.setAutoName(this.handle, isAutoName);
    }
    
    set forcePixelAlignment(forceAlignment) {
        AddChildNodesCommandBuilderApi.setForcePixelAlignment(this.handle, forceAlignment);
    }
    
    set clearCurrentSelection(clear) {
        AddChildNodesCommandBuilderApi.setClearCurrentSelection(this.handle, clear);
    }
    
    set appendCurrentSelection(append) {
        AddChildNodesCommandBuilderApi.setAppendCurrentSelection(this.handle, append);
    }
    
    setInsertionTarget(targetNode) {
        AddChildNodesCommandBuilderApi.setInsertionTarget(this.handle, targetNode.handle);
    }
    
    setInsertionTargetSelection(targetSelection) {
        AddChildNodesCommandBuilderApi.setInsertionTargetSelection(this.handle, targetSelection.handle);
    }
    
    setInsertionMode(insertionMode) {
        AddChildNodesCommandBuilderApi.setInsertionMode(this.handle, insertionMode);
    }
    
    static create() {
        return new AddChildNodesCommandBuilder(AddChildNodesCommandBuilderApi.create());
    }
}

class SetHatchFillAttributesCommandBuilder extends HandleObject {
    static create() {
        return new SetHatchFillAttributesCommandBuilder(SetHatchFillAttributesCommandBuilderApi.create());
    }

    get [Symbol.toStringTag]() {
        return 'SetHatchFillAttributesCommandBuilder';
    }

    static create() {
        return new SetHatchFillAttributesCommandBuilder(SetHatchFillAttributesCommandBuilderApi.create());
    }

    reset() {
        return SetHatchFillAttributesCommandBuilderApi.reset(this.handle);
    }

    set pattern(value) {
        SetHatchFillAttributesCommandBuilderApi.setPattern(this.handle, value.handle);
    }

    set penColour(value) {
        SetHatchFillAttributesCommandBuilderApi.setPenColour(this.handle, value?.handle);
    }

    set brushColour(value) {
        SetHatchFillAttributesCommandBuilderApi.setBrushColour(this.handle, value?.handle);
    }

    set scale(value) {
        SetHatchFillAttributesCommandBuilderApi.setScale(this.handle, value);
    }

    set rotation(value) {
        SetHatchFillAttributesCommandBuilderApi.setRotation(this.handle, value);
    }

    set lineWeight(value) {
        SetHatchFillAttributesCommandBuilderApi.setLineWeight(this.handle, value);
    }

    set fixScale(value) {
        SetHatchFillAttributesCommandBuilderApi.setFixScale(this.handle, value);
    }

    set useRelativeTransform(value) {
        SetHatchFillAttributesCommandBuilderApi.setUseRelativeTransform(this.handle, value);
    }

    set useCurrentItemOriginForRelativeTransform(value) {
        SetHatchFillAttributesCommandBuilderApi.setUseCurrentItemOriginForRelativeTransform(this.handle, value);
    }

    createBrushFillCommand(selection, contentType = ContentType.Main, useTextSelection = false, applyToAllFills = false) {
        return new DocumentCommand(SetHatchFillAttributesCommandBuilderApi.createBrushFillCommand(this.handle, contentType, useTextSelection, selection?.handle, applyToAllFills));
    }

    createPenFillCommand(selection, contentType = ContentType.Main, useTextSelection = false, applyToAllFills = false) {
        return new DocumentCommand(SetHatchFillAttributesCommandBuilderApi.createPenFillCommand(this.handle, contentType, useTextSelection, selection?.handle, applyToAllFills));
    }

    createTransparencyFillCommand(selection, contentType = ContentType.Main, useTextSelection = false, applyToAllFills = false) {
        return new DocumentCommand(SetHatchFillAttributesCommandBuilderApi.createTransparencyFillCommand(this.handle, contentType, useTextSelection, selection?.handle, applyToAllFills));
    }
}

function createCompoundCommand(subCmds) {
    if (subCmds instanceof Command) {
        return subCmds;
    }
    else {
        const builder = CompoundCommandBuilder.create();
        for (const cmd of subCmds) {
            builder.addCommand(cmd);
        }
        return builder.createCommand();
    }
}

module.exports.AddChildNodesCommandBuilder = AddChildNodesCommandBuilder;
module.exports.Command = Command;
module.exports.CompoundCommandBuilder = CompoundCommandBuilder;
module.exports.DocumentCommand = DocumentCommand;
module.exports.DocumentProperties = DocumentProperties;
module.exports.SetHatchFillAttributesCommandBuilder = SetHatchFillAttributesCommandBuilder;
// convenience
module.exports.AntialiasingMode = AntialiasingMode;
module.exports.BevelEmbossType = BevelEmbossType;
module.exports.BlendMode = BlendMode;
module.exports.ColourSpaceType = ColourSpaceType;
module.exports.ContentType = ContentType;
module.exports.CurveNodeStyle = CurveNodeStyle;
module.exports.FillMask = FillMask;
module.exports.GroupTransformAnchor = GroupTransformAnchor;
module.exports.GroupTransformData = GroupTransformData;
module.exports.GroupTransformOrder = GroupTransformOrder;
module.exports.GroupTransformType = GroupTransformType;
module.exports.InsertionMode = InsertionMode;
module.exports.LineCommandDefaultsMode = LineCommandDefaultsMode;
module.exports.LineStyleMask = LineStyleMask;
module.exports.NodeChildType = NodeChildType;
module.exports.NodeMoveType = NodeMoveType;
module.exports.PageBoundingBoxType = PageBoundingBoxType;
module.exports.PredefinedTagKey = PredefinedTagKey;
module.exports.RasterFormat = RasterFormat;
module.exports.RasterSelectionLogicalOperation = RasterSelectionLogicalOperation;
module.exports.RasterSelectionOutlineAlignment = RasterSelectionOutlineAlignment;
module.exports.ShapeBoolParam = ShapeBoolParam;
module.exports.ShapeEnumParam = ShapeEnumParam;
module.exports.ShapeFloatParam = ShapeFloatParam;
module.exports.ShapeIntParam = ShapeIntParam;
module.exports.SpatialAnchor = SpatialAnchor;
module.exports.StrokeAlignment = StrokeAlignment;
module.exports.StrokeFillType = StrokeFillType;
module.exports.UnitType = UnitType;
module.exports.VisibilityMode = VisibilityMode;
module.exports.WindingOrder = WindingOrder;
module.exports.createCompoundCommand = createCompoundCommand;
