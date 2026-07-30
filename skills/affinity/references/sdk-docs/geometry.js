'use strict';

const { EnumerationResult } = require('affinity:common');
const {
    CubicBezier,
    CubicBezierApi,
    CurveApi,
    CurveBuilderApi,
    CurveCornerData,
    CurveCornerType,
    CurveNode,
    CurveNodeStyle,
    CurveNodeType,
    Point,
    PolyCurveApi,
    PolygonApi,
    PolyPolyCurveApi,
    Rectangle,
    Size,
    SizeInt,
    SplineApi,
    SplineProfile,
    Transform,
    TransformApi,
    TransformData,
    Vector,
    WindingOrder
} = require('affinity:geometry');
const { Collection, SpanCollection } = require('./collection.js');
const { HandleObject } = require('./handleobject.js');


// Create some object-oriented functions and add them to the Transform function's prototype
Object.assign(Transform.prototype, {
    setIdentity: function() { TransformApi.setIdentity(this); return this; },

    // mutating API functions:
    assign: function(source) { TransformApi.assign(this, source); return this; },
    compose: function(data) { TransformApi.compose(this, data); return this; },
    scale: function(x, y = x) { TransformApi.scale(this, x, y); return this;},
    shear: function(x, y) { TransformApi.shear(this, x, y); return this;},
    rotate: function(rads) { TransformApi.rotate(this, rads); return this;},
    translate: function(x, y) { TransformApi.translate(this, x, y); return this;},
    invert: function() { TransformApi.invert(this); return this; },
    
    // non-mutating API functions:
    decompose: function() { return TransformApi.decompose(this); },
    applyToPoint: function(pt) { return TransformApi.applyToPoint(this, pt); },
    applyToVector: function(vec) { return TransformApi.applyToVector(this, vec); },

    // multiply helpers.
    // sets this instance to be other * this
    premultiplyBy : function(other) { TransformApi.multiply(other, this, this); return this; },

    // sets this instance to be this * other
    postmultiplyBy : function(other) { TransformApi.multiply(this, other, this); return this; },

    // returns a new instance equal to other * this
    premultipliedBy : function(other) { const res = new Transform(); TransformApi.multiply(other, this, res); return res; },

    // returns a new instance equal to this * other
    postmultipliedBy : function(other) { const res = new Transform(); TransformApi.multiply(this, other, res); return res; },

    // returns a new instance equals to this * other; same as postMultipliedBy
    multiply : function(other) { const res = new Transform(); TransformApi.multiply(this, other, res); return res; },

    // mutating helpers
    around: function(x, y) { return this.translate(x, y).postmultiplyBy(Transform.createTranslate(-x, -y)); },
    /**
    * @deprecated Use around instead.
    */
    about: function(x, y) {
        console.warn("Using deprecated Transform.about() function. Use around() instead.");
        return this.around(x, y);
    },

    // non-mutating helpers
    clone: function() { const res = new Transform(); res.assign(this); return res; },
    scaled: function(x, y = x) { return this.clone().scale(x, y); },
    sheared: function(x, y) { return this.clone().shear(x, y); },
    rotated: function(rads) { return this.clone().rotate(rads); },
    translated: function(x, y) { return this.clone().translate(x, y); },
    toString: function() { return this.data.toString(); }
});

// Add some helper properties to Transforms
Object.defineProperties(Transform.prototype, {
    xAxis: { get() { return new Vector(this.data[0], this.data[3]); } },
    yAxis: { get() { return new Vector(this.data[1], this.data[4]); } },
    origin: { get() { return new Point(this.data[2], this.data[5]); } },
    inverted: { get() { return TransformApi.inverted(this); } }
});

// Also some "static" Transform helpers
Object.assign(Transform, {
    multiply: function(a, b) { const res = new Transform(); TransformApi.multiply(a, b, res); return res; },
    add: function(a, b) { const res = new Transform(); TransformApi.add(a, b, res); return res; },
    subtract: function(a, b) { const res = new Transform(); TransformApi.subtract(a, b, res); return res; },
    createIdentity: function() { return new Transform(); },
    createTranslate: function(x, y) { return new Transform().translate(x, y); },
    createRotate: function(rads) { return new Transform().rotate(rads); },
    createScale: function(x, y = x) { return new Transform().scale(x, y); },
    createShear: function(x, y) { return new Transform().shear(x, y); },
});


