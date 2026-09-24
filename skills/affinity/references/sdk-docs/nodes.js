'use strict';

const { ColourSpaceType } = require('affinity:colours');
const { EnumerationResult, UnitType } = require('affinity:common');

// general nodes
const {
    AdjustmentRasterNodeApi,
    AdjustmentRasterNodeDefinitionApi,
    ArtTextNodeApi,
    ArtTextNodeDefinitionApi,
    ColouredLogicalNodeApi,
    ColouredLogicalNodeDefinitionApi,
    ContainerNodeApi,
    ContainerNodeDefinitionApi,
    CurvePathTextNodeApi,
    CurvePathTextNodeDefinitionApi,
    DevelopNodeApi,
    DevelopParametersApi,
    EmbeddedDocumentNodeApi,
    EnclosureRasterNodeApi,
    EnclosureRasterNodeDefinitionApi,
    FilterRasterNodeApi,
    FilterRasterNodeDefinitionApi,
    FrameTextNodeApi,
    FrameTextNodeDefinitionApi,
    GroupNodeApi,
    ImageNodeApi,
    ImageNodeDefinitionApi,
    LineDescriptors,
    LogicalNodeApi,
    LogicalNodeDefinitionApi,
    NodeApi,
    NodeDefinitionApi,
    PatternRasterNodeApi,
    PatternRasterNodeDefinitionApi,
    PhysicalNodeApi,
    PhysicalNodeDefinitionApi,
    PolyCurveNodeApi,
    PolyCurveNodeDefinitionApi,
    PolyCurveTextNodeApi,
    PolyCurveTextNodeDefinitionApi,
    RasterNodeApi,
    RasterNodeDefinitionApi,
    ShapeNodeApi,
    ShapeNodeDefinitionApi,
    ShapePathTextNodeApi,
    ShapePathTextNodeDefinitionApi,
    ShapeTextNodeApi,
    ShapeTextNodeDefinitionApi,
    SpreadNodeApi,
    MeasurementNodeApi,
    MeasurementNodeDefinitionApi,
    TableTextNodeApi,
    TableTextNodeDefinitionApi,
    TextNodeApi,
    TextNodeDefinitionApi,
    VectorNodeApi,
    VectorNodeDefinitionApi
} = require('affinity:dom');

// raster adjustment nodes
const {
    BlackAndWhiteAdjustmentRasterNodeApi,
    BlackAndWhiteAdjustmentRasterNodeDefinitionApi,
    BrightnessContrastAdjustmentRasterNodeApi,
    BrightnessContrastAdjustmentRasterNodeDefinitionApi,
    ColourBalanceAdjustmentRasterNodeApi,
    ColourBalanceAdjustmentRasterNodeDefinitionApi,
    CurvesAdjustmentRasterNodeApi,
    CurvesAdjustmentRasterNodeDefinitionApi,
    ExposureAdjustmentRasterNodeApi,
    ExposureAdjustmentRasterNodeDefinitionApi,
    HSLShiftAdjustmentRasterNodeApi,
    HSLShiftAdjustmentRasterNodeDefinitionApi,
    InvertAdjustmentRasterNodeApi,
    InvertAdjustmentRasterNodeDefinitionApi,
    LevelsAdjustmentRasterNodeApi,
    LevelsAdjustmentRasterNodeDefinitionApi,
    NormalsAdjustmentRasterNodeApi,
    NormalsAdjustmentRasterNodeDefinitionApi,
    PosteriseAdjustmentRasterNodeApi,
    PosteriseAdjustmentRasterNodeDefinitionApi,
    RecolourAdjustmentRasterNodeApi,
    RecolourAdjustmentRasterNodeDefinitionApi,
    SelectiveColourAdjustmentRasterNodeApi,
    SelectiveColourAdjustmentRasterNodeDefinitionApi,
    ShadowsHighlightsAdjustmentRasterNodeApi,
    ShadowsHighlightsAdjustmentRasterNodeDefinitionApi,
    SplitToningAdjustmentRasterNodeApi,
    SplitToningAdjustmentRasterNodeDefinitionApi,
    ThresholdAdjustmentRasterNodeApi,
    ThresholdAdjustmentRasterNodeDefinitionApi,
    ToneCompressionAdjustmentRasterNodeApi,
    ToneCompressionAdjustmentRasterNodeDefinitionApi,
    ToneStretchAdjustmentRasterNodeApi,
    ToneStretchAdjustmentRasterNodeDefinitionApi,
    VibranceAdjustmentRasterNodeApi,
    VibranceAdjustmentRasterNodeDefinitionApi,
    WhiteBalanceAdjustmentRasterNodeApi,
    WhiteBalanceAdjustmentRasterNodeDefinitionApi,
} = require('affinity:dom');

// raster adjustment parameters
const {
    BlackAndWhiteAdjustmentParametersApi,
    BrightnessContrastAdjustmentParametersApi,
    ColourBalanceAdjustmentParametersApi,
    ColourBalanceValues,
    CurvesAdjustmentParametersApi,
    ExposureAdjustmentParametersApi,
    HSLShiftAdjustmentChannelParameters,
    HSLShiftAdjustmentColourRange,
    HSLShiftAdjustmentParametersApi,
    LevelsAdjustmentChannelParameters,
    LevelsAdjustmentParametersApi,
    NormalsAdjustmentParametersApi,
    PosteriseAdjustmentParametersApi,
    RecolourAdjustmentParametersApi,
    SelectiveColourAdjustmentParametersApi,
    ShadowsHighlightsAdjustmentParametersApi,
    SplitToningAdjustmentParametersApi,
    ThresholdAdjustmentParametersApi,
    ToneCompressionAdjustmentParametersApi,
    ToneStretchAdjustmentParametersApi,
    VibranceAdjustmentParametersApi,
    WhiteBalanceAdjustmentParametersApi,
} = require('affinity:dom');


// raster filter nodes
const {
    AddNoiseFilterRasterNodeApi,
    AddNoiseFilterRasterNodeDefinitionApi,
    BilateralBlurFilterRasterNodeApi,
    BilateralBlurFilterRasterNodeDefinitionApi,
    BloomFilterRasterNodeApi,
    BloomFilterRasterNodeDefinitionApi,
    BoxBlurFilterRasterNodeApi,
    BoxBlurFilterRasterNodeDefinitionApi,
    ClarityFilterRasterNodeApi,
    ClarityFilterRasterNodeDefinitionApi,
    DefringeFilterRasterNodeApi,
    DefringeFilterRasterNodeDefinitionApi,
    DenoiseFilterRasterNodeApi,
    DenoiseFilterRasterNodeDefinitionApi,
    DepthOfFieldFilterRasterNodeApi,
    DepthOfFieldFilterRasterNodeDefinitionApi,
    DiffuseFilterRasterNodeApi,
    DiffuseFilterRasterNodeDefinitionApi,
    DiffuseGlowFilterRasterNodeApi,
    DiffuseGlowFilterRasterNodeDefinitionApi,
    DustAndScratchFilterRasterNodeApi,
    DustAndScratchFilterRasterNodeDefinitionApi,
    FieldBlurFilterRasterNodeApi,
    FieldBlurFilterRasterNodeDefinitionApi,
    GaussianBlurFilterRasterNodeApi,
    GaussianBlurFilterRasterNodeDefinitionApi,
    HalftoneFilterRasterNodeApi,
    HalftoneFilterRasterNodeDefinitionApi,
    HighPassFilterRasterNodeApi,
    HighPassFilterRasterNodeDefinitionApi,
    LensBlurFilterRasterNodeApi,
    LensBlurFilterRasterNodeDefinitionApi,
    MaximumBlurFilterRasterNodeApi,
    MaximumBlurFilterRasterNodeDefinitionApi,
    MedianBlurFilterRasterNodeApi,
    MedianBlurFilterRasterNodeDefinitionApi,
    MinimumBlurFilterRasterNodeApi,
    MinimumBlurFilterRasterNodeDefinitionApi,
    MotionBlurFilterRasterNodeApi,
    MotionBlurFilterRasterNodeDefinitionApi,
    PinchPunchFilterRasterNodeApi,
    PinchPunchFilterRasterNodeDefinitionApi,
    PixelateFilterRasterNodeApi,
    PixelateFilterRasterNodeDefinitionApi,
    RadialBlurFilterRasterNodeApi,
    RadialBlurFilterRasterNodeDefinitionApi,
    RippleFilterRasterNodeApi,
    RippleFilterRasterNodeDefinitionApi,
    ShadowsHighlightsFilterRasterNodeApi,
    ShadowsHighlightsFilterRasterNodeDefinitionApi,
    SphericalFilterRasterNodeApi,
    SphericalFilterRasterNodeDefinitionApi,
    TwirlFilterRasterNodeApi,
    TwirlFilterRasterNodeDefinitionApi,
    UnsharpMaskFilterRasterNodeApi,
    UnsharpMaskFilterRasterNodeDefinitionApi,
    VignetteFilterRasterNodeApi,
    VignetteFilterRasterNodeDefinitionApi,
    VoronoiFilterRasterNodeApi,
    VoronoiFilterRasterNodeDefinitionApi,
} = require('affinity:dom');

// raster filter parameters
const {
    AddNoiseFilterParametersApi,
    BilateralBlurFilterParametersApi,
    BloomFilterParametersApi,
    BoxBlurFilterParametersApi,
    ClarityFilterParametersApi,
    DefringeFilterParametersApi,
    DenoiseFilterParametersApi,
    DepthOfFieldFilterParametersApi,
    DiffuseFilterParametersApi,
    DiffuseGlowFilterParametersApi,
    DustAndScratchFilterParametersApi,
    EllipticalDepthOfFieldParameters,
    FieldBlurFilterParametersApi,
    FieldBlurItemParameters,
    GaussianBlurFilterParametersApi,
    HalftoneFilterParametersApi,
    HighPassFilterParametersApi,
    LensBlurFilterParametersApi,
    MaximumBlurFilterParametersApi,
    MedianBlurFilterParametersApi,
    MinimumBlurFilterParametersApi,
    MotionBlurFilterParametersApi,
    PinchPunchFilterParametersApi,
    PixelateFilterParametersApi,
    RadialBlurFilterParametersApi,
    RippleFilterParametersApi,
    ShadowsHighlightsFilterParametersApi,
    SphericalFilterParametersApi,
    TiltShiftDepthOfFieldParameters,
    TwirlFilterParametersApi,
    UnsharpMaskFilterParametersApi,
    VignetteFilterParametersApi,
    VoronoiFilterParametersApi,
} = require('affinity:dom');

// other bits
const {
    AddNoiseType,
    BloomMethod,
    DepthOfFieldMode,
    DevelopDetailRefinementMethod,
    DevelopInvertMethod,
    DevelopToneCurveMethod,
    DocumentApi,
    DocumentNodeApi,
    HalftoneDotType,
    HalftoneScreenType,
    NodeCastApi,
    NodeChildType,
    PageBoundingBoxType,
    SelectiveColour,
    SelectiveColourWeights,
    ShadowsHighlightsVersion,
    TonalRangeType,
    ToneCompressionMethod,
    ToneStretchMethod,
} = require('affinity:dom');

const { RasterExtendType, RasterFormat, RasterResamplerType } = require('affinity:raster');

const { StoryIoFormat } = require('affinity:story');

const { Collection } = require('/collection.js');
const { Colour } = require('/colours.js');
const { FillDescriptor } = require('/fills.js');
const { Endpoints, PolyCurve, Spline } = require('/geometry.js');
const { GlyphAtts } = require('/glyphatts.js');
const { HandleObject, livePoint, liveStruct, liveStructArray, setStructArray } = require('/handleobject.js');
const { LineStyle, LineStyleDescriptor, LineStyleMask } = require('/linestyle.js');
const { RasterObject } = require('/rasterobject.js');
const { Selectable } = require('/selectable.js');
const { createTypedShape, Shape } = require('/shapes.js');

// cyclics:
const ArtboardInterfaceModule = require('/artboardinterface.js');
const BaseBoxInterfaceModule = require('/baseboxinterface.js');
const BlendModeInterfaceModule = require('/blendmodeinterface.js');
const BrushFillInterfaceModule = require('/brushfillinterface.js');
const CommandsModule  = require('/commands.js');
const CompoundOperationInterfaceModule = require('/compoundoperationinterface.js');
const CurvesInterfaceModule = require('/curvesinterface.js');
const DescriptionInterfaceModule = require('/descriptioninterface.js');
const DocumentModule = require('/document.js');
const EditabilityInterfaceModule = require('/editabilityinterface.js');
const ExportableInterfaceModule = require('/exportableinterface.js');
const ImageResourceInterfaceModule = require('/imageresourceinterface.js');
const LayerEffectsInterfaceModule = require('/layereffectsinterface.js');
const LineStyleInterfaceModule = require('/linestyleinterface.js');
const PhysicalRootInterfaceModule = require('/physicalrootinterface.js');
const PhysicalRootPropertiesInterfaceModule = require('/physicalrootpropertiesinterface.js');
const PictureFrameInterfaceModule = require('/pictureframeinterface.js');
const RasterInterfaceModule = require('/rasterinterface.js');
const SelectionsModule = require('/selections.js');
const ShapeInterfaceModule = require('/shapeinterface.js');
const StoryInterfaceModule = require('/storyinterface.js');
const TagInterfaceModule = require('/taginterface.js');
const TextFrameInterfaceModule = require('/textframeinterface.js');
const TransformInterfaceModule = require('/transforminterface.js');
const TransparencyInterfaceModule = require('/transparencyinterface.js');
const VisibilityInterfaceModule = require('/visibilityinterface.js');

function* getNodeSiblings(nodeHandle, reverse) {
    const getNextSibling = reverse ? NodeApi.getPreviousSibling : NodeApi.getNextSibling;
    while (nodeHandle) {
        yield createTypedNode(nodeHandle);
        nodeHandle = getNextSibling(nodeHandle);
    }
}

function* getNodeChildren(nodeHandle, childList, reverse) {
    const getStart = reverse ? NodeApi.getLastChild : NodeApi.getFirstChild;
    const getNext = reverse ? NodeApi.getPreviousSibling : NodeApi.getNextSibling;
    let childNodeHandle = getStart(nodeHandle, childList);
    while (childNodeHandle) {
        yield createTypedNode(childNodeHandle);
        childNodeHandle = getNext(childNodeHandle);
    }
}

function* getNodeChildrenRecursive(nodeHandle, childList, reverse) {
    const getStart = reverse ? NodeApi.getLastChild : NodeApi.getFirstChild;
    let childNodeHandle = getStart(nodeHandle, childList);
    while (childNodeHandle) {
        if (reverse) {
            for (const child of getNodeChildrenRecursive(childNodeHandle, childList, reverse)) {
                yield child;
            }
            yield createTypedNode(childNodeHandle);
            childNodeHandle = NodeApi.getPreviousSibling(childNodeHandle);
        }
        else {
            yield createTypedNode(childNodeHandle);
            for (const child of getNodeChildrenRecursive(childNodeHandle, childList, reverse)) {
                yield child;
            }
            childNodeHandle = NodeApi.getNextSibling(childNodeHandle);
        }
    }
}

function* getNodesRecursive(nodeHandle, childList, reverse) {
    if (nodeHandle) {
        yield createTypedNode(nodeHandle);
        for (const node of getNodeChildrenRecursive(nodeHandle, childList, reverse)) {
            yield node;
        }
    }
}

class NodeChildrenOnly extends Collection {
    constructor(parentNodeHandle, childType, reversed) {
        const genFunc = function*() {
            for (const node of getNodeChildren(parentNodeHandle, childType, reversed)) {
                yield node;
            }
        }
        super(genFunc);

        this.reverse = function() {
            return new NodeChildrenOnly(parentNodeHandle, childType, !reversed);
        }
    }
}


class NodeChildren extends NodeChildrenOnly {
    constructor(parentNodeHandle, childType, reversed) {
        super(parentNodeHandle, childType, reversed);

        this.reverse = function() {
            return new NodeChildren(parentNodeHandle, childType, !reversed);
        }

        Object.defineProperty(this, "all", {
            get: function() {
                return new NodeDescendents(parentNodeHandle, childType, reversed);
            }
        });
    }
}

class NodeDescendents extends Collection {
    constructor(rootNodeHandle, childType, reversed) {
        const genFunc = function*() {
            for (const node of getNodeChildrenRecursive(rootNodeHandle, childType, reversed)) {
                yield node;
            }
        }
        super(genFunc);

        this.reverse = function() {
        return new NodeDescendents(parentNodeHandle, childType, !reversed);
    }
    }
}

class Node extends Selectable {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'Node';
    }

    get isNode() {
        return true;
    }

    isSameNode(otherNode) {
        return NodeApi.isSameNode(this.handle, otherNode.handle);
    }

    get document() {
        const documentHandle = NodeApi.getDocument(this.handle);
        return documentHandle ? new DocumentModule.Document(documentHandle) : null;
    }

    get selfSelection() {
        return SelectionsModule.Selection.create(this.document, this);
    }

    get nextSibling() {
        const handle = NodeApi.getNextSibling(this.handle);
        if (handle)
            return createTypedNode(handle)
        else
            return null;
    }
    
    get previousSibling() {
        const handle = NodeApi.getPreviousSibling(this.handle);
        if (handle)
            return createTypedNode(handle)
        else
            return null;
    }
    
    get parent() {
        const handle = NodeApi.getParent(this.handle);
        if (handle)
            return createTypedNode(handle)
        else
            return null;
    }
    
    get firstChild() {
        return this.getFirstChild(NodeChildType.Main);
    }
    
    get lastChild() {
        return this.getLastChild(NodeChildType.Main);
    }

    getFirstChild(nodeChildType) {
        const handle = NodeApi.getFirstChild(this.handle, nodeChildType);
        if (handle)
            return createTypedNode(handle)
        else
            return null;
    }

    getLastChild(nodeChildType) {
        const handle = NodeApi.getLastChild(this.handle, nodeChildType);
        if (handle)
            return createTypedNode(handle)
        else
            return null;
    }

    get children() {
        return new NodeChildren(this.handle, NodeChildType.Main);
    }

    get enclosures() {
        return new NodeChildren(this.handle, NodeChildType.Enclosure);
    }

    getSpreadBaseBox(includeClips = true) {
        return NodeApi.getSpreadBaseBox(this.handle, includeClips);
    }

    get spreadBaseBox() {
        return this.getSpreadBaseBox(true);
    }

    get baseToSpreadTransform() {
        return NodeApi.getBaseToSpreadTransform(this.handle);
    }

    get localToSpreadTransform() {
        return NodeApi.getLocalToSpreadTransform(this.handle);
    }

    get spreadToBaseTransform() {
        return NodeApi.getSpreadToBaseTransform(this.handle);
    }

    getLineBox(includeClips = true) {
        return NodeApi.getLineBox(this.handle, includeClips);
    }

    getTransformedLineBox(transform, scalarTransform, includeClips = true) {
        return NodeApi.getTransformedLineBox(this.handle, transform, scalarTransform, includeClips);
    }

    getSpreadVisibleBox(includeParentEffects = true) {
        return NodeApi.getSpreadVisibleBox(this.handle, includeParentEffects);
    }
    
    getLocalVisibleBox() {
        return NodeApi.getLocalVisibleBox(this.handle);
    }

    getExactSpreadBaseBox() {
        return NodeApi.getExactSpreadBaseBox(this.handle);
    }
    
    getExactSpreadVisibleBox(includeParentEffects, considerParentClips) {
        return NodeApi.getExactSpreadVisibleBox(this.handle, includeParentEffects, considerParentClips);
    }

    getContentExtentsBox(includeInvisible, includeOffCurvePoints) {
        return NodeApi.getContentExtentsBox(this.handle, includeInvisible, includeOffCurvePoints);
    }

    getContentExtentsBoxOfChildren(includeInvisible, includeOffCurvePoints) {
        return NodeApi.getContentExtentsBoxOfChildren(this.handle, includeInvisible, includeOffCurvePoints);
    }

    get lineBox() {
        return this.getLineBox();
    }

    get spreadVisibleBox() {
        return this.getSpreadVisibleBox();
    }
    
    get localVisibleBox() {
        return this.getLocalVisibleBox();
    }

    get exactSpreadBaseBox() {
        return this.getExactSpreadBaseBox();
    }

    // basebox interface
    #baseBoxInterface
    get baseBoxInterface() {
        if (!this.#baseBoxInterface)
            this.#baseBoxInterface = new BaseBoxInterfaceModule.BaseBoxInterface(NodeApi.getBaseBoxInterface(this.handle));
        return this.#baseBoxInterface;
    }

    get baseBox() {
        return this.baseBoxInterface.baseBox;
    }

    get constrainingBaseBox() {
        return this.baseBoxInterface.constrainingBaseBox;
    }

    get bmIFace() {
        return NodeApi.getBlendModeInterface(this.handle);
    }

    // blend mode interface
    #blendModeInterface;
    get blendModeInterface() {
        if (!this.#blendModeInterface)
            this.#blendModeInterface = new BlendModeInterfaceModule.BlendModeInterface(NodeApi.getBlendModeInterface(this.handle));
        return this.#blendModeInterface;
    }

    get blendMode() {
        return this.blendModeInterface.blendMode;
    }

    get blendOptions() {
        return this.blendModeInterface.blendOptions;
    }

    get antialiasingMode() {
        return this.blendModeInterface.antialiasingMode;
    }

    // description interface
    #descriptionInterface;
    get descriptionInterface() {
        if (!this.#descriptionInterface)
            this.#descriptionInterface = new DescriptionInterfaceModule.DescriptionInterface(NodeApi.getDescriptionInterface(this.handle));
        return this.#descriptionInterface;
    }

    get description() {
        return this.descriptionInterface.description;
    }

    get userDescription() {
        return this.descriptionInterface.userDescription;
    }

    get defaultDescription() {
        return this.descriptionInterface.defaultDescription;
    }

    get defaultDescriptionForDisplay() {
        return this.descriptionInterface.defaultDescriptionForDisplay;
    }

    get tagColour() {
        return this.descriptionInterface.tagColour;
    }

    set userDescription(desc) {
        const cmd = CommandsModule.DocumentCommand.createSetDescription(this.selfSelection, desc);
        this.document.executeCommand(cmd);
    }

    set tagColour(colour) {
        const cmd = CommandsModule.DocumentCommand.createSetTagColour(this.selfSelection, colour);
        this.document.executeCommand(cmd);
    }

    // editability interface
    #editabilityInterface;
    get editabilityInterface() {
        if (!this.#editabilityInterface)
            this.#editabilityInterface = new EditabilityInterfaceModule.EditabilityInterface(NodeApi.getEditabilityInterface(this.handle));
        return this.#editabilityInterface;
    }

    get isEditable() {
        return this.editabilityInterface.isEditable;
    }

    get isLocalEditable() {
        return this.editabilityInterface.isLocalEditable;
    }

    get isMasterEditable() {
        return this.editabilityInterface.isMasterEditable;
    }

    get isLocked() {
        return !this.isEditable;
    }

    lock(preview) {
        const selection = this.selfSelection;
        const command = CommandsModule.DocumentCommand.createSetEditable(selection.handle, false);
        return this.document.executeCommand(command, preview);
    }

    unlock(preview) {
        const selection = this.selfSelection;
        const command = CommandsModule.DocumentCommand.createSetEditable(selection.handle, true);
        return this.document.executeCommand(command, preview);
    }

    // exportable interface
    #exportableInterface;
    get exportableInterface() {
        if (!this.#exportableInterface)
            this.#exportableInterface = new ExportableInterfaceModule.ExportableInterface(NodeApi.getExportableInterface(this.handle));
        return this.#exportableInterface;
    }

    get exportConfig() {
        return this.exportableInterface.exportConfig;
    }

    // filter effects interface:
    #layereffectsInterface;
    get layerEffectsInterface() {
        if (!this.#layereffectsInterface)
            this.#layereffectsInterface = new LayerEffectsInterfaceModule.LayerEffectsInterface(NodeApi.getLayerEffectsInterface(this.handle));
        return this.#layereffectsInterface;
    }

    get quickFX() {
        return this.layerEffectsInterface.effects;
    }

    // transform interface:
    #transformInterface;
    get transformInterface() {
        if (!this.#transformInterface)
            this.#transformInterface = new TransformInterfaceModule.TransformInterface(NodeApi.getTransformInterface(this.handle));
        return this.#transformInterface;
    }

    get transform() {
        return this.transformInterface.transform;
    }

    // visibility interface
    #visibilityInterface;
    get visibilityInterface() {
        if (!this.#visibilityInterface)
            this.#visibilityInterface = new VisibilityInterfaceModule.VisibilityInterface(NodeApi.getVisibilityInterface(this.handle));
        return this.#visibilityInterface;
    }

    get globalOpacity() {
        return this.visibilityInterface.globalOpacity;
    }

    get fillOpacity() {
        return this.visibilityInterface.fillOpacity;
    }

    get isVisible() {
        return this.visibilityInterface.isVisible;
    }

    get isVisibleInExport() {
        return this.visibilityInterface.isVisibleInExport;
    }

    get isVisibleInDomain() {
        return this.visibilityInterface.isVisibleInDomain;
    }

    testVisibility(options) {
        return this.visibilityInterface.testVisibility(options);
    }

    // tag interface
    #tagInterface;
    get tagInterface() {
        if (!this.#tagInterface)
            this.#tagInterface = new TagInterfaceModule.TagInterface(NodeApi.getTagInterface(this.handle));
        return this.#tagInterface;
    }

    hasKey(key) {
        return this.tagInterface.hasKey(key);
    }

    getValueForKey(key) {
        return this.tagInterface.getValueForKey(key);
    }

    get isMarkAsDecoration() {
        return this.tagInterface.isMarkAsDecoration;
    }

    hasPredefinedKey(key) {
        return this.tagInterface.hasPredefinedKey(key);
    }

    getValueForPredefinedKey(key) {
        return this.tagInterface.getValueForPredefinedKey(key);
    }

    get spread() {
        let node = this;
        while (node) {
            if (node.isSpreadNode)
                return node;
            node = node.parent;
        }
        return null;
    }

    moveToFirstChild(childType) {
        NodeApi.moveToFirstChild(this.handle, childType);
    }

    moveToLastChild(childType) {
        NodeApi.moveToLastChild(this.handle, childType);
    }

    moveToNextSibling() {
        NodeApi.moveToNextSibling(this.handle);
    }

    moveToParent() {
        NodeApi.moveToParent(this.handle);
    }

    moveToPreviousSibling() {
        NodeApi.moveToPreviousSibling(this.handle);
    }

    delete() {
        this.document.deleteSelection(this);
    }

    duplicate(transform = null) {
        const doc = this.document;
        const selection = SelectionsModule.Selection.create(doc, this);
        const cmd = CommandsModule.DocumentCommand.createTransform(selection, transform, {duplicateNodes:true});
        doc.executeCommand(cmd);
        return cmd.newNodes[0];
    }
}


class NodeDefinition extends HandleObject {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'NodeDefinition';
    }
    
    get isNodeDefinition() {
        return true;
    }
    
    set transform(xf) {
        NodeDefinitionApi.setTransform(this.handle, xf);
    }
    
    get transform() {
        return NodeDefinitionApi.getTransform(this.handle);
    }

    setTransform(xf) {
        this.transform = xf;
        return this;
    }
    
    set userDescription(desc) {
        NodeDefinitionApi.setUserDescription(this.handle, desc);
    }
    
    get userDescription() {
        return NodeDefinitionApi.getUserDescription(this.handle);
    }

    setUserDescription(desc) {
        this.userDescription = desc;
        return this;
    }
}


class LogicalNode extends Node {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LogicalNode';
    }

    get isLogicalNode() {
        return true;
    }

    get hasNonMaskChildren() {
        return LogicalNodeApi.hasNonMaskChildren(this.handle);
    }

    get hasNonMaskOrAdjustmentChildren() {
        return LogicalNodeApi.hasNonMaskOrAdjustmentChildren(this.handle);
    }

    // BrushFillInterfaceModule.BrushFillInterface
    #brushFillInterface;
    get brushFillInterface() {
        if (!this.#brushFillInterface)
            this.#brushFillInterface = new BrushFillInterfaceModule.BrushFillInterface(LogicalNodeApi.getBrushFillInterface(this.handle));
        return this.#brushFillInterface;
    }

    getBrushFillDescriptor(index, obeyScaleWithObject = true) {
        return this.brushFillInterface.getDescriptor(index, obeyScaleWithObject);
    }

    setBrushFillDescriptor(fillDescriptorOrColour, options, preview) {
        return this.brushFillInterface.setCurrentDescriptor(fillDescriptorOrColour, options, preview);
    }

    get brushFillDescriptor() {
        return this.brushFillInterface.currentDescriptor;
    }

    set brushFillDescriptor(fillDescriptorOrColour) {
        this.brushFillInterface.currentDescriptor = fillDescriptorOrColour;
    }

    get hasBrushFill() {
        return !this.brushFillInterface.isNoFill;
    }

    // LineStyleInterfaceModule.LineStyleInterface
    #lineStyleInterface;
    get lineStyleInterface() {
        if (!this.#lineStyleInterface)
            this.#lineStyleInterface = new LineStyleInterfaceModule.LineStyleInterface(LogicalNodeApi.getLineStyleInterface(this.handle));
        return this.#lineStyleInterface;
    }

    get lineStyleDescriptor() {
        return this.lineStyleInterface.lineStyleDescriptor;
    }

    get lineStyleDescriptors() {
        return this.lineStyleInterface.lineStyleDescriptors;
    }

    set lineStyleDescriptor(descriptor) {
        this.lineStyleInterface.lineStyleDescriptor = descriptor;
    }

    get lineStyle() {
        return this.lineStyleInterface.lineStyle;
    }

    set lineStyle(lineStyle) {
        this.lineStyleInterface.lineStyle = lineStyle;
    }

    get penFillDescriptor() {
        return this.lineStyleInterface.penFillDescriptor;
    }

    set penFillDescriptor(fillDescriptorOrColour) {
        this.lineStyleInterface.penFillDescriptor = fillDescriptorOrColour;
    }

    get penFillDescriptors() {
        return this.lineStyleInterface.penFillDescriptors;
    }

    get penFill() {
        return this.penFillDescriptor.fill;
    }

    get hasPenFill() {
        return !this.penFill.isNoFill;
    }

    get isLineStyleVisible() {
        return this.lineStyleDescriptor.isLineStyleVisible;
    }

    get lineWeight() {
        return this.lineStyleInterface.lineWeight;
    }

    set lineWeight(pixels) {
        this.lineStyleInterface.lineWeight = pixels
    }

    get lineWeightPts() {
        return this.lineStyleInterface.lineWeightPts;
    }

    set lineWeightPts(pts) {
        this.lineStyleInterface.lineWeightPts = pts;
    }

    get lineType() {
        return this.lineStyleInterface.lineType;
    }

    set lineType(type) {
        this.lineStyleInterface.lineType = type;
    }

    get lineCap() {
        return this.lineStyleInterface.lineCap;
    }

    set lineCap(cap) {
        this.lineStyleInterface.lineCap = cap;
    }

    get lineJoin() {
        return this.lineStyleInterface.lineJoin;
    }

    set lineJoin(join) {
        this.lineStyleInterface.lineJoin = join;
    }

    get dashPhase() {
        return this.lineStyleInterface.dashPhase;
    }

    set dashPhase(dashPhase) {
        this.lineStyleInterface.dashPhase = dashPhase;
    }

    get dashPattern() {
        return this.lineStyleInterface.dashPattern;
    }

    set dashPattern(dashPattern) {
        this.lineStyleInterface.dashPattern = dashPattern;
    }

    get hasBalancedDashes() {
        return this.lineStyleInterface.hasBalancedDashes;
    }

    set hasBalancedDashes(balanced) {
        this.lineStyleInterface.hasBalancedDashes = balanced;
    }

    get strokeAlignment() {
        return this.lineStyleDescriptor.strokeAlignment;
    }

    set strokeAlignment(alignment) {
        this.lineStyleDescriptor.strokeAlignment = alignment
    }

    // TransparencyInterfaceModule.TransparencyInterface
    #transparencyInterface;
    get transparencyInterface() {
        if (!this.#transparencyInterface) {
            this.#transparencyInterface = new TransparencyInterfaceModule.TransparencyInterface(LogicalNodeApi.getTransparencyInterface(this.handle));
        }
        return this.#transparencyInterface;
    }

    get transparencyFillDescriptor() {
        return this.transparencyInterface.fillDescriptor;
    }

    get transparencyFill() {
        return this.transparencyFillDescriptor.fill;
    }
}


class LogicalNodeDefinition extends NodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'LogicalNodeDefinition';
    }
    
    get isLogicalNodeDefinition() {
        return true;
    }
}


class ColouredLogicalNode extends LogicalNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ColouredLogicalNode';
    }

    get isColouredLogicalNode() {
        return true;
    }

    get layerColour() {
        return new Colour(ColouredLogicalNodeApi.getLayerColour(this.handle));
    }
}


class ColouredLogicalNodeDefinition extends LogicalNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ColouredLogicalNodeDefinition';
    }
    
    get isColouredLogicalNodeDefinition() {
        return true;
    }
}


class DocumentNode extends LogicalNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DocumentNode';
    }

    get isDocumentNode() {
        return true;
    }

    get pageCount() {
        return DocumentNodeApi.getPageCount(this.handle);
    }

    get spreadCount() {
        return DocumentNodeApi.getSpreadCount(this.handle);
    }
}


