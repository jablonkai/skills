'use strict';
const {app} = require('/application');
const {GaussianBlurFilterRasterNodeDefinition, ExposureAdjustmentRasterNodeDefinition, createTypedNode, Node, NodeChildType, AddNoiseType} = require('/nodes');
const {LevelsAdjustmentRasterNodeDefinition, BilateralBlurFilterRasterNodeDefinition, BoxBlurFilterRasterNodeDefinition, MedianBlurFilterRasterNodeDefinition} = require("/nodes");
const {DiffuseGlowFilterRasterNodeDefinition, LensBlurFilterRasterNodeDefinition, MaximumBlurFilterRasterNodeDefinition, MinimumBlurFilterRasterNodeDefinition,
    MotionBlurFilterRasterNodeDefinition, RadialBlurFilterRasterNodeDefinition, BrightnessContrastAdjustmentRasterNodeDefinition,
    ShadowsHighlightsAdjustmentRasterNodeDefinition, BlackAndWhiteAdjustmentRasterNodeDefinition, RecolourAdjustmentRasterNodeDefinition,
    PosteriseAdjustmentRasterNodeDefinition, SplitToningAdjustmentRasterNodeDefinition, InvertAdjustmentRasterNodeDefinition,
    ThresholdAdjustmentRasterNodeDefinition, ClarityFilterRasterNodeDefinition, UnsharpMaskFilterRasterNodeDefinition,
    HighPassFilterRasterNodeDefinition, DenoiseFilterRasterNodeDefinition, DiffuseFilterRasterNodeDefinition, DustAndScratchFilterRasterNodeDefinition,
    AddNoiseFilterRasterNodeDefinition, RippleFilterRasterNodeDefinition, TwirlFilterRasterNodeDefinition, SphericalFilterRasterNodeDefinition,
    PinchPunchFilterRasterNodeDefinition, PixelateFilterRasterNodeDefinition} = require("/nodes");
const {BilateralBlurFilterParameters, BoxBlurFilterParameters, DiffuseGlowFilterParameters, FieldBlurItemParameters, GaussianBlurFilterParameters, LensBlurFilterParameters,
    MaximumBlurFilterParameters, MedianBlurFilterParameters, MinimumBlurFilterParameters, MotionBlurFilterParameters, RadialBlurFilterParameters,
    LevelsAdjustmentChannelParameters, LevelsAdjustmentParameters, ExposureAdjustmentParameters, BrightnessContrastAdjustmentParameters,
    ShadowsHighlightsAdjustmentParameters, BlackAndWhiteAdjustmentParameters, RecolourAdjustmentParameters, PosteriseAdjustmentParameters,
    SplitToningAdjustmentParameters, ThresholdAdjustmentParameters, ClarityFilterParameters, UnsharpMaskFilterParameters,
    HighPassFilterParameters, DenoiseFilterParameters, DiffuseFilterParameters, DustAndScratchFilterParameters, AddNoiseFilterParameters,
    RippleFilterParameters, TwirlFilterParameters, SphericalFilterParameters, PinchPunchFilterParameters, PixelateFilterParameters} = require("/nodes");
const {WhiteBalanceAdjustmentParameters, WhiteBalanceAdjustmentRasterNodeDefinition} = require("/nodes");
const {VibranceAdjustmentParameters, VibranceAdjustmentRasterNodeDefinition} = require("/nodes");
const {NormalsAdjustmentParameters, NormalsAdjustmentRasterNodeDefinition} = require("/nodes");
const {TonalRangeType, ColourBalanceValues, ColourBalanceAdjustmentParameters, ColourBalanceAdjustmentRasterNodeDefinition} = require("/nodes");
const {CurvesAdjustmentParameters, CurvesAdjustmentRasterNodeDefinition} = require("/nodes");
const {VignetteFilterParameters, VignetteFilterRasterNodeDefinition} = require("/nodes");
const {DefringeFilterParameters, DefringeFilterRasterNodeDefinition} = require("/nodes");
const {VoronoiFilterParameters, VoronoiFilterRasterNodeDefinition} = require("/nodes");
const {EllipticalDepthOfFieldParameters, TiltShiftDepthOfFieldParameters, DepthOfFieldFilterParameters, DepthOfFieldFilterRasterNodeDefinition, DepthOfFieldMode} = require("/nodes");
const {SelectiveColour, SelectiveColourWeights, SelectiveColourAdjustmentParameters, SelectiveColourAdjustmentRasterNodeDefinition} = require("/nodes");
const {HSLShiftAdjustmentChannelParameters, HSLShiftAdjustmentColourRange, HSLShiftAdjustmentParameters, HSLShiftAdjustmentRasterNodeDefinition} = require("/nodes");
const {FieldBlurFilterParameters, FieldBlurFilterRasterNode, FieldBlurFilterRasterNodeDefinition} = require("/nodes");
const {ToneCompressionMethod, ToneCompressionAdjustmentParameters, ToneCompressionAdjustmentRasterNodeDefinition} = require("/nodes");
const {ToneStretchMethod, ToneStretchAdjustmentParameters, ToneStretchAdjustmentRasterNodeDefinition} = require("/nodes");
const {BloomMethod, BloomFilterParameters, BloomFilterRasterNodeDefinition} = require("/nodes");
const {HalftoneScreenType, HalftoneDotType, HalftoneFilterParameters, HalftoneFilterRasterNodeDefinition} = require("/nodes");
const {ShadowsHighlightsFilterRasterNodeDefinition, ShadowsHighlightsVersion} = require("/nodes");
const {ShadowsHighlightsFilterParameters} = require("/nodes");
const {PatternRasterNodeDefinition} = require("/nodes");
const {Bitmap} = require("/rasterobject");
const {Transform} = require("/geometry");
const dommodule = require("affinity:dom");
const {DocumentCommand, AddChildNodesCommandBuilder, InsertionMode} = require("/commands");
const {Document, DocumentPromises} = require("/document.js");
const {Shape, ShapeType} = require("/shapes");
const {Fill, FillDescriptor} = require("/fills");
const {BlendMode} = require("affinity:common");
const {Rectangle, Spline, SplineProfile} = require("/geometry");
const {LineStyleDescriptor, LineType} = require("/lineStyle");
const {Colour, RGBA8, ColourSpaceType} = require("/colours");
const {ErrorCode} = require('affinity:common');
const {Selection} = require("/selections");
const {TestUtils} = require("/tests/testUtils");


function testExposureAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new ExposureAdjustmentParameters();
    params.exposure = 3.5;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = ExposureAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isExposureAdjustmentRasterNode);
        
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetExposureAdjustmentParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = ExposureAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addExposureAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isExposureAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = ExposureAdjustmentRasterNodeDefinition.create(params);
        acnBuilder.addExposureAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isExposureAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        
        doc.undo();
    }
    doc.close();
    console.log("testExposureAdjustmentRasterNode OK");
}


function testLevelsAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let lparam = new LevelsAdjustmentChannelParameters();
    lparam.blackLevel = 0.1;
    lparam.whiteLevel = 0.9;
    lparam.gamma = 0.7;
    lparam.outputBlackLevel = 0.4;
    lparam.outputWhiteLevel = 0.6;
    
    let param_bad = new LevelsAdjustmentChannelParameters();
    param_bad.blackLevel = -12;
    param_bad.whiteLevel = 123;
    param_bad.gamma = 23578;
    param_bad.outputBlackLevel = -12345;
    param_bad.outputWhiteLevel = 1436273;
    
    let param_bad2 = new LevelsAdjustmentChannelParameters();
    param_bad2.blackLevel = 12;
    param_bad2.whiteLevel = -123;
    param_bad2.gamma = -23578;
    param_bad2.outputBlackLevel = 12345;
    param_bad2.outputWhiteLevel = -1436273;
    
    let params = new LevelsAdjustmentParameters();
    params.masterParameters.blackLevel = 0.2;
    params.masterParameters.whiteLevel = 0.8;
    params.masterParameters.gamma = 1.2;
    params.masterParameters.outputBlackLevel = 0.3;
    params.masterParameters.outputWhiteLevel = 0.7;
    
    params.channelParameters[0] = param_bad;
    params.channelParameters[1] = param_bad2;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = LevelsAdjustmentRasterNodeDefinition.createDefault(doc);
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isLevelsAdjustmentRasterNode);
        
        
        let selection = Selection.create(doc, newNode);
        let updateCS = DocumentCommand.createSetLevelsAdjustmentColourSpace(selection, doc.colourProfile.colourSpace);
        let updateCmd = DocumentCommand.createSetLevelsAdjustmentParameters(selection, params);
        
        result = doc.executeCommand(updateCS);
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.blackLevel, params.masterParameters.blackLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.whiteLevel, params.masterParameters.whiteLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.gamma, params.masterParameters.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.outputBlackLevel, params.masterParameters.outputBlackLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.outputWhiteLevel, params.masterParameters.outputWhiteLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].blackLevel, 0.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].whiteLevel, 1.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].gamma, 2.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].outputBlackLevel, 0.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].outputWhiteLevel, 1.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].blackLevel, 1.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].whiteLevel, 0.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].gamma, 0.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].outputBlackLevel, 1.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].outputWhiteLevel, 0.0));
        console.assert(newNode.colourSpace.value == doc.colourProfile.colourSpace.value);
        
        doc.undo();
        doc.undo();
        doc.undo();
    }
    
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = LevelsAdjustmentRasterNodeDefinition.createDefault(doc);
        def.parameters = params;
        
        acnBuilder.addLevelsAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isLevelsAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.blackLevel, params.masterParameters.blackLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.whiteLevel, params.masterParameters.whiteLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.gamma, params.masterParameters.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.outputBlackLevel, params.masterParameters.outputBlackLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.outputWhiteLevel, params.masterParameters.outputWhiteLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].blackLevel, 0.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].whiteLevel, 1.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].gamma, 2.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].outputBlackLevel, 0.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[0].outputWhiteLevel, 1.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].blackLevel, 1.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].whiteLevel, 0.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].gamma, 0.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].outputBlackLevel, 1.0));
        console.assert(TestUtils.floatEqual(newNode.parameters.channelParameters[1].outputWhiteLevel, 0.0));
        console.assert(newNode.colourSpace.value == doc.colourProfile.colourSpace.value);
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = LevelsAdjustmentRasterNodeDefinition.create(params, doc.colourProfile.colourSpace);
        acnBuilder.addLevelsAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isLevelsAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.blackLevel, params.masterParameters.blackLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.whiteLevel, params.masterParameters.whiteLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.gamma, params.masterParameters.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.outputBlackLevel, params.masterParameters.outputBlackLevel));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.outputWhiteLevel, params.masterParameters.outputWhiteLevel));
        console.assert(newNode.colourSpace.value == doc.colourProfile.colourSpace.value);
        
        doc.undo();
    }
    doc.close();
    console.log("testLevelsAdjustmentRasterNode OK");
}


function testCurvesAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let curveSpline = Spline.createFromProfile(SplineProfile.Linear);
    let p1 = {x: 0.5, y: 0.7};
    let p2 = {x: 0.4, y: 0.8};
    curveSpline.insertPoint(p1);
    curveSpline.insertPoint(p2);
    let pCount = curveSpline.pointCount;
    console.assert(pCount === 4);
    let newPoint = curveSpline.getPoint(2);
    console.assert(TestUtils.floatEqual(newPoint.y, 0.7));
    curveSpline.removePoint(2);
    pCount = curveSpline.pointCount;
    console.assert(pCount === 3);
    newPoint.y = 0.4;
    curveSpline.insertPoint(newPoint);
    
    let cap = CurvesAdjustmentParameters.create();
    cap.setChannelSpline(1, curveSpline);
    
    curveSpline.removePoint(1);
    curveSpline.removePoint(2);
    let p3 = {x: 0.3, y: 0.6};
    let p4 = {x: 0.7, y: 0.4};
    curveSpline.insertPoint(p3);
    curveSpline.insertPoint(p4);
    cap.masterSpline = curveSpline;
    cap.min = -1.1;
    cap.max = 1.4;
    
    let def = CurvesAdjustmentRasterNodeDefinition.createDefault(doc);
    def.parameters = cap;
    
    let acnBuilder = AddChildNodesCommandBuilder.create();
    
    acnBuilder.addCurvesAdjustmentRasterNode(def);
    let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
    let result = doc.executeCommand(anCommand);
    
    let newNode = doc.layers.first;
    console.assert(newNode.isCurvesAdjustmentRasterNode);
    
    let capRead = newNode.parameters;
    let ccpRead = capRead.masterSpline;
    
    console.assert(TestUtils.floatEqual(ccpRead.getPoint(1).y, 0.6));
    
    cap.setChannelSpline(2, curveSpline);
    
    let selection = Selection.create(doc, newNode);
    
    let updateCmd = DocumentCommand.createSetCurvesAdjustmentParameters(selection, cap);
    result = doc.executeCommand(updateCmd);
 
    newNode = doc.layers.first;
    capRead = newNode.parameters;
    ccpRead = capRead.getChannelSpline(2);
    
    console.assert(TestUtils.floatEqual(ccpRead.getPoint(2).y, 0.4));
    
    doc.undo();
    doc.undo();
    
    let def2 = CurvesAdjustmentRasterNodeDefinition.create(capRead, ColourSpaceType.RGB);
    acnBuilder.addCurvesAdjustmentRasterNode(def2);
    let anCommand2 = acnBuilder.createCommand(false, NodeChildType.Main);
    result = doc.executeCommand(anCommand2);
 
    newNode = doc.layers.first;
    capRead = newNode.parameters;
    ccpRead = capRead.getChannelSpline(2);
    console.assert(TestUtils.floatEqual(ccpRead.getPoint(2).y, 0.4));
    
    doc.undo();
    
    doc.close();
    console.log("testCurvesAdjustmentRasterNode OK");
}


function testGaussianBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let parameters = new GaussianBlurFilterParameters();
    parameters.radius = 2.7;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = GaussianBlurFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isGaussianBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetGaussianBlurFilterParameters(selection, parameters);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(newNode.isGaussianBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, parameters.radius));
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = GaussianBlurFilterRasterNodeDefinition.createDefault();
        def.parameters = parameters;
        acnBuilder.addGaussianBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        
        console.assert(newNode.isGaussianBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, parameters.radius));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = GaussianBlurFilterRasterNodeDefinition.create(parameters);
        acnBuilder.addGaussianBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isGaussianBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, parameters.radius));
        
        doc.undo();
    }
    doc.close();
    console.log("testGaussianBlurFilterRasterNode OK");
}


function testMedianBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new MedianBlurFilterParameters();
    params.radius = 2.7;
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MedianBlurFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isMedianBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetMedianBlurFilterParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MedianBlurFilterRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addMedianBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isMedianBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MedianBlurFilterRasterNodeDefinition.create(params);
        acnBuilder.addMedianBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isMedianBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        
        doc.undo();
    }
    doc.close();
    console.log("testMedianBlurFilterRasterNode OK");
}


function testBoxBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new BoxBlurFilterParameters();
    params.radius = 2.7;
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = BoxBlurFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isBoxBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetBoxBlurFilterParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = BoxBlurFilterRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addBoxBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isBoxBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = BoxBlurFilterRasterNodeDefinition.create(params);
        acnBuilder.addBoxBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isBoxBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        
        doc.undo();
    }
    doc.close();
    console.log("testBoxBlurFilterRasterNode OK");
}


function testBilateralBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new BilateralBlurFilterParameters();
    params.radius = 2.7;
    params.tolerance = 0.23;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = BilateralBlurFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isBilateralBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetBilateralBlurFilterParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = BilateralBlurFilterRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addBilateralBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isBilateralBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = BilateralBlurFilterRasterNodeDefinition.create(params);
        acnBuilder.addBilateralBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isBilateralBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        
        doc.undo();
    }
    doc.close();
    console.log("testBilateralBlurFilterRasterNode OK");
}


function testDiffuseGlowFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new DiffuseGlowFilterParameters();
    params.radius = 13.7;
    params.intensity = 0.66;
    params.threshold = 0.42;
    params.opacity = 0.51;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = DiffuseGlowFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isDiffuseGlowFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetDiffuseGlowFilterParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.opacity, params.opacity));
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = DiffuseGlowFilterRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addDiffuseGlowFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isDiffuseGlowFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.opacity, params.opacity));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = DiffuseGlowFilterRasterNodeDefinition.create(params);
        acnBuilder.addDiffuseGlowFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isDiffuseGlowFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.opacity, params.opacity));
        
        doc.undo();
    }
    doc.close();
    console.log("testDiffuseGlowFilterRasterNode OK");
}


function testFieldBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
        
    let itemParams = new FieldBlurItemParameters;
    itemParams.position = {x: 100, y: 200};
    itemParams.level = 0.83;
    itemParams.power = 3.0;
    
    let fieldParams = FieldBlurFilterParameters.create();
    fieldParams.addBlurItem(itemParams);
    console.assert(fieldParams.blurItemCount === 1);
    fieldParams.globalRadius = 23.4;
    
    
    let def = FieldBlurFilterRasterNodeDefinition.createDefault(doc);
    def.parameters = fieldParams;
    
    let acnBuilder = AddChildNodesCommandBuilder.create();
    
    acnBuilder.addNode(def);
    let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
    let result = doc.executeCommand(anCommand);
    
    let newNode = doc.layers.first;
    
    console.assert(newNode.isFieldBlurFilterRasterNode);
   
    let fieldParamsRead = newNode.parameters;
    let itemParamsRead = fieldParamsRead.getBlurItem(0);
    console.assert(TestUtils.floatEqual(itemParamsRead.position.x, itemParams.position.x));
    console.assert(TestUtils.floatEqual(itemParamsRead.position.y, itemParams.position.y));
    console.assert(TestUtils.floatEqual(itemParamsRead.power, itemParams.power));
    console.assert(TestUtils.floatEqual(itemParamsRead.level, itemParams.level, 1e-2));
    
    itemParamsRead.position.x = 567.9;
    itemParamsRead.position.y = 987.6;
    itemParamsRead.level = 200;
    itemParamsRead.power = 500;
    fieldParamsRead.addBlurItem(itemParamsRead);
    
    let selection = Selection.create(doc, newNode);
    
    let updateCmd = DocumentCommand.createSetFieldBlurFilterParameters(selection, fieldParamsRead);
    result = doc.executeCommand(updateCmd);
    
    newNode = doc.layers.first;
    fieldParamsRead = newNode.parameters;
    itemParamsRead = fieldParamsRead.getBlurItem(1);
    
    console.assert(TestUtils.floatEqual(itemParamsRead.position.x, 567.9));
    console.assert(TestUtils.floatEqual(itemParamsRead.position.y, 987.6));
    console.assert(TestUtils.floatEqual(itemParamsRead.power, 5.0));
    console.assert(TestUtils.floatEqual(itemParamsRead.level, 1.0, 1e-2));
    
    doc.undo();
    doc.undo();
    
    let def2 = FieldBlurFilterRasterNodeDefinition.create(fieldParamsRead);
    acnBuilder.addFieldBlurFilterRasterNode(def2);
    let anCommand2 = acnBuilder.createCommand(false, NodeChildType.Main);
    result = doc.executeCommand(anCommand2);
    
    newNode = doc.layers.first;
    fieldParamsRead = newNode.parameters;
    itemParamsRead = fieldParamsRead.getBlurItem(1);
    
    console.assert(TestUtils.floatEqual(itemParamsRead.position.x, 567.9));
    console.assert(TestUtils.floatEqual(itemParamsRead.position.y, 987.6));
    console.assert(TestUtils.floatEqual(itemParamsRead.power, 5.0));
    console.assert(TestUtils.floatEqual(itemParamsRead.level, 1.0, 1e-2));
    
    doc.undo();
    
    doc.close();
    console.log("testFieldBlueFilterRasterNode OK");
}


function testEllipticalDepthOfFieldFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let ellipticalParams = new EllipticalDepthOfFieldParameters;
    ellipticalParams.position = {x: 150, y: 250};
    ellipticalParams.radiusX = 80;
    ellipticalParams.radiusY = 60;
    ellipticalParams.inFocus = 0.3;
    ellipticalParams.rotation = 1.2;

    let dofParams = DepthOfFieldFilterParameters.create();
    dofParams.radius = 12.5;
    dofParams.vibrance = 0.4;
    dofParams.clarity = 100;
    dofParams.ellipticalParams = ellipticalParams;

    console.assert(dofParams.mode.value === DepthOfFieldMode.Elliptical.value);

    let def = DepthOfFieldFilterRasterNodeDefinition.createDefault(doc);
    def.parameters = dofParams;

    let acnBuilder = AddChildNodesCommandBuilder.create();
    acnBuilder.addNode(def);
    let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
    let result = doc.executeCommand(anCommand);

    let newNode = doc.layers.first;
    console.assert(newNode.isDepthOfFieldFilterRasterNode);

    let readParams = newNode.parameters;
    console.assert(readParams.mode.value === DepthOfFieldMode.Elliptical.value);
    console.assert(TestUtils.floatEqual(readParams.radius, 12.5));
    console.assert(TestUtils.floatEqual(readParams.vibrance, 0.4));
    console.assert(TestUtils.floatEqual(readParams.clarity, 100));

    let readElliptical = readParams.ellipticalParams;
    console.assert(TestUtils.floatEqual(readElliptical.position.x, 150));
    console.assert(TestUtils.floatEqual(readElliptical.position.y, 250));
    console.assert(TestUtils.floatEqual(readElliptical.radiusX, 80));
    console.assert(TestUtils.floatEqual(readElliptical.radiusY, 60));
    console.assert(TestUtils.floatEqual(readElliptical.inFocus, 0.3));
    console.assert(TestUtils.floatEqual(readElliptical.rotation, 1.2));

    // Update via set command
    readElliptical.radiusX = 120;
    readElliptical.radiusY = 90;
    readParams.ellipticalParams = readElliptical;
    readParams.radius = 20.0;

    let selection = Selection.create(doc, newNode);
    let updateCmd = DocumentCommand.createSetDepthOfFieldFilterParameters(selection, readParams);
    result = doc.executeCommand(updateCmd);

    newNode = doc.layers.first;
    readParams = newNode.parameters;
    readElliptical = readParams.ellipticalParams;
    console.assert(TestUtils.floatEqual(readParams.radius, 20.0));
    console.assert(TestUtils.floatEqual(readElliptical.radiusX, 120));
    console.assert(TestUtils.floatEqual(readElliptical.radiusY, 90));

    doc.undo();
    doc.undo();

    // Create via DepthOfFieldFilterRasterNodeDefinition.create
    let def2 = DepthOfFieldFilterRasterNodeDefinition.create(readParams);
    acnBuilder.addDepthOfFieldFilterRasterNode(def2);
    let anCommand2 = acnBuilder.createCommand(false, NodeChildType.Main);
    result = doc.executeCommand(anCommand2);

    newNode = doc.layers.first;
    console.assert(newNode.isDepthOfFieldFilterRasterNode);
    readParams = newNode.parameters;
    console.assert(TestUtils.floatEqual(readParams.radius, 20.0));

    doc.undo();
    doc.close();
    console.log("testEllipticalDepthOfFieldFilterRasterNode OK");
}


function testTiltShiftDepthOfFieldFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let tiltShiftParams = new TiltShiftDepthOfFieldParameters;
    tiltShiftParams.position = {x: 200, y: 300};
    tiltShiftParams.top = -50;
    tiltShiftParams.inFocusTop = -25;
    tiltShiftParams.inFocusBottom = 150;
    tiltShiftParams.bottom = 300;
    tiltShiftParams.rotation = 0.5;

    let dofParams = DepthOfFieldFilterParameters.create();
    dofParams.radius = 8.0;
    dofParams.vibrance = 0.2;
    dofParams.clarity = 40;
    dofParams.tiltShiftParams = tiltShiftParams;

    console.assert(dofParams.mode.value === DepthOfFieldMode.TiltShift.value);

    let def = DepthOfFieldFilterRasterNodeDefinition.createDefault(doc);
    def.parameters = dofParams;

    let acnBuilder = AddChildNodesCommandBuilder.create();
    acnBuilder.addNode(def);
    let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
    let result = doc.executeCommand(anCommand);

    let newNode = doc.layers.first;
    console.assert(newNode.isDepthOfFieldFilterRasterNode);

    let readParams = newNode.parameters;
    console.assert(readParams.mode.value === DepthOfFieldMode.TiltShift.value);
    console.assert(TestUtils.floatEqual(readParams.radius, 8.0));
    console.assert(TestUtils.floatEqual(readParams.vibrance, 0.2));
    console.assert(TestUtils.floatEqual(readParams.clarity, 40));
    let readTiltShift = readParams.tiltShiftParams;
    console.assert(TestUtils.floatEqual(readTiltShift.position.x, 200));
    console.assert(TestUtils.floatEqual(readTiltShift.position.y, 300));
    console.assert(TestUtils.floatEqual(readTiltShift.top, -50));
    console.assert(TestUtils.floatEqual(readTiltShift.inFocusTop, -25));
    console.assert(TestUtils.floatEqual(readTiltShift.inFocusBottom, 150));
    console.assert(TestUtils.floatEqual(readTiltShift.bottom, 300));
    console.assert(TestUtils.floatEqual(readTiltShift.rotation, 0.5));

    // Update via set command
    readTiltShift.top = -30;
    readTiltShift.bottom = 170;
    readParams.tiltShiftParams = readTiltShift;
    readParams.radius = 15.0;

    let selection = Selection.create(doc, newNode);
    let updateCmd = DocumentCommand.createSetDepthOfFieldFilterParameters(selection, readParams);
    result = doc.executeCommand(updateCmd);
    newNode = doc.layers.first;
    readParams = newNode.parameters;
    readTiltShift = readParams.tiltShiftParams;
    console.assert(TestUtils.floatEqual(readParams.radius, 15.0));
    console.assert(TestUtils.floatEqual(readTiltShift.top, -30));
    console.assert(TestUtils.floatEqual(readTiltShift.bottom, 170));

    doc.undo();
    doc.undo();

    // Create via DepthOfFieldFilterRasterNodeDefinition.create
    let def2 = DepthOfFieldFilterRasterNodeDefinition.create(readParams);
    acnBuilder.addDepthOfFieldFilterRasterNode(def2);
    let anCommand2 = acnBuilder.createCommand(false, NodeChildType.Main);
    result = doc.executeCommand(anCommand2);

    newNode = doc.layers.first;
    console.assert(newNode.isDepthOfFieldFilterRasterNode);
    readParams = newNode.parameters;
    console.assert(TestUtils.floatEqual(readParams.radius, 15.0));

    doc.undo();
    doc.close();
    console.log("testTiltShiftDepthOfFieldFilterRasterNode OK");
}


function testLensBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new LensBlurFilterParameters();
    params.radius = 5.2;
    params.numberOfBlades = 7;
    params.bladeCurvature = 0.13;
    params.bloomThreshold = 0.07;
    params.bloomFactor = 7.4;
    params.bloomColour = 0.23;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = LensBlurFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isLensBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetLensBlurFilterParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.numberOfBlades === params.numberOfBlades);
        console.assert(TestUtils.floatEqual(newNode.parameters.bladeCurvature, params.bladeCurvature));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomThreshold, params.bloomThreshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomFactor, params.bloomFactor));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomColour, params.bloomColour));
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = LensBlurFilterRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addLensBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isLensBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.numberOfBlades === params.numberOfBlades);
        console.assert(TestUtils.floatEqual(newNode.parameters.bladeCurvature, params.bladeCurvature));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomThreshold, params.bloomThreshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomFactor, params.bloomFactor));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomColour, params.bloomColour));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = LensBlurFilterRasterNodeDefinition.create(params);
        acnBuilder.addLensBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isLensBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.numberOfBlades === params.numberOfBlades);
        console.assert(TestUtils.floatEqual(newNode.parameters.bladeCurvature, params.bladeCurvature));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomThreshold, params.bloomThreshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomFactor, params.bloomFactor));
        console.assert(TestUtils.floatEqual(newNode.parameters.bloomColour, params.bloomColour));
        
        doc.undo();
    }
    doc.close();
    console.log("testLensBlurFilterRasterNode OK");
}


function testMaximumBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new MaximumBlurFilterParameters();
    params.radius = 2.7;
    params.isCircular = true;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MaximumBlurFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isMaximumBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetMaximumBlurFilterParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isCircular === params.isCircular);
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MaximumBlurFilterRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addMaximumBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isMaximumBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isCircular === params.isCircular);
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MaximumBlurFilterRasterNodeDefinition.create(params);
        acnBuilder.addMaximumBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isMaximumBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isCircular === params.isCircular);
        
        doc.undo();
    }
    doc.close();
    console.log("testMaximumBlurFilterRasterNode OK");
}


function testMinimumBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new MinimumBlurFilterParameters();
    params.radius = 2.7;
    params.isCircular = true;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MinimumBlurFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isMinimumBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetMinimumBlurFilterParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isCircular === params.isCircular);
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MinimumBlurFilterRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addMinimumBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isMinimumBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isCircular === params.isCircular);
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MinimumBlurFilterRasterNodeDefinition.create(params);
        acnBuilder.addMinimumBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isMinimumBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isCircular === params.isCircular);
        
        doc.undo();
    }
    doc.close();
    console.log("testMinimumBlurFilterRasterNode OK");
}


function testMotionBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let params = new MotionBlurFilterParameters();
    params.radius = 2.7;
    params.angle = 45.6*Math.PI/180.0;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MotionBlurFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isMotionBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetMotionBlurFilterParameters(selection, params);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, params.angle));
        
        doc.undo();
        doc.undo();
    }
    
    {
        
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MotionBlurFilterRasterNodeDefinition.createDefault();
        def.parameters = params;
        
        acnBuilder.addMotionBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isMotionBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, params.angle));
        
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = MotionBlurFilterRasterNodeDefinition.create(params);
        acnBuilder.addMotionBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isMotionBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, params.angle));
        
        doc.undo();
    }
    doc.close();
    console.log("testMotionBlurFilterRasterNode OK");
}


function testRadialBlurFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    let angle = 34.5*Math.PI/180.0;
    let position = {x: 123.4, y: 567.8};
    let radialBlurParams = new RadialBlurFilterParameters();
    radialBlurParams.angle = angle;
    radialBlurParams.position = position;
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = RadialBlurFilterRasterNodeDefinition.createDefault(doc);
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isRadialBlurFilterRasterNode);
        
        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetRadialBlurFilterParameters(selection, radialBlurParams);
        
        result = doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, angle));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, position.x));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.y, position.y));
        
        doc.undo();
        doc.undo();
    }
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = RadialBlurFilterRasterNodeDefinition.createDefault(doc);
        def.parameters = radialBlurParams;
        
        acnBuilder.addRadialBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isRadialBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, angle));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, position.x));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.y, position.y));
        
        doc.undo();
    }
    
    {
        
        let acnBuilder = AddChildNodesCommandBuilder.create();
        
        let def = RadialBlurFilterRasterNodeDefinition.create(radialBlurParams);
        acnBuilder.addRadialBlurFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        const newNode = doc.layers.first;
        
        console.assert(newNode.isRadialBlurFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, angle));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, position.x));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.y, position.y));
        
        doc.undo();
    }
    doc.close();
    console.log("testRadialBlurFilterRasterNode OK");
}


function testBrightnessContrastAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new BrightnessContrastAdjustmentParameters();
    params.brightness = -0.3;
    params.contrast = 0.6;
    params.isLinear = true;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BrightnessContrastAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBrightnessContrastAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetBrightnessContrastAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.brightness, params.brightness));
        console.assert(TestUtils.floatEqual(newNode.parameters.contrast, params.contrast));
        console.assert(newNode.parameters.isLinear === params.isLinear);

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BrightnessContrastAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addBrightnessContrastAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBrightnessContrastAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.brightness, params.brightness));
        console.assert(TestUtils.floatEqual(newNode.parameters.contrast, params.contrast));
        console.assert(newNode.parameters.isLinear === params.isLinear);

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BrightnessContrastAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addBrightnessContrastAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBrightnessContrastAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.brightness, params.brightness));
        console.assert(TestUtils.floatEqual(newNode.parameters.contrast, params.contrast));
        console.assert(newNode.parameters.isLinear === params.isLinear);

        doc.undo();
    }
    doc.close();
    console.log("testBrightnessContrastAdjustmentRasterNode OK");

}

function testShadowsHighlightsAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new ShadowsHighlightsAdjustmentParameters();
    params.shadows = 0.3;
    params.highlights = -0.6;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ShadowsHighlightsAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isShadowsHighlightsAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetShadowsHighlightsAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.shadows, params.shadows));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlights, params.highlights));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ShadowsHighlightsAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isShadowsHighlightsAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.shadows, params.shadows));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlights, params.highlights));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ShadowsHighlightsAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isShadowsHighlightsAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.shadows, params.shadows));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlights, params.highlights));

        doc.undo();
    }
    doc.close();
    console.log("testShadowsHighlightsAdjustmentRasterNode OK");

}

function testBlackAndWhiteAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new BlackAndWhiteAdjustmentParameters();
    params.red = 3.0;
    params.green = 2.5;
    params.blue = 0.0;
    params.cyan = -1.0;
    params.magenta = -1.5;
    params.yellow = 2.0;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BlackAndWhiteAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBlackAndWhiteAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetBlackAndWhiteAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.red, params.red));
        console.assert(TestUtils.floatEqual(newNode.parameters.green, params.green));
        console.assert(TestUtils.floatEqual(newNode.parameters.blue, params.blue));
        console.assert(TestUtils.floatEqual(newNode.parameters.cyan, params.cyan));
        console.assert(TestUtils.floatEqual(newNode.parameters.magenta, params.magenta));
        console.assert(TestUtils.floatEqual(newNode.parameters.yellow, params.yellow));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BlackAndWhiteAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addBlackAndWhiteAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBlackAndWhiteAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.red, params.red));
        console.assert(TestUtils.floatEqual(newNode.parameters.green, params.green));
        console.assert(TestUtils.floatEqual(newNode.parameters.blue, params.blue));
        console.assert(TestUtils.floatEqual(newNode.parameters.cyan, params.cyan));
        console.assert(TestUtils.floatEqual(newNode.parameters.magenta, params.magenta));
        console.assert(TestUtils.floatEqual(newNode.parameters.yellow, params.yellow));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BlackAndWhiteAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addBlackAndWhiteAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBlackAndWhiteAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.red, params.red));
        console.assert(TestUtils.floatEqual(newNode.parameters.green, params.green));
        console.assert(TestUtils.floatEqual(newNode.parameters.blue, params.blue));
        console.assert(TestUtils.floatEqual(newNode.parameters.cyan, params.cyan));
        console.assert(TestUtils.floatEqual(newNode.parameters.magenta, params.magenta));
        console.assert(TestUtils.floatEqual(newNode.parameters.yellow, params.yellow));

        doc.undo();
    }
    doc.close();
    console.log("testBlackAndWhiteAdjustmentRasterNode OK");

}

function testRecolourAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new RecolourAdjustmentParameters();
    params.hue = 179.0*Math.PI/180.0;
    params.saturation = 0.4;
    params.lightness = -0.1;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = RecolourAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isRecolourAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetRecolourAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.hue, params.hue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.saturation, params.saturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.lightness, params.lightness));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = RecolourAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addRecolourAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isRecolourAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.hue, params.hue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.saturation, params.saturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.lightness, params.lightness));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = RecolourAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addRecolourAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isRecolourAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.hue, params.hue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.saturation, params.saturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.lightness, params.lightness));

        doc.undo();
    }
    doc.close();
    console.log("testRecolourAdjustmentRasterNode OK");

}

function testPosteriseAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new PosteriseAdjustmentParameters();
    params.levels = 115;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PosteriseAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPosteriseAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetPosteriseAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(newNode.parameters.levels === params.levels);

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PosteriseAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addPosteriseAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPosteriseAdjustmentRasterNode);
        console.assert(newNode.parameters.levels === params.levels);

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PosteriseAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addPosteriseAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPosteriseAdjustmentRasterNode);
        console.assert(newNode.parameters.levels === params.levels);

        doc.undo();
    }
    doc.close();
    console.log("testPosteriseAdjustmentRasterNode OK");

}

function testSplitToningAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new SplitToningAdjustmentParameters();
    params.highlightsHue = 270.0*Math.PI/180.0;
    params.highlightsSaturation = 0.8;
    params.shadowsHue = 125.0*Math.PI/180.0;
    params.shadowsSaturation = 0.75;
    params.balance = 0.61;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SplitToningAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSplitToningAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetSplitToningAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsHue, params.highlightsHue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsSaturation, params.highlightsSaturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsHue, params.shadowsHue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsSaturation, params.shadowsSaturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.balance, params.balance));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SplitToningAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addSplitToningAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSplitToningAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsHue, params.highlightsHue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsSaturation, params.highlightsSaturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsHue, params.shadowsHue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsSaturation, params.shadowsSaturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.balance, params.balance));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SplitToningAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addSplitToningAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSplitToningAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsHue, params.highlightsHue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsSaturation, params.highlightsSaturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsHue, params.shadowsHue, 0.1));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsSaturation, params.shadowsSaturation));
        console.assert(TestUtils.floatEqual(newNode.parameters.balance, params.balance));

        doc.undo();
    }
    doc.close();
    console.log("testSplitToningAdjustmentRasterNode OK");

}

function testInvertAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = InvertAdjustmentRasterNodeDefinition.create();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isInvertAdjustmentRasterNode);

        doc.undo();
    }

    doc.close();
    console.log("testInvertAdjustmentRasterNode OK");

}

function testThresholdAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new ThresholdAdjustmentParameters();
    params.threshold = 0.77;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ThresholdAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isThresholdAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetThresholdAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ThresholdAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addThresholdAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isThresholdAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ThresholdAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addThresholdAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isThresholdAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));

        doc.undo();
    }
    doc.close();
    console.log("testThresholdAdjustmentRasterNode OK");

}

function testClarityFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new ClarityFilterParameters();
    params.strength = 0.6;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ClarityFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isClarityFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetClarityFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.strength, params.strength));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ClarityFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addClarityFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isClarityFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.strength, params.strength));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ClarityFilterRasterNodeDefinition.create(params);

        acnBuilder.addClarityFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isClarityFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.strength, params.strength));

        doc.undo();
    }
    doc.close();
    console.log("testClarityFilterRasterNode OK");

}

function testUnsharpMaskFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new UnsharpMaskFilterParameters();
    params.radius = 23.0;
    params.threshold = 0.77;
    params.factor = 3.1;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = UnsharpMaskFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isUnsharpMaskFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetUnsharpMaskFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.factor, params.factor));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = UnsharpMaskFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addUnsharpMaskFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isUnsharpMaskFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.factor, params.factor));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = UnsharpMaskFilterRasterNodeDefinition.create(params);

        acnBuilder.addUnsharpMaskFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isUnsharpMaskFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.threshold, params.threshold));
        console.assert(TestUtils.floatEqual(newNode.parameters.factor, params.factor));

        doc.undo();
    }
    doc.close();
    console.log("testUnsharpMaskFilterRasterNode OK");

}

function testHighPassFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new HighPassFilterParameters();
    params.radius = 257.0;
    params.isMonochrome = true;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HighPassFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHighPassFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetHighPassFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isMonochrome === params.isMonochrome);

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HighPassFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addHighPassFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHighPassFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isMonochrome === params.isMonochrome);

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HighPassFilterRasterNodeDefinition.create(params);

        acnBuilder.addHighPassFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHighPassFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(newNode.parameters.isMonochrome === params.isMonochrome);

        doc.undo();
    }
    doc.close();
    console.log("testHighPassFilterRasterNode OK");

}

function testDenoiseFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new DenoiseFilterParameters();
    params.luminance = 0.4;
    params.luminanceDetail = 0.5;
    params.luminanceContribution = 0.6;
    params.colours = 0.7;
    params.coloursContribution = 0.8;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DenoiseFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDenoiseFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetDenoiseFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.luminance, params.luminance));
        console.assert(TestUtils.floatEqual(newNode.parameters.luminanceDetail, params.luminanceDetail));
        console.assert(TestUtils.floatEqual(newNode.parameters.luminanceContribution, params.luminanceContribution));
        console.assert(TestUtils.floatEqual(newNode.parameters.colours, params.colours));
        console.assert(TestUtils.floatEqual(newNode.parameters.coloursContribution, params.coloursContribution));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DenoiseFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addDenoiseFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDenoiseFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.luminance, params.luminance));
        console.assert(TestUtils.floatEqual(newNode.parameters.luminanceDetail, params.luminanceDetail));
        console.assert(TestUtils.floatEqual(newNode.parameters.luminanceContribution, params.luminanceContribution));
        console.assert(TestUtils.floatEqual(newNode.parameters.colours, params.colours));
        console.assert(TestUtils.floatEqual(newNode.parameters.coloursContribution, params.coloursContribution));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DenoiseFilterRasterNodeDefinition.create(params);

        acnBuilder.addDenoiseFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDenoiseFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.luminance, params.luminance));
        console.assert(TestUtils.floatEqual(newNode.parameters.luminanceDetail, params.luminanceDetail));
        console.assert(TestUtils.floatEqual(newNode.parameters.luminanceContribution, params.luminanceContribution));
        console.assert(TestUtils.floatEqual(newNode.parameters.colours, params.colours));
        console.assert(TestUtils.floatEqual(newNode.parameters.coloursContribution, params.coloursContribution));

        doc.undo();
    }
    doc.close();
    console.log("testDenoiseFilterRasterNode OK");

}

function testDiffuseFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new DiffuseFilterParameters();
    params.intensity = 0.87;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DiffuseFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDiffuseFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetDiffuseFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DiffuseFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addDiffuseFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDiffuseFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DiffuseFilterRasterNodeDefinition.create(params);

        acnBuilder.addDiffuseFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDiffuseFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));

        doc.undo();
    }
    doc.close();
    console.log("testDiffuseFilterRasterNode OK");

}

function testDustAndScratchFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new DustAndScratchFilterParameters();
    params.radius = 666;
    params.tolerance = 0.12;
    params.isChannelTolerance = true;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DustAndScratchFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDustAndScratchFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetDustAndScratchFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        console.assert(newNode.parameters.isChannelTolerance === params.isChannelTolerance);

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DustAndScratchFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addDustAndScratchFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDustAndScratchFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        console.assert(newNode.parameters.isChannelTolerance === params.isChannelTolerance);

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DustAndScratchFilterRasterNodeDefinition.create(params);

        acnBuilder.addDustAndScratchFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDustAndScratchFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        console.assert(newNode.parameters.isChannelTolerance === params.isChannelTolerance);

        doc.undo();
    }
    doc.close();
    console.log("testDustAndScratchFilterRasterNode OK");

}

function testAddNoiseFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new AddNoiseFilterParameters();
    params.intensity = 0.91;
    params.noiseType = AddNoiseType.Uniform;
    params.isMonochromatic = false;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = AddNoiseFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isAddNoiseFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetAddNoiseFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(newNode.parameters.noiseType.value == params.noiseType.value);
        console.assert(newNode.parameters.isMonochromatic === params.isMonochromatic);

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = AddNoiseFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addAddNoiseFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isAddNoiseFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(newNode.parameters.noiseType.value == params.noiseType.value);
        console.assert(newNode.parameters.isMonochromatic === params.isMonochromatic);

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = AddNoiseFilterRasterNodeDefinition.create(params);

        acnBuilder.addAddNoiseFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isAddNoiseFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(newNode.parameters.noiseType.value == params.noiseType.value);
        console.assert(newNode.parameters.isMonochromatic === params.isMonochromatic);

        doc.undo();
    }
    doc.close();
    console.log("testAddNoiseFilterRasterNode OK");

}

function testBloomFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new BloomFilterParameters();
    params.shadowBlend = 0.25;
    params.midtoneBlend = 0.5;
    params.highlightBlend = 0.75;
    params.isStrong = true;
    params.method = BloomMethod.Bright;
    params.colour = 0.6;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BloomFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBloomFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetBloomFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.log(newNode);
        console.log(newNode.parameters);
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowBlend, params.shadowBlend));
        console.assert(TestUtils.floatEqual(newNode.parameters.midtoneBlend, params.midtoneBlend));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightBlend, params.highlightBlend));
        console.assert(newNode.parameters.isStrong === params.isStrong);
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.colour, params.colour));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BloomFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addBloomFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBloomFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowBlend, params.shadowBlend));
        console.assert(TestUtils.floatEqual(newNode.parameters.midtoneBlend, params.midtoneBlend));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightBlend, params.highlightBlend));
        console.assert(newNode.parameters.isStrong === params.isStrong);
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.colour, params.colour));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = BloomFilterRasterNodeDefinition.create(params);

        acnBuilder.addBloomFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isBloomFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowBlend, params.shadowBlend));
        console.assert(TestUtils.floatEqual(newNode.parameters.midtoneBlend, params.midtoneBlend));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightBlend, params.highlightBlend));
        console.assert(newNode.parameters.isStrong === params.isStrong);
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.colour, params.colour));

        doc.undo();
    }
    doc.close();
    console.log("testBloomFilterRasterNode OK");

}

function testPixelateFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new PixelateFilterParameters();
    params.quantisation = 8.5;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PixelateFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPixelateFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetPixelateFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.quantisation, params.quantisation));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PixelateFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addPixelateFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPixelateFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.quantisation, params.quantisation));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PixelateFilterRasterNodeDefinition.create(params);

        acnBuilder.addPixelateFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPixelateFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.quantisation, params.quantisation));

        doc.undo();
    }
    doc.close();
    console.log("testPixelateFilterRasterNode OK");

}

function testHalftoneFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new HalftoneFilterParameters();
    params.cellSize = 32.0;
    params.screenAngle = Math.PI / 6;
    params.contrast = 75.0;
    params.screenType = HalftoneScreenType.Colour;
    params.dotType = HalftoneDotType.Round;
    params.greyComponentReplacement = 25.0;
    params.underColourRemoval = 10.0;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HalftoneFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHalftoneFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetHalftoneFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.log(newNode);
        console.log(newNode.parameters);
        console.assert(TestUtils.floatEqual(newNode.parameters.cellSize, params.cellSize));
        console.assert(TestUtils.floatEqual(newNode.parameters.screenAngle, params.screenAngle));
        console.assert(TestUtils.floatEqual(newNode.parameters.contrast, params.contrast));
        console.assert(newNode.parameters.screenType.value == params.screenType.value);
        console.assert(newNode.parameters.dotType.value == params.dotType.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.greyComponentReplacement, params.greyComponentReplacement));
        console.assert(TestUtils.floatEqual(newNode.parameters.underColourRemoval, params.underColourRemoval));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HalftoneFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addHalftoneFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHalftoneFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.cellSize, params.cellSize));
        console.assert(TestUtils.floatEqual(newNode.parameters.screenAngle, params.screenAngle));
        console.assert(TestUtils.floatEqual(newNode.parameters.contrast, params.contrast));
        console.assert(newNode.parameters.screenType.value == params.screenType.value);
        console.assert(newNode.parameters.dotType.value == params.dotType.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.greyComponentReplacement, params.greyComponentReplacement));
        console.assert(TestUtils.floatEqual(newNode.parameters.underColourRemoval, params.underColourRemoval));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HalftoneFilterRasterNodeDefinition.create(params);

        acnBuilder.addHalftoneFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHalftoneFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.cellSize, params.cellSize));
        console.assert(TestUtils.floatEqual(newNode.parameters.screenAngle, params.screenAngle));
        console.assert(TestUtils.floatEqual(newNode.parameters.contrast, params.contrast));
        console.assert(newNode.parameters.screenType.value == params.screenType.value);
        console.assert(newNode.parameters.dotType.value == params.dotType.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.greyComponentReplacement, params.greyComponentReplacement));
        console.assert(TestUtils.floatEqual(newNode.parameters.underColourRemoval, params.underColourRemoval));

        doc.undo();
    }
    doc.close();
    console.log("testHalftoneFilterRasterNode OK");

}

function testRippleFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new RippleFilterParameters();
    params.intensity = 345.67;
    params.position = { x:123.4, y:567.8 };

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = RippleFilterRasterNodeDefinition.createDefault(doc);
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isRippleFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetRippleFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = RippleFilterRasterNodeDefinition.createDefault(doc);
        def.parameters = params;

        acnBuilder.addRippleFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isRippleFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));


        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = RippleFilterRasterNodeDefinition.create(params);

        acnBuilder.addRippleFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isRippleFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));


        doc.undo();
    }
    doc.close();
    console.log("testRippleFilterRasterNode OK");

}

function testTwirlFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new TwirlFilterParameters();
    params.angle = 345*Math.PI/180.0;
    params.radius = 77;
    params.position = { x: 123, y: 456 };

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = TwirlFilterRasterNodeDefinition.createDefault(doc);
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isTwirlFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetTwirlFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, params.angle));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = TwirlFilterRasterNodeDefinition.createDefault(doc);
        def.parameters = params;

        acnBuilder.addTwirlFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isTwirlFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, params.angle));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = TwirlFilterRasterNodeDefinition.create(params);

        acnBuilder.addTwirlFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isTwirlFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.angle, params.angle));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
    }
    doc.close();
    console.log("testTwirlFilterRasterNode OK");

}

function testSphericalFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new SphericalFilterParameters();
    params.intensity = 0.77;
    params.radius = 999.0;
    params.position = { x: 567, y: 234 };

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SphericalFilterRasterNodeDefinition.createDefault(doc);
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSphericalFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetSphericalFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SphericalFilterRasterNodeDefinition.createDefault(doc);
        def.parameters = params;

        acnBuilder.addSphericalFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSphericalFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SphericalFilterRasterNodeDefinition.create(params);

        acnBuilder.addSphericalFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSphericalFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
    }
    doc.close();
    console.log("testSphericalFilterRasterNode OK");

}

function testPinchPunchFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new PinchPunchFilterParameters();
    params.intensity = -0.66;
    params.radius = 666;
    params.position = { x: 666, y: 666 };

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PinchPunchFilterRasterNodeDefinition.createDefault(doc);
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPinchPunchFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetPinchPunchFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PinchPunchFilterRasterNodeDefinition.createDefault(doc);
        def.parameters = params;

        acnBuilder.addPinchPunchFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPinchPunchFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PinchPunchFilterRasterNodeDefinition.create(params);

        acnBuilder.addPinchPunchFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isPinchPunchFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.intensity, params.intensity));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.position.x, params.position.x) && TestUtils.floatEqual(newNode.parameters.position.y, params.position.y));

        doc.undo();
    }
    doc.close();
    console.log("testPinchPunchFilterRasterNode OK");

}

function testWhiteBalanceAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new WhiteBalanceAdjustmentParameters();
    params.whiteBalance = 0.3;
    params.tint = -0.3447;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = WhiteBalanceAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isWhiteBalanceAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetWhiteBalanceAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.whiteBalance, params.whiteBalance));
        console.assert(TestUtils.floatEqual(newNode.parameters.tint, params.tint));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = WhiteBalanceAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addWhiteBalanceAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isWhiteBalanceAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.whiteBalance, params.whiteBalance));
        console.assert(TestUtils.floatEqual(newNode.parameters.tint, params.tint));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = WhiteBalanceAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addWhiteBalanceAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isWhiteBalanceAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.whiteBalance, params.whiteBalance));
        console.assert(TestUtils.floatEqual(newNode.parameters.tint, params.tint));

        doc.undo();
    }
    doc.close();
    console.log("testWhiteBalanceAdjustmentRasterNode OK");

}

function assertBalanceValueEqual(bv1, bv2) {
    console.assert(TestUtils.floatEqual(bv1.cyanRed, bv2.cyanRed));
    console.assert(TestUtils.floatEqual(bv1.magentaGreen, bv2.magentaGreen));
    console.assert(TestUtils.floatEqual(bv1.yellowBlue, bv2.yellowBlue));
}

function testColourBalanceAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new ColourBalanceAdjustmentParameters();
    let values = params.values[Number(TonalRangeType.Shadows)]
    values.cyanRed = 0.87;
    values.magentaGreen = 0.76;
    values.yellowBlue = 0.65;
    params.values[Number(TonalRangeType.Midtones)].cyanRed = 0.54;
    params.values[Number(TonalRangeType.Midtones)].magentaGreen = 0.43;
    params.values[Number(TonalRangeType.Midtones)].yellowBlue = 0.21;
    params.values[Number(TonalRangeType.Highlights)].cyanRed = -0.12;
    params.values[Number(TonalRangeType.Highlights)].magentaGreen = -0.34;
    params.values[Number(TonalRangeType.Highlights)].yellowBlue = -0.56;
    params.preserveLuminosity = true;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ColourBalanceAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isColourBalanceAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetColourBalanceAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Shadows)], params.values[Number(TonalRangeType.Shadows)]);
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Midtones)], params.values[Number(TonalRangeType.Midtones)]);
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Highlights)], params.values[Number(TonalRangeType.Highlights)]);
        console.assert(newNode.parameters.preserveLuminosity === params.preserveLuminosity);

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ColourBalanceAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addColourBalanceAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isColourBalanceAdjustmentRasterNode);
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Shadows)], params.values[Number(TonalRangeType.Shadows)]);
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Midtones)], params.values[Number(TonalRangeType.Midtones)]);
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Highlights)], params.values[Number(TonalRangeType.Highlights)]);
        console.assert(newNode.parameters.preserveLuminosity === params.preserveLuminosity);

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ColourBalanceAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addColourBalanceAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isColourBalanceAdjustmentRasterNode);
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Shadows)], params.values[Number(TonalRangeType.Shadows)]);
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Midtones)], params.values[Number(TonalRangeType.Midtones)]);
        assertBalanceValueEqual(newNode.parameters.values[Number(TonalRangeType.Highlights)], params.values[Number(TonalRangeType.Highlights)]);
        console.assert(newNode.parameters.preserveLuminosity === params.preserveLuminosity);

        doc.undo();
    }
    doc.close();
    console.log("testColourBalanceAdjustmentRasterNode OK");

}

function testVibranceAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new VibranceAdjustmentParameters();
    params.vibrance = -0.78;
    params.saturation = -0.23;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VibranceAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVibranceAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetVibranceAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.vibrance, params.vibrance));
        console.assert(TestUtils.floatEqual(newNode.parameters.saturation, params.saturation));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VibranceAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addVibranceAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVibranceAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.vibrance, params.vibrance));
        console.assert(TestUtils.floatEqual(newNode.parameters.saturation, params.saturation));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VibranceAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addVibranceAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVibranceAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.vibrance, params.vibrance));
        console.assert(TestUtils.floatEqual(newNode.parameters.saturation, params.saturation));

        doc.undo();
    }
    doc.close();
    console.log("testVibranceAdjustmentRasterNode OK");

}

function testNormalsAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new NormalsAdjustmentParameters();
    params.rotation = -1;
    params.scale = 1.56;
    params.flipX = true;
    params.flipY = false;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = NormalsAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isNormalsAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetNormalsAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.rotation, params.rotation));
        console.assert(TestUtils.floatEqual(newNode.parameters.scale, params.scale));
        console.assert(newNode.parameters.flipX === params.flipX);
        console.assert(newNode.parameters.flipY === params.flipY);

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = NormalsAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addNormalsAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isNormalsAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.rotation, params.rotation));
        console.assert(TestUtils.floatEqual(newNode.parameters.scale, params.scale));
        console.assert(newNode.parameters.flipX === params.flipX);
        console.assert(newNode.parameters.flipY === params.flipY);

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = NormalsAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addNormalsAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isNormalsAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.rotation, params.rotation));
        console.assert(TestUtils.floatEqual(newNode.parameters.scale, params.scale));
        console.assert(newNode.parameters.flipX === params.flipX);
        console.assert(newNode.parameters.flipY === params.flipY);

        doc.undo();
    }
    doc.close();
    console.log("testNormalsAdjustmentRasterNode OK");

}

function testVignetteFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new VignetteFilterParameters();
    params.exposure = 3.14;
    params.hardness = 0.77;
    params.scale = 1.79;
    params.shape = 0.25;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VignetteFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVignetteFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetVignetteFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        console.assert(TestUtils.floatEqual(newNode.parameters.hardness, params.hardness));
        console.assert(TestUtils.floatEqual(newNode.parameters.scale, params.scale));
        console.assert(TestUtils.floatEqual(newNode.parameters.shape, params.shape));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VignetteFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addVignetteFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVignetteFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        console.assert(TestUtils.floatEqual(newNode.parameters.hardness, params.hardness));
        console.assert(TestUtils.floatEqual(newNode.parameters.scale, params.scale));
        console.assert(TestUtils.floatEqual(newNode.parameters.shape, params.shape));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VignetteFilterRasterNodeDefinition.create(params);

        acnBuilder.addVignetteFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVignetteFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        console.assert(TestUtils.floatEqual(newNode.parameters.hardness, params.hardness));
        console.assert(TestUtils.floatEqual(newNode.parameters.scale, params.scale));
        console.assert(TestUtils.floatEqual(newNode.parameters.shape, params.shape));

        doc.undo();
    }
    doc.close();
    console.log("testVignetteFilterRasterNode OK");

}

function testDefringeFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new DefringeFilterParameters();
    params.hue = 0.66 * Math.PI;
    params.removeComplementary = true;
    params.tolerance = 0.33;
    params.radius = 47;
    params.edgeBrightnessThreshold = 0.87;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DefringeFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDefringeFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetDefringeFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.hue, params.hue));
        console.assert(newNode.parameters.removeComplementary === params.removeComplementary);
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.edgeBrightnessThreshold, params.edgeBrightnessThreshold));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DefringeFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addDefringeFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDefringeFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.hue, params.hue));
        console.assert(newNode.parameters.removeComplementary === params.removeComplementary);
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.edgeBrightnessThreshold, params.edgeBrightnessThreshold));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = DefringeFilterRasterNodeDefinition.create(params);

        acnBuilder.addDefringeFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isDefringeFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.hue, params.hue));
        console.assert(newNode.parameters.removeComplementary === params.removeComplementary);
        console.assert(TestUtils.floatEqual(newNode.parameters.tolerance, params.tolerance));
        console.assert(TestUtils.floatEqual(newNode.parameters.radius, params.radius));
        console.assert(TestUtils.floatEqual(newNode.parameters.edgeBrightnessThreshold, params.edgeBrightnessThreshold));

        doc.undo();
    }
    doc.close();
    console.log("testDefringeFilterRasterNode OK");

}

function testVoronoiFilterRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new VoronoiFilterParameters();
    params.cellSize = 33.3;
    params.lineWidth = 7.7;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VoronoiFilterRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVoronoiFilterRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetVoronoiFilterParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.cellSize, params.cellSize));
        console.assert(TestUtils.floatEqual(newNode.parameters.lineWidth, params.lineWidth));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VoronoiFilterRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addVoronoiFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVoronoiFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.cellSize, params.cellSize));
        console.assert(TestUtils.floatEqual(newNode.parameters.lineWidth, params.lineWidth));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = VoronoiFilterRasterNodeDefinition.create(params);

        acnBuilder.addVoronoiFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isVoronoiFilterRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.cellSize, params.cellSize));
        console.assert(TestUtils.floatEqual(newNode.parameters.lineWidth, params.lineWidth));

        doc.undo();
    }
    doc.close();
    console.log("testVoronoiFilterRasterNode OK");

}

function assertColourWeightEqual(cw1, cw2) {
    console.assert(TestUtils.floatEqual(cw1.cyanWeight, cw2.cyanWeight));
    console.assert(TestUtils.floatEqual(cw1.magentaWeight, cw2.magentaWeight));
    console.assert(TestUtils.floatEqual(cw1.yellowWeight, cw2.yellowWeight));
    console.assert(TestUtils.floatEqual(cw1.blackWeight, cw2.blackWeight));
}

function testSelectiveColourAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new SelectiveColourAdjustmentParameters();
    let weight = params.weights[Number(SelectiveColour.Neutrals)];
    weight.cyanWeight = 0.7;
    weight.magentaWeight = 0.4;
    weight.yellowWeight = -0.4;
    weight.blackWeight = -0.7;
    params.weights[Number(SelectiveColour.Neutrals)] = weight;
    params.isRelative = false;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SelectiveColourAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSelectiveColourAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetSelectiveColourAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        assertColourWeightEqual(newNode.parameters.weights[Number(SelectiveColour.Neutrals)], params.weights[Number(SelectiveColour.Neutrals)]);
        console.assert(newNode.parameters.isRelative === params.isRelative);

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SelectiveColourAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addSelectiveColourAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSelectiveColourAdjustmentRasterNode);
        assertColourWeightEqual(newNode.parameters.weights[Number(SelectiveColour.Neutrals)], params.weights[Number(SelectiveColour.Neutrals)]);
        console.assert(newNode.parameters.isRelative === params.isRelative);

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = SelectiveColourAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addSelectiveColourAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isSelectiveColourAdjustmentRasterNode);
        assertColourWeightEqual(newNode.parameters.weights[Number(SelectiveColour.Neutrals)], params.weights[Number(SelectiveColour.Neutrals)]);
        console.assert(newNode.parameters.isRelative === params.isRelative);

        doc.undo();
    }
    doc.close();
    console.log("testSelectiveColourAdjustmentRasterNode OK");

}

function testHSLShiftAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();
    let ToRad = Math.PI / 180.0;

    let colourRange = {rampUpBegin: 340 * ToRad, rampUpEnd: 357 * ToRad, rampDownBegin: 3 * ToRad, rampDownEnd: 20 * ToRad};
    let channelParams = {hueShift: 35.6 * ToRad, saturationShift: 0.7, luminosityShift: -0.3};
    let channel = 2;
    
    let params = HSLShiftAdjustmentParameters.create();
    params.setChannelParameters(channel, channelParams);
    params.masterParameters = channelParams;
    params.setChannelColourRange(channel, colourRange);

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HSLShiftAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHSLShiftAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetHSLShiftAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.hueShift, channelParams.hueShift, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.saturationShift, channelParams.saturationShift));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.luminosityShift, channelParams.luminosityShift));
        
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).hueShift, channelParams.hueShift, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).saturationShift, channelParams.saturationShift));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).luminosityShift, channelParams.luminosityShift));
        
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampUpBegin, colourRange.rampUpBegin));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampUpEnd, colourRange.rampUpEnd));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampDownBegin, colourRange.rampDownBegin));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampDownEnd, colourRange.rampDownEnd));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HSLShiftAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addHSLShiftAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHSLShiftAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.hueShift, channelParams.hueShift, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.saturationShift, channelParams.saturationShift));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.luminosityShift, channelParams.luminosityShift));
        
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).hueShift, channelParams.hueShift, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).saturationShift, channelParams.saturationShift));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).luminosityShift, channelParams.luminosityShift));
        
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampUpBegin, colourRange.rampUpBegin, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampUpEnd, colourRange.rampUpEnd, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampDownBegin, colourRange.rampDownBegin, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampDownEnd, colourRange.rampDownEnd, 0.01));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = HSLShiftAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addHSLShiftAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isHSLShiftAdjustmentRasterNode);
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.hueShift, channelParams.hueShift, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.saturationShift, channelParams.saturationShift));
        console.assert(TestUtils.floatEqual(newNode.parameters.masterParameters.luminosityShift, channelParams.luminosityShift));
        
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).hueShift, channelParams.hueShift, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).saturationShift, channelParams.saturationShift));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelParameters(channel).luminosityShift, channelParams.luminosityShift));
        
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampUpBegin, colourRange.rampUpBegin, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampUpEnd, colourRange.rampUpEnd, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampDownBegin, colourRange.rampDownBegin, 0.01));
        console.assert(TestUtils.floatEqual(newNode.parameters.getChannelColourRange(channel).rampDownEnd, colourRange.rampDownEnd, 0.01));

        doc.undo();
    }
    doc.close();
    console.log("testHSLShiftAdjustmentRasterNode OK");

}

function testToneCompressionAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new ToneCompressionAdjustmentParameters();
    params.method = ToneCompressionMethod.Filmic;
    params.exposure = 0.77;
    params.gamma = 0.66;
    params.colour = 0.55;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ToneCompressionAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isToneCompressionAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetToneCompressionAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        console.assert(TestUtils.floatEqual(newNode.parameters.gamma, params.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.colour, params.colour));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ToneCompressionAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addToneCompressionAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isToneCompressionAdjustmentRasterNode);
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        console.assert(TestUtils.floatEqual(newNode.parameters.gamma, params.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.colour, params.colour));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ToneCompressionAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addToneCompressionAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isToneCompressionAdjustmentRasterNode);
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.exposure, params.exposure));
        console.assert(TestUtils.floatEqual(newNode.parameters.gamma, params.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.colour, params.colour));

        doc.undo();
    }
    doc.close();
    console.log("testToneCompressionAdjustmentRasterNode OK");

}