// Same for CubicBezier:
Object.assign(CubicBezier.prototype, {
    assign: function(source) { CubicBezierApi.assign(this, source); return this; },
    makeLine: function(ptA, ptB) { CubicBezierApi.makeLine(this, ptA, ptB); return this; },
    reverse: function() { CubicBezierApi.reverse(this); return this; },
    transform: function(xf) { CubicBezierApi.transform(this, xf); return this; },
    evaluate: function(t) { return CubicBezierApi.evaluate(this, t); },
    getCurvature: function(t) { return CubicBezierApi.getCurvature(this, t); },
    getNormal: function(t, normalise = true) { return CubicBezierApi.getNormal(this, t, normalise); },
    getTangent: function(t, normalise = true) { return CubicBezierApi.getTangent(this, t, normalise); },
    getClosestPoint: function(pt) { return CubicBezierApi.getClosestPoint(this, pt); },
    split: function(t) { return CubicBezierApi.split(this, t); },
    splitLeft: function(t) { return CubicBezierApi.splitLeft(this, t); },
    splitRight: function(t) { return CubicBezierApi.splitRight(this, t); },
    getParamAtLength: function(length) { return CubicBezierApi.getParamAtLength(this, length); },

    // non-mutating helpers
    clone: function() { const res = new CubicBezier(); res.assign(this); return res; },
    toString : function() { return `[${this.start} ${this.c1} ${this.c2} ${this.end}]`; },
    reversed: function() { return this.clone().reverse(); },
    transformed: function(xf) { return this.clone().transform(xf); }
});

Object.defineProperties(CubicBezier.prototype, {
    length: { get() { return CubicBezierApi.getLength(this); } },
    boundingBox: { get() { return CubicBezierApi.getBoundingBox(this); } },
    controlBox: { get() { return CubicBezierApi.getControlBox(this); } },
});

CubicBezier.createLine = function(ptA, ptB) { return new CubicBezier().makeLine(ptA, ptB); };


// sorting function for numbers
function numberComp(a, b) {
    return a - b;
}

// returns true IFF the ranges intersect
function rangesIntersect(a1, a2, b1, b2) {
    let a = [a1, a2].sort(numberComp);
    let b = [b1, b2].sort(numberComp);
    return !(a[1] <= b[0] || b[1] <= a[0]);
}

// returns the intersection of two ranges, or nothing if the ranges don't intersect
function intersectRanges(a1, a2, b1, b2) {
	let a = [a1, a2].sort(numberComp)
    let b = [b1, b2].sort(numberComp);
			
    if (a[1] < b[0] || b[1] < a[0]) {
    	return;
    }
    
    let res =
    [
   		Math.max(a[0], b[0]),
    	Math.min(a[1], b[1])
   	];
    return res;
}

// returns true IFF the rectangles overlap
function rectsIntersect(rc1, rc2) {
    let r =
        rangesIntersect(rc1.x, rc1.x + rc1.width, rc2.x, rc2.x + rc2.width) &&
        rangesIntersect(rc1.y, rc1.y + rc1.height, rc2.y, rc2.y + rc2.height);
 return r;
}

// returns the intersection of two rectangles, or nothing if the rectangles don't intersect
function intersectRects(rc1, rc2) {
	let a = intersectRanges(rc1.x, rc1.x + rc1.width, rc2.x, rc2.x + rc2.width);
	if (a) {
		let b = intersectRanges(rc1.y, rc1.y + rc1.height, rc2.y, rc2.y + rc2.height);
		if (b) {
			let res = new Rectangle(
				a[0],
				b[0],
				a[1] - a[0],
				b[1] - b[0],
			);
			return res;
		}
	}
}

function unionRanges(a1, a2, b1, b2) {
	let res = 
	[
		Math.min(a1, b1),
		Math.max(a2, b2)
	];
	return res;
}

function unionRects(rc1, rc2) {
	const xs = unionRanges(rc1.x, rc1.x + rc1.width, rc2.x, rc2.x + rc2.width);
	const ys = unionRanges(rc1.y, rc1.y + rc1.height, rc2.y, rc2.y + rc2.height);
	return new Rectangle(xs[0], ys[0], xs[1] - xs[0], ys[1] - ys[0]);
}