class GroupNode extends LogicalNode {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'GroupNode';
    }
    
    get isGroupNode() {
        return true;
    }
}


class GroupNodeDefinition extends LogicalNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'GroupNodeDefinition';
    }
    
    get isGroupNodeDefinition() {
        return true;
    }
}


class ContainerNode extends ColouredLogicalNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ContainerNode';
    }

    get isContainerNode() {
        return true;
    }
}


class ContainerNodeDefinition extends ColouredLogicalNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ContainerNodeDefinition';
    }
    
    static createDefault() {
        return new ContainerNodeDefinition(ContainerNodeDefinitionApi.createDefault());
    }

    static create(name = null) {
        const def = new ContainerNodeDefinition(ContainerNodeDefinitionApi.createDefault())
        if (name) {
            def.userDescription = name;
        }
        return def;
    }
}


class PhysicalNode extends Node {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PhysicalNode';
    }

    get isPhysicalNode() {
        return true;
    }

    get canTransformWhileProtectingChildList() {
        return PhysicalNodeApi.canTransformWhileProtectingChildList(this.handle);
    }
}


class PhysicalNodeDefinition extends NodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'PhysicalNodeDefinition';
    }
    
    get isPhysicalNodeDefinition() {
        return true;
    }
}


class DevelopParameters extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DevelopParameters';
    }

    get isDevelopParameters() {
        return true;
    }

    set exposure(value) {
        DevelopParametersApi.setExposure(this.handle, value);
    }

    get exposure() {
        return DevelopParametersApi.getExposure(this.handle);
    }

    set exposureEnabled(value) {
        DevelopParametersApi.setExposureEnabled(this.handle, value);
    }

    get exposureEnabled() {
        return DevelopParametersApi.getExposureEnabled(this.handle);
    }

    set blackpoint(value) {
        DevelopParametersApi.setBlackpoint(this.handle, value);
    }

    get blackpoint() {
        return DevelopParametersApi.getBlackpoint(this.handle);
    }

    set whitepoint(value) {
        DevelopParametersApi.setWhitepoint(this.handle, value);
    }

    get whitepoint() {
        return DevelopParametersApi.getWhitepoint(this.handle);
    }

    set contrast(value) {
        DevelopParametersApi.setContrast(this.handle, value);
    }

    get contrast() {
        return DevelopParametersApi.getContrast(this.handle);
    }

    set enhanceEnabled(value) {
        DevelopParametersApi.setEnhanceEnabled(this.handle, value);
    }

    get enhanceEnabled() {
        return DevelopParametersApi.getEnhanceEnabled(this.handle);
    }

    set saturation(value) {
        DevelopParametersApi.setSaturation(this.handle, value);
    }

    get saturation() {
        return DevelopParametersApi.getSaturation(this.handle);
    }

    set vibrance(value) {
        DevelopParametersApi.setVibrance(this.handle, value);
    }

    get vibrance() {
        return DevelopParametersApi.getVibrance(this.handle);
    }

    set clarity(value) {
        DevelopParametersApi.setClarity(this.handle, value);
    }

    get clarity() {
        return DevelopParametersApi.getClarity(this.handle);
    }

    set texture(value) {
        DevelopParametersApi.setTexture(this.handle, value);
    }

    get texture() {
        return DevelopParametersApi.getTexture(this.handle);
    }

    set shadowsIntensity(value) {
        DevelopParametersApi.setShadowsIntensity(this.handle, value);
    }

    get shadowsIntensity() {
        return DevelopParametersApi.getShadowsIntensity(this.handle);
    }

    set highlightsIntensity(value) {
        DevelopParametersApi.setHighlightsIntensity(this.handle, value);
    }

    get highlightsIntensity() {
        return DevelopParametersApi.getHighlightsIntensity(this.handle);
    }

    set shadowsHighlightsEnabled(value) {
        DevelopParametersApi.setShadowsHighlightsEnabled(this.handle, value);
    }

    get shadowsHighlightsEnabled() {
        return DevelopParametersApi.getShadowsHighlightsEnabled(this.handle);
    }

    set whiteBalance(value) {
        DevelopParametersApi.setWhiteBalance(this.handle, value);
    }

    get whiteBalance() {
        return DevelopParametersApi.getWhiteBalance(this.handle);
    }

    set tint(value) {
        DevelopParametersApi.setTint(this.handle, value);
    }

    get tint() {
        return DevelopParametersApi.getTint(this.handle);
    }

    set whiteBalanceEnabled(value) {
        DevelopParametersApi.setWhiteBalanceEnabled(this.handle, value);
    }

    get whiteBalanceEnabled() {
        return DevelopParametersApi.getWhiteBalanceEnabled(this.handle);
    }

    get rawWhiteBalance() {
        return DevelopParametersApi.getRawWhiteBalance(this.handle);
    }

    set applyToneCurve(value) {
        DevelopParametersApi.setApplyToneCurve(this.handle, value);
    }

    get applyToneCurve() {
        return DevelopParametersApi.getApplyToneCurve(this.handle);
    }

    set toneCurveEnabled(value) {
        DevelopParametersApi.setToneCurveEnabled(this.handle, value);
    }

    get toneCurveEnabled() {
        return DevelopParametersApi.getToneCurveEnabled(this.handle);
    }

    set toneCurveMethod(value) {
        DevelopParametersApi.setToneCurveMethod(this.handle, value);
    }

    get toneCurveMethod() {
        return DevelopParametersApi.getToneCurveMethod(this.handle);
    }

    set curves(value) {
        DevelopParametersApi.setCurves(this.handle, value?.handle);
    }

    get curves() {
        return new CurvesAdjustmentParameters(DevelopParametersApi.getCurves(this.handle));
    }

    set curvesEnabled(value) {
        DevelopParametersApi.setCurvesEnabled(this.handle, value);
    }

    get curvesEnabled() {
        return DevelopParametersApi.getCurvesEnabled(this.handle);
    }

    set noiseReductionLuminanceSigma(value) {
        DevelopParametersApi.setNoiseReductionLuminanceSigma(this.handle, value);
    }

    get noiseReductionLuminanceSigma() {
        return DevelopParametersApi.getNoiseReductionLuminanceSigma(this.handle);
    }

    set noiseReductionChromaSigma(value) {
        DevelopParametersApi.setNoiseReductionChromaSigma(this.handle, value);
    }

    get noiseReductionChromaSigma() {
        return DevelopParametersApi.getNoiseReductionChromaSigma(this.handle);
    }

    set noiseReductionDetail(value) {
        DevelopParametersApi.setNoiseReductionDetail(this.handle, value);
    }

    get noiseReductionDetail() {
        return DevelopParametersApi.getNoiseReductionDetail(this.handle);
    }

    set luminanceContribution(value) {
        DevelopParametersApi.setLuminanceContribution(this.handle, value);
    }

    get luminanceContribution() {
        return DevelopParametersApi.getLuminanceContribution(this.handle);
    }

    set colourContribution(value) {
        DevelopParametersApi.setColourContribution(this.handle, value);
    }

    get colourContribution() {
        return DevelopParametersApi.getColourContribution(this.handle);
    }

    set noiseReductionEnabled(value) {
        DevelopParametersApi.setNoiseReductionEnabled(this.handle, value);
    }

    get noiseReductionEnabled() {
        return DevelopParametersApi.getNoiseReductionEnabled(this.handle);
    }

    set waveletLumaSigma(value) {
        DevelopParametersApi.setWaveletLumaSigma(this.handle, value);
    }

    get waveletLumaSigma() {
        return DevelopParametersApi.getWaveletLumaSigma(this.handle);
    }

    set waveletChromaSigma(value) {
        DevelopParametersApi.setWaveletChromaSigma(this.handle, value);
    }

    get waveletChromaSigma() {
        return DevelopParametersApi.getWaveletChromaSigma(this.handle);
    }

    set waveletLevels(value) {
        DevelopParametersApi.setWaveletLevels(this.handle, value);
    }

    get waveletLevels() {
        return DevelopParametersApi.getWaveletLevels(this.handle);
    }

    set waveletChromaLevels(value) {
        DevelopParametersApi.setWaveletChromaLevels(this.handle, value);
    }

    get waveletChromaLevels() {
        return DevelopParametersApi.getWaveletChromaLevels(this.handle);
    }

    set waveletDetail(value) {
        DevelopParametersApi.setWaveletDetail(this.handle, value);
    }

    get waveletDetail() {
        return DevelopParametersApi.getWaveletDetail(this.handle);
    }

    set waveletNoiseReductionEnabled(value) {
        DevelopParametersApi.setWaveletNoiseReductionEnabled(this.handle, value);
    }

    get waveletNoiseReductionEnabled() {
        return DevelopParametersApi.getWaveletNoiseReductionEnabled(this.handle);
    }

    set noiseAdditionIntensity(value) {
        DevelopParametersApi.setNoiseAdditionIntensity(this.handle, value);
    }

    get noiseAdditionIntensity() {
        return DevelopParametersApi.getNoiseAdditionIntensity(this.handle);
    }

    set noiseAdditionGaussian(value) {
        DevelopParametersApi.setNoiseAdditionGaussian(this.handle, value);
    }

    get noiseAdditionGaussian() {
        return DevelopParametersApi.getNoiseAdditionGaussian(this.handle);
    }

    set noiseAdditionColour(value) {
        DevelopParametersApi.setNoiseAdditionColour(this.handle, value);
    }

    get noiseAdditionColour() {
        return DevelopParametersApi.getNoiseAdditionColour(this.handle);
    }

    set noiseAdditionEnabled(value) {
        DevelopParametersApi.setNoiseAdditionEnabled(this.handle, value);
    }

    get noiseAdditionEnabled() {
        return DevelopParametersApi.getNoiseAdditionEnabled(this.handle);
    }

    set profileEnabled(value) {
        DevelopParametersApi.setProfileEnabled(this.handle, value);
    }

    get profileEnabled() {
        return DevelopParametersApi.getProfileEnabled(this.handle);
    }

    set detailRefinementRadius(value) {
        DevelopParametersApi.setDetailRefinementRadius(this.handle, value);
    }

    get detailRefinementRadius() {
        return DevelopParametersApi.getDetailRefinementRadius(this.handle);
    }

    set detailRefinementAmount(value) {
        DevelopParametersApi.setDetailRefinementAmount(this.handle, value);
    }

    get detailRefinementAmount() {
        return DevelopParametersApi.getDetailRefinementAmount(this.handle);
    }

    set detailRefinementMethod(value) {
        DevelopParametersApi.setDetailRefinementMethod(this.handle, value);
    }

    get detailRefinementMethod() {
        return DevelopParametersApi.getDetailRefinementMethod(this.handle);
    }

    set detailRefinementEnabled(value) {
        DevelopParametersApi.setDetailRefinementEnabled(this.handle, value);
    }

    get detailRefinementEnabled() {
        return DevelopParametersApi.getDetailRefinementEnabled(this.handle);
    }

    set defringeHue(value) {
        DevelopParametersApi.setDefringeHue(this.handle, value);
    }

    get defringeHue() {
        return DevelopParametersApi.getDefringeHue(this.handle);
    }

    set defringeComplementary(value) {
        DevelopParametersApi.setDefringeComplementary(this.handle, value);
    }

    get defringeComplementary() {
        return DevelopParametersApi.getDefringeComplementary(this.handle);
    }

    set defringeTolerance(value) {
        DevelopParametersApi.setDefringeTolerance(this.handle, value);
    }

    get defringeTolerance() {
        return DevelopParametersApi.getDefringeTolerance(this.handle);
    }

    set defringeThreshold(value) {
        DevelopParametersApi.setDefringeThreshold(this.handle, value);
    }

    get defringeThreshold() {
        return DevelopParametersApi.getDefringeThreshold(this.handle);
    }

    set defringeRadius(value) {
        DevelopParametersApi.setDefringeRadius(this.handle, value);
    }

    get defringeRadius() {
        return DevelopParametersApi.getDefringeRadius(this.handle);
    }

    set defringeEnabled(value) {
        DevelopParametersApi.setDefringeEnabled(this.handle, value);
    }

    get defringeEnabled() {
        return DevelopParametersApi.getDefringeEnabled(this.handle);
    }

    set chromaticAberrationEnabled(value) {
        DevelopParametersApi.setChromaticAberrationEnabled(this.handle, value);
    }

    get chromaticAberrationEnabled() {
        return DevelopParametersApi.getChromaticAberrationEnabled(this.handle);
    }

    set chromaticAberrationUseProfile(value) {
        DevelopParametersApi.setChromaticAberrationUseProfile(this.handle, value);
    }

    get chromaticAberrationUseProfile() {
        return DevelopParametersApi.getChromaticAberrationUseProfile(this.handle);
    }

    set lensVignetteEnabled(value) {
        DevelopParametersApi.setLensVignetteEnabled(this.handle, value);
    }

    get lensVignetteEnabled() {
        return DevelopParametersApi.getLensVignetteEnabled(this.handle);
    }

    set lensVignetteUseProfile(value) {
        DevelopParametersApi.setLensVignetteUseProfile(this.handle, value);
    }

    get lensVignetteUseProfile() {
        return DevelopParametersApi.getLensVignetteUseProfile(this.handle);
    }

    set lensVignetteIntensity(value) {
        DevelopParametersApi.setLensVignetteIntensity(this.handle, value);
    }

    get lensVignetteIntensity() {
        return DevelopParametersApi.getLensVignetteIntensity(this.handle);
    }

    set postVignetteEnabled(value) {
        DevelopParametersApi.setPostVignetteEnabled(this.handle, value);
    }

    get postVignetteEnabled() {
        return DevelopParametersApi.getPostVignetteEnabled(this.handle);
    }

    set postVignetteIntensity(value) {
        DevelopParametersApi.setPostVignetteIntensity(this.handle, value);
    }

    get postVignetteIntensity() {
        return DevelopParametersApi.getPostVignetteIntensity(this.handle);
    }

    set postVignetteScale(value) {
        DevelopParametersApi.setPostVignetteScale(this.handle, value);
    }

    get postVignetteScale() {
        return DevelopParametersApi.getPostVignetteScale(this.handle);
    }

    set postVignetteHardness(value) {
        DevelopParametersApi.setPostVignetteHardness(this.handle, value);
    }

    get postVignetteHardness() {
        return DevelopParametersApi.getPostVignetteHardness(this.handle);
    }

    set lensCorrectionEnabled(value) {
        DevelopParametersApi.setLensCorrectionEnabled(this.handle, value);
    }

    get lensCorrectionEnabled() {
        return DevelopParametersApi.getLensCorrectionEnabled(this.handle);
    }

    set lensProfileDistortion(value) {
        DevelopParametersApi.setLensProfileDistortion(this.handle, value);
    }

    get lensProfileDistortion() {
        return DevelopParametersApi.getLensProfileDistortion(this.handle);
    }

    set lensDistortion(value) {
        DevelopParametersApi.setLensDistortion(this.handle, value);
    }

    get lensDistortion() {
        return DevelopParametersApi.getLensDistortion(this.handle);
    }

    set lensRotation(value) {
        DevelopParametersApi.setLensRotation(this.handle, value);
    }

    get lensRotation() {
        return DevelopParametersApi.getLensRotation(this.handle);
    }

    set lensScale(value) {
        DevelopParametersApi.setLensScale(this.handle, value);
    }

    get lensScale() {
        return DevelopParametersApi.getLensScale(this.handle);
    }

    set lensHorizontal(value) {
        DevelopParametersApi.setLensHorizontal(this.handle, value);
    }

    get lensHorizontal() {
        return DevelopParametersApi.getLensHorizontal(this.handle);
    }

    set lensVertical(value) {
        DevelopParametersApi.setLensVertical(this.handle, value);
    }

    get lensVertical() {
        return DevelopParametersApi.getLensVertical(this.handle);
    }

    get lensProfileName() {
        return DevelopParametersApi.getLensProfileName(this.handle);
    }

    set invertEnabled(value) {
        DevelopParametersApi.setInvertEnabled(this.handle, value);
    }

    get invertEnabled() {
        return DevelopParametersApi.getInvertEnabled(this.handle);
    }

    set invertMethod(value) {
        DevelopParametersApi.setInvertMethod(this.handle, value);
    }

    get invertMethod() {
        return DevelopParametersApi.getInvertMethod(this.handle);
    }

    set invertStrength(value) {
        DevelopParametersApi.setInvertStrength(this.handle, value);
    }

    get invertStrength() {
        return DevelopParametersApi.getInvertStrength(this.handle);
    }

    set hslEnabled(value) {
        DevelopParametersApi.setHSLEnabled(this.handle, value);
    }

    get hslEnabled() {
        return DevelopParametersApi.getHSLEnabled(this.handle);
    }

    set blackAndWhiteEnabled(value) {
        DevelopParametersApi.setBlackAndWhiteEnabled(this.handle, value);
    }

    get blackAndWhiteEnabled() {
        return DevelopParametersApi.getBlackAndWhiteEnabled(this.handle);
    }

    set splitToningEnabled(value) {
        DevelopParametersApi.setSplitToningEnabled(this.handle, value);
    }

    get splitToningEnabled() {
        return DevelopParametersApi.getSplitToningEnabled(this.handle);
    }

    set selectiveColourEnabled(value) {
        DevelopParametersApi.setSelectiveColourEnabled(this.handle, value);
    }

    get selectiveColourEnabled() {
        return DevelopParametersApi.getSelectiveColourEnabled(this.handle);
    }

    set colourBalanceEnabled(value) {
        DevelopParametersApi.setColourBalanceEnabled(this.handle, value);
    }

    get colourBalanceEnabled() {
        return DevelopParametersApi.getColourBalanceEnabled(this.handle);
    }

    set hsl(value) {
        DevelopParametersApi.setHSL(this.handle, value?.handle);
    }

    get hsl() {
        return new HSLShiftAdjustmentParameters(DevelopParametersApi.getHSL(this.handle));
    }

    set blackAndWhite(value) {
        DevelopParametersApi.setBlackAndWhite(this.handle, value?.handle);
    }

    get blackAndWhite() {
        return new BlackAndWhiteAdjustmentParameters(DevelopParametersApi.getBlackAndWhite(this.handle));
    }

    set splitToning(value) {
        DevelopParametersApi.setSplitToning(this.handle, value?.handle);
    }

    get splitToning() {
        return new SplitToningAdjustmentParameters(DevelopParametersApi.getSplitToning(this.handle));
    }

    set selectiveColour(value) {
        DevelopParametersApi.setSelectiveColour(this.handle, value?.handle);
    }

    get selectiveColour() {
        return new SelectiveColourAdjustmentParameters(DevelopParametersApi.getSelectiveColour(this.handle));
    }

    set colourBalance(value) {
        DevelopParametersApi.setColourBalance(this.handle, value?.handle);
    }

    get colourBalance() {
        return new ColourBalanceAdjustmentParameters(DevelopParametersApi.getColourBalance(this.handle));
    }

    set showClippedHighlights(value) {
        DevelopParametersApi.setShowClippedHighlights(this.handle, value);
    }

    get showClippedHighlights() {
        return DevelopParametersApi.getShowClippedHighlights(this.handle);
    }

    set showClippedShadows(value) {
        DevelopParametersApi.setShowClippedShadows(this.handle, value);
    }

    get showClippedShadows() {
        return DevelopParametersApi.getShowClippedShadows(this.handle);
    }

    set showClippedTones(value) {
        DevelopParametersApi.setShowClippedTones(this.handle, value);
    }

    get showClippedTones() {
        return DevelopParametersApi.getShowClippedTones(this.handle);
    }

    set showFocusPeaking(value) {
        DevelopParametersApi.setShowFocusPeaking(this.handle, value);
    }

    get showFocusPeaking() {
        return DevelopParametersApi.getShowFocusPeaking(this.handle);
    }

    set focusPeakingHue(value) {
        DevelopParametersApi.setFocusPeakingHue(this.handle, value);
    }

    get focusPeakingHue() {
        return DevelopParametersApi.getFocusPeakingHue(this.handle);
    }
}


