'use strict';

const { EnumerationResult } = require('affinity:common');
const { BrushFillInterfaceApi, ContentType } = require('affinity:dom');
const { FillDescriptor } = require('./fills.js');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');
const SelectionsModule = require('./selections.js');

// monkey patches:
require('/geometry.js');

class BrushFillInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'BrushFillInterface';
    }

    get isBrushFillInterface() {
        return true;
    }
    
    get isNoFill() {
        return BrushFillInterfaceApi.isNoFill(this.handle);
    }

    getIsVisible(minAlpha) {
        return BrushFillInterfaceApi.isBrushFillVisible(this.handle, minAlpha);
    }

    domainTransform() {
        return BrushFillInterfaceApi.getDomainTransform(this.handle);
    }

    get contentType() {
        return BrushFillInterfaceApi.getContentType(this.handle);
    }

    get descriptorCount() {
        return BrushFillInterfaceApi.getDescriptorCount(this.handle);
    }

    getDescriptor(index, obeyScaleWithObject = true) {
        return new FillDescriptor(BrushFillInterfaceApi.getDescriptor(this.handle, index, obeyScaleWithObject));
    }

    getCurrentDescriptor(obeyScaleWithObject = true) {
        return new FillDescriptor(BrushFillInterfaceApi.getCurrentDescriptor(this.handle, obeyScaleWithObject));
    }

    get currentIndex() {
        return BrushFillInterfaceApi.getCurrentIndex(this.handle);
    }

    enumerateDescriptors(callback, obeyScaleWithObject = true) {
        function wrapped(fillDescriptorHandle) {
            return callback(fillDescriptorHandle ? new FillDescriptor(fillDescriptorHandle) : null);
        }
        return BrushFillInterfaceApi.enumerateDescriptors(this.handle, obeyScaleWithObject, wrapped);
    }

    get subSelectionCount() {
        return BrushFillInterfaceApi.getSubSelectionCount(this.handle);
    }

    getSubSelection(index) {
        return SelectionsModule.createTypedSubSelection(BrushFillInterfaceApi.getSubSelection(this.handle, index));
    }

    get node() {
        return NodesModule.createTypedNode(BrushFillInterfaceApi.getNode(this.handle));
    }

    // helpers
    setCurrentDescriptor(fillDescriptorOrColour, options, preview) {
        const node = this.node;
        const doc = node.document;
        doc.setBrushFillDescriptor(fillDescriptorOrColour, node, options, preview);
    }

    get currentDescriptor() {
        return this.getCurrentDescriptor(true);
    }

    set currentDescriptor(fillDescriptorOrColour) {
        this.setCurrentDescriptor(fillDescriptorOrColour, null, false);
    }
    
    getAllDescriptors(obeyScaleWithObject = true) {
        let descriptors = [];
        this.enumerateDescriptors(descriptor => {
            descriptors.push(descriptor);
            return EnumerationResult.Continue;
        }, obeyScaleWithObject);
        return descriptors;
    }

    get isAnchoredToSpread() {
        return this.currentDescriptor.isAnchoredToSpread
    }

    setIsAnchoredToSpread(anchored, applyToAllFills, preview) {
        const node = this.node;
        const doc = node.document;
        return doc.setBrushFillIsAnchoredToSpread(anchored, node, {applyToAllFills: applyToAllFills}, preview);
    }

    set isAnchoredToSpread(value) {
        this.setIsAnchoredToSpread(value);
    }

    // aliases
    get fillDescriptor() {
        return this.getCurrentDescriptor(true);
    }

    set fillDescriptor(fillDescriptorOrColour) {
        this.setCurrentDescriptor(fillDescriptorOrColour, null, false);
    }

    get allDescriptors() {
        return this.getAllDescriptors();
    }
}

module.exports.BrushFillInterface = BrushFillInterface;
module.exports.ContentType = ContentType;