// returns true IFF a value is within a range
function valueInRange(r1, r2, value) {
    let range = [r1, r2].sort(numberComp);
    return value >= range[0] && value <= range[1];
}

// returns true if a points is within a rectangle
function pointInRect(rc, pt) {
    return valueInRange(rc.x, rc.x + rc.width, pt.x) && valueInRange(rc.y, rc.y + rc.height, pt.y);
}


class CurveBuilder extends HandleObject {
	constructor(handle) {
		if (handle === undefined)
			super(CurveBuilderApi.create());
		else
			super(handle);
	}

	static create() {
		return new CurveBuilder(CurveBuilderApi.create());
	}

	get [Symbol.toStringTag]() {
		return 'CurveBuilder';
	}

	clone() {
		return new CurveBuilder(CurveBuilderApi.clone(this.handle));
	}

	begin(point) {
		CurveBuilderApi.begin(this.handle, point);
		return this;
	}

	beginXY(x, y) {
		CurveBuilderApi.begin(this.handle, { x:x, y:y });
		return this;
	}

	lineTo(point) {
		CurveBuilderApi.lineTo(this.handle, point);
		return this;
	}

	lineToXY(x, y) {
		CurveBuilderApi.lineTo(this.handle, { x:x, y:y });
		return this;
	}

	lineRelative(vector) {
		CurveBuilderApi.lineRelative(this.handle, vector);
		return this;
	}

	lineRelativeXY(dx, dy) {
		CurveBuilderApi.lineRelative(this.handle, { x:dx, y:dy });
		return this;
	}

	close() {
		CurveBuilderApi.close(this.handle);
		return this;
	}

	createCurve() {
		const curveHandle = CurveBuilderApi.createCurve(this.handle);
		return new Curve(curveHandle);
	}

	transform(xf) {
		CurveBuilderApi.transform(this.handle, xf);
		return this;
	}

	translate(dx, dy) {
		return this.transform(Transform.createTranslate(dx, dy));
	}

	rotate(angle) {
		return this.transform(Transform.createRotate(angle));
	}

	scale(x, y) {
		if (y === undefined) {
			y = x;
		}
		return this.transform(Transform.createScale(x, y));
	}
    
    versineTo(point, versine) {
        CurveBuilderApi.versineTo(this.handle, point, versine);
        return this;
    }

    versineToXY(x, y, versine) {
        CurveBuilderApi.versineTo(this.handle, { x:x, y:y }, versine);
        return this;
    }
    
    versineRelative(vector, versine) {
        CurveBuilderApi.versineRelative(this.handle, vector, versine);
        return this;
    }

    versineRelativeXY(dx, dy, versine) {
        CurveBuilderApi.versineRelative(this.handle, { x:dx, y:dy }, versine);
        return this;
    }
    
    addArc(startAngle, endAngle, radius, reverse) {
        CurveBuilderApi.addArc(this.handle, startAngle, endAngle, radius, reverse);
        return this;
    }
    
    addBezier(c0, c1, end) {
        CurveBuilderApi.addBezier(this.handle, c0, c1, end);
        return this;
    }

    addBezierXY(c0x, c0y, c1x, c1y, endx, endy) {
        CurveBuilderApi.addBezier(this.handle, { x:c0x, y:c0y }, { x:c1x, y:c1y }, { x:endx, y:endy });
        return this;
    }
    
    addEllipse(startAngle, endAngle, majorRadius, minorRadius, rotation, reverse) {
        CurveBuilderApi.addEllipse(this.handle, startAngle, endAngle, majorRadius, minorRadius, rotation, reverse);
        return this;
    }
    
    setCorner(pointID, cornerData, force) {
        CurveBuilderApi.setCorner(this.handle, pointID, cornerData, force);
        return this;
    }

    bulgeTo(point, bulge) {
        CurveBuilderApi.bulgeTo(this.handle, point, bulge);
        return this;
    }

    bulgeToXY(x, y, bulge) {
        CurveBuilderApi.bulgeTo(this.handle, { x:x, y:y }, bulge);
        return this;
    }

