'use strict';

const { EnumerationResult } = require('affinity:common');
const { LayerEffectsInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');
const { createTypedLayerEffect } = require('./layereffects.js');

// cyclics:
const NodesModule = require('./nodes.js');

class LayerEffectsInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LayerEffectsInterface';
    }

    get effectCount() {
        return LayerEffectsInterfaceApi.getEffectCount(this.handle);
    }

    getEffect(index) {
        return createTypedLayerEffect(LayerEffectsInterfaceApi.getEffect(this.handle, index));
    }

    enumerateEffects(callback) {
        if (typeof callback === 'function') {
            function wrapped(effectHandle) {
                return callback(createTypedLayerEffect(effectHandle));
            }
            return LayerEffectsInterfaceApi.enumerateEffects(this.handle, wrapped);
        }
        return LayerEffectsInterfaceApi.enumerateEffects(this.handle, callback);
    }

    get effects() {
        const res = [];
        this.enumerateEffects(effect => {
            res.push(effect);
            return EnumerationResult.Continue;
        });
        return res;
    }

    get hasAnyVisibleEffects() {
        return LayerEffectsInterfaceApi.hasAnyVisibleEffects(this.handle);
    }

    get hasActiveEffects() {
        return LayerEffectsInterfaceApi.hasActiveEffects(this.handle);
    }

    get isScaleWithObject() {
        return LayerEffectsInterfaceApi.isScaleWithObject(this.handle);
    }

    get node() {
        return NodesModule.createTypedNode(LayerEffectsInterfaceApi.getNode(this.handle));
    }
}

module.exports.LayerEffectsInterface = LayerEffectsInterface;
