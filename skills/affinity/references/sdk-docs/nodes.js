'use strict';

const { ColourSpaceType } = require('affinity:colours');
const { EnumerationResult } = require('affinity:common');

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
    RasterNodeApi,
    RasterNodeDefinitionApi,
    ShapeNodeApi,
    ShapeNodeDefinitionApi,
    ShapePathTextNodeApi,
    ShapeTextNodeApi,
    SpreadNodeApi,
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
    BlackAndWhiteAdjustmentParameters,
    BrightnessContrastAdjustmentParameters,
    ColourBalanceAdjustmentParameters,
    ColourBalanceValues,
    CurvesAdjustmentParametersApi,
    ExposureAdjustmentParameters,
    HSLShiftAdjustmentChannelParameters,
    HSLShiftAdjustmentColourRange,
    HSLShiftAdjustmentParametersApi,
    LevelsAdjustmentChannelParameters,
    LevelsAdjustmentParameters,
    NormalsAdjustmentParameters,
    PosteriseAdjustmentParameters,
    RecolourAdjustmentParameters,
    SelectiveColourAdjustmentParameters,
    ShadowsHighlightsAdjustmentParameters,
    SplitToningAdjustmentParameters,
    ThresholdAdjustmentParameters,
    ToneCompressionAdjustmentParameters,
    ToneStretchAdjustmentParameters,
    VibranceAdjustmentParameters,
    WhiteBalanceAdjustmentParameters,
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
    AddNoiseFilterParameters,
    BilateralBlurFilterParameters,
    BloomFilterParameters,
    BoxBlurFilterParameters,
    ClarityFilterParameters,
    DefringeFilterParameters,
    DenoiseFilterParameters,
    DepthOfFieldFilterParametersApi,
    DiffuseFilterParameters,
    DiffuseGlowFilterParameters,
    DustAndScratchFilterParameters,
    EllipticalDepthOfFieldParameters,
    FieldBlurFilterParametersApi,
    FieldBlurItemParameters,
    GaussianBlurFilterParameters,
    HalftoneFilterParameters,
    HighPassFilterParameters,
    LensBlurFilterParameters,
    MaximumBlurFilterParameters,
    MedianBlurFilterParameters,
    MinimumBlurFilterParameters,
    MotionBlurFilterParameters,
    PinchPunchFilterParameters,
    PixelateFilterParameters,
    RadialBlurFilterParameters,
    RippleFilterParameters,
    ShadowsHighlightsFilterParameters,
    SphericalFilterParameters,
    TiltShiftDepthOfFieldParameters,
    TwirlFilterParameters,
    UnsharpMaskFilterParameters,
    VignetteFilterParameters,
    VoronoiFilterParameters,
} = require('affinity:dom');

// other bits
const {
    AddNoiseType,
    BloomMethod,
    DepthOfFieldMode,
    DocumentApi,
    DocumentNodeApi,
    HalftoneDotType,
    HalftoneScreenType,
    NodeCastApi,
    NodeChildType,
    PageBoundingBoxType,
    SelectiveColour,
    ShadowsHighlightsVersion,
    TonalRangeType,
    ToneCompressionMethod,
    ToneStretchMethod,
} = require('affinity:dom');

const { RasterExtendType, RasterFormat, RasterResamplerType } = require('affinity:raster');

const { StoryIoFormat } = require('affinity:story');

const { Collection } = require('./collection.js');
const { Colour } = require('./colours.js');
const { FillDescriptor } = require('./fills.js');
const { PolyCurve, Spline } = require('./geometry.js');
const { HandleObject } = require('./handleobject.js');
const { LineStyle, LineStyleDescriptor, LineStyleMask } = require('./linestyle.js');
const { RasterObject } = require('./rasterobject.js');
const { Selectable } = require('./selectable.js');
const { createTypedShape, Shape } = require('./shapes.js');