    bulgeRelative(vector, bulge) {
        CurveBuilderApi.bulgeRelative(this.handle, vector, bulge);
        return this;
    }

    bulgeRelativeXY(dx, dy, bulge) {
        CurveBuilderApi.bulgeRelative(this.handle, { x:dx, y:dy }, bulge);
        return this;
    }

}


class Curve extends HandleObject {
    
    get [Symbol.toStringTag]() {
        return 'Curve';
    }
    
    constructor(handle) {
        super(handle);
    }
    
    static create() {
        return new Curve(CurveApi.create());
    }
    
    static createLine(p1, p2) {
        return new Curve(CurveApi.createLine(p1, p2));
    }

    static createLineXY(x1, y1, x2, y2) {
        return new Curve(CurveApi.createLine({ x:x1, y:y1 }, { x:x2, y:y2 }));
    }
    
    static createRectangle(rc) {
        return new Curve(CurveApi.createRectangle(rc));
    }
    
    static createEllipse(rc) {
        return new Curve(CurveApi.createEllipse(rc));
    }
    
    static createDiamond(rc) {
        return new Curve(CurveApi.createDiamond(rc));
    }
    
    static createLozenge(p1, p2, radius) {
        return new Curve(CurveApi.createLozenge(p1, p2, radius));
    }

    static createLozengeXY(x1, y1, x2, y2, radius) {
        return new Curve(CurveApi.createLozenge({ x:x1, y:y1 }, { x:x2, y:y2 }, radius));
    }
    
    static createPrecisionUnitCircle() {
        return new Curve(CurveApi.createPrecisionUnitCircle());
    }