class DevelopNode extends PhysicalNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DevelopNode';
    }

    get isDevelopNode() {
        return true;
    }

    get parameters() {
        return new DevelopParameters(DevelopNodeApi.getParameters(this.handle));
    }

    get sourceIsRaw() {
        return DevelopNodeApi.getSourceIsRaw(this.handle);
    }

    get imageSize() {
        return DevelopNodeApi.getImageSize(this.handle);
    }

    // ImageResourceInterfaceModule.ImageResourceInterface
    #imageResourceInterface;
    get imageResourceInterface() {
        if (!this.#imageResourceInterface)
            this.#imageResourceInterface = new ImageResourceInterfaceModule.ImageResourceInterface(DevelopNodeApi.getImageResourceInterface(this.handle));
        return this.#imageResourceInterface;
    }

    // RasterInterfaceModule.RasterInterface
    #rasterInterface;
    get rasterInterface() {
        if (!this.#rasterInterface)
            this.#rasterInterface = new RasterInterfaceModule.RasterInterface(DevelopNodeApi.getRasterInterface(this.handle));
        return this.#rasterInterface;
    }
}

class EmbeddedDocumentNode extends PhysicalNode {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'EmbeddedDocumentNode';
    }

    get isEmbeddedDocumentNode() {
        return true;
    }
    
    get selectedSpreadId () {
        return EmbeddedDocumentNodeApi.getSelectedSpreadId(this.handle);
    }
    
    get selectedArtboardId () {
        return EmbeddedDocumentNodeApi.getSelectedArtboardId(this.handle);
    }
    
    get embeddedDocumentHasSpreads () {
        return EmbeddedDocumentNodeApi.embeddedDocumentHasSpreads(this.handle);
    }
    
    get embeddedDocumentHasArtboards () {
        return EmbeddedDocumentNodeApi.embeddedDocumentHasArtboards(this.handle);
    }
    
    get embeddedDocumentHasPageBoundingBoxes () {
        return EmbeddedDocumentNodeApi.embeddedDocumentHasPageBoundingBoxes(this.handle);
    }
    
    get embeddedDocumentHasLayers () {
        return EmbeddedDocumentNodeApi.embeddedDocumentHasLayers(this.handle);
    }
    
    get selectedArtboardOffset () {
        return EmbeddedDocumentNodeApi.getSelectedArtboardOffset(this.handle);
    }
    
    get pageBoundingBoxType () {
        return EmbeddedDocumentNodeApi.getPageBoundingBoxType(this.handle);
    }
    
    get PDFPassthrough () {
        return EmbeddedDocumentNodeApi.getPDFPassthrough(this.handle);
    }
    
    get canSetPDFPassthrough () {
        return EmbeddedDocumentNodeApi.canSetPDFPassthrough(this.handle);
    }
    
    get rasterDPI () {
        return EmbeddedDocumentNodeApi.getRasterDPI(this.handle);
    }
    
    get originalHostDPI () {
        return EmbeddedDocumentNodeApi.getOriginalHostDPI(this.handle);
    }
    
    get isAffinityFile () {
        return EmbeddedDocumentNodeApi.isAffinityFile(this.handle);
    }
    
    get canMakeLinked () {
        return EmbeddedDocumentNodeApi.canMakeLinked(this.handle);
    }
    
    get canEditEmbeddedImage () {
        return EmbeddedDocumentNodeApi.canEditEmbeddedImage(this.handle);
    }
    
    get loadDocumentOptions() {
        return new DocumentModule.LoadDocumentOptions(EmbeddedDocumentNodeApi.getLoadDocumentOptions(this.handle));
    }
    
    get shouldAllowSelectDocument () {
        return EmbeddedDocumentNodeApi.shouldAllowSelectDocument(this.handle);
    }
    
    get isArtboardSelected () {
        return EmbeddedDocumentNodeApi.isArtboardSelected(this.handle);
    }
    
    get isArtboardDoc () {
        return EmbeddedDocumentNodeApi.isArtboardDoc(this.handle);
    }
    
    get needsPassword () {
        return EmbeddedDocumentNodeApi.needsPassword(this.handle);
    }
    
    enumerateSpreads(includeMasters, func) {
        return EmbeddedDocumentNodeApi.enumerateSpreads(this.handle, includeMasters, func);
    }
    
    enumerateArtboards(func) {
        return EmbeddedDocumentNodeApi.enumerateArtboards(this.handle, func);
    }
    
    enumeratePageBoundingBoxes(func) {
        return EmbeddedDocumentNodeApi.enumeratePageBoundingBoxes(this.handle, func);
    }
    
    enumerateLayerVisibilities(func) {
        return EmbeddedDocumentNodeApi.enumerateLayerVisibilities(this.handle, func);
    }
    
    getSpreads(includeMasters) {
        let results = [];
        this.enumerateSpreads(includeMasters, (description, ID) => {
            results.push({spreadDescription: description, spreadID: ID});
            return EnumerationResult.Continue;
        });
        return results;
    }

    get artboards() {
        let results = [];
        this.enumerateArtboards((description, ID) => {
            results.push({artboardDescription: description, artboardID: ID});
            return EnumerationResult.Continue;
        });
        return results;
    }

    get pageBoundingBoxes() {
        let results = [];
        this.enumeratePageBoundingBoxes((pageBBox, ID) => {
            results.push({pageBoundingBox: pageBBox, boxID: ID});
            return EnumerationResult.Continue;
        });
        return results;
    }

    get layerVisibilities() {
        let results = [];
        this.enumerateLayerVisibilities((name, visible) => {
            results.push({layerName: name, visible: visible});
            return EnumerationResult.Continue;
        });
        return results;
    }

    // ImageResourceInterfaceModule.ImageResourceInterface
    #imageResourceInterface;
    get imageResourceInterface() {
        if (!this.#imageResourceInterface)
            this.#imageResourceInterface = new ImageResourceInterfaceModule.ImageResourceInterface(EmbeddedDocumentNodeApi.getImageResourceInterface(this.handle));
        return this.#imageResourceInterface;
    }

    get imageFilePath() {
        return this.imageResourceInterface.imageFilePath;
    }

    getImageFileSize(asBigInt) {
        return this.imageResourceInterface.getImageFileSize(asBigInt);
    }

    get imageFileSize() {
        return this.getImageFileSize();
    }

    get imageFileType() {
        return this.imageResourceInterface.fileType;
    }

    get imageFileTypeName() {
        return this.imageResourceInterface.fileTypeName;
    }
    
    // TransparencyInterfaceModule.TransparencyInterface
    #transparencyInterface;
    get transparencyInterface() {
        if (!this.#transparencyInterface) {
            this.#transparencyInterface = new TransparencyInterfaceModule.TransparencyInterface(EmbeddedDocumentNodeApi.getTransparencyInterface(this.handle));
        }
        return this.#transparencyInterface;
    }

    get transparencyFillDescriptor() {
        return this.transparencyInterface.fillDescriptor;
    }

    get transparencyFill() {
        return this.transparencyFillDescriptor.fill;
    }
}


class RasterNode extends PhysicalNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RasterNode';
    }

    get isRasterNode() {
        return true;
    }

    get extendEmpty() {
        return RasterNodeApi.isExtendEmpty(this.handle);
    }
    
    // RasterInterfaceModule.RasterInterface
    #rasterInterface;
    get rasterInterface() {
        if (!this.#rasterInterface)
            this.#rasterInterface = new RasterInterfaceModule.RasterInterface(RasterNodeApi.getRasterInterface(this.handle));
        return this.#rasterInterface;
    }

    get rasterWidth() {
        return this.rasterInterface.width;
    }

    get rasterHeight() {
        return this.rasterInterface.height;
    }

    get rasterFormat() {
        return this.rasterInterface.format;
    }

    get pixelSize() {
        return this.rasterInterface.pixelSize;
    }

    createCompatibleBitmap(copyContents) {
        return this.rasterInterface.createCompatibleBitmap(copyContents);
    }

    createCompatibleBuffer(copyContents) {
        return this.rasterInterface.createCompatibleBuffer(copyContents);
    }

    copyTo(dest, destRect, srcX, srcY) {
        return this.rasterInterface.copyTo(dest, destRect, srcX, srcY);
    }
}


class RasterNodeDefinition extends PhysicalNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'RasterNodeDefinition';
    }
    
    static create(format) {
        return new RasterNodeDefinition(RasterNodeDefinitionApi.create(format));
    }

    get isRasterNodeDefinition() {
        return true;
    }
    
    set bitmap(bm) {
        RasterNodeDefinitionApi.setBitmap(this.handle, bm.handle);
    }
    
    get bitmap() {
        return new RasterObject(RasterNodeDefinitionApi.getBitmap(this.handle));
    }

    setBitmap(bm) {
        this.bitmap = bm;
        return this;
    }
}


class PatternRasterNode extends RasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PatternRasterNode';
    }

    get isPatternRasterNode() {
        return true;
    }

    get mirror() {
        return PatternRasterNodeApi.getMirror(this.handle);
    }
}


class PatternRasterNodeDefinition extends RasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PatternRasterNodeDefinition';
    }

    get isPatternRasterNodeDefinition() {
        return true;
    }

    get mirror() {
        return PatternRasterNodeDefinitionApi.getMirror(this.handle);
    }

    set mirror(value) {
        PatternRasterNodeDefinitionApi.setMirror(this.handle, value);
    }

    setMirror(value) {
        this.mirror = value;
        return this;
    }

    static createDefault(document) {
        return new PatternRasterNodeDefinition(PatternRasterNodeDefinitionApi.createDefault(document.handle));
    }

    static create(bitmap, transform, mirror) {
        return new PatternRasterNodeDefinition(PatternRasterNodeDefinitionApi.create(bitmap.handle, transform, mirror));
    }
}


class EnclosureRasterNode extends RasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'EnclosureRasterNode';
    }

    get isEnclosureRasterNode() {
        return true;
    }
}


class EnclosureRasterNodeDefinition extends RasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'EnclosureRasterNodeDefinition';
    }
    
    get isEnclosureRasterNodeDefinition() {
        return true;
    }
}


class AdjustmentRasterNode extends EnclosureRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'AdjustmentRasterNode';
    }

    get isAdjustmentRasterNode() {
        return true;
    }
}


class AdjustmentRasterNodeDefinition extends EnclosureRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'AdjustmentRasterNodeDefinition';
    }
    
    get isAdjustmentRasterNodeDefinition() {
        return true;
    }
}


class BlackAndWhiteAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use BlackAndWhiteAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new BlackAndWhiteAdjustmentParameters(). Use BlackAndWhiteAdjustmentParameters.create() instead.");
            super(BlackAndWhiteAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'BlackAndWhiteAdjustmentParameters';
    }

    get isBlackAndWhiteAdjustmentParameters() {
        return true;
    }

    set red(value) {
        BlackAndWhiteAdjustmentParametersApi.setRed(this.handle, value);
    }

    get red() {
        return BlackAndWhiteAdjustmentParametersApi.getRed(this.handle);
    }

    set green(value) {
        BlackAndWhiteAdjustmentParametersApi.setGreen(this.handle, value);
    }

    get green() {
        return BlackAndWhiteAdjustmentParametersApi.getGreen(this.handle);
    }

    set blue(value) {
        BlackAndWhiteAdjustmentParametersApi.setBlue(this.handle, value);
    }

    get blue() {
        return BlackAndWhiteAdjustmentParametersApi.getBlue(this.handle);
    }

    set cyan(value) {
        BlackAndWhiteAdjustmentParametersApi.setCyan(this.handle, value);
    }

    get cyan() {
        return BlackAndWhiteAdjustmentParametersApi.getCyan(this.handle);
    }

    set magenta(value) {
        BlackAndWhiteAdjustmentParametersApi.setMagenta(this.handle, value);
    }

    get magenta() {
        return BlackAndWhiteAdjustmentParametersApi.getMagenta(this.handle);
    }

    set yellow(value) {
        BlackAndWhiteAdjustmentParametersApi.setYellow(this.handle, value);
    }

    get yellow() {
        return BlackAndWhiteAdjustmentParametersApi.getYellow(this.handle);
    }

    static create() {
        return new BlackAndWhiteAdjustmentParameters(BlackAndWhiteAdjustmentParametersApi.create());
    }
}


class BlackAndWhiteAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BlackAndWhiteAdjustmentRasterNode';
    }

    get isBlackAndWhiteAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new BlackAndWhiteAdjustmentParameters(BlackAndWhiteAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class BlackAndWhiteAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BlackAndWhiteAdjustmentRasterNodeDefinition';
    }

    get isBlackAndWhiteAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        BlackAndWhiteAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new BlackAndWhiteAdjustmentParameters(BlackAndWhiteAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new BlackAndWhiteAdjustmentRasterNodeDefinition(BlackAndWhiteAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new BlackAndWhiteAdjustmentRasterNodeDefinition(BlackAndWhiteAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class BrightnessContrastAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use BrightnessContrastAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new BrightnessContrastAdjustmentParameters(). Use BrightnessContrastAdjustmentParameters.create() instead.");
            super(BrightnessContrastAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'BrightnessContrastAdjustmentParameters';
    }

    get isBrightnessContrastAdjustmentParameters() {
        return true;
    }

    set brightness(value) {
        BrightnessContrastAdjustmentParametersApi.setBrightness(this.handle, value);
    }

    get brightness() {
        return BrightnessContrastAdjustmentParametersApi.getBrightness(this.handle);
    }

    set contrast(value) {
        BrightnessContrastAdjustmentParametersApi.setContrast(this.handle, value);
    }

    get contrast() {
        return BrightnessContrastAdjustmentParametersApi.getContrast(this.handle);
    }

    set isLinear(value) {
        BrightnessContrastAdjustmentParametersApi.setIsLinear(this.handle, value);
    }

    get isLinear() {
        return BrightnessContrastAdjustmentParametersApi.getIsLinear(this.handle);
    }

    static create() {
        return new BrightnessContrastAdjustmentParameters(BrightnessContrastAdjustmentParametersApi.create());
    }
}


class BrightnessContrastAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BrightnessContrastAdjustmentRasterNode';
    }

    get isBrightnessContrastAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new BrightnessContrastAdjustmentParameters(BrightnessContrastAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class BrightnessContrastAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BrightnessContrastAdjustmentRasterNodeDefinition';
    }

    get isBrightnessContrastAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        BrightnessContrastAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new BrightnessContrastAdjustmentParameters(BrightnessContrastAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new BrightnessContrastAdjustmentRasterNodeDefinition(BrightnessContrastAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new BrightnessContrastAdjustmentRasterNodeDefinition(BrightnessContrastAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


const COLOUR_BALANCE_ADJUSTMENT_VALUES_FIELDS = ['cyanRed', 'magentaGreen', 'yellowBlue'];

class ColourBalanceAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use ColourBalanceAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new ColourBalanceAdjustmentParameters(). Use ColourBalanceAdjustmentParameters.create() instead.");
            super(ColourBalanceAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'ColourBalanceAdjustmentParameters';
    }

    get isColourBalanceAdjustmentParameters() {
        return true;
    }

    get valuesCount() {
        return ColourBalanceAdjustmentParametersApi.getValuesCount(this.handle);
    }

    setValues(tonalRange, value) {
        ColourBalanceAdjustmentParametersApi.setValues(this.handle, tonalRange, value);
    }

    getValues(tonalRange) {
        return ColourBalanceAdjustmentParametersApi.getValues(this.handle, tonalRange);
    }

    // The callback is invoked as callback(tonalRange, values), with tonalRange a TonalRangeType, and returns an EnumerationResult.
    enumerateValues(callback) {
        return ColourBalanceAdjustmentParametersApi.enumerateValues(this.handle, callback);
    }

    // Whole-array assignment: params.values = [{...}, ...] sends every element (any array-like with valuesCount object elements).
    set values(values) {
        setStructArray(this.valuesCount, values, (tonalRange, value) => this.setValues(tonalRange, value), 'ColourBalanceValues');
    }

    // Array-like live view indexed by TonalRangeType: params.values[i] = {...} and params.values[i].cyanRed = v both write through.
    get values() {
        return liveStructArray(this.valuesCount, COLOUR_BALANCE_ADJUSTMENT_VALUES_FIELDS, tonalRange => this.getValues(tonalRange), (tonalRange, value) => this.setValues(tonalRange, value));
    }

    set preserveLuminosity(value) {
        ColourBalanceAdjustmentParametersApi.setPreserveLuminosity(this.handle, value);
    }

    get preserveLuminosity() {
        return ColourBalanceAdjustmentParametersApi.getPreserveLuminosity(this.handle);
    }

    static create() {
        return new ColourBalanceAdjustmentParameters(ColourBalanceAdjustmentParametersApi.create());
    }
}


class ColourBalanceAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ColourBalanceAdjustmentRasterNode';
    }

    get isColourBalanceAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new ColourBalanceAdjustmentParameters(ColourBalanceAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class ColourBalanceAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ColourBalanceAdjustmentRasterNodeDefinition';
    }

    get isColourBalanceAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        ColourBalanceAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new ColourBalanceAdjustmentParameters(ColourBalanceAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ColourBalanceAdjustmentRasterNodeDefinition(ColourBalanceAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new ColourBalanceAdjustmentRasterNodeDefinition(ColourBalanceAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class CurvesAdjustmentParameters extends HandleObject {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'CurvesAdjustmentParameters';
    }
    
    get isCurvesAdjustmentParameters() {
        return true;
    }
    
    set masterSpline(masterSpline) {
        return CurvesAdjustmentParametersApi.setMasterSpline(this.handle, masterSpline.handle);
    }
    
    setChannelSpline(channel, channelSpline) {
        return CurvesAdjustmentParametersApi.setChannelSpline(this.handle, channel, channelSpline.handle);
    }
    
    set min(minV) {
        return CurvesAdjustmentParametersApi.setMin(this.handle, minV);
    }
    
    set max(maxV) {
        return CurvesAdjustmentParametersApi.setMax(this.handle, maxV);
    }
    
    get masterSpline() {
        return new Spline(CurvesAdjustmentParametersApi.getMasterSpline(this.handle));
    }
    
    getChannelSpline(channel) {
        return new Spline(CurvesAdjustmentParametersApi.getChannelSpline(this.handle, channel));
    }

    get channelSplineCount() {
        return CurvesAdjustmentParametersApi.getChannelSplineCount(this.handle);
    }

    // The callback is invoked as callback(channel, spline) and returns an EnumerationResult; spline is null for an unset channel.
    enumerateChannelSplines(callback) {
        return CurvesAdjustmentParametersApi.enumerateChannelSplines(this.handle, (channel, splineHandle) => callback(channel, splineHandle ? new Spline(splineHandle) : null));
    }
    
    get min() {
        return CurvesAdjustmentParametersApi.getMin(this.handle);
    }
    
    get max() {
        return CurvesAdjustmentParametersApi.getMax(this.handle);
    }
    
    static create() {
        return new CurvesAdjustmentParameters(CurvesAdjustmentParametersApi.create());
    }
}


class CurvesAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CurvesAdjustmentRasterNode';
    }

    get isCurvesAdjustmentRasterNode() {
        return true;
    }
    
    get parameters() {
        return new CurvesAdjustmentParameters(CurvesAdjustmentRasterNodeApi.getParameters(this.handle));
    }
    
    get colourSpace() {
        return CurvesAdjustmentRasterNodeApi.getColourSpace(this.handle);
    }
}

class CurvesAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'CurvesAdjustmentRasterNodeDefinition';
    }
    
    get isCurvesAdjustmentRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        CurvesAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new CurvesAdjustmentParameters(CurvesAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    set colourSpace(csType) {
        CurvesAdjustmentRasterNodeDefinitionApi.setColourSpace(this.handle, csType);
    }

    get colourSpace() {
        return CurvesAdjustmentRasterNodeDefinitionApi.getColourSpace(this.handle);
    }
    
    setColourSpace(csType) {
        this.colourSpace = csType;
        return this;
    }
    
    static create(params, colourSpace) {
        return new CurvesAdjustmentRasterNodeDefinition(CurvesAdjustmentRasterNodeDefinitionApi.create(params.handle, colourSpace));
    }

    static createDefault(document) {
        return new CurvesAdjustmentRasterNodeDefinition(CurvesAdjustmentRasterNodeDefinitionApi.createDefault(document.handle));
    }
}


class ExposureAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use ExposureAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new ExposureAdjustmentParameters(). Use ExposureAdjustmentParameters.create() instead.");
            super(ExposureAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'ExposureAdjustmentParameters';
    }

    get isExposureAdjustmentParameters() {
        return true;
    }

    set exposure(value) {
        ExposureAdjustmentParametersApi.setExposure(this.handle, value);
    }

    get exposure() {
        return ExposureAdjustmentParametersApi.getExposure(this.handle);
    }

    static create() {
        return new ExposureAdjustmentParameters(ExposureAdjustmentParametersApi.create());
    }
}


class ExposureAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ExposureAdjustmentRasterNode';
    }

    get isExposureAdjustmentRasterNode() {
        return true;
    }
    
    get parameters() {
        return new ExposureAdjustmentParameters(ExposureAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class ExposureAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ExposureAdjustmentRasterNodeDefinition';
    }
    
    get isExposureAdjustmentRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        ExposureAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new ExposureAdjustmentParameters(ExposureAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }
    
    static create(params) {
        return new ExposureAdjustmentRasterNodeDefinition(ExposureAdjustmentRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new ExposureAdjustmentRasterNodeDefinition(ExposureAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class HSLShiftAdjustmentParameters extends HandleObject {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'HSLShiftAdjustmentParameters';
    }
    
    get isHSLShiftAdjustmentParameters() {
        return true;
    }
    
    set masterParameters(masterParameter) {
        return HSLShiftAdjustmentParametersApi.setMasterParameters(this.handle, masterParameter);
    }
    
    setChannelParameters(channel, channelParameter) {
        return HSLShiftAdjustmentParametersApi.setChannelParameters(this.handle, channel, channelParameter);
    }
    
    setChannelColourRange(channel, colourRange) {
        return HSLShiftAdjustmentParametersApi.setChannelColourRange(this.handle, channel, colourRange);
    }
    
    set useHSV(useHSV) {
        return HSLShiftAdjustmentParametersApi.setUseHSV(this.handle, useHSV);
    }
    
    get masterParameters() {
        return HSLShiftAdjustmentParametersApi.getMasterParameters(this.handle);
    }
    
    getChannelParameters(channel) {
        return HSLShiftAdjustmentParametersApi.getChannelParameters(this.handle, channel);
    }
    
    getChannelColourRange(channel) {
        return HSLShiftAdjustmentParametersApi.getChannelColourRange(this.handle, channel);
    }
    
    get useHSV() {
        return HSLShiftAdjustmentParametersApi.getUseHSV(this.handle);
    }

    get channelCount() {
        return HSLShiftAdjustmentParametersApi.getChannelCount(this.handle);
    }

    // The callback is invoked as callback(channel, channelParameters) and returns an EnumerationResult.
    enumerateChannelParameters(callback) {
        return HSLShiftAdjustmentParametersApi.enumerateChannelParameters(this.handle, callback);
    }

    // The callback is invoked as callback(channel, colourRange) and returns an EnumerationResult.
    enumerateChannelColourRanges(callback) {
        return HSLShiftAdjustmentParametersApi.enumerateChannelColourRanges(this.handle, callback);
    }
    
    static create() {
        return new HSLShiftAdjustmentParameters(HSLShiftAdjustmentParametersApi.create());
    }
}


class HSLShiftAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'HSLShiftAdjustmentRasterNode';
    }

    get isHSLShiftAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new HSLShiftAdjustmentParameters(HSLShiftAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class HSLShiftAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'HSLShiftAdjustmentRasterNodeDefinition';
    }

    get isHSLShiftAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        HSLShiftAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new HSLShiftAdjustmentParameters(HSLShiftAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    static create(parameters) {
        return new HSLShiftAdjustmentRasterNodeDefinition(HSLShiftAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new HSLShiftAdjustmentRasterNodeDefinition(HSLShiftAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class InvertAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'InvertAdjustmentRasterNode';
    }

    get isInvertAdjustmentRasterNode() {
        return true;
    }
}


class InvertAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'InvertAdjustmentRasterNodeDefinition';
    }

    get isInvertAdjustmentRasterNodeDefinition() {
        return true;
    }

    static create() {
        return new InvertAdjustmentRasterNodeDefinition(InvertAdjustmentRasterNodeDefinitionApi.create());
    }
}


const LEVELS_ADJUSTMENT_CHANNEL_FIELDS = ['blackLevel', 'whiteLevel', 'gamma', 'outputBlackLevel', 'outputWhiteLevel'];

class LevelsAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use LevelsAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new LevelsAdjustmentParameters(). Use LevelsAdjustmentParameters.create() instead.");
            super(LevelsAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'LevelsAdjustmentParameters';
    }

    get isLevelsAdjustmentParameters() {
        return true;
    }

    set masterParameters(value) {
        LevelsAdjustmentParametersApi.setMasterParameters(this.handle, value);
    }

    // Live view: params.masterParameters = {...} and params.masterParameters.gamma = v both write through.
    get masterParameters() {
        return liveStruct(LEVELS_ADJUSTMENT_CHANNEL_FIELDS, () => LevelsAdjustmentParametersApi.getMasterParameters(this.handle), value => LevelsAdjustmentParametersApi.setMasterParameters(this.handle, value));
    }

    get channelParametersCount() {
        return LevelsAdjustmentParametersApi.getChannelParametersCount(this.handle);
    }

    setChannelParameters(channel, value) {
        LevelsAdjustmentParametersApi.setChannelParameters(this.handle, channel, value);
    }

    getChannelParameters(channel) {
        return LevelsAdjustmentParametersApi.getChannelParameters(this.handle, channel);
    }

    // The callback is invoked as callback(channel, channelParameters) and returns an EnumerationResult.
    enumerateChannelParameters(callback) {
        return LevelsAdjustmentParametersApi.enumerateChannelParameters(this.handle, callback);
    }

    // Whole-array assignment: params.channelParameters = [{...}, ...] sends every element (any array-like with channelParametersCount object elements).
    set channelParameters(values) {
        setStructArray(this.channelParametersCount, values, (channel, value) => this.setChannelParameters(channel, value), 'LevelsAdjustmentChannelParameters');
    }

    // Array-like live view: params.channelParameters[1] = {...} and params.channelParameters[1].gamma = v both write through.
    get channelParameters() {
        return liveStructArray(this.channelParametersCount, LEVELS_ADJUSTMENT_CHANNEL_FIELDS, channel => this.getChannelParameters(channel), (channel, value) => this.setChannelParameters(channel, value));
    }

    static create() {
        return new LevelsAdjustmentParameters(LevelsAdjustmentParametersApi.create());
    }
}


class LevelsAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LevelsAdjustmentRasterNode';
    }

    get isLevelsAdjustmentRasterNode() {
        return true;
    }
    
    get parameters() {
        return new LevelsAdjustmentParameters(LevelsAdjustmentRasterNodeApi.getParameters(this.handle));
    }
    
    get colourSpace() {
        return LevelsAdjustmentRasterNodeApi.getColourSpace(this.handle);
    }
}

class LevelsAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'LevelsAdjustmentRasterNodeDefinition';
    }
    
    get isLevelsAdjustmentRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        LevelsAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new LevelsAdjustmentParameters(LevelsAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    set colourSpace(csType) {
        LevelsAdjustmentRasterNodeDefinitionApi.setColourSpace(this.handle, csType);
    }

    get colourSpace() {
        return LevelsAdjustmentRasterNodeDefinitionApi.getColourSpace(this.handle);
    }

    setColourSpace(csType) {
        this.colourSpace = csType;
        return this;
    }

    static create(params, colourSpace) {
        return new LevelsAdjustmentRasterNodeDefinition(LevelsAdjustmentRasterNodeDefinitionApi.create(params.handle, colourSpace));
    }

    static createDefault(document) {
        return new LevelsAdjustmentRasterNodeDefinition(LevelsAdjustmentRasterNodeDefinitionApi.createDefault(document.handle));
    }
}


class NormalsAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use NormalsAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new NormalsAdjustmentParameters(). Use NormalsAdjustmentParameters.create() instead.");
            super(NormalsAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'NormalsAdjustmentParameters';
    }

    get isNormalsAdjustmentParameters() {
        return true;
    }

    set rotation(value) {
        NormalsAdjustmentParametersApi.setRotation(this.handle, value);
    }

    get rotation() {
        return NormalsAdjustmentParametersApi.getRotation(this.handle);
    }

    set scale(value) {
        NormalsAdjustmentParametersApi.setScale(this.handle, value);
    }

    get scale() {
        return NormalsAdjustmentParametersApi.getScale(this.handle);
    }

    set flipX(value) {
        NormalsAdjustmentParametersApi.setFlipX(this.handle, value);
    }

    get flipX() {
        return NormalsAdjustmentParametersApi.getFlipX(this.handle);
    }

    set flipY(value) {
        NormalsAdjustmentParametersApi.setFlipY(this.handle, value);
    }

    get flipY() {
        return NormalsAdjustmentParametersApi.getFlipY(this.handle);
    }

    static create() {
        return new NormalsAdjustmentParameters(NormalsAdjustmentParametersApi.create());
    }
}


class NormalsAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'NormalsAdjustmentRasterNode';
    }

    get isNormalsAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new NormalsAdjustmentParameters(NormalsAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class NormalsAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'NormalsAdjustmentRasterNodeDefinition';
    }

    get isNormalsAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        NormalsAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new NormalsAdjustmentParameters(NormalsAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new NormalsAdjustmentRasterNodeDefinition(NormalsAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new NormalsAdjustmentRasterNodeDefinition(NormalsAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class PosteriseAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use PosteriseAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new PosteriseAdjustmentParameters(). Use PosteriseAdjustmentParameters.create() instead.");
            super(PosteriseAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'PosteriseAdjustmentParameters';
    }

    get isPosteriseAdjustmentParameters() {
        return true;
    }

    set levels(value) {
        PosteriseAdjustmentParametersApi.setLevels(this.handle, value);
    }

    get levels() {
        return PosteriseAdjustmentParametersApi.getLevels(this.handle);
    }

    static create() {
        return new PosteriseAdjustmentParameters(PosteriseAdjustmentParametersApi.create());
    }
}


class PosteriseAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PosteriseAdjustmentRasterNode';
    }

    get isPosteriseAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new PosteriseAdjustmentParameters(PosteriseAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class PosteriseAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PosteriseAdjustmentRasterNodeDefinition';
    }

    get isPosteriseAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        PosteriseAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new PosteriseAdjustmentParameters(PosteriseAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new PosteriseAdjustmentRasterNodeDefinition(PosteriseAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new PosteriseAdjustmentRasterNodeDefinition(PosteriseAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class RecolourAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use RecolourAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new RecolourAdjustmentParameters(). Use RecolourAdjustmentParameters.create() instead.");
            super(RecolourAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'RecolourAdjustmentParameters';
    }

    get isRecolourAdjustmentParameters() {
        return true;
    }

    set hue(value) {
        RecolourAdjustmentParametersApi.setHue(this.handle, value);
    }

    get hue() {
        return RecolourAdjustmentParametersApi.getHue(this.handle);
    }

    set saturation(value) {
        RecolourAdjustmentParametersApi.setSaturation(this.handle, value);
    }

    get saturation() {
        return RecolourAdjustmentParametersApi.getSaturation(this.handle);
    }

    set lightness(value) {
        RecolourAdjustmentParametersApi.setLightness(this.handle, value);
    }

    get lightness() {
        return RecolourAdjustmentParametersApi.getLightness(this.handle);
    }

    static create() {
        return new RecolourAdjustmentParameters(RecolourAdjustmentParametersApi.create());
    }
}


class RecolourAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RecolourAdjustmentRasterNode';
    }

    get isRecolourAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new RecolourAdjustmentParameters(RecolourAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class RecolourAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RecolourAdjustmentRasterNodeDefinition';
    }

    get isRecolourAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        RecolourAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new RecolourAdjustmentParameters(RecolourAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new RecolourAdjustmentRasterNodeDefinition(RecolourAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new RecolourAdjustmentRasterNodeDefinition(RecolourAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


const SELECTIVE_COLOUR_ADJUSTMENT_WEIGHTS_FIELDS = ['cyanWeight', 'magentaWeight', 'yellowWeight', 'blackWeight'];

class SelectiveColourAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use SelectiveColourAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new SelectiveColourAdjustmentParameters(). Use SelectiveColourAdjustmentParameters.create() instead.");
            super(SelectiveColourAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'SelectiveColourAdjustmentParameters';
    }

    get isSelectiveColourAdjustmentParameters() {
        return true;
    }

    get weightsCount() {
        return SelectiveColourAdjustmentParametersApi.getWeightsCount(this.handle);
    }

    setWeights(colour, value) {
        SelectiveColourAdjustmentParametersApi.setWeights(this.handle, colour, value);
    }

    getWeights(colour) {
        return SelectiveColourAdjustmentParametersApi.getWeights(this.handle, colour);
    }

    // The callback is invoked as callback(colour, weights), with colour a SelectiveColour, and returns an EnumerationResult.
    enumerateWeights(callback) {
        return SelectiveColourAdjustmentParametersApi.enumerateWeights(this.handle, callback);
    }

    // Whole-array assignment: params.weights = [{...}, ...] sends every element (any array-like with weightsCount object elements).
    set weights(values) {
        setStructArray(this.weightsCount, values, (colour, value) => this.setWeights(colour, value), 'SelectiveColourWeights');
    }

    // Array-like live view indexed by SelectiveColour: params.weights[i] = {...} and params.weights[i].cyanWeight = v both write through.
    get weights() {
        return liveStructArray(this.weightsCount, SELECTIVE_COLOUR_ADJUSTMENT_WEIGHTS_FIELDS, colour => this.getWeights(colour), (colour, value) => this.setWeights(colour, value));
    }

    set isRelative(value) {
        SelectiveColourAdjustmentParametersApi.setIsRelative(this.handle, value);
    }

    get isRelative() {
        return SelectiveColourAdjustmentParametersApi.getIsRelative(this.handle);
    }

    static create() {
        return new SelectiveColourAdjustmentParameters(SelectiveColourAdjustmentParametersApi.create());
    }
}


class SelectiveColourAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SelectiveColourAdjustmentRasterNode';
    }

    get isSelectiveColourAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new SelectiveColourAdjustmentParameters(SelectiveColourAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class SelectiveColourAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SelectiveColourAdjustmentRasterNodeDefinition';
    }

    get isSelectiveColourAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        SelectiveColourAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new SelectiveColourAdjustmentParameters(SelectiveColourAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new SelectiveColourAdjustmentRasterNodeDefinition(SelectiveColourAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new SelectiveColourAdjustmentRasterNodeDefinition(SelectiveColourAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class ShadowsHighlightsAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use ShadowsHighlightsAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new ShadowsHighlightsAdjustmentParameters(). Use ShadowsHighlightsAdjustmentParameters.create() instead.");
            super(ShadowsHighlightsAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'ShadowsHighlightsAdjustmentParameters';
    }

    get isShadowsHighlightsAdjustmentParameters() {
        return true;
    }

    set shadows(value) {
        ShadowsHighlightsAdjustmentParametersApi.setShadows(this.handle, value);
    }

    get shadows() {
        return ShadowsHighlightsAdjustmentParametersApi.getShadows(this.handle);
    }

    set highlights(value) {
        ShadowsHighlightsAdjustmentParametersApi.setHighlights(this.handle, value);
    }

    get highlights() {
        return ShadowsHighlightsAdjustmentParametersApi.getHighlights(this.handle);
    }

    static create() {
        return new ShadowsHighlightsAdjustmentParameters(ShadowsHighlightsAdjustmentParametersApi.create());
    }
}


class ShadowsHighlightsAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShadowsHighlightsAdjustmentRasterNode';
    }

    get isShadowsHighlightsAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new ShadowsHighlightsAdjustmentParameters(ShadowsHighlightsAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class ShadowsHighlightsAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShadowsHighlightsAdjustmentRasterNodeDefinition';
    }

    get isShadowsHighlightsAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new ShadowsHighlightsAdjustmentParameters(ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ShadowsHighlightsAdjustmentRasterNodeDefinition(ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new ShadowsHighlightsAdjustmentRasterNodeDefinition(ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class SplitToningAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use SplitToningAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new SplitToningAdjustmentParameters(). Use SplitToningAdjustmentParameters.create() instead.");
            super(SplitToningAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'SplitToningAdjustmentParameters';
    }

    get isSplitToningAdjustmentParameters() {
        return true;
    }

    set highlightsHue(value) {
        SplitToningAdjustmentParametersApi.setHighlightsHue(this.handle, value);
    }

    get highlightsHue() {
        return SplitToningAdjustmentParametersApi.getHighlightsHue(this.handle);
    }

    set highlightsSaturation(value) {
        SplitToningAdjustmentParametersApi.setHighlightsSaturation(this.handle, value);
    }

    get highlightsSaturation() {
        return SplitToningAdjustmentParametersApi.getHighlightsSaturation(this.handle);
    }

    set shadowsHue(value) {
        SplitToningAdjustmentParametersApi.setShadowsHue(this.handle, value);
    }

    get shadowsHue() {
        return SplitToningAdjustmentParametersApi.getShadowsHue(this.handle);
    }

    set shadowsSaturation(value) {
        SplitToningAdjustmentParametersApi.setShadowsSaturation(this.handle, value);
    }

    get shadowsSaturation() {
        return SplitToningAdjustmentParametersApi.getShadowsSaturation(this.handle);
    }

    set balance(value) {
        SplitToningAdjustmentParametersApi.setBalance(this.handle, value);
    }

    get balance() {
        return SplitToningAdjustmentParametersApi.getBalance(this.handle);
    }

    static create() {
        return new SplitToningAdjustmentParameters(SplitToningAdjustmentParametersApi.create());
    }
}


class SplitToningAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SplitToningAdjustmentRasterNode';
    }

    get isSplitToningAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new SplitToningAdjustmentParameters(SplitToningAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class SplitToningAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SplitToningAdjustmentRasterNodeDefinition';
    }

    get isSplitToningAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        SplitToningAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new SplitToningAdjustmentParameters(SplitToningAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new SplitToningAdjustmentRasterNodeDefinition(SplitToningAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new SplitToningAdjustmentRasterNodeDefinition(SplitToningAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class ThresholdAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use ThresholdAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new ThresholdAdjustmentParameters(). Use ThresholdAdjustmentParameters.create() instead.");
            super(ThresholdAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'ThresholdAdjustmentParameters';
    }

    get isThresholdAdjustmentParameters() {
        return true;
    }

    set threshold(value) {
        ThresholdAdjustmentParametersApi.setThreshold(this.handle, value);
    }

    get threshold() {
        return ThresholdAdjustmentParametersApi.getThreshold(this.handle);
    }

    static create() {
        return new ThresholdAdjustmentParameters(ThresholdAdjustmentParametersApi.create());
    }
}


class ThresholdAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ThresholdAdjustmentRasterNode';
    }

    get isThresholdAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new ThresholdAdjustmentParameters(ThresholdAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class ThresholdAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ThresholdAdjustmentRasterNodeDefinition';
    }

    get isThresholdAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        ThresholdAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new ThresholdAdjustmentParameters(ThresholdAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ThresholdAdjustmentRasterNodeDefinition(ThresholdAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new ThresholdAdjustmentRasterNodeDefinition(ThresholdAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class ToneCompressionAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use ToneCompressionAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new ToneCompressionAdjustmentParameters(). Use ToneCompressionAdjustmentParameters.create() instead.");
            super(ToneCompressionAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'ToneCompressionAdjustmentParameters';
    }

    get isToneCompressionAdjustmentParameters() {
        return true;
    }

    set method(value) {
        ToneCompressionAdjustmentParametersApi.setMethod(this.handle, value);
    }

    get method() {
        return ToneCompressionAdjustmentParametersApi.getMethod(this.handle);
    }

    set exposure(value) {
        ToneCompressionAdjustmentParametersApi.setExposure(this.handle, value);
    }

    get exposure() {
        return ToneCompressionAdjustmentParametersApi.getExposure(this.handle);
    }

    set gamma(value) {
        ToneCompressionAdjustmentParametersApi.setGamma(this.handle, value);
    }

    get gamma() {
        return ToneCompressionAdjustmentParametersApi.getGamma(this.handle);
    }

    set colour(value) {
        ToneCompressionAdjustmentParametersApi.setColour(this.handle, value);
    }

    get colour() {
        return ToneCompressionAdjustmentParametersApi.getColour(this.handle);
    }

    static create() {
        return new ToneCompressionAdjustmentParameters(ToneCompressionAdjustmentParametersApi.create());
    }
}


class ToneCompressionAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ToneCompressionAdjustmentRasterNode';
    }

    get isToneCompressionAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new ToneCompressionAdjustmentParameters(ToneCompressionAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class ToneCompressionAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ToneCompressionAdjustmentRasterNodeDefinition';
    }

    get isToneCompressionAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        ToneCompressionAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new ToneCompressionAdjustmentParameters(ToneCompressionAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ToneCompressionAdjustmentRasterNodeDefinition(ToneCompressionAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new ToneCompressionAdjustmentRasterNodeDefinition(ToneCompressionAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class ToneStretchAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use ToneStretchAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new ToneStretchAdjustmentParameters(). Use ToneStretchAdjustmentParameters.create() instead.");
            super(ToneStretchAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'ToneStretchAdjustmentParameters';
    }

    get isToneStretchAdjustmentParameters() {
        return true;
    }

    set method(value) {
        ToneStretchAdjustmentParametersApi.setMethod(this.handle, value);
    }

    get method() {
        return ToneStretchAdjustmentParametersApi.getMethod(this.handle);
    }

    set gamma(value) {
        ToneStretchAdjustmentParametersApi.setGamma(this.handle, value);
    }

    get gamma() {
        return ToneStretchAdjustmentParametersApi.getGamma(this.handle);
    }

    set stretchFactor(value) {
        ToneStretchAdjustmentParametersApi.setStretchFactor(this.handle, value);
    }

    get stretchFactor() {
        return ToneStretchAdjustmentParametersApi.getStretchFactor(this.handle);
    }

    set compression(value) {
        ToneStretchAdjustmentParametersApi.setCompression(this.handle, value);
    }

    get compression() {
        return ToneStretchAdjustmentParametersApi.getCompression(this.handle);
    }

    static create() {
        return new ToneStretchAdjustmentParameters(ToneStretchAdjustmentParametersApi.create());
    }
}


class ToneStretchAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ToneStretchAdjustmentRasterNode';
    }

    get isToneStretchAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new ToneStretchAdjustmentParameters(ToneStretchAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class ToneStretchAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ToneStretchAdjustmentRasterNodeDefinition';
    }

    get isToneStretchAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        ToneStretchAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new ToneStretchAdjustmentParameters(ToneStretchAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ToneStretchAdjustmentRasterNodeDefinition(ToneStretchAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new ToneStretchAdjustmentRasterNodeDefinition(ToneStretchAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class VibranceAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use VibranceAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new VibranceAdjustmentParameters(). Use VibranceAdjustmentParameters.create() instead.");
            super(VibranceAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'VibranceAdjustmentParameters';
    }

    get isVibranceAdjustmentParameters() {
        return true;
    }

    set vibrance(value) {
        VibranceAdjustmentParametersApi.setVibrance(this.handle, value);
    }

    get vibrance() {
        return VibranceAdjustmentParametersApi.getVibrance(this.handle);
    }

    set saturation(value) {
        VibranceAdjustmentParametersApi.setSaturation(this.handle, value);
    }

    get saturation() {
        return VibranceAdjustmentParametersApi.getSaturation(this.handle);
    }

    static create() {
        return new VibranceAdjustmentParameters(VibranceAdjustmentParametersApi.create());
    }
}


class VibranceAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'VibranceAdjustmentRasterNode';
    }

    get isVibranceAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new VibranceAdjustmentParameters(VibranceAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class VibranceAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'VibranceAdjustmentRasterNodeDefinition';
    }

    get isVibranceAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        VibranceAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new VibranceAdjustmentParameters(VibranceAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new VibranceAdjustmentRasterNodeDefinition(VibranceAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new VibranceAdjustmentRasterNodeDefinition(VibranceAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class WhiteBalanceAdjustmentParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use WhiteBalanceAdjustmentParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new WhiteBalanceAdjustmentParameters(). Use WhiteBalanceAdjustmentParameters.create() instead.");
            super(WhiteBalanceAdjustmentParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'WhiteBalanceAdjustmentParameters';
    }

    get isWhiteBalanceAdjustmentParameters() {
        return true;
    }

    set whiteBalance(value) {
        WhiteBalanceAdjustmentParametersApi.setWhiteBalance(this.handle, value);
    }

    get whiteBalance() {
        return WhiteBalanceAdjustmentParametersApi.getWhiteBalance(this.handle);
    }

    set tint(value) {
        WhiteBalanceAdjustmentParametersApi.setTint(this.handle, value);
    }

    get tint() {
        return WhiteBalanceAdjustmentParametersApi.getTint(this.handle);
    }

    static create() {
        return new WhiteBalanceAdjustmentParameters(WhiteBalanceAdjustmentParametersApi.create());
    }
}


class WhiteBalanceAdjustmentRasterNode extends AdjustmentRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'WhiteBalanceAdjustmentRasterNode';
    }

    get isWhiteBalanceAdjustmentRasterNode() {
        return true;
    }

    get parameters() {
        return new WhiteBalanceAdjustmentParameters(WhiteBalanceAdjustmentRasterNodeApi.getParameters(this.handle));
    }
}


class WhiteBalanceAdjustmentRasterNodeDefinition extends AdjustmentRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'WhiteBalanceAdjustmentRasterNodeDefinition';
    }

    get isWhiteBalanceAdjustmentRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        WhiteBalanceAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new WhiteBalanceAdjustmentParameters(WhiteBalanceAdjustmentRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new WhiteBalanceAdjustmentRasterNodeDefinition(WhiteBalanceAdjustmentRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new WhiteBalanceAdjustmentRasterNodeDefinition(WhiteBalanceAdjustmentRasterNodeDefinitionApi.createDefault());
    }
}


class FilterRasterNode extends EnclosureRasterNode {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'FilterRasterNode';
    }
    
    get isFilterRasterNode() {
        return true;
    }

    get preserveAlpha() {
        return FilterRasterNodeApi.getPreserveAlpha(this.handle);
    }
}


class FilterRasterNodeDefinition extends EnclosureRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'FilterRasterNodeDefinition';
    }
    
    get isFilterRasterNodeDefinition() {
        return true;
    }

    get preserveAlpha() {
        return FilterRasterNodeDefinitionApi.getPreserveAlpha(this.handle);
    }

    set preserveAlpha(value) {
        return FilterRasterNodeDefinitionApi.setPreserveAlpha(this.handle, value);
    }

    setPreserveAlpha(value) {
        this.preserveAlpha = value;
        return this;
    }
}


class AddNoiseFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use AddNoiseFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new AddNoiseFilterParameters(). Use AddNoiseFilterParameters.create() instead.");
            super(AddNoiseFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'AddNoiseFilterParameters';
    }

    get isAddNoiseFilterParameters() {
        return true;
    }

    set intensity(value) {
        AddNoiseFilterParametersApi.setIntensity(this.handle, value);
    }

    get intensity() {
        return AddNoiseFilterParametersApi.getIntensity(this.handle);
    }

    set noiseType(value) {
        AddNoiseFilterParametersApi.setNoiseType(this.handle, value);
    }

    get noiseType() {
        return AddNoiseFilterParametersApi.getNoiseType(this.handle);
    }

    set isMonochromatic(value) {
        AddNoiseFilterParametersApi.setIsMonochromatic(this.handle, value);
    }

    get isMonochromatic() {
        return AddNoiseFilterParametersApi.getIsMonochromatic(this.handle);
    }

    static create() {
        return new AddNoiseFilterParameters(AddNoiseFilterParametersApi.create());
    }
}


class AddNoiseFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'AddNoiseFilterRasterNode';
    }

    get isAddNoiseFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new AddNoiseFilterParameters(AddNoiseFilterRasterNodeApi.getParameters(this.handle));
    }
}


class AddNoiseFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'AddNoiseFilterRasterNodeDefinition';
    }

    get isAddNoiseFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        AddNoiseFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new AddNoiseFilterParameters(AddNoiseFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new AddNoiseFilterRasterNodeDefinition(AddNoiseFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new AddNoiseFilterRasterNodeDefinition(AddNoiseFilterRasterNodeDefinitionApi.createDefault());
    }
}


class BilateralBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use BilateralBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new BilateralBlurFilterParameters(). Use BilateralBlurFilterParameters.create() instead.");
            super(BilateralBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'BilateralBlurFilterParameters';
    }

    get isBilateralBlurFilterParameters() {
        return true;
    }

    set radius(value) {
        BilateralBlurFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return BilateralBlurFilterParametersApi.getRadius(this.handle);
    }

    set tolerance(value) {
        BilateralBlurFilterParametersApi.setTolerance(this.handle, value);
    }

    get tolerance() {
        return BilateralBlurFilterParametersApi.getTolerance(this.handle);
    }

    static create() {
        return new BilateralBlurFilterParameters(BilateralBlurFilterParametersApi.create());
    }
}


class BilateralBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BilateralBlurFilterRasterNode';
    }

    get isBilateralBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new BilateralBlurFilterParameters(BilateralBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class BilateralBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'BilateralBlurFilterRasterNodeDefinition';
    }
    
    get isBilateralBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        BilateralBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new BilateralBlurFilterParameters(BilateralBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(params) {
        return new BilateralBlurFilterRasterNodeDefinition(BilateralBlurFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new BilateralBlurFilterRasterNodeDefinition(BilateralBlurFilterRasterNodeDefinitionApi.createDefault());
    }
}


class BoxBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use BoxBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new BoxBlurFilterParameters(). Use BoxBlurFilterParameters.create() instead.");
            super(BoxBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'BoxBlurFilterParameters';
    }

    get isBoxBlurFilterParameters() {
        return true;
    }

    set radius(value) {
        BoxBlurFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return BoxBlurFilterParametersApi.getRadius(this.handle);
    }

    static create() {
        return new BoxBlurFilterParameters(BoxBlurFilterParametersApi.create());
    }
}


class BoxBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BoxBlurFilterRasterNode';
    }

    get isBoxBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new BoxBlurFilterParameters(BoxBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class BoxBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'BoxBlurFilterRasterNodeDefinition';
    }
    
    get isBoxBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        BoxBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new BoxBlurFilterParameters(BoxBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(params) {
        return new BoxBlurFilterRasterNodeDefinition(BoxBlurFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new BoxBlurFilterRasterNodeDefinition(BoxBlurFilterRasterNodeDefinitionApi.createDefault());
    }
}


class ClarityFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use ClarityFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new ClarityFilterParameters(). Use ClarityFilterParameters.create() instead.");
            super(ClarityFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'ClarityFilterParameters';
    }

    get isClarityFilterParameters() {
        return true;
    }

    set strength(value) {
        ClarityFilterParametersApi.setStrength(this.handle, value);
    }

    get strength() {
        return ClarityFilterParametersApi.getStrength(this.handle);
    }

    static create() {
        return new ClarityFilterParameters(ClarityFilterParametersApi.create());
    }
}


class ClarityFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ClarityFilterRasterNode';
    }

    get isClarityFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new ClarityFilterParameters(ClarityFilterRasterNodeApi.getParameters(this.handle));
    }
}


class ClarityFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ClarityFilterRasterNodeDefinition';
    }

    get isClarityFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        ClarityFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new ClarityFilterParameters(ClarityFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ClarityFilterRasterNodeDefinition(ClarityFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new ClarityFilterRasterNodeDefinition(ClarityFilterRasterNodeDefinitionApi.createDefault());
    }
}


class DefringeFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use DefringeFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new DefringeFilterParameters(). Use DefringeFilterParameters.create() instead.");
            super(DefringeFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'DefringeFilterParameters';
    }

    get isDefringeFilterParameters() {
        return true;
    }

    set hue(value) {
        DefringeFilterParametersApi.setHue(this.handle, value);
    }

    get hue() {
        return DefringeFilterParametersApi.getHue(this.handle);
    }

    set removeComplementary(value) {
        DefringeFilterParametersApi.setRemoveComplementary(this.handle, value);
    }

    get removeComplementary() {
        return DefringeFilterParametersApi.getRemoveComplementary(this.handle);
    }

    set tolerance(value) {
        DefringeFilterParametersApi.setTolerance(this.handle, value);
    }

    get tolerance() {
        return DefringeFilterParametersApi.getTolerance(this.handle);
    }

    set radius(value) {
        DefringeFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return DefringeFilterParametersApi.getRadius(this.handle);
    }

    set edgeBrightnessThreshold(value) {
        DefringeFilterParametersApi.setEdgeBrightnessThreshold(this.handle, value);
    }

    get edgeBrightnessThreshold() {
        return DefringeFilterParametersApi.getEdgeBrightnessThreshold(this.handle);
    }

    static create() {
        return new DefringeFilterParameters(DefringeFilterParametersApi.create());
    }
}


class DefringeFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DefringeFilterRasterNode';
    }

    get isDefringeFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new DefringeFilterParameters(DefringeFilterRasterNodeApi.getParameters(this.handle));
    }
}


class DefringeFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DefringeFilterRasterNodeDefinition';
    }

    get isDefringeFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        DefringeFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new DefringeFilterParameters(DefringeFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new DefringeFilterRasterNodeDefinition(DefringeFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new DefringeFilterRasterNodeDefinition(DefringeFilterRasterNodeDefinitionApi.createDefault());
    }
}


class DenoiseFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use DenoiseFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new DenoiseFilterParameters(). Use DenoiseFilterParameters.create() instead.");
            super(DenoiseFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'DenoiseFilterParameters';
    }

    get isDenoiseFilterParameters() {
        return true;
    }

    set luminance(value) {
        DenoiseFilterParametersApi.setLuminance(this.handle, value);
    }

    get luminance() {
        return DenoiseFilterParametersApi.getLuminance(this.handle);
    }

    set luminanceDetail(value) {
        DenoiseFilterParametersApi.setLuminanceDetail(this.handle, value);
    }

    get luminanceDetail() {
        return DenoiseFilterParametersApi.getLuminanceDetail(this.handle);
    }

    set luminanceContribution(value) {
        DenoiseFilterParametersApi.setLuminanceContribution(this.handle, value);
    }

    get luminanceContribution() {
        return DenoiseFilterParametersApi.getLuminanceContribution(this.handle);
    }

    set colours(value) {
        DenoiseFilterParametersApi.setColours(this.handle, value);
    }

    get colours() {
        return DenoiseFilterParametersApi.getColours(this.handle);
    }

    set coloursContribution(value) {
        DenoiseFilterParametersApi.setColoursContribution(this.handle, value);
    }

    get coloursContribution() {
        return DenoiseFilterParametersApi.getColoursContribution(this.handle);
    }

    static create() {
        return new DenoiseFilterParameters(DenoiseFilterParametersApi.create());
    }
}


class DenoiseFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DenoiseFilterRasterNode';
    }

    get isDenoiseFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new DenoiseFilterParameters(DenoiseFilterRasterNodeApi.getParameters(this.handle));
    }
}


class DenoiseFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DenoiseFilterRasterNodeDefinition';
    }

    get isDenoiseFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        DenoiseFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new DenoiseFilterParameters(DenoiseFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new DenoiseFilterRasterNodeDefinition(DenoiseFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new DenoiseFilterRasterNodeDefinition(DenoiseFilterRasterNodeDefinitionApi.createDefault());
    }
}


class DiffuseFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use DiffuseFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new DiffuseFilterParameters(). Use DiffuseFilterParameters.create() instead.");
            super(DiffuseFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'DiffuseFilterParameters';
    }

    get isDiffuseFilterParameters() {
        return true;
    }

    set intensity(value) {
        DiffuseFilterParametersApi.setIntensity(this.handle, value);
    }

    get intensity() {
        return DiffuseFilterParametersApi.getIntensity(this.handle);
    }

    static create() {
        return new DiffuseFilterParameters(DiffuseFilterParametersApi.create());
    }
}


class DiffuseFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DiffuseFilterRasterNode';
    }

    get isDiffuseFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new DiffuseFilterParameters(DiffuseFilterRasterNodeApi.getParameters(this.handle));
    }
}


class DiffuseFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DiffuseFilterRasterNodeDefinition';
    }

    get isDiffuseFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        DiffuseFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new DiffuseFilterParameters(DiffuseFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new DiffuseFilterRasterNodeDefinition(DiffuseFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new DiffuseFilterRasterNodeDefinition(DiffuseFilterRasterNodeDefinitionApi.createDefault());
    }
}


class DiffuseGlowFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use DiffuseGlowFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new DiffuseGlowFilterParameters(). Use DiffuseGlowFilterParameters.create() instead.");
            super(DiffuseGlowFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'DiffuseGlowFilterParameters';
    }

    get isDiffuseGlowFilterParameters() {
        return true;
    }

    set radius(value) {
        DiffuseGlowFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return DiffuseGlowFilterParametersApi.getRadius(this.handle);
    }

    set intensity(value) {
        DiffuseGlowFilterParametersApi.setIntensity(this.handle, value);
    }

    get intensity() {
        return DiffuseGlowFilterParametersApi.getIntensity(this.handle);
    }

    set threshold(value) {
        DiffuseGlowFilterParametersApi.setThreshold(this.handle, value);
    }

    get threshold() {
        return DiffuseGlowFilterParametersApi.getThreshold(this.handle);
    }

    set opacity(value) {
        DiffuseGlowFilterParametersApi.setOpacity(this.handle, value);
    }

    get opacity() {
        return DiffuseGlowFilterParametersApi.getOpacity(this.handle);
    }

    static create() {
        return new DiffuseGlowFilterParameters(DiffuseGlowFilterParametersApi.create());
    }
}


class DiffuseGlowFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DiffuseGlowFilterRasterNode';
    }

    get isDiffuseGlowFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new DiffuseGlowFilterParameters(DiffuseGlowFilterRasterNodeApi.getParameters(this.handle));
    }
}


class DiffuseGlowFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'DiffuseGlowFilterRasterNodeDefinition';
    }
    
    get isDiffuseGlowFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        DiffuseGlowFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }
    
    get parameters() {
        return new DiffuseGlowFilterParameters(DiffuseGlowFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new DiffuseGlowFilterRasterNodeDefinition(DiffuseGlowFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new DiffuseGlowFilterRasterNodeDefinition(DiffuseGlowFilterRasterNodeDefinitionApi.createDefault());
    }
}


class DustAndScratchFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use DustAndScratchFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new DustAndScratchFilterParameters(). Use DustAndScratchFilterParameters.create() instead.");
            super(DustAndScratchFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'DustAndScratchFilterParameters';
    }

    get isDustAndScratchFilterParameters() {
        return true;
    }

    set radius(value) {
        DustAndScratchFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return DustAndScratchFilterParametersApi.getRadius(this.handle);
    }

    set tolerance(value) {
        DustAndScratchFilterParametersApi.setTolerance(this.handle, value);
    }

    get tolerance() {
        return DustAndScratchFilterParametersApi.getTolerance(this.handle);
    }

    set isChannelTolerance(value) {
        DustAndScratchFilterParametersApi.setIsChannelTolerance(this.handle, value);
    }

    get isChannelTolerance() {
        return DustAndScratchFilterParametersApi.getIsChannelTolerance(this.handle);
    }

    static create() {
        return new DustAndScratchFilterParameters(DustAndScratchFilterParametersApi.create());
    }
}


class DustAndScratchFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DustAndScratchFilterRasterNode';
    }

    get isDustAndScratchFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new DustAndScratchFilterParameters(DustAndScratchFilterRasterNodeApi.getParameters(this.handle));
    }
}


class DustAndScratchFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DustAndScratchFilterRasterNodeDefinition';
    }

    get isDustAndScratchFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        DustAndScratchFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new DustAndScratchFilterParameters(DustAndScratchFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new DustAndScratchFilterRasterNodeDefinition(DustAndScratchFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new DustAndScratchFilterRasterNodeDefinition(DustAndScratchFilterRasterNodeDefinitionApi.createDefault());
    }
}

