'use strict';

const { CurvesInterfaceApi, SubSelectionType } = require('affinity:dom');
const { WindingOrder } = require('affinity:geometry');
const { PolyCurve, PolyPolyCurve } = require('./geometry.js');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');
const SelectionsModule = require('./selections.js');

class CurvesInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CurvesInterface';
    }

    get polyCurve() {
        return new PolyCurve(CurvesInterfaceApi.getCurves(this.handle));
    }

    get corneredPolyCurve() {
        return new PolyCurve(CurvesInterfaceApi.getCorneredCurves(this.handle));
    }

    get polyPolyCurves() {
        return new PolyPolyCurve(CurvesInterfaceApi.getPolyPolyCurves(this.handle));
    }

    get windingOrder() {
        return CurvesInterfaceApi.getWindingOrder(this.handle);
    }

    get domainTransform() {
        return CurvesInterfaceApi.getDomainTransform(this.handle);
    }

    getSubSelectionCount(subSelectionType) {
        return CurvesInterfaceApi.getSubSelectionCount(this.handle, subSelectionType);
    }

    getSubSelection(subSelectionType, index) {
        return SelectionsModule.createTypedSubSelection(CurvesInterfaceApi.getSubSelection(this.handle, subSelectionType, index));
    }

    get node() {
        return NodesModule.createTypedNode(CurvesInterfaceApi.getNode(this.handle));
    }

    get isMutable() {
        return CurvesInterfaceApi.isMutable(this.handle);
    }
}

module.exports.CurvesInterface = CurvesInterface;
module.exports.SubSelectionType = SubSelectionType;
module.exports.WindingOrder = WindingOrder;