    #convIndex(pointIndex) {
        return pointIndex < 0 ? Math.max(0, this.pointCount + pointIndex) : pointIndex; 
    }

    clone() {
        return new Curve(CurveApi.clone(this.handle));
    }
    
    transform(xf) {
        CurveApi.transform(this.handle, xf);
        return this;
    }
    
    translate(dx, dy) {
        return this.transform(Transform.createTranslate(dx, dy));
    }
    
    get pointCount() {
        return CurveApi.getPointCount(this.handle);
    }
    
    get length() {
        return CurveApi.getLength(this.handle);
    }
    
    get isClockwise() {
        return CurveApi.isClockwise(this.handle);
    }
    
    get isEmpty() {
        return CurveApi.isEmpty(this.handle);
    }
    
    get isClosed() {
        return CurveApi.isClosed(this.handle);
    }
    
    get isRectangle() {
        return CurveApi.isRectangle(this.handle);
    }
    
    get isEllipse() {
        return CurveApi.isEllipse(this.handle);
    }
    
    get isStraightLine() {
        return CurveApi.isStraightLine(this.handle);
    }
    
    get isPolyline() {
        return CurveApi.isPolyline(this.handle);
    }

    isRectangleTolerance(tolerance) {
        return CurveApi.isRectangleTolerance(this.handle, tolerance);
    }

    isEllipseTolerance(tolerance) {
        return CurveApi.isEllipseTolerance(this.handle, tolerance);
    }

    isStraightLineTolerance(tolerance) {
        return CurveApi.isStraightLineTolerance(this.handle, tolerance);
    }

    isPolylineTolerance(tolerance) {
        return CurveApi.isPolylineTolerance(this.handle, tolerance);
    }
    
    getApproxBoundingBox(transform = null) {
        const bbox = CurveApi.getApproxBoundingBox(this.handle, transform);
        return bbox.isSet ? bbox.bounds : null;
    }

    getExactBoundingBox(transform = null) {
        const bbox = CurveApi.getExactBoundingBox(this.handle, transform);
        return bbox.isSet ? bbox.bounds : null;
    }

    getBoundingBox(transform = null) {
        return this.getExactBoundingBox(transform);
    }
    
    get path() {
        return CurveApi.getPath(this.handle);
    }
    
    get points() {
        const handle = this.handle
        const span = {
            get length() {
                return CurveApi.getPointCount(handle);
            },
            at(index) {
                return CurveApi.getPoint(handle, index);
            }
        };
        return new SpanCollection(span);
    }
    
    getPoint(pointIndex) {
        const pt = CurveApi.getPoint(this.handle, this.#convIndex(pointIndex));
        return new Point(pt.x, pt.y);
    }
    
    setPoint(pointIndex, point) {
        CurveApi.setPoint(this.handle, this.#convIndex(pointIndex), point);
    }

    setPointXY(pointIndex, x, y) {
        CurveApi.setPoint(this.handle, this.#convIndex(pointIndex), { x:x, y:y });
    }
    
    getSubPath(pointIndex, count) {
        return CurveApi.getSubPath(this.handle, this.#convIndex(pointIndex), count);
    }
    
    getCorner(pointID) {
        return CurveApi.getCorner(this.handle, pointID);
    }
    
    setCorner(pointID, cornerData, force) {
        CurveApi.setCorner(this.handle, pointID, cornerData, force);
        return this;
    }
    
    cut(isParametric, distance) {
        let curves = CurveApi.cut(this.handle, isParametric, distance);
        return { "curveA": new Curve(curves.curveA), "curveB": new Curve(curves.curveB) };
    }
    
    getCubicBezier(pointIndex) {
        return CurveApi.getCubicBezier(this.handle, this.#convIndex(pointIndex));
    }
    
    get firstOnCurvePointIndex() {
        return CurveApi.getFirstOnCurvePointIndex(this.handle);
    }
    
    getNextOnCurvePointIndex(pointIndex, allowWrapIfClosed) {
        return CurveApi.getNextOnCurvePointIndex(this.handle, pointIndex, allowWrapIfClosed);
    }
    
    getPreviousOnCurvePointIndex(pointIndex, allowWrapIfClosed) {
        return CurveApi.getPreviousOnCurvePointIndex(this.handle, pointIndex, allowWrapIfClosed);
    }
    
    get lastOnCurvePointIndex() {
        return CurveApi.getLastOnCurvePointIndex(this.handle);
    }
    
    get beziers() {
        const me = this;
        const gen = function*() {
            for (let i = me.firstOnCurvePointIndex; i < me.lastOnCurvePointIndex; i = me.getNextOnCurvePointIndex(i)) {
                yield me.getCubicBezier(i);
            }
        }
        return new Collection(gen);
    }

    get nodeCount() {
        return CurveApi.getNodeCount(this.handle);
    }

    getNode(pointIndex) {
        return CurveApi.getNode(this.handle, this.#convIndex(pointIndex));
    }

    appendNode(node) {
        CurveApi.appendNode(this.handle, node);
    }

    enumerateNodes(callback) {
        CurveApi.enumerateNodes(this.handle, callback);
    }

    get nodes() {
        let res = [];
        this.enumerateNodes(node => {
            res.push(node);
            return EnumerationResult.Continue;
        });
        return res;
    }

    makeClosed() {
        CurveApi.makeClosed(this.handle);
    }

    generatePolygon(tolerance) {
        return CurveApi.generatePolygon(this.handle, tolerance);
    }

    get exactBoundingBox() {
        return this.getExactBoundingBox();
    }

    get approxBoundingBox() {
        return this.getApproxBoundingBox();
    }

    get boundingBox() {
        return this.getBoundingBox();
    }
}


class PolyCurve extends HandleObject {
    constructor(handle) {
        if (handle === undefined)
            super(PolyCurveApi.create())
        else
            super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PolyCurve';
    }

    static create() {
        return new PolyCurve(PolyCurveApi.create());
    }

    clone() {
        return new PolyCurve(PolyCurveApi.clone(this.handle));
    }

    clear() {
        PolyCurveApi.clear(this.handle);
    }

    transform(xf) {
        PolyCurveApi.transform(this.handle, xf);
        return this;
    }

    get curveCount() {
        return PolyCurveApi.getCurveCount(this.handle);
    }

    getApproxBoundingBox(transform = null) {
        const bbox = PolyCurveApi.getApproxBoundingBox(this.handle, transform);
        return bbox.isSet ? bbox.bounds : null;
    }

    getExactBoundingBox(transform = null) {
        const bbox = PolyCurveApi.getExactBoundingBox(this.handle, transform);
        return bbox.isSet ? bbox.bounds : null;
    }

    getControlBoundingBox(transform = null) {
        const bbox = PolyCurveApi.getControlBoundingBox(this.handle, transform);
        return bbox.isSet ? bbox.bounds : null;
    }

    getBoundingBox(transform = null) {
        return this.getExactBoundingBox(transform);
    }

    at(index) {
        return new Curve(PolyCurveApi.getCurve(this.handle, index));
    }

    *[Symbol.iterator]() {
        for (let i = 0; i < this.curveCount; ++i) {
            yield this.at(i);
        }
    }

    get curves() {
        return new SpanCollection(new PolyCurveCurves(this.handle));
    }
    
    addCurve(curve) {
        return PolyCurveApi.addCurve(this.handle, curve.handle);
    }

    removeEmptyCurves() {
        PolyCurveApi.removeEmptyCurves(this.handle);
    }

    get approxBoundingBox() {
        return this.getApproxBoundingBox();
    }

    get exactBoundingBox() {
        return this.getExactBoundingBox();
    }

    get controlBoundingBox () {
        return this.getControlBoundingBox();
    }

    get boundingBox() {
        return this.getBoundingBox();
    }
}


// Collection for the curves in a PolyCurve
class PolyCurveCurves extends HandleObject {

    constructor(polyCurveHandle) {
        super(polyCurveHandle);
    }

    at(index) {
        return new Curve(PolyCurveApi.getCurve(this.handle, index));
    }

    get length() {
        return PolyCurveApi.getCurveCount(this.handle);
    }
}


class PolyPolyCurve extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PolyPolyCurve';
    }

    clone() {
        return new PolyPolyCurve(PolyPolyCurveApi.clone(this.handle));
    }

    containsPoint(point, allowUnclosed, windingOrder, performBoundsCheck) {
        return PolyPolyCurveApi.containsPoint(this.handle, point, allowUnclosed, windingOrder, performBoundsCheck);
    }

    intersectsRectangle(transform, rectangle, closeCurves) {
        return PolyPolyCurveApi.intersectsRectangle(this.handle, transform, rectangle, closeCurves);
    }

    isNearPoint(point, xTolerance, yTolerance, expansionTolerance) {
        return PolyPolyCurveApi.isNearPoint(this.handle, point, xTolerance, yTolerance, expansionTolerance);
    }

    isNearRectangle(rectangle, tolerance) {
        return PolyPolyCurveApi.isNearRectangle(this.handle, rectangle, tolerance);
    }

    get hasJoins() {
        return PolyPolyCurveApi.hasJoins(this.handle);
    }

    get hasCorners() {
        return PolyPolyCurveApi.hasCorners(this.handle);
    }

    get hasCurves() {
        return PolyPolyCurveApi.hasCurves(this.handle);
    }

    get polyCurveCount() {
        return PolyPolyCurveApi.getPolyCurveCount(this.handle);
    }

    getPolyCurve(index) {
        return new PolyCurve(PolyPolyCurveApi.getPolyCurve(this.handle, index));
    }

    getPolyCurveTransform(index) {
        return PolyPolyCurveApi.getPolyCurveTransform(this.handle, index);
    }

    getTransformedPolyCurve(index) {
        return new PolyCurve(PolyPolyCurveApi.getTransformedPolyCurve(this.handle, index));
    }

    getApproxBoundingBox(transform = null) {
        const bbox = PolyPolyCurveApi.getApproxBoundingBox(this.handle, transform);
        return bbox.isSet ? bbox.bounds : null;
    }

    getExactBoundingBox(transform = null) {
        const bbox = PolyPolyCurveApi.getExactBoundingBox(this.handle, transform);
        return bbox.isSet ? bbox.bounds : null;
    }

    getBoundingBox(transform = null) {
        return this.getExactBoundingBox(transform);
    }

    addRectangle(rectangle, transform) {
        PolyPolyCurveApi.addRectangle(this.handle, rectangle, transform);
    }

    addPolyCurve(polyCurve, transform) {
        PolyPolyCurveApi.addPolyCurve(this.handle, polyCurve.handle, transform);
    }

    addPolyPolyCurve(polyPolyCurve, transform) {
        PolyPolyCurveApi.addPolyPolyCurve(this.handle, polyPolyCurve.handle, transform);
    }

    transform(xf) {
        PolyPolyCurveApi.transform(this.handle, xf);
        return this;
    }

    get polyCurves() {
        return new SpanCollection(new PolyPolyCurvePolyCurves(this.handle));
    }

    get approxBoundingBox() {
        return this.getApproxBoundingBox();
    }

    get exactBoundingBox() {
        return this.getExactBoundingBox();
    }

    get boundingBox() {
        return this.getBoundingBox();
    }

    *[Symbol.iterator]() {
        for (let i = 0; i < this.polyCurveCount; ++i) {
            yield this.getPolyCurve(i);
        }
    }
}


class PolyPolyCurvePolyCurves extends HandleObject {
    constructor(polyPolyCurveHandle) {
        super(polyPolyCurveHandle);
    }

    at(index) {
        return new PolyCurve(PolyPolyCurveApi.getPolyCurve(this.handle, index));
    }

    get length() {
        return PolyPolyCurveApi.getPolyCurveCount(this.handle);
    }
}


class TransformBuilder {
	#transform;
	
	constructor() {
		this.#transform = Transform.createIdentity();
	}
	
    translate(xy) {
		return this.translateXY(xy.x, xy.y);
	}

	translateXY(x, y) {
		this.#transform = Transform.createTranslate(x, y).multiply(this.#transform);
		return this;
	}
	
	scale(xy) {
		return this.scaleXY(xy.x, xy.y);
	}

    scaleXY(x, y) {
		this.#transform = Transform.createScale(x, y).multiply(this.#transform);
		return this;
	}
	
	rotate(rads) {
		this.#transform = Transform.createRotate(rads).multiply(this.#transform);
		return this;
	}
	
	shear(xy) {
		return this.shearXY(xy.x, xy.y);
	}

    shearXY(x, y) {
		this.#transform = Transform.createShear(x, y).multiply(this.#transform);
		return this;
	}
	
	get transform() {
		return this.#transform;
	}
}

class Spline extends HandleObject {
    
    get [Symbol.toStringTag]() {
        return 'Spline';
    }
    
    constructor(handle) {
        super(handle);
    }
    
    static create() {
        return new Spline(SplineApi.create());
    }
    
    static createFromProfile(profile) {
        return new Spline(SplineApi.createFromProfile(profile));
    }
    
    static createFromPoints(points) {
        return new Spline(SplineApi.createFromPoints(points));
    }
    
    #convIndex(pointIndex) {
        return pointIndex < 0 ? Math.max(0, this.pointCount + pointIndex) : pointIndex; 
    } 

    clone() {
        return new Spline(SplineApi.clone(this.handle));
    }
    
    get pointCount() {
        return SplineApi.getPointCount(this.handle);
    }
    
    get isLinear() {
        return SplineApi.isLinear(this.handle);
    }
    
    set isLinear(value) {
        return SplineApi.setIsLinear(this.handle, value);
    }
    
    getPoint(pointIndex) {
        return SplineApi.getPoint(this.handle, this.#convIndex(pointIndex));
    }
    
    insertPoint(point) {
        return SplineApi.insertPoint(this.handle, point);
    }

    insertPointXY(x, y) {
        return SplineApi.insertPoint(this.handle, { x:x, y:y });
    }
    
    replaceOrInsertPoint(point) {
        return SplineApi.replaceOrInsertPoint(this.handle, point);
    }

    replaceOrInsertPointXY(x, y) {
        return SplineApi.replaceOrInsertPoint(this.handle, { x:x, y:y });
    }
    
    findPoint(point) {
        return SplineApi.findPoint(this.handle, point);
    }

    findPointXY(x, y) {
        return SplineApi.findPoint(this.handle, { x:x, y:y });
    }
    
    removePoint(pointIndex) {
        return SplineApi.removePoint(this.handle, this.#convIndex(pointIndex));
    }
    
    clear() {
        return SplineApi.clear(this.handle);
    }
    
    *points() {
        const num = this.pointCount;
        for (let i = 0; i < num; i++) {
            yield this.getPoint(i);
        }
    }
}

class Polygon extends HandleObject {
    
    get [Symbol.toStringTag]() {
        return 'Polygon';
    }
    
    constructor(handle) {
        super(handle);
    }
    
    static create() {
        return new Polygon(PolygonApi.create());
    }
    
    static createLine(p1, p2) {
        return new Polygon(PolygonApi.createLine(p1, p2));
    }

    static createLineXY(x1, y1, x2, y2) {
        return new Polygon(PolygonApi.createLine({ x:x1, y:y1 }, { x:x2, y:y2 }));
    }
    
    static createTriangle(p1, p2, p3) {
        return new Polygon(PolygonApi.createTriangle(p1, p2, p3));
    }

    static createTriangleXY(x1, y1, x2, y2, x3, y3) {
        return new Polygon(PolygonApi.createTriangle({ x:x1, y:y1 }, { x:x2, y:y2 }, { x:x3, y:y3 }));
    }
    
    static createRectangle(rect) {
        return new Polygon(PolygonApi.createRectangle(rect));
    }

    #convIndex(pointIndex) {
        return pointIndex < 0 ? Math.max(0, this.pointCount + pointIndex) : pointIndex; 
    }

    get isEmpty() {
        return PolygonApi.isEmpty(this.handle);
    }
    
    get isClosed() {
        return PolygonApi.isClosed(this.handle);
    }
    
    get isRectangle() {
        return PolygonApi.isRectangle(this.handle);
    }
    
    get isClockwise() {
        return PolygonApi.isClockwise(this.handle);
    }

    getBoundingBox(transform = null) {
        const bbox = PolygonApi.getBoundingBox(this.handle, transform);
        return bbox.isSet ? bbox.bounds : null;
    }

    get boundingBox() {
        return this.getBoundingBox();
    }
    
    get pointCount() {
        return PolygonApi.getPointCount(this.handle);
    }
    
    getPoint(pointIndex) {
        return PolygonApi.getPoint(this.handle, this.#convIndex(pointIndex));
    }

    enumeratePoints(callback) {
        return PolygonApi.enumeratePoints(this.handle, callback);
    }
    
    clear() {
        return PolygonApi.clear(this.handle);
    }
    
    addPoint(point) {
        return PolygonApi.addPoint(this.handle, point);
    }

    addPointXY(x, y) {
        return PolygonApi.addPoint(this.handle, { x:x, y:y });
    }
    
    insertPoint(pointIndex, point) {
        return PolygonApi.insertPoint(this.handle, this.#convIndex(pointIndex), point);
    }

    insertPointXY(pointIndex, x, y) {
        return PolygonApi.insertPoint(this.handle, this.#convIndex(pointIndex), { x:x, y:y });
    }
    
    close() {
        return PolygonApi.close(this.handle);
    }
    
    reverse() {
        return PolygonApi.reverse(this.handle);
    }

    clone() {
        return new Polygon(PolygonApi.clone(this.handle));
    }
}

module.exports.intersectRanges = intersectRanges;
module.exports.intersectRects = intersectRects;
module.exports.pointInRect = pointInRect;
module.exports.rangesIntersect = rangesIntersect;
module.exports.rectsIntersect = rectsIntersect;
module.exports.unionRanges = unionRanges;
module.exports.unionRects = unionRects;
module.exports.valueInRange = valueInRange;

module.exports.CubicBezier = CubicBezier;
module.exports.Curve = Curve;
module.exports.CurveBuilder = CurveBuilder;
module.exports.CurveCornerData = CurveCornerData;
module.exports.CurveCornerType = CurveCornerType;
module.exports.CurveNode = CurveNode;
module.exports.CurveNodeStyle = CurveNodeStyle;
module.exports.CurveNodeType = CurveNodeType;
module.exports.Point = Point;
module.exports.PolyCurve = PolyCurve;
module.exports.PolyPolyCurve = PolyPolyCurve;
module.exports.Polygon = Polygon;
module.exports.Rectangle = Rectangle;
module.exports.Size = Size;
module.exports.SizeInt = SizeInt;
module.exports.Spline = Spline;
module.exports.SplineProfile = SplineProfile;
module.exports.Transform = Transform;
module.exports.TransformData = TransformData;
module.exports.TransformBuilder = TransformBuilder;
module.exports.Vector = Vector;
module.exports.WindingOrder = WindingOrder;