class DepthOfFieldFilterParameters extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DepthOfFieldFilterParameters';
    }

    get isDepthOfFieldFilterParameters() {
        return true;
    }

    get mode() {
        return DepthOfFieldFilterParametersApi.getMode(this.handle);
    }

    get radius() {
        return DepthOfFieldFilterParametersApi.getRadius(this.handle);
    }

    set radius(value) {
        DepthOfFieldFilterParametersApi.setRadius(this.handle, value);
    }

    get vibrance() {
        return DepthOfFieldFilterParametersApi.getVibrance(this.handle);
    }

    set vibrance(value) {
        DepthOfFieldFilterParametersApi.setVibrance(this.handle, value);
    }

    get clarity() {
        return DepthOfFieldFilterParametersApi.getClarity(this.handle);
    }

    set clarity(value) {
        DepthOfFieldFilterParametersApi.setClarity(this.handle, value);
    }

    get ellipticalParams() {
        return DepthOfFieldFilterParametersApi.getEllipticalParams(this.handle);
    }

    set ellipticalParams(value) {
        DepthOfFieldFilterParametersApi.setEllipticalParams(this.handle, value);
    }

    get tiltShiftParams() {
        return DepthOfFieldFilterParametersApi.getTiltShiftParams(this.handle);
    }

    set tiltShiftParams(value) {
        DepthOfFieldFilterParametersApi.setTiltShiftParams(this.handle, value);
    }

    static create() {
        return new DepthOfFieldFilterParameters(DepthOfFieldFilterParametersApi.create());
    }
}


class DepthOfFieldFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DepthOfFieldFilterRasterNode';
    }

    get isDepthOfFieldFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new DepthOfFieldFilterParameters(DepthOfFieldFilterRasterNodeApi.getParameters(this.handle));
    }
}


class DepthOfFieldFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DepthOfFieldFilterRasterNodeDefinition';
    }

    get isDepthOfFieldFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(params) {
        DepthOfFieldFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new DepthOfFieldFilterParameters(DepthOfFieldFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new DepthOfFieldFilterRasterNodeDefinition(DepthOfFieldFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault(doc) {
        return new DepthOfFieldFilterRasterNodeDefinition(DepthOfFieldFilterRasterNodeDefinitionApi.createDefault(doc.handle));
    }
}


class FieldBlurFilterParameters extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FieldBlurFilterParameters';
    }

    get isFieldBlurFilterParameters() {
        return true;
    }
    
    get blurItemCount() {
        return FieldBlurFilterParametersApi.getBlurItemCount(this.handle);
    }
    
    getBlurItem(index) {
        return FieldBlurFilterParametersApi.getBlurItem(this.handle, index);
    }

    // The callback is invoked as callback(index, itemParameters) and returns an EnumerationResult.
    enumerateBlurItems(callback) {
        return FieldBlurFilterParametersApi.enumerateBlurItems(this.handle, callback);
    }
    
    addBlurItem(itemParams) {
        return FieldBlurFilterParametersApi.addBlurItem(this.handle, itemParams);
    }
    
    deleteBlurItem(index) {
        return FieldBlurFilterParametersApi.deleteBlurItem(this.handle, index);
    }
    
    get globalRadius() {
        return FieldBlurFilterParametersApi.getGlobalRadius(this.handle);
    }
    
    set globalRadius(radius) {
        return FieldBlurFilterParametersApi.setGlobalRadius(this.handle, radius);
    }
    
    static create() {
        return new FieldBlurFilterParameters(FieldBlurFilterParametersApi.create());
    }
}


class FieldBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FieldBlurFilterRasterNode';
    }

    get isFieldBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new FieldBlurFilterParameters(FieldBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class FieldBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'FieldBlurFilterRasterNodeDefinition';
    }
    
    get isFieldBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        FieldBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new FieldBlurFilterParameters(FieldBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(params) {
        return new FieldBlurFilterRasterNodeDefinition(FieldBlurFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault(doc) {
        return new FieldBlurFilterRasterNodeDefinition(FieldBlurFilterRasterNodeDefinitionApi.createDefault(doc.handle));
    }
}


class GaussianBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use GaussianBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new GaussianBlurFilterParameters(). Use GaussianBlurFilterParameters.create() instead.");
            super(GaussianBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'GaussianBlurFilterParameters';
    }

    get isGaussianBlurFilterParameters() {
        return true;
    }

    set radius(value) {
        GaussianBlurFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return GaussianBlurFilterParametersApi.getRadius(this.handle);
    }

    static create() {
        return new GaussianBlurFilterParameters(GaussianBlurFilterParametersApi.create());
    }
}


class GaussianBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'GaussianBlurFilterRasterNode';
    }

    get isGaussianBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new GaussianBlurFilterParameters(GaussianBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class GaussianBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'GaussianBlurFilterRasterNodeDefinition';
    }
    
    get isGaussianBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(parameters) {
        GaussianBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new GaussianBlurFilterParameters(GaussianBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(parameters) {
        return new GaussianBlurFilterRasterNodeDefinition(GaussianBlurFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new GaussianBlurFilterRasterNodeDefinition(GaussianBlurFilterRasterNodeDefinitionApi.createDefault());
    }
}


class ShadowsHighlightsFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use ShadowsHighlightsFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new ShadowsHighlightsFilterParameters(). Use ShadowsHighlightsFilterParameters.create() instead.");
            super(ShadowsHighlightsFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'ShadowsHighlightsFilterParameters';
    }

    get isShadowsHighlightsFilterParameters() {
        return true;
    }

    set version(value) {
        ShadowsHighlightsFilterParametersApi.setVersion(this.handle, value);
    }

    get version() {
        return ShadowsHighlightsFilterParametersApi.getVersion(this.handle);
    }

    set shadowsStrength(value) {
        ShadowsHighlightsFilterParametersApi.setShadowsStrength(this.handle, value);
    }

    get shadowsStrength() {
        return ShadowsHighlightsFilterParametersApi.getShadowsStrength(this.handle);
    }

    set shadowsRange(value) {
        ShadowsHighlightsFilterParametersApi.setShadowsRange(this.handle, value);
    }

    get shadowsRange() {
        return ShadowsHighlightsFilterParametersApi.getShadowsRange(this.handle);
    }

    set shadowsRadius(value) {
        ShadowsHighlightsFilterParametersApi.setShadowsRadius(this.handle, value);
    }

    get shadowsRadius() {
        return ShadowsHighlightsFilterParametersApi.getShadowsRadius(this.handle);
    }

    set highlightsStrength(value) {
        ShadowsHighlightsFilterParametersApi.setHighlightsStrength(this.handle, value);
    }

    get highlightsStrength() {
        return ShadowsHighlightsFilterParametersApi.getHighlightsStrength(this.handle);
    }

    set highlightsRange(value) {
        ShadowsHighlightsFilterParametersApi.setHighlightsRange(this.handle, value);
    }

    get highlightsRange() {
        return ShadowsHighlightsFilterParametersApi.getHighlightsRange(this.handle);
    }

    set highlightsRadius(value) {
        ShadowsHighlightsFilterParametersApi.setHighlightsRadius(this.handle, value);
    }

    get highlightsRadius() {
        return ShadowsHighlightsFilterParametersApi.getHighlightsRadius(this.handle);
    }

    static create() {
        return new ShadowsHighlightsFilterParameters(ShadowsHighlightsFilterParametersApi.create());
    }
}


class ShadowsHighlightsFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShadowsHighlightsFilterRasterNode';
    }

    get isShadowsHighlightsFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new ShadowsHighlightsFilterParameters(ShadowsHighlightsFilterRasterNodeApi.getParameters(this.handle));
    }
}


class ShadowsHighlightsFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShadowsHighlightsFilterRasterNodeDefinition';
    }
    
    get isShadowsHighlightsFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(parameters) {
        ShadowsHighlightsFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new ShadowsHighlightsFilterParameters(ShadowsHighlightsFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(parameters) {
        return new ShadowsHighlightsFilterRasterNodeDefinition(ShadowsHighlightsFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new ShadowsHighlightsFilterRasterNodeDefinition(ShadowsHighlightsFilterRasterNodeDefinitionApi.createDefault());
    }
}


class HighPassFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use HighPassFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new HighPassFilterParameters(). Use HighPassFilterParameters.create() instead.");
            super(HighPassFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'HighPassFilterParameters';
    }

    get isHighPassFilterParameters() {
        return true;
    }

    set radius(value) {
        HighPassFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return HighPassFilterParametersApi.getRadius(this.handle);
    }

    set isMonochrome(value) {
        HighPassFilterParametersApi.setIsMonochrome(this.handle, value);
    }

    get isMonochrome() {
        return HighPassFilterParametersApi.getIsMonochrome(this.handle);
    }

    static create() {
        return new HighPassFilterParameters(HighPassFilterParametersApi.create());
    }
}


class HighPassFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'HighPassFilterRasterNode';
    }

    get isHighPassFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new HighPassFilterParameters(HighPassFilterRasterNodeApi.getParameters(this.handle));
    }
}


class HighPassFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'HighPassFilterRasterNodeDefinition';
    }

    get isHighPassFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        HighPassFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new HighPassFilterParameters(HighPassFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new HighPassFilterRasterNodeDefinition(HighPassFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new HighPassFilterRasterNodeDefinition(HighPassFilterRasterNodeDefinitionApi.createDefault());
    }
}


class LensBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use LensBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new LensBlurFilterParameters(). Use LensBlurFilterParameters.create() instead.");
            super(LensBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'LensBlurFilterParameters';
    }

    get isLensBlurFilterParameters() {
        return true;
    }

    set radius(value) {
        LensBlurFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return LensBlurFilterParametersApi.getRadius(this.handle);
    }

    set numberOfBlades(value) {
        LensBlurFilterParametersApi.setNumberOfBlades(this.handle, value);
    }

    get numberOfBlades() {
        return LensBlurFilterParametersApi.getNumberOfBlades(this.handle);
    }

    set bladeCurvature(value) {
        LensBlurFilterParametersApi.setBladeCurvature(this.handle, value);
    }

    get bladeCurvature() {
        return LensBlurFilterParametersApi.getBladeCurvature(this.handle);
    }

    set bloomThreshold(value) {
        LensBlurFilterParametersApi.setBloomThreshold(this.handle, value);
    }

    get bloomThreshold() {
        return LensBlurFilterParametersApi.getBloomThreshold(this.handle);
    }

    set bloomFactor(value) {
        LensBlurFilterParametersApi.setBloomFactor(this.handle, value);
    }

    get bloomFactor() {
        return LensBlurFilterParametersApi.getBloomFactor(this.handle);
    }

    set bloomColour(value) {
        LensBlurFilterParametersApi.setBloomColour(this.handle, value);
    }

    get bloomColour() {
        return LensBlurFilterParametersApi.getBloomColour(this.handle);
    }

    static create() {
        return new LensBlurFilterParameters(LensBlurFilterParametersApi.create());
    }
}


class LensBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LensBlurFilterRasterNode';
    }

    get isLensBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new LensBlurFilterParameters(LensBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class LensBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'LensBlurFilterRasterNodeDefinition';
    }
    
    get isLensBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        LensBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new LensBlurFilterParameters(LensBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new LensBlurFilterRasterNodeDefinition(LensBlurFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new LensBlurFilterRasterNodeDefinition(LensBlurFilterRasterNodeDefinitionApi.createDefault());
    }
}


class BloomFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use BloomFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new BloomFilterParameters(). Use BloomFilterParameters.create() instead.");
            super(BloomFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'BloomFilterParameters';
    }

    get isBloomFilterParameters() {
        return true;
    }

    set shadowBlend(value) {
        BloomFilterParametersApi.setShadowBlend(this.handle, value);
    }

    get shadowBlend() {
        return BloomFilterParametersApi.getShadowBlend(this.handle);
    }

    set midtoneBlend(value) {
        BloomFilterParametersApi.setMidtoneBlend(this.handle, value);
    }

    get midtoneBlend() {
        return BloomFilterParametersApi.getMidtoneBlend(this.handle);
    }

    set highlightBlend(value) {
        BloomFilterParametersApi.setHighlightBlend(this.handle, value);
    }

    get highlightBlend() {
        return BloomFilterParametersApi.getHighlightBlend(this.handle);
    }

    set isStrong(value) {
        BloomFilterParametersApi.setIsStrong(this.handle, value);
    }

    get isStrong() {
        return BloomFilterParametersApi.getIsStrong(this.handle);
    }

    set method(value) {
        BloomFilterParametersApi.setMethod(this.handle, value);
    }

    get method() {
        return BloomFilterParametersApi.getMethod(this.handle);
    }

    set colour(value) {
        BloomFilterParametersApi.setColour(this.handle, value);
    }

    get colour() {
        return BloomFilterParametersApi.getColour(this.handle);
    }

    static create() {
        return new BloomFilterParameters(BloomFilterParametersApi.create());
    }
}


class BloomFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BloomFilterRasterNode';
    }

    get isBloomFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new BloomFilterParameters(BloomFilterRasterNodeApi.getParameters(this.handle));
    }
}


class BloomFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'BloomFilterRasterNodeDefinition';
    }
    
    get isBloomFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        BloomFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new BloomFilterParameters(BloomFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new BloomFilterRasterNodeDefinition(BloomFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new BloomFilterRasterNodeDefinition(BloomFilterRasterNodeDefinitionApi.createDefault());
    }
}


class PixelateFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use PixelateFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new PixelateFilterParameters(). Use PixelateFilterParameters.create() instead.");
            super(PixelateFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'PixelateFilterParameters';
    }

    get isPixelateFilterParameters() {
        return true;
    }

    set quantisation(value) {
        PixelateFilterParametersApi.setQuantisation(this.handle, value);
    }

    get quantisation() {
        return PixelateFilterParametersApi.getQuantisation(this.handle);
    }

    static create() {
        return new PixelateFilterParameters(PixelateFilterParametersApi.create());
    }
}


class PixelateFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PixelateFilterRasterNode';
    }

    get isPixelateFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new PixelateFilterParameters(PixelateFilterRasterNodeApi.getParameters(this.handle));
    }
}


class PixelateFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'PixelateFilterRasterNodeDefinition';
    }
    
    get isPixelateFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        PixelateFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new PixelateFilterParameters(PixelateFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(params) {
        return new PixelateFilterRasterNodeDefinition(PixelateFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new PixelateFilterRasterNodeDefinition(PixelateFilterRasterNodeDefinitionApi.createDefault());
    }
}


class HalftoneFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use HalftoneFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new HalftoneFilterParameters(). Use HalftoneFilterParameters.create() instead.");
            super(HalftoneFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'HalftoneFilterParameters';
    }

    get isHalftoneFilterParameters() {
        return true;
    }

    set cellSize(value) {
        HalftoneFilterParametersApi.setCellSize(this.handle, value);
    }

    get cellSize() {
        return HalftoneFilterParametersApi.getCellSize(this.handle);
    }

    set screenAngle(value) {
        HalftoneFilterParametersApi.setScreenAngle(this.handle, value);
    }

    get screenAngle() {
        return HalftoneFilterParametersApi.getScreenAngle(this.handle);
    }

    set contrast(value) {
        HalftoneFilterParametersApi.setContrast(this.handle, value);
    }

    get contrast() {
        return HalftoneFilterParametersApi.getContrast(this.handle);
    }

    set screenType(value) {
        HalftoneFilterParametersApi.setScreenType(this.handle, value);
    }

    get screenType() {
        return HalftoneFilterParametersApi.getScreenType(this.handle);
    }

    set dotType(value) {
        HalftoneFilterParametersApi.setDotType(this.handle, value);
    }

    get dotType() {
        return HalftoneFilterParametersApi.getDotType(this.handle);
    }

    set greyComponentReplacement(value) {
        HalftoneFilterParametersApi.setGreyComponentReplacement(this.handle, value);
    }

    get greyComponentReplacement() {
        return HalftoneFilterParametersApi.getGreyComponentReplacement(this.handle);
    }

    set underColourRemoval(value) {
        HalftoneFilterParametersApi.setUnderColourRemoval(this.handle, value);
    }

    get underColourRemoval() {
        return HalftoneFilterParametersApi.getUnderColourRemoval(this.handle);
    }

    static create() {
        return new HalftoneFilterParameters(HalftoneFilterParametersApi.create());
    }
}


class HalftoneFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'HalftoneFilterRasterNode';
    }

    get isHalftoneFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new HalftoneFilterParameters(HalftoneFilterRasterNodeApi.getParameters(this.handle));
    }
}


class HalftoneFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'HalftoneFilterRasterNodeDefinition';
    }
    
    get isHalftoneFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        HalftoneFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new HalftoneFilterParameters(HalftoneFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    static create(params) {
        return new HalftoneFilterRasterNodeDefinition(HalftoneFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new HalftoneFilterRasterNodeDefinition(HalftoneFilterRasterNodeDefinitionApi.createDefault());
    }
}


class MaximumBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use MaximumBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new MaximumBlurFilterParameters(). Use MaximumBlurFilterParameters.create() instead.");
            super(MaximumBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'MaximumBlurFilterParameters';
    }

    get isMaximumBlurFilterParameters() {
        return true;
    }

    set radius(value) {
        MaximumBlurFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return MaximumBlurFilterParametersApi.getRadius(this.handle);
    }

    set isCircular(value) {
        MaximumBlurFilterParametersApi.setIsCircular(this.handle, value);
    }

    get isCircular() {
        return MaximumBlurFilterParametersApi.getIsCircular(this.handle);
    }

    static create() {
        return new MaximumBlurFilterParameters(MaximumBlurFilterParametersApi.create());
    }
}


class MaximumBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'MaximumBlurFilterRasterNode';
    }

    get isMaximumBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new MaximumBlurFilterParameters(MaximumBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class MaximumBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'MaximumBlurFilterRasterNodeDefinition';
    }
    
    get isMaximumBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        MaximumBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }

    get parameters() {
        return new MaximumBlurFilterParameters(MaximumBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new MaximumBlurFilterRasterNodeDefinition(MaximumBlurFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new MaximumBlurFilterRasterNodeDefinition(MaximumBlurFilterRasterNodeDefinitionApi.createDefault());
    }
}


class MedianBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use MedianBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new MedianBlurFilterParameters(). Use MedianBlurFilterParameters.create() instead.");
            super(MedianBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'MedianBlurFilterParameters';
    }

    get isMedianBlurFilterParameters() {
        return true;
    }

    set radius(value) {
        MedianBlurFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return MedianBlurFilterParametersApi.getRadius(this.handle);
    }

    static create() {
        return new MedianBlurFilterParameters(MedianBlurFilterParametersApi.create());
    }
}


class MedianBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'MedianBlurFilterRasterNode';
    }

    get isMedianBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new MedianBlurFilterParameters(MedianBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class MedianBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'MedianBlurFilterRasterNodeDefinition';
    }
    
    get isMedianBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        MedianBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }
    
    get parameters() {
        return new MedianBlurFilterParameters(MedianBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new MedianBlurFilterRasterNodeDefinition(MedianBlurFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new MedianBlurFilterRasterNodeDefinition(MedianBlurFilterRasterNodeDefinitionApi.createDefault());
    }
}


class MinimumBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use MinimumBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new MinimumBlurFilterParameters(). Use MinimumBlurFilterParameters.create() instead.");
            super(MinimumBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'MinimumBlurFilterParameters';
    }

    get isMinimumBlurFilterParameters() {
        return true;
    }

    set radius(value) {
        MinimumBlurFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return MinimumBlurFilterParametersApi.getRadius(this.handle);
    }

    set isCircular(value) {
        MinimumBlurFilterParametersApi.setIsCircular(this.handle, value);
    }

    get isCircular() {
        return MinimumBlurFilterParametersApi.getIsCircular(this.handle);
    }

    static create() {
        return new MinimumBlurFilterParameters(MinimumBlurFilterParametersApi.create());
    }
}


class MinimumBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'MinimumBlurFilterRasterNode';
    }

    get isMinimumBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new MinimumBlurFilterParameters(MinimumBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class MinimumBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'MinimumBlurFilterRasterNodeDefinition';
    }
    
    get isMinimumBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        MinimumBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }
    
    get parameters() {
        return new MinimumBlurFilterParameters(MinimumBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new MinimumBlurFilterRasterNodeDefinition(MinimumBlurFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new MinimumBlurFilterRasterNodeDefinition(MinimumBlurFilterRasterNodeDefinitionApi.createDefault());
    }
}


class MotionBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use MotionBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new MotionBlurFilterParameters(). Use MotionBlurFilterParameters.create() instead.");
            super(MotionBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'MotionBlurFilterParameters';
    }

    get isMotionBlurFilterParameters() {
        return true;
    }

    set radius(value) {
        MotionBlurFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return MotionBlurFilterParametersApi.getRadius(this.handle);
    }

    set angle(value) {
        MotionBlurFilterParametersApi.setAngle(this.handle, value);
    }

    get angle() {
        return MotionBlurFilterParametersApi.getAngle(this.handle);
    }

    static create() {
        return new MotionBlurFilterParameters(MotionBlurFilterParametersApi.create());
    }
}


class MotionBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'MotionBlurFilterRasterNode';
    }

    get isMotionBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new MotionBlurFilterParameters(MotionBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class MotionBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'MotionBlurFilterRasterNodeDefinition';
    }
    
    get isMotionBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(params) {
        MotionBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params.handle);
    }
    
    get parameters() {
        return new MotionBlurFilterParameters(MotionBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new MotionBlurFilterRasterNodeDefinition(MotionBlurFilterRasterNodeDefinitionApi.create(params.handle));
    }

    static createDefault() {
        return new MotionBlurFilterRasterNodeDefinition(MotionBlurFilterRasterNodeDefinitionApi.createDefault());
    }
}


class PinchPunchFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use PinchPunchFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new PinchPunchFilterParameters(). Use PinchPunchFilterParameters.create() instead.");
            super(PinchPunchFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'PinchPunchFilterParameters';
    }

    get isPinchPunchFilterParameters() {
        return true;
    }

    set intensity(value) {
        PinchPunchFilterParametersApi.setIntensity(this.handle, value);
    }

    get intensity() {
        return PinchPunchFilterParametersApi.getIntensity(this.handle);
    }

    set radius(value) {
        PinchPunchFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return PinchPunchFilterParametersApi.getRadius(this.handle);
    }

    set position(value) {
        PinchPunchFilterParametersApi.setPosition(this.handle, value);
    }

    get position() {
        return livePoint(() => PinchPunchFilterParametersApi.getPosition(this.handle), value => PinchPunchFilterParametersApi.setPosition(this.handle, value));
    }

    static create() {
        return new PinchPunchFilterParameters(PinchPunchFilterParametersApi.create());
    }
}


class PinchPunchFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PinchPunchFilterRasterNode';
    }

    get isPinchPunchFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new PinchPunchFilterParameters(PinchPunchFilterRasterNodeApi.getParameters(this.handle));
    }
}


class PinchPunchFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PinchPunchFilterRasterNodeDefinition';
    }

    get isPinchPunchFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        PinchPunchFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new PinchPunchFilterParameters(PinchPunchFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new PinchPunchFilterRasterNodeDefinition(PinchPunchFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault(document) {
        return new PinchPunchFilterRasterNodeDefinition(PinchPunchFilterRasterNodeDefinitionApi.createDefault(document.handle));
    }
}


class RadialBlurFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use RadialBlurFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new RadialBlurFilterParameters(). Use RadialBlurFilterParameters.create() instead.");
            super(RadialBlurFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'RadialBlurFilterParameters';
    }

    get isRadialBlurFilterParameters() {
        return true;
    }

    set angle(value) {
        RadialBlurFilterParametersApi.setAngle(this.handle, value);
    }

    get angle() {
        return RadialBlurFilterParametersApi.getAngle(this.handle);
    }

    set position(value) {
        RadialBlurFilterParametersApi.setPosition(this.handle, value);
    }

    get position() {
        return livePoint(() => RadialBlurFilterParametersApi.getPosition(this.handle), value => RadialBlurFilterParametersApi.setPosition(this.handle, value));
    }

    static create() {
        return new RadialBlurFilterParameters(RadialBlurFilterParametersApi.create());
    }
}


class RadialBlurFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RadialBlurFilterRasterNode';
    }

    get isRadialBlurFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new RadialBlurFilterParameters(RadialBlurFilterRasterNodeApi.getParameters(this.handle));
    }
}


class RadialBlurFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'RadialBlurFilterRasterNodeDefinition';
    }
    
    get isRadialBlurFilterRasterNodeDefinition() {
        return true;
    }
    
    set parameters(parameters) {
        RadialBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }
    
    get parameters() {
        return new RadialBlurFilterParameters(RadialBlurFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new RadialBlurFilterRasterNodeDefinition(RadialBlurFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault(document) {
        return new RadialBlurFilterRasterNodeDefinition(RadialBlurFilterRasterNodeDefinitionApi.createDefault(document.handle));
    }
}


class RippleFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use RippleFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new RippleFilterParameters(). Use RippleFilterParameters.create() instead.");
            super(RippleFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'RippleFilterParameters';
    }

    get isRippleFilterParameters() {
        return true;
    }

    set intensity(value) {
        RippleFilterParametersApi.setIntensity(this.handle, value);
    }

    get intensity() {
        return RippleFilterParametersApi.getIntensity(this.handle);
    }

    set position(value) {
        RippleFilterParametersApi.setPosition(this.handle, value);
    }

    get position() {
        return livePoint(() => RippleFilterParametersApi.getPosition(this.handle), value => RippleFilterParametersApi.setPosition(this.handle, value));
    }

    static create() {
        return new RippleFilterParameters(RippleFilterParametersApi.create());
    }
}


class RippleFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RippleFilterRasterNode';
    }

    get isRippleFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new RippleFilterParameters(RippleFilterRasterNodeApi.getParameters(this.handle));
    }
}


class RippleFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'RippleFilterRasterNodeDefinition';
    }

    get isRippleFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        RippleFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new RippleFilterParameters(RippleFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new RippleFilterRasterNodeDefinition(RippleFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault(document) {
        return new RippleFilterRasterNodeDefinition(RippleFilterRasterNodeDefinitionApi.createDefault(document.handle));
    }
}


class SphericalFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use SphericalFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new SphericalFilterParameters(). Use SphericalFilterParameters.create() instead.");
            super(SphericalFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'SphericalFilterParameters';
    }

    get isSphericalFilterParameters() {
        return true;
    }

    set intensity(value) {
        SphericalFilterParametersApi.setIntensity(this.handle, value);
    }

    get intensity() {
        return SphericalFilterParametersApi.getIntensity(this.handle);
    }

    set radius(value) {
        SphericalFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return SphericalFilterParametersApi.getRadius(this.handle);
    }

    set position(value) {
        SphericalFilterParametersApi.setPosition(this.handle, value);
    }

    get position() {
        return livePoint(() => SphericalFilterParametersApi.getPosition(this.handle), value => SphericalFilterParametersApi.setPosition(this.handle, value));
    }

    static create() {
        return new SphericalFilterParameters(SphericalFilterParametersApi.create());
    }
}


class SphericalFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SphericalFilterRasterNode';
    }

    get isSphericalFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new SphericalFilterParameters(SphericalFilterRasterNodeApi.getParameters(this.handle));
    }
}


class SphericalFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SphericalFilterRasterNodeDefinition';
    }

    get isSphericalFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        SphericalFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new SphericalFilterParameters(SphericalFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new SphericalFilterRasterNodeDefinition(SphericalFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault(document) {
        return new SphericalFilterRasterNodeDefinition(SphericalFilterRasterNodeDefinitionApi.createDefault(document.handle));
    }
}


class TwirlFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use TwirlFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new TwirlFilterParameters(). Use TwirlFilterParameters.create() instead.");
            super(TwirlFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'TwirlFilterParameters';
    }

    get isTwirlFilterParameters() {
        return true;
    }

    set angle(value) {
        TwirlFilterParametersApi.setAngle(this.handle, value);
    }

    get angle() {
        return TwirlFilterParametersApi.getAngle(this.handle);
    }

    set radius(value) {
        TwirlFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return TwirlFilterParametersApi.getRadius(this.handle);
    }

    set position(value) {
        TwirlFilterParametersApi.setPosition(this.handle, value);
    }

    get position() {
        return livePoint(() => TwirlFilterParametersApi.getPosition(this.handle), value => TwirlFilterParametersApi.setPosition(this.handle, value));
    }

    static create() {
        return new TwirlFilterParameters(TwirlFilterParametersApi.create());
    }
}


class TwirlFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TwirlFilterRasterNode';
    }

    get isTwirlFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new TwirlFilterParameters(TwirlFilterRasterNodeApi.getParameters(this.handle));
    }
}


class TwirlFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TwirlFilterRasterNodeDefinition';
    }

    get isTwirlFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        TwirlFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new TwirlFilterParameters(TwirlFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new TwirlFilterRasterNodeDefinition(TwirlFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault(document) {
        return new TwirlFilterRasterNodeDefinition(TwirlFilterRasterNodeDefinitionApi.createDefault(document.handle));
    }
}


class UnsharpMaskFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use UnsharpMaskFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new UnsharpMaskFilterParameters(). Use UnsharpMaskFilterParameters.create() instead.");
            super(UnsharpMaskFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'UnsharpMaskFilterParameters';
    }

    get isUnsharpMaskFilterParameters() {
        return true;
    }

    set radius(value) {
        UnsharpMaskFilterParametersApi.setRadius(this.handle, value);
    }

    get radius() {
        return UnsharpMaskFilterParametersApi.getRadius(this.handle);
    }

    set threshold(value) {
        UnsharpMaskFilterParametersApi.setThreshold(this.handle, value);
    }

    get threshold() {
        return UnsharpMaskFilterParametersApi.getThreshold(this.handle);
    }

    set factor(value) {
        UnsharpMaskFilterParametersApi.setFactor(this.handle, value);
    }

    get factor() {
        return UnsharpMaskFilterParametersApi.getFactor(this.handle);
    }

    static create() {
        return new UnsharpMaskFilterParameters(UnsharpMaskFilterParametersApi.create());
    }
}


class UnsharpMaskFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'UnsharpMaskFilterRasterNode';
    }

    get isUnsharpMaskFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new UnsharpMaskFilterParameters(UnsharpMaskFilterRasterNodeApi.getParameters(this.handle));
    }
}


class UnsharpMaskFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'UnsharpMaskFilterRasterNodeDefinition';
    }

    get isUnsharpMaskFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        UnsharpMaskFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new UnsharpMaskFilterParameters(UnsharpMaskFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new UnsharpMaskFilterRasterNodeDefinition(UnsharpMaskFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new UnsharpMaskFilterRasterNodeDefinition(UnsharpMaskFilterRasterNodeDefinitionApi.createDefault());
    }
}


class VignetteFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use VignetteFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new VignetteFilterParameters(). Use VignetteFilterParameters.create() instead.");
            super(VignetteFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'VignetteFilterParameters';
    }

    get isVignetteFilterParameters() {
        return true;
    }

    set exposure(value) {
        VignetteFilterParametersApi.setExposure(this.handle, value);
    }

    get exposure() {
        return VignetteFilterParametersApi.getExposure(this.handle);
    }

    set hardness(value) {
        VignetteFilterParametersApi.setHardness(this.handle, value);
    }

    get hardness() {
        return VignetteFilterParametersApi.getHardness(this.handle);
    }

    set scale(value) {
        VignetteFilterParametersApi.setScale(this.handle, value);
    }

    get scale() {
        return VignetteFilterParametersApi.getScale(this.handle);
    }

    set shape(value) {
        VignetteFilterParametersApi.setShape(this.handle, value);
    }

    get shape() {
        return VignetteFilterParametersApi.getShape(this.handle);
    }

    static create() {
        return new VignetteFilterParameters(VignetteFilterParametersApi.create());
    }
}


class VignetteFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'VignetteFilterRasterNode';
    }

    get isVignetteFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new VignetteFilterParameters(VignetteFilterRasterNodeApi.getParameters(this.handle));
    }
}


class VignetteFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'VignetteFilterRasterNodeDefinition';
    }

    get isVignetteFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        VignetteFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new VignetteFilterParameters(VignetteFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new VignetteFilterRasterNodeDefinition(VignetteFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new VignetteFilterRasterNodeDefinition(VignetteFilterRasterNodeDefinitionApi.createDefault());
    }
}


class VoronoiFilterParameters extends HandleObject {
    // Takes an existing handle. Calling with no arguments still works but is deprecated;
    // use VoronoiFilterParameters.create() instead.
    constructor(...args) {
        if (args.length === 1 && typeof args[0] === 'object' && args[0] !== null) {
            super(args[0]);
        }
        else {
            console.warn("Using deprecated new VoronoiFilterParameters(). Use VoronoiFilterParameters.create() instead.");
            super(VoronoiFilterParametersApi.create());
        }
    }

    get [Symbol.toStringTag]() {
        return 'VoronoiFilterParameters';
    }

    get isVoronoiFilterParameters() {
        return true;
    }

    set cellSize(value) {
        VoronoiFilterParametersApi.setCellSize(this.handle, value);
    }

    get cellSize() {
        return VoronoiFilterParametersApi.getCellSize(this.handle);
    }

    set lineWidth(value) {
        VoronoiFilterParametersApi.setLineWidth(this.handle, value);
    }

    get lineWidth() {
        return VoronoiFilterParametersApi.getLineWidth(this.handle);
    }

    static create() {
        return new VoronoiFilterParameters(VoronoiFilterParametersApi.create());
    }
}


class VoronoiFilterRasterNode extends FilterRasterNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'VoronoiFilterRasterNode';
    }

    get isVoronoiFilterRasterNode() {
        return true;
    }

    get parameters() {
        return new VoronoiFilterParameters(VoronoiFilterRasterNodeApi.getParameters(this.handle));
    }
}


class VoronoiFilterRasterNodeDefinition extends FilterRasterNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'VoronoiFilterRasterNodeDefinition';
    }

    get isVoronoiFilterRasterNodeDefinition() {
        return true;
    }

    set parameters(parameters) {
        VoronoiFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters.handle);
    }

    get parameters() {
        return new VoronoiFilterParameters(VoronoiFilterRasterNodeDefinitionApi.getParameters(this.handle));
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new VoronoiFilterRasterNodeDefinition(VoronoiFilterRasterNodeDefinitionApi.create(parameters.handle));
    }

    static createDefault() {
        return new VoronoiFilterRasterNodeDefinition(VoronoiFilterRasterNodeDefinitionApi.createDefault());
    }
}


class SpreadNode extends PhysicalNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'SpreadNode';
    }

    get isSpreadNode() {
        return true;
    }

    get layers() {
        return new NodeChildren(this.handle, NodeChildType.Main, false);
    }

    getSpreadExtents(options) {
        const includeSpread = options?.includeSpread === undefined ? true : Boolean(options.includeSpread);
        const includeBleed = options?.includeBleed === undefined ? false : Boolean(options.includeBleed);
        const includeChildren = options?.includeChildren === undefined ? false : Boolean(options.includeChildren);
        return SpreadNodeApi.getSpreadExtents(this.handle, includeSpread, includeBleed, includeChildren);
    }

    #physicalRootInterface;
    get physicalRootInterface() {
        if (!this.#physicalRootInterface)
            this.#physicalRootInterface = new PhysicalRootInterfaceModule.PhysicalRootInterface(SpreadNodeApi.getPhysicalRootInterface(this.handle));
        return this.#physicalRootInterface;
    }
    
    #physicalRootPropertiesInterface;
    get physicalRootPropertiesInterface() {
        if (!this.#physicalRootPropertiesInterface)
            this.#physicalRootPropertiesInterface = new PhysicalRootPropertiesInterfaceModule.PhysicalRootPropertiesInterface(SpreadNodeApi.getPhysicalRootPropertiesInterface(this.handle));
        return this.#physicalRootPropertiesInterface;
    }
    
    get physicalRootProperties() {
        return this.physicalRootInterface.physicalRootProperties;
    }
    
    get pageCount() {
        return this.physicalRootProperties.pageCount;
    }
    
    get artboardCount() {
        return SpreadNodeApi.getArtboardCount(this.handle);
    }
    
    getArtboard(index) {
        return new ArtboardInterfaceModule.ArtboardInterface(SpreadNodeApi.getArtboard(this.handle, index));
    }
    
    enumerateArtboards(callback) {
        if (typeof callback === 'function') {
            function wrapped(artboardInterfaceHandle) {
                return callback(new ArtboardInterfaceModule.ArtboardInterface(artboardInterfaceHandle));
            }
            return SpreadNodeApi.enumerateArtboards(this.handle, wrapped);
        }
        return SpreadNodeApi.enumerateArtboards(this.handle, callback);
    }
    
    get artboards() {
        let artboardInterfaces = [];
        this.enumerateArtboards(artboardInterface => {
            artboardInterfaces.push(artboardInterface);
            return EnumerationResult.Continue;
        });
        return artboardInterfaces;
    }

    get firstPageIndex() {
        return SpreadNodeApi.getFirstPageIndex(this.handle);
    }

    get lastPageIndex() {
        return SpreadNodeApi.getLastPageIndex(this.handle);
    }

    get isFirstPage() {
        return SpreadNodeApi.isFirstPage(this.handle);
    }

    getPageIndexOfPoint(pt, relativeToSpread) {
        return SpreadNodeApi.getPageIndexOfPoint(this.handle, pt, relativeToSpread);
    }

    getPageIndexOfBox(box, relativeToSpread) {
        return SpreadNodeApi.getPageIndexOfBox(this.handle, box, relativeToSpread);
    }
}

class TextNode extends PhysicalNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TextNode';
    }

    get isTextNode() {
        return true;
    }

    // ArtboardInterfaceModule.ArtboardInterface
    #artboardInterface;
    get artboardInterface() {
        if (!this.#artboardInterface)
            this.#artboardInterface = new ArtboardInterfaceModule.ArtboardInterface(TextNodeApi.getArtboardInterface(this.handle));
        return this.#artboardInterface;
    }

    /**
    * @deprecated Use get isArtboardEnabled()
    */
    get artboardEnabled() {
        console.warn("Using deprecated get artboardEnabled() property. Use get isArtboardEnabled() instead.");
        return this.isArtboardEnabled;
    }

    get isArtboardEnabled() {
        return this.artboardInterface.isArtboardEnabled;
    }

    get artboardDescription() {
        return this.artboardInterface.description;
    }

    get artboardBaseBox() {
        return this.artboardInterface.baseBox;
    }

    get artboardSpreadBaseBox() {
        return this.artboardInterface.spreadBaseBox;
    }

    get artboardOrigin() {
        return this.artboardInterface.origin;
    }

    /**
    * @deprecated Use set isArtboardEnabled()
    */
    set artboardEnabled(value) {
        console.warn("Using deprecated set artboardEnabled() property. Use set isArtboardEnabled() instead.");
        this.isArtboardEnabled = value;
    }

    set isArtboardEnabled(value) {
        this.document.setArtboardEnabled(value, this);
    }

    // BrushFillInterfaceModule.BrushFillInterface
    #brushFillInterface;
    get brushFillInterface() {
        if (!this.#brushFillInterface)
            this.#brushFillInterface = new BrushFillInterfaceModule.BrushFillInterface(TextNodeApi.getBrushFillInterface(this.handle));
        return this.#brushFillInterface;
    }

    getBrushFillDescriptor(index, obeyScaleWithObject = true) {
        return this.brushFillInterface.getDescriptor(index, obeyScaleWithObject);
    }

    setBrushFillDescriptor(fillDescriptorOrColour, options, preview) {
        return this.brushFillInterface.setCurrentDescriptor(fillDescriptorOrColour, options, preview);
    }

    get brushFillDescriptor() {
        return this.brushFillInterface.currentDescriptor;
    }

    set brushFillDescriptor(fillDescriptorOrColour) {
        return this.brushFillInterface.currentDescriptor = fillDescriptorOrColour;
    }

    get hasBrushFill() {
        return !this.brushFillInterface.isNoFill;
    }

    // CompoundOperationInterfaceModule.CompoundOperationInterface
    #compoundOperationInterface;
    get compoundOperationInterface() {
        if (!this.#compoundOperationInterface)
            this.#compoundOperationInterface = new CompoundOperationInterfaceModule.CompoundOperationInterface(TextNodeApi.getCompoundOperationInterface(this.handle));
        return this.#compoundOperationInterface;
    }

    get compoundOperation() {
        return this.compoundOperationInterface.compoundOperation;
    }

    // CurvesInterfaceModule.CurvesInterface
    #curvesInterface;
    get curvesInterface() {
        if (!this.#curvesInterface)
            this.#curvesInterface = new CurvesInterfaceModule.CurvesInterface(TextNodeApi.getCurvesInterface(this.handle));
        return this.#curvesInterface;
    }

    get polyCurve() {
        return this.curvesInterface.polyCurve;
    }

    // LineStyleInterfaceModule.LineStyleInterface
    #lineStyleInterface;
    get lineStyleInterface() {
        if (!this.#lineStyleInterface)
            this.#lineStyleInterface = new LineStyleInterfaceModule.LineStyleInterface(TextNodeApi.getLineStyleInterface(this.handle));
        return this.#lineStyleInterface;
    }

    get lineStyleDescriptor() {
        return this.lineStyleInterface.lineStyleDescriptor;
    }

    get lineStyleDescriptors() {
        return this.lineStyleInterface.lineStyleDescriptors;
    }

    set lineStyleDescriptor(descriptor) {
        this.lineStyleInterface.lineStyleDescriptor = descriptor;
    }

    get lineStyle() {
        return this.lineStyleInterface.lineStyle;
    }

    set lineStyle(lineStyle) {
        this.lineStyleInterface.lineStyle = lineStyle;
    }

    get penFillDescriptor() {
        return this.lineStyleInterface.penFillDescriptor;
    }

    set penFillDescriptor(fillDescriptorOrColour) {
        this.lineStyleInterface.penFillDescriptor = fillDescriptorOrColour;
    }

    get penFillDescriptors() {
        return this.lineStyleInterface.penFillDescriptors;
    }

    get penFill() {
        return this.penFillDescriptor.fill;
    }

    get hasPenFill() {
        return !this.penFill.isNoFill;
    }

    get isLineStyleVisible() {
        return this.lineStyleDescriptor.isLineStyleVisible;
    }

    get lineWeight() {
        return this.lineStyleInterface.lineWeight;
    }

    set lineWeight(pixels) {
        this.lineStyleInterface.lineWeight = pixels
    }

    get lineWeightPts() {
        return this.lineStyleInterface.lineWeightPts;
    }

    set lineWeightPts(pts) {
        this.lineStyleInterface.lineWeightPts = pts;
    }

    get lineType() {
        return this.lineStyleInterface.lineType;
    }

    set lineType(type) {
        this.lineStyleInterface.lineType = type;
    }

    get lineCap() {
        return this.lineStyleInterface.lineCap;
    }

    set lineCap(cap) {
        this.lineStyleInterface.lineCap = cap;
    }

    get lineJoin() {
        return this.lineStyleInterface.lineJoin;
    }

    set lineJoin(join) {
        this.lineStyleInterface.lineJoin = join;
    }

    get dashPhase() {
        return this.lineStyleInterface.dashPhase;
    }

    set dashPhase(dashPhase) {
        this.lineStyleInterface.dashPhase = dashPhase;
    }

    get dashPattern() {
        return this.lineStyleInterface.dashPattern;
    }

    set dashPattern(dashPattern) {
        return this.lineStyleInterface.dashPattern = dashPattern;
    }

    get hasBalancedDashes() {
        return this.lineStyleInterface.hasBalancedDashes;
    }

    set hasBalancedDashes(balanced) {
        this.lineStyleInterface.hasBalancedDashes = balanced;
    }

    get strokeAlignment() {
        return this.lineStyleDescriptor.strokeAlignment;
    }

    set strokeAlignment(alignment) {
        this.lineStyleDescriptor.strokeAlignment = alignment
    }
     

    // StoryInterface
    get storyInterface() {
        return new StoryInterfaceModule.StoryInterface(TextNodeApi.getStoryInterface(this.handle));
    }

    getText(startPos = 0, maxLength = -1, format = StoryIoFormat.ClipboardDescriptions) {
        return this.storyInterface.getText(startPos, maxLength, format);
    }

    get text() {
        return this.getText();
    }
    
    get story() {
        return this.storyInterface.story;
    }

    get storyRange() {
        return this.storyInterface.storyRange;
    }
    
    setText(str) {
        const selection = this.selfSelection;
        const subSel = SelectionsModule.TextSelection.create(this.storyRange);
        selection.addSubSelectionForNode(this, subSel);
        const cmd = CommandsModule.DocumentCommand.createSetText(selection, str);
        this.document.executeCommand(cmd);
    }

    // TextFrameInterfaceModule.TextFrameInterface
    #textFrameInterface;
    get textFrameInterface() {
        if (!this.#textFrameInterface) {
            this.#textFrameInterface = new TextFrameInterfaceModule.TextFrameInterface(TextNodeApi.getTextFrameInterface(this.handle));
        }
        return this.#textFrameInterface;
    }

    // TransparencyInterfaceModule.TransparencyInterface
    #transparencyInterface;
    get transparencyInterface() {
        if (!this.#transparencyInterface) {
            this.#transparencyInterface = new TransparencyInterfaceModule.TransparencyInterface(TextNodeApi.getTransparencyInterface(this.handle));
        }
        return this.#transparencyInterface;
    }

    get transparencyFillDescriptor() {
        return this.transparencyInterface.fillDescriptor;
    }

    get transparencyFill() {
        return this.transparencyFillDescriptor.fill;
    }
}


class TextNodeDefinition extends PhysicalNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TextNodeDefinition';
    }

    get isTextNodeDefinition() {
        return true;
    }
};


class ArtTextNode extends TextNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ArtTextNode';
    }

    get isArtTextNode() {
        return true;
    }
}


class ArtTextNodeDefinition extends TextNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ArtTextNodeDefinition';
    }

    get isArtTextNodeDefinition() {
        return true;
    }

    static createFromStoryBuilder(position, storyBuilder) {
        return new ArtTextNodeDefinition(ArtTextNodeDefinitionApi.createFromStoryBuilder(position, storyBuilder.handle));
    }
}


class FrameTextNode extends TextNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FrameTextNode';
    }

    get isFrameTextNode() {
        return true;
    }
}


class FrameTextNodeDefinition extends TextNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'FrameTextNodeDefinition';
    }

    get isFrameTextNodeDefinition() {
        return true;
    }

    static createFromStoryBuilder(frameBox, storyBuilder) {
        return new FrameTextNodeDefinition(FrameTextNodeDefinitionApi.createFromStoryBuilder(frameBox, storyBuilder.handle));
    }
}


class CurvePathTextNode extends TextNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CurvePathTextNode';
    }

    get isCurvePathTextNode() {
        return true;
    }
}


class CurvePathTextNodeDefinition extends TextNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CurvePathTextNodeDefinition';
    }

    get isCurvePathTextNodeDefinition() {
        return true;
    }

    static createFromStoryBuilder(polyCurve, storyBuilder) {
        return new CurvePathTextNodeDefinition(CurvePathTextNodeDefinitionApi.createFromStoryBuilder(polyCurve.handle, storyBuilder.handle));
    }
}


class PolyCurveTextNode extends TextNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PolyCurveTextNode';
    }

    get isPolyCurveTextNode() {
        return true;
    }
}


class PolyCurveTextNodeDefinition extends TextNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PolyCurveTextNodeDefinition';
    }

    get isPolyCurveTextNodeDefinition() {
        return true;
    }

    static createFromStoryBuilder(polyCurve, storyBuilder) {
        return new PolyCurveTextNodeDefinition(PolyCurveTextNodeDefinitionApi.createFromStoryBuilder(polyCurve.handle, storyBuilder.handle));
    }
}


class ShapePathTextNode extends TextNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapePathTextNode';
    }

    get isShapePathTextNode() {
        return true;
    }

    // ShapeInterfaceModule.ShapeInterface
    #shapeInterface;
    get shapeInterface() {
        if (!this.#shapeInterface)
            this.#shapeInterface = new ShapeInterfaceModule.ShapeInterface(ShapePathTextNodeApi.getShapeInterface(this.handle));
        return this.#shapeInterface;
    }

    get shape() {
        return this.shapeInterface.shape;
    }

    get shapeType() {
        return this.shapeInterface.type;
    }

    get shapeBoundingBox() {
        return this.shapeInterface.boundingBox;
    }
}


class ShapePathTextNodeDefinition extends TextNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapePathTextNodeDefinition';
    }

    get isShapePathTextNodeDefinition() {
        return true;
    }

    static createFromStoryBuilder(shape, rectangle, storyBuilder) {
        return new ShapePathTextNodeDefinition(ShapePathTextNodeDefinitionApi.createFromStoryBuilder(shape.handle, rectangle, storyBuilder.handle));
    }
}


class TableTextNode extends TextNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TableTextNode';
    }

    get isTableTextNode() {
        return true;
    }
}


class TableTextNodeDefinition extends TextNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TableTextNodeDefinition';
    }

    get isTableTextNodeDefinition() {
        return true;
    }

    static create(box, size) {
        return new TableTextNodeDefinition(TableTextNodeDefinitionApi.create(box, size));
    }
}


class ShapeTextNode extends TextNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeTextNode';
    }

    get isShapeTextNode() {
        return true;
    }

    // ShapeInterfaceModule.ShapeInterface
    #shapeInterface;
    get shapeInterface() {
        if (!this.#shapeInterface)
            this.#shapeInterface = new ShapeInterfaceModule.ShapeInterface(ShapeTextNodeApi.getShapeInterface(this.handle));
        return this.#shapeInterface;
    }

    get shape() {
        return this.shapeInterface.shape;
    }

    get shapeType() {
        return this.shapeInterface.type;
    }

    get shapeBoundingBox() {
        return this.shapeInterface.boundingBox;
    }
}


class ShapeTextNodeDefinition extends TextNodeDefinition {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeTextNodeDefinition';
    }

    get isShapeTextNodeDefinition() {
        return true;
    }

    static createFromStoryBuilder(shape, rectangle, storyBuilder) {
        return new ShapeTextNodeDefinition(ShapeTextNodeDefinitionApi.createFromStoryBuilder(shape.handle, rectangle, storyBuilder.handle));
    }
}


class VectorNode extends PhysicalNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'VectorNode';
    }

    get isVectorNode() {
        return true;
    }

    get canBeExpressedAsVectorClip() {
        return VectorNodeApi.canBeExpressedAsVectorClip(this.handle);
    }

    // BrushFillInterfaceModule.BrushFillInterface
    #brushFillInterface;
    get brushFillInterface() {
        if (!this.#brushFillInterface)
            this.#brushFillInterface = new BrushFillInterfaceModule.BrushFillInterface(VectorNodeApi.getBrushFillInterface(this.handle));
        return this.#brushFillInterface;
    }

    getBrushFillDescriptor(index, obeyScaleWithObject = true) {
        return this.brushFillInterface.getDescriptor(index, obeyScaleWithObject);
    }

    setBrushFillDescriptor(fillDescriptorOrColour, options, preview) {
        return this.brushFillInterface.setCurrentDescriptor(fillDescriptorOrColour, options, preview);
    }

    get brushFillDescriptor() {
        return this.brushFillInterface.currentDescriptor;
    }

    set brushFillDescriptor(fillDescriptorOrColour) {
        return this.brushFillInterface.currentDescriptor = fillDescriptorOrColour;
    }

    get hasBrushFill() {
        return !this.brushFillInterface.isNoFill;
    }

    // CompoundOperationInterfaceModule.CompoundOperationInterface
    #compoundOperationInterface;
    get compoundOperationInterface() {
        if (!this.#compoundOperationInterface)
            this.#compoundOperationInterface = new CompoundOperationInterfaceModule.CompoundOperationInterface(VectorNodeApi.getCompoundOperationInterface(this.handle));
        return this.#compoundOperationInterface;
    }

    get compoundOperation() {
        return this.compoundOperationInterface.compoundOperation;
    }
    
    // CurvesInterfaceModule.CurvesInterface
    #curvesInterface;
    get curvesInterface() {
        if (!this.#curvesInterface)
            this.#curvesInterface = new CurvesInterfaceModule.CurvesInterface(VectorNodeApi.getCurvesInterface(this.handle));
        return this.#curvesInterface;
    }

    get polyCurve() {
        return this.curvesInterface.polyCurve;
    }

    // LineStyleInterfaceModule.LineStyleInterface
    #lineStyleInterface;
    get lineStyleInterface() {
        if (!this.#lineStyleInterface)
            this.#lineStyleInterface = new LineStyleInterfaceModule.LineStyleInterface(VectorNodeApi.getLineStyleInterface(this.handle));
        return this.#lineStyleInterface;
    }

    get lineStyleDescriptor() {
        return this.lineStyleInterface.lineStyleDescriptor;
    }

    get lineStyleDescriptors() {
        return this.lineStyleInterface.lineStyleDescriptors;
    }

    set lineStyleDescriptor(descriptor) {
        this.lineStyleInterface.lineStyleDescriptor = descriptor;
    }

    get lineStyle() {
        return this.lineStyleInterface.lineStyle;
    }

    set lineStyle(lineStyle) {
        this.lineStyleInterface.lineStyle = lineStyle;
    }

    get penFillDescriptor() {
        return this.lineStyleInterface.penFillDescriptor;
    }

    set penFillDescriptor(fillDescriptorOrColour) {
        this.lineStyleInterface.penFillDescriptor = fillDescriptorOrColour;
    }

    get penFillDescriptors() {
        return this.lineStyleInterface.penFillDescriptors;
    }

    get penFill() {
        return this.penFillDescriptor.fill;
    }

    get hasPenFill() {
        return !this.penFill.isNoFill;
    }

    get isLineStyleVisible() {
        return this.lineStyleDescriptor.isLineStyleVisible;
    }

    get lineWeight() {
        return this.lineStyleInterface.lineWeight;
    }

    set lineWeight(pixels) {
        this.lineStyleInterface.lineWeight = pixels
    }

    get lineWeightPts() {
        return this.lineStyleInterface.lineWeightPts;
    }

    set lineWeightPts(pts) {
        this.lineStyleInterface.lineWeightPts = pts;
    }

    get lineType() {
        return this.lineStyleInterface.lineType;
    }

    set lineType(type) {
        this.lineStyleInterface.lineType = type;
    }

    get lineCap() {
        return this.lineStyleInterface.lineCap;
    }

    set lineCap(cap) {
        this.lineStyleInterface.lineCap = cap;
    }

    get lineJoin() {
        return this.lineStyleInterface.lineJoin;
    }

    set lineJoin(join) {
        this.lineStyleInterface.lineJoin = join;
    }

    get dashPhase() {
        return this.lineStyleInterface.dashPhase;
    }

    set dashPhase(dashPhase) {
        this.lineStyleInterface.dashPhase = dashPhase;
    }

    get dashPattern() {
        return this.lineStyleInterface.dashPattern;
    }

    set dashPattern(dashPattern) {
        return this.lineStyleInterface.dashPattern = dashPattern;
    }

    get hasBalancedDashes() {
        return this.lineStyleInterface.hasBalancedDashes;
    }

    set hasBalancedDashes(balanced) {
        this.lineStyleInterface.hasBalancedDashes = balanced;
    }

    get strokeAlignment() {
        return this.lineStyleDescriptor.strokeAlignment;
    }

    set strokeAlignment(alignment) {
        this.lineStyleDescriptor.strokeAlignment = alignment
    }

    // PictureFrameInterfaceModule.PictureFrameInterface
    #pictureFrameInterface;
    get pictureFrameInterface() {
        if (!this.#pictureFrameInterface) {
            this.#pictureFrameInterface = new PictureFrameInterfaceModule.PictureFrameInterface(VectorNodeApi.getPictureFrameInterface(this.handle));
        }
        return this.#pictureFrameInterface;
    }

    get pictureFrameEnabled() {
        return this.pictureFrameInterface.enabled;
    }

    get pictureFrameDescription() {
        return this.pictureFrameInterface.description;
    }

    // TransparencyInterfaceModule.TransparencyInterface
    #transparencyInterface;
    get transparencyInterface() {
        if (!this.#transparencyInterface) {
            this.#transparencyInterface = new TransparencyInterfaceModule.TransparencyInterface(VectorNodeApi.getTransparencyInterface(this.handle));
        }
        return this.#transparencyInterface;
    }

    get transparencyFillDescriptor() {
        return this.transparencyInterface.fillDescriptor;
    }

    get transparencyFill() {
        return this.transparencyFillDescriptor.fill;
    }
}

// Let colours be used in place of true fill descriptors
const asFillDescriptor = (x) => x instanceof Colour ? FillDescriptor.createSolid(x) : x;

class VectorNodeDefinition extends PhysicalNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'VectorNodeDefinition';
    }
    
    get isVectorNodeDefinition() {
        return true;
    }
    
    addBrushFillDescriptor(brushFillDescriptor) {
        VectorNodeDefinitionApi.addBrushFillDescriptor(this.handle, asFillDescriptor(brushFillDescriptor)?.handle);
        return this;
    }
    
    addLineDescriptors(lineFillDescriptor, lineStyleDescriptor) {
        VectorNodeDefinitionApi.addLineDescriptors(this.handle, asFillDescriptor(lineFillDescriptor)?.handle, lineStyleDescriptor?.handle);
        return this;
    }
    
    setTransparencyDescriptor(transparencyDescriptor) {
        this.transparencyDescriptor = transparencyDescriptor;
        return this;
    }

    set transparencyDescriptor(fillDescriptor) {
        VectorNodeDefinitionApi.setTransparencyDescriptor(this.handle, fillDescriptor?.handle);
    }
    
    get transparencyDescriptor() {
        return new FillDescriptor(VectorNodeDefinitionApi.getTransparencyDescriptor(this.handle));
    }
    
    get brushFillDescriptorCount() {
        return VectorNodeDefinitionApi.getBrushFillDescriptorCount(this.handle);
    }
    
    getBrushFillDescriptor(index) {
        return new FillDescriptor(VectorNodeDefinitionApi.getBrushFillDescriptor(this.handle, index));
    }
    
    insertBrushFillDescriptor(brushFillDescriptor, index) {
        VectorNodeDefinitionApi.insertBrushFillDescriptor(this.handle, index, asFillDescriptor(brushFillDescriptor)?.handle);
        return this;
    }
    
    setBrushFillDescriptor(brushFillDescriptor, index) {
        VectorNodeDefinitionApi.setBrushFillDescriptor(this.handle, index, asFillDescriptor(brushFillDescriptor)?.handle);
        return this;
    }
    
    removeBrushFillDescriptor(index) {
        VectorNodeDefinitionApi.removeBrushFillDescriptor(this.handle, index);
        return this;
    }
    
    get currentBrushFillIndex() {
        return VectorNodeDefinitionApi.getCurrentBrushFillIndex(this.handle);
    }
    
    set currentBrushFillIndex(index) {
        VectorNodeDefinitionApi.setCurrentBrushFillIndex(this.handle, index);
    }
    
    get lineDescriptorsCount() {
        return VectorNodeDefinitionApi.getLineDescriptorsCount(this.handle);
    }
    
    getLineDescriptors(index) {
        const descriptors = VectorNodeDefinitionApi.getLineDescriptors(this.handle, index);
        return {
            lineStyle: new LineStyleDescriptor(descriptors.lineStyle),
            fill: new FillDescriptor(descriptors.fill)
        };
    }
    
    insertLineDescriptors(lineFillDescriptor, lineStyleDescriptor, index) {
        VectorNodeDefinitionApi.insertLineDescriptors(this.handle, index, asFillDescriptor(lineFillDescriptor)?.handle, lineStyleDescriptor?.handle);
        return this;
    }
    
    setLineDescriptors(lineFillDescriptor, lineStyleDescriptor, index) {
        VectorNodeDefinitionApi.setLineDescriptors(this.handle, index, asFillDescriptor(lineFillDescriptor)?.handle, lineStyleDescriptor?.handle);
        return this;
    }
    
    removeLineDescriptors(index) {
        VectorNodeDefinitionApi.removeLineDescriptors(this.handle, index);
        return this;
    }
    
    get currentLineDescriptorsIndex() {
        return VectorNodeDefinitionApi.getCurrentLineDescriptorsIndex(this.handle);
    }
    
    set currentLineDescriptorsIndex(index) {
        VectorNodeDefinitionApi.setCurrentLineDescriptorsIndex(this.handle, index);
    }

    setPictureFrameEnabled(pictureFrameEnabled) {
        this.pictureFrameEnabled = pictureFrameEnabled;
        return this;
    }

    set pictureFrameEnabled(pictureFrameEnabled) {
        VectorNodeDefinitionApi.setPictureFrameEnabled(this.handle, Boolean(pictureFrameEnabled));
    }

    get pictureFrameEnabled() {
        return VectorNodeDefinitionApi.getPictureFrameEnabled(this.handle);
    }
}


class MeasurementNode extends VectorNode {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'MeasurementNode';
	}

	get isMeasurementNode() {
		return true;
	}

	get factor() {
		return MeasurementNodeApi.getFactor(this.handle);
	}

	get scaledUnitType() {
		return MeasurementNodeApi.getScaledUnitType(this.handle);
	}

	// UnitType.number means "follow the document units" rather than a unit the user pinned.
	get displayUnitType() {
		return MeasurementNodeApi.getDisplayUnitType(this.handle);
	}

	get annotationOffset() {
		return MeasurementNodeApi.getAnnotationOffset(this.handle);
	}

	get showEndpointMarkers() {
		return MeasurementNodeApi.getShowEndpointMarkers(this.handle);
	}

	get useDocumentPrecision() {
		return MeasurementNodeApi.getUseDocumentPrecision(this.handle);
	}

	get decimalPlaces() {
		return MeasurementNodeApi.getDecimalPlaces(this.handle);
	}

	get spreadDistance() {
		return MeasurementNodeApi.getSpreadDistance(this.handle);
	}

	// Returns {start, end} as Points in spread space.
	get spreadEndpoints() {
		return MeasurementNodeApi.getSpreadEndpoints(this.handle);
	}
}


