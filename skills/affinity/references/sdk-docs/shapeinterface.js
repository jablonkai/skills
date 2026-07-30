'use strict';

const { ShapeInterfaceApi, } = require('affinity:dom');
const { ShapeType } = require('affinity:geometry');
const { HandleObject } = require('./handleobject.js');
const { createTypedShape } = require('./shapes.js');

// cyclics:
const NodesModule = require('./nodes.js');

// monkey patches:
require('/geometry.js');

class ShapeInterface extends HandleObject {

    constructor(handle) {
        super(handle);
    }

    get isShapeInterface() {
        return true;
    }

    get boundingBox() {
        return ShapeInterfaceApi.getShapeBoundingBox(this.handle);
    }

    get shape() {
        let shapeHandle = ShapeInterfaceApi.getShape(this.handle);
        return createTypedShape(shapeHandle);
    }

    get type() {
        return ShapeInterfaceApi.getType(this.handle);
    }

    get domainTransform() {
        return ShapeInterfaceApi.getDomainTransform(this.handle);
    }

    get node() {
        return NodesModule.createTypedNode(ShapeInterfaceApi.getNode(this.handle));
    }

    // mutating helpers
    setShape(shape, preview) {
        const node = this.node;
        return node.document.setShape(shape, node, null, preview);
    }

    // mutating async helpers
    setShapeAsync(shape, callback, preview) {
        const node = this.node;
        return node.document.setShapeAsync(shape, node, callback, preview);
    }

    // mutating properties
    set shape(shape) {
        this.setShape(shape);
    }
}

module.exports.ShapeInterface = ShapeInterface;
module.exports.ShapeType = ShapeType;
