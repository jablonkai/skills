'use strict';

const { AntialiasingMode, BlendModeInterfaceApi, BlendOptionsApi } = require('affinity:dom');
const { BlendMode } = require('affinity:common');
const { Spline } = require('./geometry.js');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class BlendOptions extends HandleObject {
    get [Symbol.toStringTag]() {
        return 'BlendOptions';
    }
    
    constructor(handle) {
        super(handle);
    }

    get isBlendOptions() {
        return true;
    }
    
    get gamma() {
        return BlendOptionsApi.getGamma(this.handle);
    }
    
    set gamma(value) {
        BlendOptionsApi.setGamma(this.handle, value);
    }
    
    get masterSourceLayerRanges() {
        return new Spline(BlendOptionsApi.getMasterSourceLayerRanges(this.handle));
    }
    
    set masterSourceLayerRanges(spline) {
        BlendOptionsApi.setMasterSourceLayerRanges(this.handle, spline.handle);
    }
    
    get masterUnderlyingCompositionRanges() {
        return new Spline(BlendOptionsApi.getMasterUnderlyingCompositionRanges(this.handle));
    }
    
    set masterUnderlyingCompositionRanges(spline) {
        BlendOptionsApi.setMasterUnderlyingCompositionRanges(this.handle, spline.handle);
    }
    
    getChannelSourceLayerRanges(channel) {
        return new Spline(BlendOptionsApi.getChannelSourceLayerRanges(this.handle, channel));
    }
    
    setChannelSourceLayerRanges(channel, spline) {
        BlendOptionsApi.setChannelSourceLayerRanges(this.handle, channel, spline.handle);
    }
    
    getChannelUnderlyingCompositionRanges(channel) {
        return new Spline(BlendOptionsApi.getChannelUnderlyingCompositionRanges(this.handle, channel));
    }
    
    setChannelUnderlyingCompositionRanges(channel, spline) {
        BlendOptionsApi.setChannelUnderlyingCompositionRanges(this.handle, channel, spline.handle);
    }
}

class BlendModeInterface extends HandleObject {
    get [Symbol.toStringTag]() {
        return 'BlendModeInterface';
    }
    
    constructor(handle) {
        super(handle);
    }

    get isBlendModeInterface() {
        return true;
    }
    
    get blendMode() {
        return BlendModeInterfaceApi.getBlendMode(this.handle);
    }
    
    get blendOptions() {
        return new BlendOptions(BlendModeInterfaceApi.getBlendOptions(this.handle));
    }
    
    get antialiasingMode() {
        return BlendModeInterfaceApi.getAntialiasingMode(this.handle);
    }

    get node() {  
        return NodesModule.createTypedNode(BlendModeInterfaceApi.getNode(this.handle));
    }

    setBlendMode(blendMode, setPassthrough) {
        const node = this.node;
        const doc = node.document;
        return doc.setBlendMode(blendMode, setPassthrough, node);
    }
}

module.exports.BlendOptions = BlendOptions;
module.exports.BlendModeInterface = BlendModeInterface;
module.exports.BlendMode = BlendMode;
module.exports.AntialiasingMode = AntialiasingMode;