// cyclics:
const ArtboardInterfaceModule = require('./artboardinterface.js');
const BaseBoxInterfaceModule = require('./baseboxinterface.js');
const BlendModeInterfaceModule = require('./blendmodeinterface.js');
const BrushFillInterfaceModule = require('./brushfillinterface.js');
const CommandsModule  = require('./commands.js');
const CompoundOperationInterfaceModule = require('./compoundoperationinterface.js');
const CurvesInterfaceModule = require('./curvesinterface.js');
const DescriptionInterfaceModule = require('./descriptioninterface.js');
const DocumentModule = require('./document.js');
const EditabilityInterfaceModule = require('./editabilityinterface.js');
const ExportableInterfaceModule = require('./exportableinterface.js');
const ImageResourceInterfaceModule = require('./imageresourceinterface.js');
const LayerEffectsInterfaceModule = require('./layereffectsinterface.js');
const LineStyleInterfaceModule = require('./linestyleinterface.js');
const PhysicalRootInterfaceModule = require('./physicalrootinterface.js');
const PhysicalRootPropertiesInterfaceModule = require('./physicalrootpropertiesinterface.js');
const PictureFrameInterfaceModule = require('./pictureframeinterface.js');
const RasterInterfaceModule = require('./rasterinterface.js');
const SelectionsModule = require('./selections.js');
const ShapeInterfaceModule = require('./shapeinterface.js');
const StoryInterfaceModule = require('./storyinterface.js');
const TagInterfaceModule = require('./taginterface.js');
const TextFrameInterfaceModule = require('./textframeinterface.js');
const TransformInterfaceModule = require('./transforminterface.js');
const TransparencyInterfaceModule = require('./transparencyinterface.js');
const VisibilityInterfaceModule = require('./visibilityinterface.js');

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

    get imageFileSize() {
        return this.imageResourceInterface.imageFileSize;
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
        return BlackAndWhiteAdjustmentRasterNodeApi.getParameters(this.handle);
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
        BlackAndWhiteAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return BlackAndWhiteAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new BlackAndWhiteAdjustmentRasterNodeDefinition(BlackAndWhiteAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new BlackAndWhiteAdjustmentRasterNodeDefinition(BlackAndWhiteAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return BrightnessContrastAdjustmentRasterNodeApi.getParameters(this.handle);
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
        BrightnessContrastAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return BrightnessContrastAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new BrightnessContrastAdjustmentRasterNodeDefinition(BrightnessContrastAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new BrightnessContrastAdjustmentRasterNodeDefinition(BrightnessContrastAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return ColourBalanceAdjustmentRasterNodeApi.getParameters(this.handle);
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
        ColourBalanceAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return ColourBalanceAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ColourBalanceAdjustmentRasterNodeDefinition(ColourBalanceAdjustmentRasterNodeDefinitionApi.create(parameters));
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
        return CurvesAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
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
        return ExposureAdjustmentRasterNodeApi.getParameters(this.handle);
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
        ExposureAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return ExposureAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }
    
    static create(params) {
        return new ExposureAdjustmentRasterNodeDefinition(ExposureAdjustmentRasterNodeDefinitionApi.create(params));
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
        return HSLShiftAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
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
        return LevelsAdjustmentRasterNodeApi.getParameters(this.handle);
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
        LevelsAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return LevelsAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
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
        return new LevelsAdjustmentRasterNodeDefinition(LevelsAdjustmentRasterNodeDefinitionApi.create(params, colourSpace));
    }

    static createDefault(document) {
        return new LevelsAdjustmentRasterNodeDefinition(LevelsAdjustmentRasterNodeDefinitionApi.createDefault(document.handle));
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
        return NormalsAdjustmentRasterNodeApi.getParameters(this.handle);
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
        NormalsAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return NormalsAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new NormalsAdjustmentRasterNodeDefinition(NormalsAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new NormalsAdjustmentRasterNodeDefinition(NormalsAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return PosteriseAdjustmentRasterNodeApi.getParameters(this.handle);
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
        PosteriseAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return PosteriseAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new PosteriseAdjustmentRasterNodeDefinition(PosteriseAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new PosteriseAdjustmentRasterNodeDefinition(PosteriseAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return RecolourAdjustmentRasterNodeApi.getParameters(this.handle);
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
        RecolourAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return RecolourAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new RecolourAdjustmentRasterNodeDefinition(RecolourAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new RecolourAdjustmentRasterNodeDefinition(RecolourAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return SelectiveColourAdjustmentRasterNodeApi.getParameters(this.handle);
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
        SelectiveColourAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return SelectiveColourAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new SelectiveColourAdjustmentRasterNodeDefinition(SelectiveColourAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new SelectiveColourAdjustmentRasterNodeDefinition(SelectiveColourAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return ShadowsHighlightsAdjustmentRasterNodeApi.getParameters(this.handle);
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
        ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ShadowsHighlightsAdjustmentRasterNodeDefinition(ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new ShadowsHighlightsAdjustmentRasterNodeDefinition(ShadowsHighlightsAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return SplitToningAdjustmentRasterNodeApi.getParameters(this.handle);
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
        SplitToningAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return SplitToningAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new SplitToningAdjustmentRasterNodeDefinition(SplitToningAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new SplitToningAdjustmentRasterNodeDefinition(SplitToningAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return ThresholdAdjustmentRasterNodeApi.getParameters(this.handle);
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
        ThresholdAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return ThresholdAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ThresholdAdjustmentRasterNodeDefinition(ThresholdAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new ThresholdAdjustmentRasterNodeDefinition(ThresholdAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return ToneCompressionAdjustmentRasterNodeApi.getParameters(this.handle);
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
        ToneCompressionAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return ToneCompressionAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ToneCompressionAdjustmentRasterNodeDefinition(ToneCompressionAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new ToneCompressionAdjustmentRasterNodeDefinition(ToneCompressionAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return ToneStretchAdjustmentRasterNodeApi.getParameters(this.handle);
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
        ToneStretchAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return ToneStretchAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ToneStretchAdjustmentRasterNodeDefinition(ToneStretchAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new ToneStretchAdjustmentRasterNodeDefinition(ToneStretchAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return VibranceAdjustmentRasterNodeApi.getParameters(this.handle);
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
        VibranceAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return VibranceAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new VibranceAdjustmentRasterNodeDefinition(VibranceAdjustmentRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new VibranceAdjustmentRasterNodeDefinition(VibranceAdjustmentRasterNodeDefinitionApi.createDefault());
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
        return WhiteBalanceAdjustmentRasterNodeApi.getParameters(this.handle);
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
        WhiteBalanceAdjustmentRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return WhiteBalanceAdjustmentRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new WhiteBalanceAdjustmentRasterNodeDefinition(WhiteBalanceAdjustmentRasterNodeDefinitionApi.create(parameters));
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
        return AddNoiseFilterRasterNodeApi.getParameters(this.handle);
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
        AddNoiseFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return AddNoiseFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new AddNoiseFilterRasterNodeDefinition(AddNoiseFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new AddNoiseFilterRasterNodeDefinition(AddNoiseFilterRasterNodeDefinitionApi.createDefault());
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
        return BilateralBlurFilterRasterNodeApi.getParameters(this.handle);
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
        BilateralBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return BilateralBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(params) {
        return new BilateralBlurFilterRasterNodeDefinition(BilateralBlurFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new BilateralBlurFilterRasterNodeDefinition(BilateralBlurFilterRasterNodeDefinitionApi.createDefault());
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
        return BoxBlurFilterRasterNodeApi.getParameters(this.handle);
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
        BoxBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return BoxBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(params) {
        return new BoxBlurFilterRasterNodeDefinition(BoxBlurFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new BoxBlurFilterRasterNodeDefinition(BoxBlurFilterRasterNodeDefinitionApi.createDefault());
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
        return ClarityFilterRasterNodeApi.getParameters(this.handle);
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
        ClarityFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return ClarityFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new ClarityFilterRasterNodeDefinition(ClarityFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new ClarityFilterRasterNodeDefinition(ClarityFilterRasterNodeDefinitionApi.createDefault());
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
        return DefringeFilterRasterNodeApi.getParameters(this.handle);
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
        DefringeFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return DefringeFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new DefringeFilterRasterNodeDefinition(DefringeFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new DefringeFilterRasterNodeDefinition(DefringeFilterRasterNodeDefinitionApi.createDefault());
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
        return DenoiseFilterRasterNodeApi.getParameters(this.handle);
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
        DenoiseFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return DenoiseFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new DenoiseFilterRasterNodeDefinition(DenoiseFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new DenoiseFilterRasterNodeDefinition(DenoiseFilterRasterNodeDefinitionApi.createDefault());
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
        return DiffuseFilterRasterNodeApi.getParameters(this.handle);
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
        DiffuseFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return DiffuseFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new DiffuseFilterRasterNodeDefinition(DiffuseFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new DiffuseFilterRasterNodeDefinition(DiffuseFilterRasterNodeDefinitionApi.createDefault());
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
        return DiffuseGlowFilterRasterNodeApi.getParameters(this.handle);
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
        DiffuseGlowFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }
    
    get parameters() {
        return DiffuseGlowFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new DiffuseGlowFilterRasterNodeDefinition(DiffuseGlowFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new DiffuseGlowFilterRasterNodeDefinition(DiffuseGlowFilterRasterNodeDefinitionApi.createDefault());
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
        return DustAndScratchFilterRasterNodeApi.getParameters(this.handle);
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
        DustAndScratchFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return DustAndScratchFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new DustAndScratchFilterRasterNodeDefinition(DustAndScratchFilterRasterNodeDefinitionApi.create(parameters));
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
        return FieldBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
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
        return GaussianBlurFilterRasterNodeApi.getParameters(this.handle);
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
        GaussianBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return GaussianBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(parameters) {
        return new GaussianBlurFilterRasterNodeDefinition(GaussianBlurFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new GaussianBlurFilterRasterNodeDefinition(GaussianBlurFilterRasterNodeDefinitionApi.createDefault());
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
        return ShadowsHighlightsFilterRasterNodeApi.getParameters(this.handle);
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
        ShadowsHighlightsFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return ShadowsHighlightsFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(parameters) {
        return new ShadowsHighlightsFilterRasterNodeDefinition(ShadowsHighlightsFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new ShadowsHighlightsFilterRasterNodeDefinition(ShadowsHighlightsFilterRasterNodeDefinitionApi.createDefault());
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
        return HighPassFilterRasterNodeApi.getParameters(this.handle);
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
        HighPassFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return HighPassFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new HighPassFilterRasterNodeDefinition(HighPassFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new HighPassFilterRasterNodeDefinition(HighPassFilterRasterNodeDefinitionApi.createDefault());
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
        return LensBlurFilterRasterNodeApi.getParameters(this.handle);
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
        LensBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return LensBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new LensBlurFilterRasterNodeDefinition(LensBlurFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new LensBlurFilterRasterNodeDefinition(LensBlurFilterRasterNodeDefinitionApi.createDefault());
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
        return BloomFilterRasterNodeApi.getParameters(this.handle);
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
        BloomFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return BloomFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new BloomFilterRasterNodeDefinition(BloomFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new BloomFilterRasterNodeDefinition(BloomFilterRasterNodeDefinitionApi.createDefault());
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
        return PixelateFilterRasterNodeApi.getParameters(this.handle);
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
        PixelateFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return PixelateFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }
    
    static create(params) {
        return new PixelateFilterRasterNodeDefinition(PixelateFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new PixelateFilterRasterNodeDefinition(PixelateFilterRasterNodeDefinitionApi.createDefault());
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
        return HalftoneFilterRasterNodeApi.getParameters(this.handle);
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
        HalftoneFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return HalftoneFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    static create(params) {
        return new HalftoneFilterRasterNodeDefinition(HalftoneFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new HalftoneFilterRasterNodeDefinition(HalftoneFilterRasterNodeDefinitionApi.createDefault());
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
        return MaximumBlurFilterRasterNodeApi.getParameters(this.handle);
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
        MaximumBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }

    get parameters() {
        return MaximumBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new MaximumBlurFilterRasterNodeDefinition(MaximumBlurFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new MaximumBlurFilterRasterNodeDefinition(MaximumBlurFilterRasterNodeDefinitionApi.createDefault());
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
        return MedianBlurFilterRasterNodeApi.getParameters(this.handle);
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
        MedianBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }
    
    get parameters() {
        return MedianBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new MedianBlurFilterRasterNodeDefinition(MedianBlurFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new MedianBlurFilterRasterNodeDefinition(MedianBlurFilterRasterNodeDefinitionApi.createDefault());
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
        return MinimumBlurFilterRasterNodeApi.getParameters(this.handle);
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
        MinimumBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }
    
    get parameters() {
        return MinimumBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new MinimumBlurFilterRasterNodeDefinition(MinimumBlurFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new MinimumBlurFilterRasterNodeDefinition(MinimumBlurFilterRasterNodeDefinitionApi.createDefault());
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
        return MotionBlurFilterRasterNodeApi.getParameters(this.handle);
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
        MotionBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, params);
    }
    
    get parameters() {
        return MotionBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(params) {
        return new MotionBlurFilterRasterNodeDefinition(MotionBlurFilterRasterNodeDefinitionApi.create(params));
    }

    static createDefault() {
        return new MotionBlurFilterRasterNodeDefinition(MotionBlurFilterRasterNodeDefinitionApi.createDefault());
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
        return PinchPunchFilterRasterNodeApi.getParameters(this.handle);
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
        PinchPunchFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return PinchPunchFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new PinchPunchFilterRasterNodeDefinition(PinchPunchFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault(document) {
        return new PinchPunchFilterRasterNodeDefinition(PinchPunchFilterRasterNodeDefinitionApi.createDefault(document.handle));
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
        return RadialBlurFilterRasterNodeApi.getParameters(this.handle);
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
        RadialBlurFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }
    
    get parameters() {
        return RadialBlurFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }
    
    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new RadialBlurFilterRasterNodeDefinition(RadialBlurFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault(document) {
        return new RadialBlurFilterRasterNodeDefinition(RadialBlurFilterRasterNodeDefinitionApi.createDefault(document.handle));
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
        return RippleFilterRasterNodeApi.getParameters(this.handle);
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
        RippleFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return RippleFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new RippleFilterRasterNodeDefinition(RippleFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault(document) {
        return new RippleFilterRasterNodeDefinition(RippleFilterRasterNodeDefinitionApi.createDefault(document.handle));
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
        return SphericalFilterRasterNodeApi.getParameters(this.handle);
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
        SphericalFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return SphericalFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new SphericalFilterRasterNodeDefinition(SphericalFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault(document) {
        return new SphericalFilterRasterNodeDefinition(SphericalFilterRasterNodeDefinitionApi.createDefault(document.handle));
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
        return TwirlFilterRasterNodeApi.getParameters(this.handle);
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
        TwirlFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return TwirlFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new TwirlFilterRasterNodeDefinition(TwirlFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault(document) {
        return new TwirlFilterRasterNodeDefinition(TwirlFilterRasterNodeDefinitionApi.createDefault(document.handle));
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
        return UnsharpMaskFilterRasterNodeApi.getParameters(this.handle);
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
        UnsharpMaskFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return UnsharpMaskFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new UnsharpMaskFilterRasterNodeDefinition(UnsharpMaskFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new UnsharpMaskFilterRasterNodeDefinition(UnsharpMaskFilterRasterNodeDefinitionApi.createDefault());
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
        return VignetteFilterRasterNodeApi.getParameters(this.handle);
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
        VignetteFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return VignetteFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new VignetteFilterRasterNodeDefinition(VignetteFilterRasterNodeDefinitionApi.create(parameters));
    }

    static createDefault() {
        return new VignetteFilterRasterNodeDefinition(VignetteFilterRasterNodeDefinitionApi.createDefault());
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
        return VoronoiFilterRasterNodeApi.getParameters(this.handle);
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
        VoronoiFilterRasterNodeDefinitionApi.setParameters(this.handle, parameters);
    }

    get parameters() {
        return VoronoiFilterRasterNodeDefinitionApi.getParameters(this.handle);
    }

    setParameters(parameters) {
        this.parameters = parameters;
        return this;
    }

    static create(parameters) {
        return new VoronoiFilterRasterNodeDefinition(VoronoiFilterRasterNodeDefinitionApi.create(parameters));
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

    get artboardEnabled() {
        return this.artboardInterface.enabled;
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

    set artboardEnabled(value) {
        return this.document.setArtboardEnabled(value, this);
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
		const range = this.storyInterface.story.all;
		const subSel = SelectionsModule.TextSelection.from(range);
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

    get imageFileSize() {
        return this.imageResourceInterface.imageFileSize;
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

    get artboardEnabled() {
        return this.artboardInterface.enabled;
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

    set artboardEnabled(value) {
        return this.document.setArtboardEnabled(value, this);
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
    
    static create(curve, brushFill, lineStyle, lineFill, transparencyFill) {
        return new PolyCurveNodeDefinition(PolyCurveNodeDefinitionApi.create(curve.handle, brushFill.handle, lineStyle.handle, lineFill.handle, transparencyFill.handle));
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

    get artboardEnabled() {
        return this.artboardInterface.enabled;
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

    set artboardEnabled(value) {
        return this.document.setArtboardEnabled(value, this);
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
module.exports.RasterNode = RasterNode;
module.exports.RasterNodeDefinition = RasterNodeDefinition;
module.exports.PatternRasterNode = PatternRasterNode;
module.exports.PatternRasterNodeDefinition = PatternRasterNodeDefinition;
module.exports.ContainerNode = ContainerNode;
module.exports.ContainerNodeDefinition = ContainerNodeDefinition;
module.exports.ShapeNode = ShapeNode;
module.exports.ShapeNodeDefinition = ShapeNodeDefinition;
module.exports.ShapePathTextNode = ShapePathTextNode;
module.exports.ShapeTextNode = ShapeTextNode;
module.exports.SpreadNode = SpreadNode;
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
module.exports.createTypedNode = createTypedNode;
module.exports.AddNoiseType = AddNoiseType;
module.exports.ColourSpaceType = ColourSpaceType;
module.exports.DepthOfFieldMode = DepthOfFieldMode;
module.exports.PageBoundingBoxType = PageBoundingBoxType;
module.exports.RasterExtendType = RasterExtendType;
module.exports.RasterFormat = RasterFormat;
module.exports.RasterResamplerType = RasterResamplerType;
module.exports.ShadowsHighlightsVersion = ShadowsHighlightsVersion;
module.exports.SelectiveColour = SelectiveColour;
module.exports.TonalRangeType = TonalRangeType;
module.exports.ToneCompressionMethod = ToneCompressionMethod;
module.exports.ToneStretchMethod = ToneStretchMethod;
module.exports.BloomMethod = BloomMethod;
module.exports.HalftoneScreenType = HalftoneScreenType;
module.exports.HalftoneDotType = HalftoneDotType;
module.exports.NodeChildType = NodeChildType;
module.exports.NodeCast = NodeCast;
module.exports.getNodeSiblings = getNodeSiblings;
module.exports.getNodeChildren = getNodeChildren;
module.exports.getNodesRecursive = getNodesRecursive;
module.exports.getNodeChildrenRecursive = getNodeChildrenRecursive;

module.exports.NodeChildren = NodeChildren;
module.exports.NodeChildrenOnly = NodeChildrenOnly;
