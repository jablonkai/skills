'use strict';

const { EnumerationResult } = require('affinity:common');
const { ContentType, LineStyleInterfaceApi } = require('affinity:dom');
const { FillDescriptor } = require('./fills.js');
const { HandleObject } = require('./handleobject.js');
const { LineStyleDescriptor} = require('./linestyle.js');

// cyclics:
const NodesModule = require('./nodes.js');

// Transforms:
require('/geometry.js');

class LineStyleInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LineStyleInterface';
    }

    get isNoFill() {
        return LineStyleInterfaceApi.isNoFill(this.handle);
    }

    get isLineStyleVisible() {
        return LineStyleInterfaceApi.isLineStyleVisible(this.handle);
    }

    get domainTransform() {
        return LineStyleInterfaceApi.getDomainTransform(this.handle);
    }

    get scalarDomainTransform() {
        return LineStyleInterfaceApi.getScalarDomainTransform(this.handle);
    }

    get contentType() {
        return LineStyleInterfaceApi.getContentType(this.handle);
    }

    get descriptorCount() {
        return LineStyleInterfaceApi.getDescriptorCount(this.handle);
    }

    getCurrentFillDescriptor(obeyScaleWithObject = true) {
        return new FillDescriptor(LineStyleInterfaceApi.getCurrentFillDescriptor(this.handle, obeyScaleWithObject));
    }

    getCurrentLineStyleDescriptor() {
        return new LineStyleDescriptor(LineStyleInterfaceApi.getCurrentLineStyleDescriptor(this.handle));
    }

    getCurrentDescriptors(obeyScaleWithObject = true) {
        const descriptors = LineStyleInterfaceApi.getCurrentDescriptors(this.handle, obeyScaleWithObject);
        return {
            fill: new FillDescriptor(descriptors.fill),
            lineStyle: new LineStyleDescriptor(descriptors.lineStyle),
        };
    }

    get currentIndex() {
        return LineStyleInterfaceApi.getCurrentIndex(this.handle);
    }

    getFillDescriptor(index, obeyScaleWithObject = true) {
        return new FillDescriptor(LineStyleInterfaceApi.getFillDescriptor(this.handle, index, obeyScaleWithObject));
    }

    getLineStyleDescriptor(index) {
        return new LineStyleDescriptor(LineStyleInterfaceApi.getLineStyleDescriptor(this.handle, index));
    }

    getDescriptors(index, obeyScaleWithObject = true) {
        const descriptors = LineStyleInterfaceApi.getDescriptors(this.handle, index, obeyScaleWithObject);
        return {
            fill: new FillDescriptor(descriptors.fill),
            lineStyle: new LineStyleDescriptor(descriptors.lineStyle),
        };
    }

    enumerateFillDescriptors(callback, obeyScaleWithObject = true) {
        if (typeof callback === 'function') {
            function wrapped(fillDescriptorHandle) {
                return callback(new FillDescriptor(fillDescriptorHandle));
            }
            return LineStyleInterfaceApi.enumerateFillDescriptors(this.handle, obeyScaleWithObject, wrapped);
        }
        return LineStyleInterfaceApi.enumerateFillDescriptors(this.handle, obeyScaleWithObject, callback);
    }

    enumerateLineStyleDescriptors(callback) {
        if (typeof callback === 'function') {
            function wrapped(lineStyleDescriptorHandle) {
                return callback(new LineStyleDescriptor(lineStyleDescriptorHandle));
            }
            return LineStyleInterfaceApi.enumerateLineStyleDescriptors(this.handle, wrapped);
        }
        return LineStyleInterfaceApi.enumerateLineStyleDescriptors(this.handle, callback);
    }

    enumerateDescriptors(callback, obeyScaleWithObject) {
        if (typeof callback === 'function') {
            function wrapped(fillDescriptorHandle, lineStyleDescriptorHandle) {
                return callback(new FillDescriptor(fillDescriptorHandle), new LineStyleDescriptor(lineStyleDescriptorHandle));
            }
            return LineStyleInterfaceApi.enumerateDescriptors(this.handle, obeyScaleWithObject, wrapped);
        }
        return LineStyleInterfaceApi.enumerateDescriptors(this.handle, obeyScaleWithObject, callback);
    }

    get node() {
        return NodesModule.createTypedNode(LineStyleInterfaceApi.getNode(this.handle));
    }
    
    // aliases
    get penFillDescriptor() {
        return this.getCurrentFillDescriptor(true);
    }

    get lineStyleDescriptor() {
        return this.getCurrentLineStyleDescriptor();
    }

    // helpers
    get lineStyle() {
        return this.lineStyleDescriptor.lineStyle;
    }

    setCurrentLineStyle(lineStyle, options, preview) {
        const node = this.node;
        const doc = node.document;
        doc.setLineStyle(lineStyle, node, options, preview);
    }
    
    set lineStyle(lineStyle) {
        this.setCurrentLineStyle(lineStyle, null, false);
    }

    setCurrentFillDescriptor(fillDescriptorOrColour, options, preview) {
        const node = this.node;
        const doc = node.document;
        doc.setPenFillDescriptor(fillDescriptorOrColour, node, options, preview);
    }
    
    set penFillDescriptor(fillDescriptorOrColour) {
        this.setCurrentFillDescriptor(fillDescriptorOrColour, null, false);
    }

    setCurrentLineStyleDescriptor(descriptor, options, preview) {
        const node = this.node;
        const doc = node.document;
        doc.setLineStyleDescriptor(descriptor, node, options, preview);
    }
    
    set lineStyleDescriptor(descriptor) {
        this.setCurrentLineStyleDescriptor(descriptor, null, false);
    }

    get lineWeight() {
        return this.lineStyle.weight;
    }

    set lineWeight(pixels) {
        const node = this.node;
        const doc = node.document;
        doc.setLineWeight(pixels, node, false);
    }

    get lineWeightPts() {
        const node = this.node;
        const document = node.document;
        const pixelsToPoints = 72 / document.dpi;
        return this.lineStyle.weight * pixelsToPoints;
    }

    set lineWeightPts(pts) {
        const node = this.node;
        const doc = node.document;
        doc.setLineWeightPts(pts, node, false);
    }

    get lineType() {
        return this.lineStyle.type;
    }

    set lineType(type) {
        const node = this.node;
        const doc = node.document;
        doc.setLineType(type, node, false);
    }

    get lineCap() {
        return this.lineStyle.cap;
    }

    set lineCap(cap) {
        const node = this.node;
        const doc = node.document;
        doc.setLineCap(cap, node, false);
    }

    get lineJoin() {
        return this.lineStyle.join;
    }

    set lineJoin(join) {
        const node = this.node;
        const doc = node.document;
        doc.setLineJoin(join, node, false);
    }

    get dashPhase() {
        return this.lineStyle.dashPhase;
    }

    set dashPhase(phase) {
        const node = this.node;
        const doc = node.document;
        doc.setDashPhase(phase, node, false);
    }

    get dashPattern() {
        return this.lineStyle.dashPattern;
    }

    set dashPattern(pattern) {
        const node = this.node;
        const doc = node.document;
        doc.setDashPattern(pattern, node, false);
    }

    get hasBalancedDashes() {
        return this.lineStyle.hasBalancedDashes;
    }

    set hasBalancedDashes(balanced) {
        const node = this.node;
        const doc = node.document;
        doc.setBalancedDashes(balanced, node, false);
    }

    get strokeAlignment() {
        return this.lineStyleDescriptor.strokeAlignment;
    }

    set strokeAlignment(alignment) {
        const node = this.node;
        const doc = node.document;
        doc.setStrokeAlignment(alignment, node, false);
    }

    getAllFillDescriptors(obeyScaleWithObject = true) {
        let descriptors = [];
        this.enumerateFillDescriptors((descriptor) => {
            descriptors.push(descriptor);
            return EnumerationResult.Continue;
        }, obeyScaleWithObject);
        return descriptors;
    }

    getAllLineStyleDescriptors() {
        let descriptors = [];
        this.enumerateLineStyleDescriptors((descriptor) => {
            descriptors.push(descriptor);
            return EnumerationResult.Continue;
        });
        return descriptors;
    }

    get penFillDescriptors() {
        return this.getAllFillDescriptors(true);
    }

    get lineStyleDescriptors() {
        return this.getAllLineStyleDescriptors();
    }

    get isAnchoredToSpread() {
        return this.penFillDescriptor.isAnchoredToSpread;
    }

    setIsAnchoredToSpread(anchored, applyToAllFills, preview) {
        const node = this.node;
        const doc = node.document;
        return doc.setPenFillIsAnchoredToSpread(anchored, node, {applyToAllFills: applyToAllFills}, preview);
    }

    set isAnchoredToSpread(value) {
        this.setIsAnchoredToSpread(value);
    }
}

module.exports.ContentType = ContentType;
module.exports.LineStyleInterface = LineStyleInterface;
