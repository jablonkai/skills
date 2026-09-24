'use strict';

const { TestUtils } = require('/tests/testUtils.js');
const { ShapeNodeDefinition, NodeChildType } = require('/nodes.js');
const { AddChildNodesCommandBuilder } = require('/commands.js');
const { DiffusionCurveKind, DiffusionCurveSet, DiffusionCurveSide, DiffusionFill, FillDescriptor, FillType } = require('/fills.js');
const { RGBA8 } = require('/colours.js');
const { Transform } = require('/geometry.js');

function testDiffusionFill() {
    let doc = TestUtils.newA4Empty();

    const red = RGBA8(255, 0, 0, 255);
    const blue = RGBA8(0, 0, 255, 255);

    // Two-colour default set carries a single centered curve
    let curveSet = DiffusionCurveSet.createDefault(red, blue);
    console.assert(curveSet.curveCount === 1, "Default two-colour curve set should have 1 curve");

    // Add a single-segment cubic curve (3n+1 = 4 control points)
    const points = [{x: 0.2, y: 0.2}, {x: 0.4, y: 0.3}, {x: 0.6, y: 0.7}, {x: 0.8, y: 0.8}];
    curveSet.addCurve(points, red, blue);
    console.assert(curveSet.curveCount === 2, "Curve set should have 2 curves after addCurve");

    const readPoints = curveSet.getCurvePoints(1);
    console.assert(readPoints.length === 4, "Added curve should have 4 points");
    console.assert(TestUtils.floatEqual(readPoints[2].x, 0.6), "Point 2 x should round trip");
    console.assert(TestUtils.floatEqual(readPoints[2].y, 0.7), "Point 2 y should round trip");

    const leftColour = curveSet.getCurveColour(1, DiffusionCurveSide.Left);
    console.assert(leftColour !== null, "Left colour should be set");
    console.assert(leftColour.rgba8.r === red.rgba8.r, "Left colour should be red");

    const rightColour = curveSet.getCurveColour(1, DiffusionCurveSide.Right);
    console.assert(rightColour !== null, "Right colour should be set");
    console.assert(rightColour.rgba8.b === blue.rgba8.b, "Right colour should be blue");

    curveSet.setCurveBlur(1, 0.5);
    console.assert(TestUtils.floatEqual(curveSet.getCurveBlur(1), 0.5), "Blur should read back as 0.5");

    console.assert(TestUtils.floatEqual(curveSet.getCurveStrength(1), 1.0), "Strength should default to 1.0");
    curveSet.setCurveStrength(1, 1.5);
    console.assert(TestUtils.floatEqual(curveSet.getCurveStrength(1), 1.5), "Strength should read back as 1.5 (overdrive allowed)");

    console.assert(curveSet.getCurvePressure(1) === null, "Pressure should default to null (full strength)");

    console.assert(TestUtils.floatEqual(curveSet.backgroundStrength, 1.0), "Boundary strength should default to 1.0");
    curveSet.backgroundStrength = 0.4;
    console.assert(TestUtils.floatEqual(curveSet.backgroundStrength, 0.4), "Boundary strength should read back as 0.4");

    // Standalone fill construction round trip
    let diffusionFill = DiffusionFill.create(curveSet);
    console.assert(diffusionFill.fillType.value === FillType.Diffusion.value, "DiffusionFill should have Diffusion fill type");
    console.assert(diffusionFill.curveSet.curveCount === 2, "Fill's curve set should have 2 curves");

    // Apply to a node's brush fill and read back through the node
    let shapeDef = ShapeNodeDefinition.createDefault();

    let acnBuilder = AddChildNodesCommandBuilder.create();
    acnBuilder.addNode(shapeDef);
    let addCommand = acnBuilder.createCommand(false, NodeChildType.Main);
    doc.executeCommand(addCommand);

    let shapeNode = doc.layers.first;
    console.assert(shapeNode.isShapeNode, "Should be a ShapeNode");

    // The descriptor transform maps the unit-square curves onto the node
    const bounds = shapeNode.baseBox;
    const fillTransform = Transform.multiply(Transform.createTranslate(bounds.x, bounds.y), Transform.createScale(bounds.width, bounds.height));
    let descriptor = FillDescriptor.create(DiffusionFill.create(curveSet), true, fillTransform, undefined, false);
    console.assert(descriptor.fillType.value === FillType.Diffusion.value, "Descriptor should carry a diffusion fill");

    const bfIface = shapeNode.brushFillInterface;
    bfIface.fillDescriptor = descriptor;

    const readDescriptor = bfIface.fillDescriptor;
    const readFill = readDescriptor.fill;
    console.assert(readFill.fillType.value === FillType.Diffusion.value, "Node's brush fill should be a diffusion fill");

    const readCurveSet = readFill.curveSet;
    console.assert(readCurveSet.curveCount === 2, "Curve set should round trip through the node");
    console.assert(TestUtils.floatEqual(readCurveSet.getCurveBlur(1), 0.5), "Blur should round trip through the node");

    const nodePoints = readCurveSet.getCurvePoints(1);
    console.assert(nodePoints.length === 4, "Curve points should round trip through the node");
    console.assert(TestUtils.floatEqual(nodePoints[2].y, 0.7), "Point 2 y should round trip through the node");

    doc.close();
    console.log("testDiffusionFill OK");
}