class MeasurementNodeDefinition extends VectorNodeDefinition {
	constructor(handle) {
		super(handle);
	}

	get [Symbol.toStringTag]() {
		return 'MeasurementNodeDefinition';
	}

	get isMeasurementNodeDefinition() {
		return true;
	}

	get annotationOffset() {
		return MeasurementNodeDefinitionApi.getAnnotationOffset(this.handle);
	}

	set annotationOffset(offset) {
		MeasurementNodeDefinitionApi.setAnnotationOffset(this.handle, offset);
	}

    setAnnotationOffset(offset) {
		this.annotationOffset = offset;
        return this;
	}

	get showEndpointMarkers() {
		return MeasurementNodeDefinitionApi.getShowEndpointMarkers(this.handle);
	}

	set showEndpointMarkers(show) {
		MeasurementNodeDefinitionApi.setShowEndpointMarkers(this.handle, show);
	}

	setShowEndpointMarkers(show) {
		this.showEndpointMarkers = show;
		return this;
	}

	// {start, end} as Points.
	get endpoints() {
		return MeasurementNodeDefinitionApi.getEndpoints(this.handle);
	}

	set endpoints(endpoints) {
		MeasurementNodeDefinitionApi.setEndpoints(this.handle, endpoints.start, endpoints.end);
	}

	setEndpoints(start, end) {
		MeasurementNodeDefinitionApi.setEndpoints(this.handle, start, end);
		return this;
	}

	get factor() {
		return MeasurementNodeDefinitionApi.getFactor(this.handle);
	}

	set factor(factor) {
		MeasurementNodeDefinitionApi.setFactor(this.handle, factor);
	}

	setFactor(factor) {
		this.factor = factor;
		return this;
	}

	get scaledUnitType() {
		return MeasurementNodeDefinitionApi.getScaledUnitType(this.handle);
	}

	set scaledUnitType(unitType) {
		MeasurementNodeDefinitionApi.setScaledUnitType(this.handle, unitType);
	}

	setScaledUnitType(unitType) {
		this.scaledUnitType = unitType;
		return this;
	}

	get useDocumentPrecision() {
		return MeasurementNodeDefinitionApi.getUseDocumentPrecision(this.handle);
	}

	set useDocumentPrecision(useDocumentPrecision) {
		MeasurementNodeDefinitionApi.setDisplayPrecision(this.handle, useDocumentPrecision, this.decimalPlaces);
	}

	get decimalPlaces() {
		return MeasurementNodeDefinitionApi.getDecimalPlaces(this.handle);
	}

	set decimalPlaces(decimalPlaces) {
		MeasurementNodeDefinitionApi.setDisplayPrecision(this.handle, this.useDocumentPrecision, decimalPlaces);
	}

	setDisplayPrecision(useDocumentPrecision, decimalPlaces) {
		MeasurementNodeDefinitionApi.setDisplayPrecision(this.handle, useDocumentPrecision, decimalPlaces);
		return this;
	}

	// The label's whole text appearance - font, size and colours. Set to null to follow the document default.
	// The getter hands back a mutable copy, so editing it does not affect the definition until it is set back.
	get labelGlyphAtts() {
		const handle = MeasurementNodeDefinitionApi.getLabelGlyphAtts(this.handle);
		return handle ? new GlyphAtts(handle) : null;
	}

	set labelGlyphAtts(glyphAtts) {
		MeasurementNodeDefinitionApi.setLabelGlyphAtts(this.handle, glyphAtts?.handle);
	}

	setLabelGlyphAtts(glyphAtts) {
		this.labelGlyphAtts = glyphAtts;
		return this;
	}

	static create(start, end, factor, unitType) {
		return new MeasurementNodeDefinition(MeasurementNodeDefinitionApi.create(start, end, factor, unitType));
	}
}


class ImageNode extends VectorNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ImageNode';
    }

    get isImageNode() {
        return true;
    }
    
    get extendType() {
        return ImageNodeApi.getExtendType(this.handle);
    }
    
    get upsamplerType() {
        return ImageNodeApi.getUpsamplerType(this.handle);
    }
    
    get stockURL() {
        return ImageNodeApi.getStockURL(this.handle);
    }
    
    get stockUserProfileURL() {
        return ImageNodeApi.getStockUserProfileURL(this.handle);
    }
    
    get stockAuthor() {
        return ImageNodeApi.getStockAuthor(this.handle);
    }
    
    get lastRendered() {
        return ImageNodeApi.getLastRendered(this.handle);
    }
    
    get bitmapBrushFillDescriptor() {
        return ImageNodeApi.getBitmapBrushFillDescriptor(this.handle);
    }
    
    get isKOnly() {
        return ImageNodeApi.isKOnly(this.handle);
    }

    // ImageResourceInterfaceModule.ImageResourceInterface
    #imageResourceInterface;
    get imageResourceInterface() {
        if (!this.#imageResourceInterface)
            this.#imageResourceInterface = new ImageResourceInterfaceModule.ImageResourceInterface(ImageNodeApi.getImageResourceInterface(this.handle));
        return this.#imageResourceInterface;
    }

    get imageFilePath() {
        return this.imageResourceInterface.imageFilePath;
    }

    getImageFileSize(asBigInt) {
        return this.imageResourceInterface.getImageFileSize(asBigInt);
    }

    get imageFileSize() {
        return this.getImageFileSize();
    }

    get imageFileType() {
        return this.imageResourceInterface.fileType;
    }

    get imageFileTypeName() {
        return this.imageResourceInterface.fileTypeName;
    }
    
    // RasterInterfaceModule.RasterInterface
    #rasterInterface;
    get rasterInterface() {
        if (!this.#rasterInterface)
            this.#rasterInterface = new RasterInterfaceModule.RasterInterface(ImageNodeApi.getRasterInterface(this.handle));
        return this.#rasterInterface;
    }

    get rasterWidth() {
        return this.rasterInterface.width;
    }

    get rasterHeight() {
        return this.rasterInterface.height;
    }

    get rasterFormat() {
        return this.rasterInterface.format;
    }

    get pixelSize() {
        return this.rasterInterface.pixelSize;
    }

    createCompatibleBitmap(copyContents) {
        return this.rasterInterface.createCompatibleBitmap(copyContents);
    }

    createCompatibleBuffer(copyContents) {
        return this.rasterInterface.createCompatibleBuffer(copyContents);
    }

    copyTo(dest, destRect, srcX, srcY) {
        return this.rasterInterface.copyTo(dest, destRect, srcX, srcY);
    }
}


class ImageNodeDefinition extends VectorNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ImageNodeDefinition';
    }
    
    static create(format) {
        return new ImageNodeDefinition(ImageNodeDefinitionApi.create(format));
    }

    get isImageNodeDefinition() {
        return true;
    }
    
    set bitmap(bm) {
        ImageNodeDefinitionApi.setBitmap(this.handle, bm.handle);
    }
    
    get bitmap() {
        return new RasterObject(ImageNodeDefinitionApi.getBitmap(this.handle));
    }

    setBitmap(bm) {
        this.bitmap = bm;
        return this;
    }
}


class PolyCurveNode extends VectorNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PolyCurveNode';
    }

    get isPolyCurveNode() {
        return true;
    }
    
    // ArtboardInterfaceModule.ArtboardInterface
    #artboardInterface;
    get artboardInterface() {
        if (!this.#artboardInterface)
            this.#artboardInterface = new ArtboardInterfaceModule.ArtboardInterface(PolyCurveNodeApi.getArtboardInterface(this.handle));
        return this.#artboardInterface;
    }

    /**
    * @deprecated Use get isArtboardEnabled()
    */
    get artboardEnabled() {
        console.warn("Using deprecated get artboardEnabled() property. Use get isArtboardEnabled() instead.");
        return this.isArtboardEnabled;
    }

    get isArtboardEnabled() {
        return this.artboardInterface.isArtboardEnabled;
    }

    get artboardDescription() {
        return this.artboardInterface.description;
    }

    get artboardBaseBox() {
        return this.artboardInterface.baseBox;
    }

    get artboardSpreadBaseBox() {
        return this.artboardInterface.spreadBaseBox;
    }

    get artboardOrigin() {
        return this.artboardInterface.origin;
    }

    /**
    * @deprecated Use set isArtboardEnabled()
    */
    set artboardEnabled(value) {
        console.warn("Using deprecated set artboardEnabled() property. Use set isArtboardEnabled() instead.");
        this.isArtboardEnabled = value;
    }

    set isArtboardEnabled(value) {
        this.document.setArtboardEnabled(value, this);
    }
}


class PolyCurveNodeDefinition extends VectorNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'PolyCurveNodeDefinition';
    }
    
    get isPolyCurveNodeDefinition() {
        return true;
    }
    
    setCurves(curve) {
        this.curves = curve;
        return this;
    }
    
    get curves() {
        return new PolyCurve(PolyCurveNodeDefinitionApi.getCurves(this.handle));
    }

    set curves(curve) {
        PolyCurveNodeDefinitionApi.setCurves(this.handle, curve.handle);
    }
    
    static create(curve, brushFill, lineFill, lineStyle, transparencyFill) {
        return new PolyCurveNodeDefinition(PolyCurveNodeDefinitionApi.create(curve.handle, brushFill.handle, lineFill.handle, lineStyle.handle, transparencyFill.handle));
    }

    static createDefault() {
        return new PolyCurveNodeDefinition(PolyCurveNodeDefinitionApi.createDefault());
    }
}


class ShapeNode extends VectorNode {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ShapeNode';
    }

    get isShapeNode() {
        return true;
    }

    // ArtboardInterfaceModule.ArtboardInterface
    #artboardInterface;
    get artboardInterface() {
        if (!this.#artboardInterface)
            this.#artboardInterface = new ArtboardInterfaceModule.ArtboardInterface(ShapeNodeApi.getArtboardInterface(this.handle));
        return this.#artboardInterface;
    }

    /**
    * @deprecated Use get isArtboardEnabled()
    */
    get artboardEnabled() {
        console.warn("Using deprecated get artboardEnabled() property. Use get isArtboardEnabled() instead.");
        return this.isArtboardEnabled;
    }

    get isArtboardEnabled() {
        return this.artboardInterface.isArtboardEnabled;
    }

    get artboardDescription() {
        return this.artboardInterface.description;
    }

    get artboardBaseBox() {
        return this.artboardInterface.baseBox;
    }

    get artboardSpreadBaseBox() {
        return this.artboardInterface.spreadBaseBox;
    }

    get artboardOrigin() {
        return this.artboardInterface.origin;
    }

    /**
    * @deprecated Use set isArtboardEnabled()
    */
    set artboardEnabled(value) {
        console.warn("Using deprecated set artboardEnabled() property. Use set isArtboardEnabled() instead.");
        this.isArtboardEnabled = value;
    }

    set isArtboardEnabled(value) {
        this.document.setArtboardEnabled(value, this);
    }

    // ShapeInterfaceModule.ShapeInterface
    #shapeInterface;
    get shapeInterface() {
        if (!this.#shapeInterface)
            this.#shapeInterface = new ShapeInterfaceModule.ShapeInterface(ShapeNodeApi.getShapeInterface(this.handle));
        return this.#shapeInterface;
    }

    get shape() {
        return this.shapeInterface.shape;
    }

    get shapeType() {
        return this.shapeInterface.type;
    }

    get shapeBoundingBox() {
        return this.shapeInterface.boundingBox;
    }
}


class ShapeNodeDefinition extends VectorNodeDefinition {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'ShapeNodeDefinition';
    }
    
    get isShapeNodeDefinition() {
        return true;
    }
    
    setShape(shape) {
        this.shape = shape;
        return this;
    }
    
    get shape() {
        let shapeHandle = ShapeNodeDefinitionApi.getShape(this.handle);
        return createTypedShape(shapeHandle);
    }
    
    set shape(shape) {
        return ShapeNodeDefinitionApi.setShape(this.handle, shape.handle);
    }
    
    setBoundingRectangle(rectangle) {
        this.boundingRectangle = rectangle;
        return this;
    }
    
    get boundingRectangle() {
        return ShapeNodeDefinitionApi.getBoundingRectangle(this.handle);
    }

    set boundingRectangle(rectangle) {
        ShapeNodeDefinitionApi.setBoundingRectangle(this.handle, rectangle);
    }
    
    static create(shape, rectangle, brushFill, lineFill, lineStyle, transparencyFill) {
        if (brushFill instanceof Colour)
            brushFill = FillDescriptor.createSolid(brushFill);
        if (lineFill instanceof Colour)
            lineFill = FillDescriptor.createSolid(lineFill);
        return new ShapeNodeDefinition(ShapeNodeDefinitionApi.create(shape?.handle, rectangle, brushFill?.handle, lineFill?.handle, lineStyle?.handle, transparencyFill?.handle));
    }

    static createDefault() {
        return new ShapeNodeDefinition(ShapeNodeDefinitionApi.createDefault());
    }
}


// This takes a NodeHandle and converts it to the real handle type in an efficient way.
class NodeCast extends HandleObject{

    constructor(handle) {
        if (!handle)
            handle = NodeCastApi.create();
        super(handle);
    }

    setNodeHandler(callback) {
        return NodeCastApi.setNodeHandler(this.handle, callback);
    }

    setArtTextNodeHandler(callback) {
        return NodeCastApi.setArtTextNodeHandler(this.handle, callback);
    }
    
    setAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setColouredLogicalNodeHandler(callback) {
        return NodeCastApi.setColouredLogicalNodeHandler(this.handle, callback);
    }
    
    setCurvePathTextNodeHandler(callback) {
        return NodeCastApi.setCurvePathTextNodeHandler(this.handle, callback);
    }
    
    setCurvesAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setCurvesAdjustmentRasterNodeHandler(this.handle, callback);
    }

    setDocumentNodeHandler(callback) {
        return NodeCastApi.setDocumentNodeHandler(this.handle, callback);
    }
    
    setDevelopNodeHandler(callback) {
        return NodeCastApi.setDevelopNodeHandler(this.handle, callback);
    }

    setEmbeddedDocumentNodeHandler(callback) {
        return NodeCastApi.setEmbeddedDocumentNodeHandler(this.handle, callback);
    }
    
    setEnclosureRasterNodeHandler(callback) {
        return NodeCastApi.setEnclosureRasterNodeHandler(this.handle, callback);
    }
    
    setExposureAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setExposureAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setFilterRasterNodeHandler(callback) {
        return NodeCastApi.setFilterRasterNodeHandler(this.handle, callback);
    }
    
    setGaussianBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setGaussianBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setBoxBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setBoxBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setBilateralBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setBilateralBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setBloomFilterRasterNodeHandler(callback) {
        return NodeCastApi.setBloomFilterRasterNodeHandler(this.handle, callback);
    }
    
    setMedianBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setMedianBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setDiffuseGlowFilterRasterNodeHandler(callback) {
        return NodeCastApi.setDiffuseGlowFilterRasterNodeHandler(this.handle, callback);
    }
    
    setFieldBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setFieldBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setDepthOfFieldFilterRasterNodeHandler(callback) {
        return NodeCastApi.setDepthOfFieldFilterRasterNodeHandler(this.handle, callback);
    }
    
    setLensBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setLensBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setMaximumBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setMaximumBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setMinimumBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setMinimumBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setMotionBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setMotionBlurFilterRasterNodeHandler(this.handle, callback);
    }
    
    setRadialBlurFilterRasterNodeHandler(callback) {
        return NodeCastApi.setRadialBlurFilterRasterNodeHandler(this.handle, callback);
    }

    setShadowsHighlightsFilterRasterNodeHandler(callback) {
        return NodeCastApi.setShadowsHighlightsFilterRasterNodeHandler(this.handle, callback);
    }

    setBrightnessContrastAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setBrightnessContrastAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setShadowsHighlightsAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setShadowsHighlightsAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setBlackAndWhiteAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setBlackAndWhiteAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setRecolourAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setRecolourAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setPosteriseAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setPosteriseAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setSplitToningAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setSplitToningAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setInvertAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setInvertAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setThresholdAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setThresholdAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setClarityFilterRasterNodeHandler(callback) {
        return NodeCastApi.setClarityFilterRasterNodeHandler(this.handle, callback);
    }
    
    setUnsharpMaskFilterRasterNodeHandler(callback) {
        return NodeCastApi.setUnsharpMaskFilterRasterNodeHandler(this.handle, callback);
    }
    
    setHighPassFilterRasterNodeHandler(callback) {
        return NodeCastApi.setHighPassFilterRasterNodeHandler(this.handle, callback);
    }
    
    setDenoiseFilterRasterNodeHandler(callback) {
        return NodeCastApi.setDenoiseFilterRasterNodeHandler(this.handle, callback);
    }
    
    setDiffuseFilterRasterNodeHandler(callback) {
        return NodeCastApi.setDiffuseFilterRasterNodeHandler(this.handle, callback);
    }
    
    setDustAndScratchFilterRasterNodeHandler(callback) {
        return NodeCastApi.setDustAndScratchFilterRasterNodeHandler(this.handle, callback);
    }
    
    setAddNoiseFilterRasterNodeHandler(callback) {
        return NodeCastApi.setAddNoiseFilterRasterNodeHandler(this.handle, callback);
    }
    
    setRippleFilterRasterNodeHandler(callback) {
        return NodeCastApi.setRippleFilterRasterNodeHandler(this.handle, callback);
    }
    
    setTwirlFilterRasterNodeHandler(callback) {
        return NodeCastApi.setTwirlFilterRasterNodeHandler(this.handle, callback);
    }
    
    setSphericalFilterRasterNodeHandler(callback) {
        return NodeCastApi.setSphericalFilterRasterNodeHandler(this.handle, callback);
    }
    
    setPinchPunchFilterRasterNodeHandler(callback) {
        return NodeCastApi.setPinchPunchFilterRasterNodeHandler(this.handle, callback);
    }
    
    setPixelateFilterRasterNodeHandler(callback) {
        return NodeCastApi.setPixelateFilterRasterNodeHandler(this.handle, callback);
    }
    
    setHalftoneFilterRasterNodeHandler(callback) {
        return NodeCastApi.setHalftoneFilterRasterNodeHandler(this.handle, callback);
    }
    
    setWhiteBalanceAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setWhiteBalanceAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setColourBalanceAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setColourBalanceAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setVibranceAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setVibranceAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setNormalsAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setNormalsAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setVignetteFilterRasterNodeHandler(callback) {
        return NodeCastApi.setVignetteFilterRasterNodeHandler(this.handle, callback);
    }
    
    setDefringeFilterRasterNodeHandler(callback) {
        return NodeCastApi.setDefringeFilterRasterNodeHandler(this.handle, callback);
    }
    
    setVoronoiFilterRasterNodeHandler(callback) {
        return NodeCastApi.setVoronoiFilterRasterNodeHandler(this.handle, callback);
    }
    
    setSelectiveColourAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setSelectiveColourAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setHSLShiftAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setHSLShiftAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setToneCompressionAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setToneCompressionAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setToneStretchAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setToneStretchAdjustmentRasterNodeHandler(this.handle, callback);
    }
    
    setFrameTextNodeHandler(callback) {
        return NodeCastApi.setFrameTextNodeHandler(this.handle, callback);
    }
    
    setGroupNodeHandler(callback) {
        return NodeCastApi.setGroupNodeHandler(this.handle, callback);
    }
    
    setImageNodeHandler(callback) {
        return NodeCastApi.setImageNodeHandler(this.handle, callback);
    }
    
    setLevelsAdjustmentRasterNodeHandler(callback) {
        return NodeCastApi.setLevelsAdjustmentRasterNodeHandler(this.handle, callback);
    }

    setLogicalNodeHandler(callback) {
        return NodeCastApi.setLogicalNodeHandler(this.handle, callback);
    }

    setPatternRasterNodeHandler(callback) {
        return NodeCastApi.setPatternRasterNodeHandler(this.handle, callback);
    }

    setPhysicalNodeHandler(callback) {
        return NodeCastApi.setPhysicalNodeHandler(this.handle, callback);
    }

    setPolyCurveNodeHandler(callback) {
        return NodeCastApi.setPolyCurveNodeHandler(this.handle, callback);
    }
    
    setPolyCurveTextNodeHandler(callback) {
        return NodeCastApi.setPolyCurveTextNodeHandler(this.handle, callback);
    }
    
    setRasterNodeHandler(callback) {
        return NodeCastApi.setRasterNodeHandler(this.handle, callback);
    }
    
    setContainerNodeHandler(callback) {
        return NodeCastApi.setContainerNodeHandler(this.handle, callback)
    }

    setShapeNodeHandler(callback) {
        return NodeCastApi.setShapeNodeHandler(this.handle, callback);
    }

    setShapePathTextNodeHandler(callback) {
        return NodeCastApi.setShapePathTextNodeHandler(this.handle, callback);
    }

    setShapeTextNodeHandler(callback) {
        return NodeCastApi.setShapeTextNodeHandler(this.handle, callback);
    }

    setSpreadNodeHandler(callback) {
        return NodeCastApi.setSpreadNodeHandler(this.handle, callback);
    }

    setMeasurementNodeHandler(callback) {
        return NodeCastApi.setMeasurementNodeHandler(this.handle, callback);
    }

    setTableTextNodeHandler(callback) {
        return NodeCastApi.setTableTextNodeHandler(this.handle, callback);
    }

    setTextNodeHandler(callback) {
        return NodeCastApi.setTextNodeHandler(this.handle, callback);
    }

    setVectorNodeHandler(callback) {
        return NodeCastApi.setVectorNodeHandler(this.handle, callback);
    }

    exec(nodeHandle) {
        return NodeCastApi.exec(this.handle, nodeHandle);
    }
}

// Allows re-entry, if you're that mad.
class NodeFactory {
    #caster;
    #nodes;

