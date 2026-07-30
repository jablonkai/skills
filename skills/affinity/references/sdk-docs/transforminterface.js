'use strict';

const { TransformInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

// monkey patches:
require('/geometry.js');

class TransformInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TransformInterface';
    }

    get transform() {
        return TransformInterfaceApi.getTransform(this.handle, false);
    }

    getTransform(forceConstraints) {
        return TransformInterfaceApi.getTransform(this.handle, forceConstraints);
    }

    get unconstrainedTransform() {
        return TransformInterfaceApi.getUnconstrainedTransform(this.handle);
    }

    get frameTextScale() {
        return TransformInterfaceApi.getFrameTextScale(this.handle);
    }

    get storyPinPathTransform() {
        return TransformInterfaceApi.getStoryPinPathTransform(this.handle);
    }

    get prefersAspectRatioLockedResize() {
        return TransformInterfaceApi.prefersAspectRatioLockedResize(this.handle);
    }

    get focalPoint() {
        return TransformInterfaceApi.getFocalPoint(this.handle);
    }

    get domainTransform() {
        return TransformInterfaceApi.getDomainTransform(this.handle);
    }

    get node() {
        return NodesModule.createTypedNode(TransformInterfaceApi.getNode(this.handle));
    }

    getDomainTransform() {
        return TransformInterfaceApi.getDomainTransform(this.handle);
    }

    getTextFrameScaleToDomainTransform() {
        return TransformInterfaceApi.getTextFrameScaleToDomainTransform(this.handle);
    }

    getNode() {
        return NodesModule.createTypedNode(TransformInterfaceApi.getNode(this.handle));
    }
}

module.exports.TransformInterface = TransformInterface;