function testDiffusionParametric() {
    const red = RGBA8(255, 0, 0, 255);
    const blue = RGBA8(0, 0, 255, 255);

    let curveSet = DiffusionCurveSet.create();

    // Parametric creators
    curveSet.addEllipse({x: 0.5, y: 0.5}, 0.2, 0.1, 0.25, red, blue);
    curveSet.addArc({x: 0.5, y: 0.5}, 0.3, 0.3, 0, 0, Math.PI * 0.5, red, blue);
    curveSet.addLine({x: 0.1, y: 0.1}, {x: 0.9, y: 0.9}, red, blue);
    console.assert(curveSet.curveCount === 3, "Curve set should have 3 parametric curves");

    console.assert(curveSet.getCurveKind(0) === DiffusionCurveKind.Ellipse.value, "Curve 0 should be an ellipse");
    console.assert(curveSet.getCurveKind(1) === DiffusionCurveKind.Arc.value, "Curve 1 should be an arc");
    console.assert(curveSet.getCurveKind(2) === DiffusionCurveKind.Line.value, "Curve 2 should be a line");

    // Parametric definitions round trip
    const ellipse = curveSet.getCurveParametric(0);
    console.assert(TestUtils.floatEqual(ellipse.centre.x, 0.5), "Ellipse centre x should round trip");
    console.assert(TestUtils.floatEqual(ellipse.radiusX, 0.2), "Ellipse radiusX should round trip");
    console.assert(TestUtils.floatEqual(ellipse.radiusY, 0.1), "Ellipse radiusY should round trip");
    console.assert(TestUtils.floatEqual(ellipse.rotation, 0.25), "Ellipse rotation should round trip");

    const line = curveSet.getCurveParametric(2);
    console.assert(TestUtils.floatEqual(line.centre.x, 0.1), "Line start x rides in centre");
    console.assert(TestUtils.floatEqual(line.angle0, 0.9), "Line end x rides in angle0");
    console.assert(TestUtils.floatEqual(line.angle1, 0.9), "Line end y rides in angle1");

    // The projection is readable as ordinary Bezier points
    console.assert(curveSet.getCurvePoints(0).length >= 4, "Ellipse should project to a Bezier chain");

    // Re-defining converts in place
    curveSet.setCurveLine(0, {x: 0.2, y: 0.2}, {x: 0.8, y: 0.2});
    console.assert(curveSet.getCurveKind(0) === DiffusionCurveKind.Line.value, "setCurveLine should convert the curve");

    // Explicit points demote a parametric curve to a plain Bezier chain
    curveSet.setCurvePoints(1, [{x: 0.2, y: 0.2}, {x: 0.4, y: 0.3}, {x: 0.6, y: 0.7}, {x: 0.8, y: 0.8}]);
    console.assert(curveSet.getCurveKind(1) === DiffusionCurveKind.Bezier.value, "setCurvePoints should demote to Bezier");

    // Node styles on the demoted (now Bezier) curve
    console.assert(curveSet.getCurveNodeCount(1) === 2, "Single-segment curve should have 2 nodes");
    console.assert(curveSet.getCurveNodeSmooth(1, 0) === true, "Nodes default to smooth");
    curveSet.setCurveNodeSmooth(1, 0, false);
    console.assert(curveSet.getCurveNodeSmooth(1, 0) === false, "Node style should round trip");
    curveSet.setCurveNodeSmooth(1, 0, true);
    console.assert(curveSet.getCurveNodeSmooth(1, 0) === true, "Node style should round trip back to smooth");

    // Node styles are rejected on parametric curves
    let threw = false;
    try { curveSet.setCurveNodeSmooth(0, 0, false); } catch (e) { threw = true; }
    console.assert(threw, "setCurveNodeSmooth on a parametric curve should throw");

    // getCurveParametric is rejected on Bezier curves
    threw = false;
    try { curveSet.getCurveParametric(1); } catch (e) { threw = true; }
    console.assert(threw, "getCurveParametric on a Bezier curve should throw");

    console.log("testDiffusionParametric OK");
}

module.exports.testDiffusionFill = testDiffusionFill;
function testDiffusionValidation() {
    const red = RGBA8(255, 0, 0, 255);
    const blue = RGBA8(0, 0, 255, 255);
    let curveSet = DiffusionCurveSet.createDefault(red, blue);

    function throws(fn, label) {
        let threw = false;
        try { fn(); } catch (e) { threw = true; }
        console.assert(threw, label);
    }

    throws(() => curveSet.getCurveBlur(99), "Out-of-range curve index should throw");
    throws(() => curveSet.addCurve([{x: 0, y: 0}, {x: 1, y: 1}], red, blue), "Invalid point count should throw");
    throws(() => curveSet.setCurveBlur(0, 2.0), "Out-of-range blur should throw");
    throws(() => curveSet.setCurveStrength(0, -1.0), "Out-of-range strength should throw");
    throws(() => curveSet.setBackgroundStrength(1.5), "Out-of-range background strength should throw");
    throws(() => curveSet.addCurve([{x: NaN, y: 0}, {x: 0.3, y: 0.3}, {x: 0.6, y: 0.6}, {x: 1, y: 1}], red, blue), "Non-finite points should throw");
    throws(() => curveSet.addEllipse({x: 0.5, y: 0.5}, 0, 0.1, 0, red, blue), "Zero radius should throw");
    throws(() => curveSet.addLine({x: Infinity, y: 0}, {x: 1, y: 1}, red, blue), "Non-finite line point should throw");

    // Clone independence: edits to the clone leave the original untouched
    let clone = curveSet.clone();
    clone.setCurveBlur(0, 0.75);
    console.assert(TestUtils.floatEqual(curveSet.getCurveBlur(0), 0.0), "Clone edits must not touch the original");

    // removeCurve
    const before = clone.curveCount;
    clone.removeCurve(0);
    console.assert(clone.curveCount === before - 1, "removeCurve should shrink the set");

    console.log("testDiffusionValidation OK");
}

module.exports.testDiffusionParametric = testDiffusionParametric;
module.exports.testDiffusionValidation = testDiffusionValidation;