function testToneStretchAdjustmentRasterNode() {
    let doc = TestUtils.newA4Empty();

    let params = new ToneStretchAdjustmentParameters();
    params.method = ToneStretchMethod.Arcsinh;
    params.gamma = 0.77;
    params.stretchFactor = 0.66;
    params.compression = 0.55;

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ToneStretchAdjustmentRasterNodeDefinition.createDefault();
        acnBuilder.addNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isToneStretchAdjustmentRasterNode);

        let selection = Selection.create(doc, newNode);
        let updateCmd = DocumentCommand.createSetToneStretchAdjustmentParameters(selection, params);

        result = doc.executeCommand(updateCmd);

        newNode = doc.layers.first;
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.gamma, params.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.stretchFactor, params.stretchFactor));
        console.assert(TestUtils.floatEqual(newNode.parameters.compression, params.compression));

        doc.undo();
        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ToneStretchAdjustmentRasterNodeDefinition.createDefault();
        def.parameters = params;

        acnBuilder.addToneStretchAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isToneStretchAdjustmentRasterNode);
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.gamma, params.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.stretchFactor, params.stretchFactor));
        console.assert(TestUtils.floatEqual(newNode.parameters.compression, params.compression));

        doc.undo();
    }

    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ToneStretchAdjustmentRasterNodeDefinition.create(params);

        acnBuilder.addToneStretchAdjustmentRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);

        let newNode = doc.layers.first;
        console.assert(newNode.isToneStretchAdjustmentRasterNode);
        console.assert(newNode.parameters.method.value == params.method.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.gamma, params.gamma));
        console.assert(TestUtils.floatEqual(newNode.parameters.stretchFactor, params.stretchFactor));
        console.assert(TestUtils.floatEqual(newNode.parameters.compression, params.compression));

        doc.undo();
    }
    doc.close();
    console.log("testToneStretchAdjustmentRasterNode OK");

}

function testRasterNode() {
    const doc = app.documents.current;
    if (doc) {
        // make sure your doc has a rasternode as its first node
        const rasterNode = doc.layers.first;

        console.log("Is raster node extend empty");
        console.log(rasterNode.extendEmpty);
    }
}


function testShadowsHighlightsFilterRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    // Test Default (New) mode - RasterNewShadowsHighlightsCommand, strength [-1,1], no radius
    {
        let parameters = new ShadowsHighlightsFilterParameters();
        parameters.version = ShadowsHighlightsVersion.Default;
        parameters.shadowsStrength = 0.5;
        parameters.shadowsRange = 0.3;
        parameters.shadowsRadius = 0;
        parameters.highlightsStrength = -0.7;
        parameters.highlightsRange = 0.6;
        parameters.highlightsRadius = 0;
        
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ShadowsHighlightsFilterRasterNodeDefinition.createDefault();
        def.parameters = parameters;
        acnBuilder.addShadowsHighlightsFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isShadowsHighlightsFilterRasterNode);
        console.assert(newNode.parameters.version.value === ShadowsHighlightsVersion.Default.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsStrength, 0.5));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsRange, 0.3));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsRadius, 0));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsStrength, -0.7));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsRange, 0.6));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsRadius, 0));
        
        doc.undo();
    }
    
    // Test V16 (Legacy) mode - RasterShadowsHighlightsCommand, strength [0,1], has radius
    {
        let parameters = new ShadowsHighlightsFilterParameters();
        parameters.version = ShadowsHighlightsVersion.V16;
        parameters.shadowsStrength = 0.8;
        parameters.shadowsRange = 0.4;
        parameters.shadowsRadius = 50;
        parameters.highlightsStrength = 0.6;
        parameters.highlightsRange = 0.7;
        parameters.highlightsRadius = 120;
        
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ShadowsHighlightsFilterRasterNodeDefinition.create(parameters);
        acnBuilder.addShadowsHighlightsFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        let result = doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isShadowsHighlightsFilterRasterNode);
        console.assert(newNode.parameters.version.value === ShadowsHighlightsVersion.V16.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsStrength, 0.8));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsRange, 0.4));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsRadius, 50));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsStrength, 0.6));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsRange, 0.7));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsRadius, 120));
        
        doc.undo();
    }
    // Test set parameters command
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = ShadowsHighlightsFilterRasterNodeDefinition.createDefault();
        acnBuilder.addShadowsHighlightsFilterRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        let selection = Selection.create(doc, newNode);
        
        let parameters = new ShadowsHighlightsFilterParameters();
        parameters.version = ShadowsHighlightsVersion.V16;
        parameters.shadowsStrength = 0.3;
        parameters.shadowsRange = 0.2;
        parameters.shadowsRadius = 120;
        parameters.highlightsStrength = 0.4;
        parameters.highlightsRange = 0.8;
        parameters.highlightsRadius = 240;
        
        let updateCmd = DocumentCommand.createSetShadowsHighlightsFilterParameters(selection, parameters);
        doc.executeCommand(updateCmd);
        
        newNode = doc.layers.first;
        console.assert(newNode.isShadowsHighlightsFilterRasterNode);
        console.assert(newNode.parameters.version.value === ShadowsHighlightsVersion.V16.value);
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsStrength, 0.3));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsRange, 0.2));
        console.assert(TestUtils.floatEqual(newNode.parameters.shadowsRadius, 120));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsStrength, 0.4));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsRange, 0.8));
        console.assert(TestUtils.floatEqual(newNode.parameters.highlightsRadius, 240));
        
        doc.undo();
        doc.undo();
    }
    
    doc.close();
    console.log("testShadowsHighlightsFilterRasterNode OK");
}


function testPatternRasterNode() {
    let doc = TestUtils.newA4Empty();
    
    {
        let acnBuilder = AddChildNodesCommandBuilder.create();
        let def = PatternRasterNodeDefinition.createDefault(doc);
        console.assert(def.isPatternRasterNodeDefinition);
        console.assert(def.mirror === false);
        
        def.mirror = true;
        console.assert(def.mirror === true);
        
        acnBuilder.addPatternRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isPatternRasterNode);
        console.assert(newNode.mirror === true);
        
        doc.undo();
    }
    
    {
        let bitmap = Bitmap.create(64, 64, doc.format);
        let transform = Transform.createIdentity();
        let def = PatternRasterNodeDefinition.create(bitmap, transform, false);
        console.assert(def.isPatternRasterNodeDefinition);
        console.assert(def.mirror === false);
        
        let acnBuilder = AddChildNodesCommandBuilder.create();
        acnBuilder.addPatternRasterNode(def);
        let anCommand = acnBuilder.createCommand(false, NodeChildType.Main);
        doc.executeCommand(anCommand);
        
        let newNode = doc.layers.first;
        console.assert(newNode.isPatternRasterNode);
        console.assert(newNode.isRasterNode);
        console.assert(newNode.mirror === false);
        
        doc.undo();
    }
    
    doc.close();
    console.log("testPatternRasterNode OK");
}


function testRasterNodes() {
    testExposureAdjustmentRasterNode();
    testLevelsAdjustmentRasterNode();
    testGaussianBlurFilterRasterNode();
    testBilateralBlurFilterRasterNode();
    testBoxBlurFilterRasterNode();
    testMedianBlurFilterRasterNode();
    testDiffuseGlowFilterRasterNode();
    testLensBlurFilterRasterNode();
    testMaximumBlurFilterRasterNode();
    testMinimumBlurFilterRasterNode();
    testMotionBlurFilterRasterNode();
    testRadialBlurFilterRasterNode();
    testBrightnessContrastAdjustmentRasterNode();
    testShadowsHighlightsAdjustmentRasterNode();
    testBlackAndWhiteAdjustmentRasterNode();
    testRecolourAdjustmentRasterNode();
    testPosteriseAdjustmentRasterNode();
    testSplitToningAdjustmentRasterNode();
    testInvertAdjustmentRasterNode();
    testThresholdAdjustmentRasterNode();
    testClarityFilterRasterNode();
    testUnsharpMaskFilterRasterNode();
    testHighPassFilterRasterNode();
    testDenoiseFilterRasterNode();
    testDiffuseFilterRasterNode();
    testDustAndScratchFilterRasterNode();
    testAddNoiseFilterRasterNode();
    testRippleFilterRasterNode();
    testTwirlFilterRasterNode();
    testSphericalFilterRasterNode();
    testPinchPunchFilterRasterNode();
    testWhiteBalanceAdjustmentRasterNode();
    testColourBalanceAdjustmentRasterNode();
    testVibranceAdjustmentRasterNode();
    testNormalsAdjustmentRasterNode();
    testVignetteFilterRasterNode();
    testDefringeFilterRasterNode();
    testVoronoiFilterRasterNode();
    testSelectiveColourAdjustmentRasterNode();
    testHSLShiftAdjustmentRasterNode();
    testCurvesAdjustmentRasterNode();
    testFieldBlurFilterRasterNode();
    testToneCompressionAdjustmentRasterNode();
    testToneStretchAdjustmentRasterNode();
    testBloomFilterRasterNode();
    testPixelateFilterRasterNode();
    testHalftoneFilterRasterNode();
    testEllipticalDepthOfFieldFilterRasterNode();
    testTiltShiftDepthOfFieldFilterRasterNode();
    testShadowsHighlightsFilterRasterNode();
    testPatternRasterNode();
}

module.exports.testRasterNode = testRasterNode;
module.exports.testRasterNodes = testRasterNodes;
module.exports.testCurvesAdjustmentRasterNode = testCurvesAdjustmentRasterNode;