    constructor() {
        this.#caster = new NodeCast();
        this.#nodes = [];
        let nodes = this.#nodes;
        
        this.#caster.setNodeHandler(handle => nodes.push(new Node(handle)));
        this.#caster.setArtTextNodeHandler(handle => nodes.push(new ArtTextNode(handle)));
        this.#caster.setAdjustmentRasterNodeHandler(handle => nodes.push(new AdjustmentRasterNode(handle)));
        this.#caster.setCurvePathTextNodeHandler(handle => nodes.push(new CurvePathTextNode(handle)));
        this.#caster.setCurvesAdjustmentRasterNodeHandler(handle => nodes.push(new CurvesAdjustmentRasterNode(handle)));
        this.#caster.setColouredLogicalNodeHandler(handle => nodes.push(new ColouredLogicalNode(handle)));
        this.#caster.setDocumentNodeHandler(handle => nodes.push(new DocumentNode(handle)));
        this.#caster.setDevelopNodeHandler(handle => nodes.push(new DevelopNode(handle)));
        this.#caster.setEmbeddedDocumentNodeHandler(handle => nodes.push(new EmbeddedDocumentNode(handle)));
        this.#caster.setEnclosureRasterNodeHandler(handle => nodes.push(new EnclosureRasterNode(handle)));
        this.#caster.setExposureAdjustmentRasterNodeHandler(handle => nodes.push(new ExposureAdjustmentRasterNode(handle)));
        this.#caster.setFilterRasterNodeHandler(handle => nodes.push(new FilterRasterNode(handle)));
        this.#caster.setGaussianBlurFilterRasterNodeHandler(handle => nodes.push(new GaussianBlurFilterRasterNode(handle)));
        this.#caster.setBoxBlurFilterRasterNodeHandler(handle => nodes.push(new BoxBlurFilterRasterNode(handle)));
        this.#caster.setBilateralBlurFilterRasterNodeHandler(handle => nodes.push(new BilateralBlurFilterRasterNode(handle)));
        this.#caster.setBloomFilterRasterNodeHandler(handle => nodes.push(new BloomFilterRasterNode(handle)));
        this.#caster.setMedianBlurFilterRasterNodeHandler(handle => nodes.push(new MedianBlurFilterRasterNode(handle)));
        this.#caster.setDiffuseGlowFilterRasterNodeHandler(handle => nodes.push(new DiffuseGlowFilterRasterNode(handle)));
        this.#caster.setFieldBlurFilterRasterNodeHandler(handle => nodes.push(new FieldBlurFilterRasterNode(handle)));
        this.#caster.setDepthOfFieldFilterRasterNodeHandler(handle => nodes.push(new DepthOfFieldFilterRasterNode(handle)));
        this.#caster.setLensBlurFilterRasterNodeHandler(handle => nodes.push(new LensBlurFilterRasterNode(handle)));
        this.#caster.setMaximumBlurFilterRasterNodeHandler(handle => nodes.push(new MaximumBlurFilterRasterNode(handle)));
        this.#caster.setMinimumBlurFilterRasterNodeHandler(handle => nodes.push(new MinimumBlurFilterRasterNode(handle)));
        this.#caster.setMotionBlurFilterRasterNodeHandler(handle => nodes.push(new MotionBlurFilterRasterNode(handle)));
        this.#caster.setShadowsHighlightsFilterRasterNodeHandler(handle => nodes.push(new ShadowsHighlightsFilterRasterNode(handle)));
        this.#caster.setRadialBlurFilterRasterNodeHandler(handle => nodes.push(new RadialBlurFilterRasterNode(handle)));
        this.#caster.setBrightnessContrastAdjustmentRasterNodeHandler(handle => nodes.push(new BrightnessContrastAdjustmentRasterNode(handle)));
        this.#caster.setShadowsHighlightsAdjustmentRasterNodeHandler(handle => nodes.push(new ShadowsHighlightsAdjustmentRasterNode(handle)));
        this.#caster.setBlackAndWhiteAdjustmentRasterNodeHandler(handle => nodes.push(new BlackAndWhiteAdjustmentRasterNode(handle)));
        this.#caster.setRecolourAdjustmentRasterNodeHandler(handle => nodes.push(new RecolourAdjustmentRasterNode(handle)));
        this.#caster.setPosteriseAdjustmentRasterNodeHandler(handle => nodes.push(new PosteriseAdjustmentRasterNode(handle)));
        this.#caster.setSplitToningAdjustmentRasterNodeHandler(handle => nodes.push(new SplitToningAdjustmentRasterNode(handle)));
        this.#caster.setInvertAdjustmentRasterNodeHandler(handle => nodes.push(new InvertAdjustmentRasterNode(handle)));
        this.#caster.setThresholdAdjustmentRasterNodeHandler(handle => nodes.push(new ThresholdAdjustmentRasterNode(handle)));
        this.#caster.setClarityFilterRasterNodeHandler(handle => nodes.push(new ClarityFilterRasterNode(handle)));
        this.#caster.setUnsharpMaskFilterRasterNodeHandler(handle => nodes.push(new UnsharpMaskFilterRasterNode(handle)));
        this.#caster.setHighPassFilterRasterNodeHandler(handle => nodes.push(new HighPassFilterRasterNode(handle)));
        this.#caster.setDenoiseFilterRasterNodeHandler(handle => nodes.push(new DenoiseFilterRasterNode(handle)));
        this.#caster.setDiffuseFilterRasterNodeHandler(handle => nodes.push(new DiffuseFilterRasterNode(handle)));
        this.#caster.setDustAndScratchFilterRasterNodeHandler(handle => nodes.push(new DustAndScratchFilterRasterNode(handle)));
        this.#caster.setAddNoiseFilterRasterNodeHandler(handle => nodes.push(new AddNoiseFilterRasterNode(handle)));
        this.#caster.setRippleFilterRasterNodeHandler(handle => nodes.push(new RippleFilterRasterNode(handle)));
        this.#caster.setTwirlFilterRasterNodeHandler(handle => nodes.push(new TwirlFilterRasterNode(handle)));
        this.#caster.setSphericalFilterRasterNodeHandler(handle => nodes.push(new SphericalFilterRasterNode(handle)));
        this.#caster.setPinchPunchFilterRasterNodeHandler(handle => nodes.push(new PinchPunchFilterRasterNode(handle)));
        this.#caster.setPixelateFilterRasterNodeHandler(handle => nodes.push(new PixelateFilterRasterNode(handle)));
        this.#caster.setHalftoneFilterRasterNodeHandler(handle => nodes.push(new HalftoneFilterRasterNode(handle)));
        this.#caster.setWhiteBalanceAdjustmentRasterNodeHandler(handle => nodes.push(new WhiteBalanceAdjustmentRasterNode(handle)));
        this.#caster.setColourBalanceAdjustmentRasterNodeHandler(handle => nodes.push(new ColourBalanceAdjustmentRasterNode(handle)));
        this.#caster.setVibranceAdjustmentRasterNodeHandler(handle => nodes.push(new VibranceAdjustmentRasterNode(handle)));
        this.#caster.setNormalsAdjustmentRasterNodeHandler(handle => nodes.push(new NormalsAdjustmentRasterNode(handle)));
        this.#caster.setVignetteFilterRasterNodeHandler(handle => nodes.push(new VignetteFilterRasterNode(handle)));
        this.#caster.setDefringeFilterRasterNodeHandler(handle => nodes.push(new DefringeFilterRasterNode(handle)));
        this.#caster.setVoronoiFilterRasterNodeHandler(handle => nodes.push(new VoronoiFilterRasterNode(handle)));
        this.#caster.setSelectiveColourAdjustmentRasterNodeHandler(handle => nodes.push(new SelectiveColourAdjustmentRasterNode(handle)));
        this.#caster.setHSLShiftAdjustmentRasterNodeHandler(handle => nodes.push(new HSLShiftAdjustmentRasterNode(handle)));
        this.#caster.setToneCompressionAdjustmentRasterNodeHandler(handle => nodes.push(new ToneCompressionAdjustmentRasterNode(handle)));
        this.#caster.setToneStretchAdjustmentRasterNodeHandler(handle => nodes.push(new ToneStretchAdjustmentRasterNode(handle)));
        this.#caster.setFrameTextNodeHandler(handle => nodes.push(new FrameTextNode(handle)));
        this.#caster.setGroupNodeHandler(handle => nodes.push(new GroupNode(handle)));
        this.#caster.setImageNodeHandler(handle => nodes.push(new ImageNode(handle)));
        this.#caster.setLevelsAdjustmentRasterNodeHandler(handle => nodes.push(new LevelsAdjustmentRasterNode(handle)));
        this.#caster.setLogicalNodeHandler(handle => nodes.push(new LogicalNode(handle)));
        this.#caster.setPatternRasterNodeHandler(handle => nodes.push(new PatternRasterNode(handle)));
        this.#caster.setPhysicalNodeHandler(handle => nodes.push(new PhysicalNode(handle)));
        this.#caster.setPolyCurveNodeHandler(handle => nodes.push(new PolyCurveNode(handle)));
        this.#caster.setPolyCurveTextNodeHandler(handle => nodes.push(new PolyCurveTextNode(handle)));
        this.#caster.setRasterNodeHandler(handle => nodes.push(new RasterNode(handle)));
        this.#caster.setContainerNodeHandler(handle => nodes.push(new ContainerNode(handle)));
        this.#caster.setSpreadNodeHandler(handle => nodes.push(new SpreadNode(handle)));
        this.#caster.setShapeNodeHandler(handle => nodes.push(new ShapeNode(handle)));
        this.#caster.setShapePathTextNodeHandler(handle => nodes.push(new ShapePathTextNode(handle)));
        this.#caster.setShapeTextNodeHandler(handle => nodes.push(new ShapeTextNode(handle)));
        this.#caster.setMeasurementNodeHandler(handle => nodes.push(new MeasurementNode(handle)));
        this.#caster.setTableTextNodeHandler(handle => nodes.push(new TableTextNode(handle)));
        this.#caster.setTextNodeHandler(handle => nodes.push(new TextNode(handle)));
        this.#caster.setVectorNodeHandler(handle => nodes.push(new VectorNode(handle)));
    }

    create(handle) {
        this.#caster.exec(handle);
        return this.#nodes.pop();
    }
}

const nodeFactory = new NodeFactory;

function createTypedNode(handle) {
    return nodeFactory.create(handle);
}

// general nodes
module.exports.ArtTextNode = ArtTextNode;
module.exports.ArtTextNodeDefinition = ArtTextNodeDefinition;
module.exports.CurvePathTextNode = CurvePathTextNode;
module.exports.CurvePathTextNodeDefinition = CurvePathTextNodeDefinition;
module.exports.DocumentNode = DocumentNode;
module.exports.FrameTextNode = FrameTextNode;
module.exports.FrameTextNodeDefinition = FrameTextNodeDefinition;
module.exports.ImageNode = ImageNode;
module.exports.ImageNodeDefinition = ImageNodeDefinition;
module.exports.LogicalNode = LogicalNode;
module.exports.LogicalNodeDefinition = LogicalNodeDefinition;
module.exports.ColouredLogicalNode = ColouredLogicalNode;
module.exports.ColouredLogicalNodeDefinition = ColouredLogicalNodeDefinition;
module.exports.Node = Node;
module.exports.NodeDefinition = NodeDefinition;
module.exports.PhysicalNode = PhysicalNode;
module.exports.PhysicalNodeDefinition = PhysicalNodeDefinition;
module.exports.PolyCurveNode = PolyCurveNode;
module.exports.PolyCurveNodeDefinition = PolyCurveNodeDefinition;
module.exports.PolyCurveTextNode = PolyCurveTextNode;
module.exports.PolyCurveTextNodeDefinition = PolyCurveTextNodeDefinition;
module.exports.RasterNode = RasterNode;
module.exports.RasterNodeDefinition = RasterNodeDefinition;
module.exports.PatternRasterNode = PatternRasterNode;
module.exports.PatternRasterNodeDefinition = PatternRasterNodeDefinition;
module.exports.ContainerNode = ContainerNode;
module.exports.ContainerNodeDefinition = ContainerNodeDefinition;
module.exports.ShapeNode = ShapeNode;
module.exports.ShapeNodeDefinition = ShapeNodeDefinition;
module.exports.ShapePathTextNode = ShapePathTextNode;
module.exports.ShapePathTextNodeDefinition = ShapePathTextNodeDefinition;
module.exports.ShapeTextNode = ShapeTextNode;
module.exports.ShapeTextNodeDefinition = ShapeTextNodeDefinition;
module.exports.SpreadNode = SpreadNode;
module.exports.MeasurementNode = MeasurementNode;
module.exports.MeasurementNodeDefinition = MeasurementNodeDefinition;
module.exports.TableTextNode = TableTextNode;
module.exports.TableTextNodeDefinition = TableTextNodeDefinition;
module.exports.TextNode = TextNode;
module.exports.TextNodeDefinition = TextNodeDefinition;

// raster adjustment nodes
module.exports.BlackAndWhiteAdjustmentRasterNode = BlackAndWhiteAdjustmentRasterNode;
module.exports.BlackAndWhiteAdjustmentRasterNodeDefinition = BlackAndWhiteAdjustmentRasterNodeDefinition;
module.exports.BrightnessContrastAdjustmentRasterNode = BrightnessContrastAdjustmentRasterNode;
module.exports.BrightnessContrastAdjustmentRasterNodeDefinition = BrightnessContrastAdjustmentRasterNodeDefinition;
module.exports.ColourBalanceAdjustmentRasterNode = ColourBalanceAdjustmentRasterNode;
module.exports.ColourBalanceAdjustmentRasterNodeDefinition = ColourBalanceAdjustmentRasterNodeDefinition;
module.exports.CurvesAdjustmentRasterNode = CurvesAdjustmentRasterNode;
module.exports.CurvesAdjustmentRasterNodeDefinition = CurvesAdjustmentRasterNodeDefinition;
module.exports.ExposureAdjustmentRasterNode = ExposureAdjustmentRasterNode;
module.exports.ExposureAdjustmentRasterNodeDefinition = ExposureAdjustmentRasterNodeDefinition;
module.exports.HSLShiftAdjustmentRasterNode = HSLShiftAdjustmentRasterNode;
module.exports.HSLShiftAdjustmentRasterNodeDefinition = HSLShiftAdjustmentRasterNodeDefinition;
module.exports.InvertAdjustmentRasterNode = InvertAdjustmentRasterNode;
module.exports.InvertAdjustmentRasterNodeDefinition = InvertAdjustmentRasterNodeDefinition;
module.exports.LevelsAdjustmentRasterNode = LevelsAdjustmentRasterNode;
module.exports.LevelsAdjustmentRasterNodeDefinition = LevelsAdjustmentRasterNodeDefinition;
module.exports.NormalsAdjustmentRasterNode = NormalsAdjustmentRasterNode;
module.exports.NormalsAdjustmentRasterNodeDefinition = NormalsAdjustmentRasterNodeDefinition;
module.exports.PosteriseAdjustmentRasterNode = PosteriseAdjustmentRasterNode;
module.exports.PosteriseAdjustmentRasterNodeDefinition = PosteriseAdjustmentRasterNodeDefinition;
module.exports.RecolourAdjustmentRasterNode = RecolourAdjustmentRasterNode;
module.exports.RecolourAdjustmentRasterNodeDefinition = RecolourAdjustmentRasterNodeDefinition;
module.exports.SelectiveColourAdjustmentRasterNode = SelectiveColourAdjustmentRasterNode;
module.exports.SelectiveColourAdjustmentRasterNodeDefinition = SelectiveColourAdjustmentRasterNodeDefinition;
module.exports.ShadowsHighlightsAdjustmentRasterNode = ShadowsHighlightsAdjustmentRasterNode;
module.exports.ShadowsHighlightsAdjustmentRasterNodeDefinition = ShadowsHighlightsAdjustmentRasterNodeDefinition;
module.exports.SplitToningAdjustmentRasterNode = SplitToningAdjustmentRasterNode;
module.exports.SplitToningAdjustmentRasterNodeDefinition = SplitToningAdjustmentRasterNodeDefinition;
module.exports.ThresholdAdjustmentRasterNode = ThresholdAdjustmentRasterNode;
module.exports.ThresholdAdjustmentRasterNodeDefinition = ThresholdAdjustmentRasterNodeDefinition;
module.exports.ToneCompressionAdjustmentRasterNode = ToneCompressionAdjustmentRasterNode;
module.exports.ToneCompressionAdjustmentRasterNodeDefinition = ToneCompressionAdjustmentRasterNodeDefinition;
module.exports.ToneStretchAdjustmentRasterNode = ToneStretchAdjustmentRasterNode;
module.exports.ToneStretchAdjustmentRasterNodeDefinition = ToneStretchAdjustmentRasterNodeDefinition;
module.exports.VibranceAdjustmentRasterNode = VibranceAdjustmentRasterNode;
module.exports.VibranceAdjustmentRasterNodeDefinition = VibranceAdjustmentRasterNodeDefinition;
module.exports.WhiteBalanceAdjustmentRasterNode = WhiteBalanceAdjustmentRasterNode;
module.exports.WhiteBalanceAdjustmentRasterNodeDefinition = WhiteBalanceAdjustmentRasterNodeDefinition;

// raster filter nodes
module.exports.AddNoiseFilterRasterNode = AddNoiseFilterRasterNode;
module.exports.AddNoiseFilterRasterNodeDefinition = AddNoiseFilterRasterNodeDefinition;
module.exports.BilateralBlurFilterRasterNode = BilateralBlurFilterRasterNode;
module.exports.BilateralBlurFilterRasterNodeDefinition = BilateralBlurFilterRasterNodeDefinition;
module.exports.BloomFilterRasterNode = BloomFilterRasterNode;
module.exports.BloomFilterRasterNodeDefinition = BloomFilterRasterNodeDefinition;
module.exports.BoxBlurFilterRasterNode = BoxBlurFilterRasterNode;
module.exports.BoxBlurFilterRasterNodeDefinition = BoxBlurFilterRasterNodeDefinition;
module.exports.ClarityFilterRasterNode = ClarityFilterRasterNode;
module.exports.ClarityFilterRasterNodeDefinition = ClarityFilterRasterNodeDefinition;
module.exports.DefringeFilterRasterNode = DefringeFilterRasterNode;
module.exports.DefringeFilterRasterNodeDefinition = DefringeFilterRasterNodeDefinition;
module.exports.DenoiseFilterRasterNode = DenoiseFilterRasterNode;
module.exports.DenoiseFilterRasterNodeDefinition = DenoiseFilterRasterNodeDefinition;
module.exports.DiffuseFilterRasterNode = DiffuseFilterRasterNode;
module.exports.DiffuseFilterRasterNodeDefinition = DiffuseFilterRasterNodeDefinition;
module.exports.DiffuseGlowFilterRasterNode = DiffuseGlowFilterRasterNode;
module.exports.DiffuseGlowFilterRasterNodeDefinition = DiffuseGlowFilterRasterNodeDefinition;
module.exports.DustAndScratchFilterRasterNode = DustAndScratchFilterRasterNode;
module.exports.DustAndScratchFilterRasterNodeDefinition = DustAndScratchFilterRasterNodeDefinition;
module.exports.DepthOfFieldFilterRasterNode = DepthOfFieldFilterRasterNode;
module.exports.DepthOfFieldFilterRasterNodeDefinition = DepthOfFieldFilterRasterNodeDefinition;
module.exports.FieldBlurFilterRasterNode = FieldBlurFilterRasterNode;
module.exports.FieldBlurFilterRasterNodeDefinition = FieldBlurFilterRasterNodeDefinition;
module.exports.GaussianBlurFilterRasterNode = GaussianBlurFilterRasterNode;
module.exports.GaussianBlurFilterRasterNodeDefinition = GaussianBlurFilterRasterNodeDefinition;
module.exports.HalftoneFilterRasterNode = HalftoneFilterRasterNode;
module.exports.HalftoneFilterRasterNodeDefinition = HalftoneFilterRasterNodeDefinition;
module.exports.ShadowsHighlightsFilterRasterNode = ShadowsHighlightsFilterRasterNode;
module.exports.ShadowsHighlightsFilterRasterNodeDefinition = ShadowsHighlightsFilterRasterNodeDefinition;
module.exports.HighPassFilterRasterNode = HighPassFilterRasterNode;
module.exports.HighPassFilterRasterNodeDefinition = HighPassFilterRasterNodeDefinition;
module.exports.LensBlurFilterRasterNode = LensBlurFilterRasterNode;
module.exports.LensBlurFilterRasterNodeDefinition = LensBlurFilterRasterNodeDefinition;
module.exports.MaximumBlurFilterRasterNode = MaximumBlurFilterRasterNode;
module.exports.MaximumBlurFilterRasterNodeDefinition = MaximumBlurFilterRasterNodeDefinition;
module.exports.MedianBlurFilterRasterNode = MedianBlurFilterRasterNode;
module.exports.MedianBlurFilterRasterNodeDefinition = MedianBlurFilterRasterNodeDefinition;
module.exports.MinimumBlurFilterRasterNode = MinimumBlurFilterRasterNode;
module.exports.MinimumBlurFilterRasterNodeDefinition = MinimumBlurFilterRasterNodeDefinition;
module.exports.MotionBlurFilterRasterNode = MotionBlurFilterRasterNode;
module.exports.MotionBlurFilterRasterNodeDefinition = MotionBlurFilterRasterNodeDefinition;
module.exports.PinchPunchFilterRasterNode = PinchPunchFilterRasterNode;
module.exports.PinchPunchFilterRasterNodeDefinition = PinchPunchFilterRasterNodeDefinition;
module.exports.PixelateFilterRasterNode = PixelateFilterRasterNode;
module.exports.PixelateFilterRasterNodeDefinition = PixelateFilterRasterNodeDefinition;
module.exports.RadialBlurFilterRasterNode = RadialBlurFilterRasterNode;
module.exports.RadialBlurFilterRasterNodeDefinition = RadialBlurFilterRasterNodeDefinition;
module.exports.RippleFilterRasterNode = RippleFilterRasterNode;
module.exports.RippleFilterRasterNodeDefinition = RippleFilterRasterNodeDefinition;
module.exports.SphericalFilterRasterNode = SphericalFilterRasterNode;
module.exports.SphericalFilterRasterNodeDefinition = SphericalFilterRasterNodeDefinition;
module.exports.TwirlFilterRasterNode = TwirlFilterRasterNode;
module.exports.TwirlFilterRasterNodeDefinition = TwirlFilterRasterNodeDefinition;
module.exports.UnsharpMaskFilterRasterNode = UnsharpMaskFilterRasterNode;
module.exports.UnsharpMaskFilterRasterNodeDefinition = UnsharpMaskFilterRasterNodeDefinition;
module.exports.VignetteFilterRasterNode = VignetteFilterRasterNode;
module.exports.VignetteFilterRasterNodeDefinition = VignetteFilterRasterNodeDefinition;
module.exports.VoronoiFilterRasterNode = VoronoiFilterRasterNode;
module.exports.VoronoiFilterRasterNodeDefinition = VoronoiFilterRasterNodeDefinition;

// raster adjustment parameters
module.exports.BlackAndWhiteAdjustmentParameters = BlackAndWhiteAdjustmentParameters;
module.exports.BrightnessContrastAdjustmentParameters = BrightnessContrastAdjustmentParameters;
module.exports.ColourBalanceAdjustmentParameters = ColourBalanceAdjustmentParameters;
module.exports.ColourBalanceValues = ColourBalanceValues;
module.exports.CurvesAdjustmentParameters = CurvesAdjustmentParameters;
module.exports.ExposureAdjustmentParameters = ExposureAdjustmentParameters;
module.exports.HSLShiftAdjustmentChannelParameters = HSLShiftAdjustmentChannelParameters;
module.exports.HSLShiftAdjustmentColourRange = HSLShiftAdjustmentColourRange;
module.exports.HSLShiftAdjustmentParameters = HSLShiftAdjustmentParameters;
module.exports.LevelsAdjustmentChannelParameters = LevelsAdjustmentChannelParameters;
module.exports.LevelsAdjustmentParameters = LevelsAdjustmentParameters;
module.exports.NormalsAdjustmentParameters = NormalsAdjustmentParameters;
module.exports.PosteriseAdjustmentParameters = PosteriseAdjustmentParameters;
module.exports.RecolourAdjustmentParameters = RecolourAdjustmentParameters;
module.exports.ShadowsHighlightsAdjustmentParameters = ShadowsHighlightsAdjustmentParameters;
module.exports.SelectiveColourAdjustmentParameters = SelectiveColourAdjustmentParameters;
module.exports.SplitToningAdjustmentParameters = SplitToningAdjustmentParameters;
module.exports.ThresholdAdjustmentParameters = ThresholdAdjustmentParameters;
module.exports.ToneCompressionAdjustmentParameters = ToneCompressionAdjustmentParameters;
module.exports.ToneStretchAdjustmentParameters = ToneStretchAdjustmentParameters;
module.exports.VibranceAdjustmentParameters = VibranceAdjustmentParameters;
module.exports.WhiteBalanceAdjustmentParameters = WhiteBalanceAdjustmentParameters;

// raster filter parameters
module.exports.AddNoiseFilterParameters = AddNoiseFilterParameters;
module.exports.BilateralBlurFilterParameters = BilateralBlurFilterParameters;
module.exports.BloomFilterParameters = BloomFilterParameters;
module.exports.BoxBlurFilterParameters = BoxBlurFilterParameters;
module.exports.ClarityFilterParameters = ClarityFilterParameters;
module.exports.DefringeFilterParameters = DefringeFilterParameters;
module.exports.DenoiseFilterParameters = DenoiseFilterParameters;
module.exports.DepthOfFieldFilterParameters = DepthOfFieldFilterParameters;
module.exports.DiffuseFilterParameters = DiffuseFilterParameters;
module.exports.DiffuseGlowFilterParameters = DiffuseGlowFilterParameters;
module.exports.DustAndScratchFilterParameters = DustAndScratchFilterParameters;
module.exports.EllipticalDepthOfFieldParameters = EllipticalDepthOfFieldParameters;
module.exports.FieldBlurFilterParameters = FieldBlurFilterParameters;
module.exports.FieldBlurItemParameters = FieldBlurItemParameters;
module.exports.GaussianBlurFilterParameters = GaussianBlurFilterParameters;
module.exports.HalftoneFilterParameters = HalftoneFilterParameters;
module.exports.ShadowsHighlightsFilterParameters = ShadowsHighlightsFilterParameters;
module.exports.HighPassFilterParameters = HighPassFilterParameters;
module.exports.LensBlurFilterParameters = LensBlurFilterParameters;
module.exports.MedianBlurFilterParameters = MedianBlurFilterParameters;
module.exports.MaximumBlurFilterParameters = MaximumBlurFilterParameters;
module.exports.MinimumBlurFilterParameters = MinimumBlurFilterParameters;
module.exports.MotionBlurFilterParameters = MotionBlurFilterParameters;
module.exports.PinchPunchFilterParameters = PinchPunchFilterParameters;
module.exports.PixelateFilterParameters = PixelateFilterParameters;
module.exports.RadialBlurFilterParameters = RadialBlurFilterParameters;
module.exports.RippleFilterParameters = RippleFilterParameters;
module.exports.SphericalFilterParameters = SphericalFilterParameters;
module.exports.TiltShiftDepthOfFieldParameters = TiltShiftDepthOfFieldParameters;
module.exports.TwirlFilterParameters = TwirlFilterParameters;
module.exports.UnsharpMaskFilterParameters = UnsharpMaskFilterParameters;
module.exports.VignetteFilterParameters = VignetteFilterParameters;
module.exports.VoronoiFilterParameters = VoronoiFilterParameters;

// other bits
module.exports.AddNoiseType = AddNoiseType;
module.exports.BloomMethod = BloomMethod;
module.exports.ColourSpaceType = ColourSpaceType;
module.exports.DepthOfFieldMode = DepthOfFieldMode;
module.exports.DevelopDetailRefinementMethod = DevelopDetailRefinementMethod;
module.exports.DevelopInvertMethod = DevelopInvertMethod;
module.exports.DevelopNode = DevelopNode;
module.exports.DevelopParameters = DevelopParameters;
module.exports.DevelopToneCurveMethod = DevelopToneCurveMethod;
module.exports.HalftoneDotType = HalftoneDotType;
module.exports.HalftoneScreenType = HalftoneScreenType;
module.exports.LineDescriptors = LineDescriptors;
module.exports.NodeCast = NodeCast;
module.exports.NodeChildType = NodeChildType;
module.exports.PageBoundingBoxType = PageBoundingBoxType;
module.exports.RasterExtendType = RasterExtendType;
module.exports.RasterFormat = RasterFormat;
module.exports.RasterResamplerType = RasterResamplerType;
module.exports.ShadowsHighlightsVersion = ShadowsHighlightsVersion;
module.exports.SelectiveColour = SelectiveColour;
module.exports.SelectiveColourWeights = SelectiveColourWeights;
module.exports.TonalRangeType = TonalRangeType;
module.exports.ToneCompressionMethod = ToneCompressionMethod;
module.exports.ToneStretchMethod = ToneStretchMethod;
module.exports.UnitType = UnitType;
module.exports.createTypedNode = createTypedNode;
module.exports.getNodeSiblings = getNodeSiblings;
module.exports.getNodeChildren = getNodeChildren;
module.exports.getNodesRecursive = getNodesRecursive;
module.exports.getNodeChildrenRecursive = getNodeChildrenRecursive;

module.exports.NodeChildren = NodeChildren;
module.exports.NodeChildrenOnly = NodeChildrenOnly;
