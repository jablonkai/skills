'use strict';

const { ContentType, TransparencyInterfaceApi } = require('affinity:dom');
const { FillDescriptor } = require('./fills.js');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

// monkey patches:
require('/geometry.js');

class TransparencyInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TransparencyInterface';
    }

    get fillDescriptor() {
        return new FillDescriptor(TransparencyInterfaceApi.getFillDescriptor(this.handle));
    }

    get isTransparencyNone() {
        return TransparencyInterfaceApi.isTransparencyNone(this.handle);
    }

    get domainTransform() {
        return TransparencyInterfaceApi.getDomainTransform(this.handle);
    }

    get contentType() {
        return TransparencyInterfaceApi.getContentType(this.handle);
    }

    get node() {
        return NodesModule.createTypedNode(TransparencyInterfaceApi.getNode(this.handle));
    }

    get isAnchoredToSpread() {
        return this.fillDescriptor.isAnchoredToSpread;
    }

    setIsAnchoredToSpread(anchored, applyToAllFills, preview) {
        const node = this.node;
        const doc = node.document;
        return doc.setTransparencyFillIsAnchoredToSpread(anchored, node, {applyToAllFills: applyToAllFills}, preview);
    }

    set isAnchoredToSpread(value) {
        this.setIsAnchoredToSpread(value);
    }
}

module.exports.ContentType = ContentType;
module.exports.TransparencyInterface = TransparencyInterface;
