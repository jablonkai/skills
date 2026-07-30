'use strict';

const { PredefinedTagKey, TagInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class TagInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }
    
    get [Symbol.toStringTag]() {
        return 'TagInterface';
    }
    
    hasKey(key) {
        return TagInterfaceApi.hasKey(this.handle, key);
    }
    
    getValueForKey(key) {
        return TagInterfaceApi.getValueForKey(this.handle, key);
    }
    
    get isMarkAsDecoration() {
        return TagInterfaceApi.isMarkAsDecoration(this.handle);
    }
    
    hasPredefinedKey(key) {
        return TagInterfaceApi.hasPredefinedKey(this.handle, key);
    }
    
    getValueForPredefinedKey(key) {
        return TagInterfaceApi.getValueForPredefinedKey(this.handle, key);
    }
    
    get node() {
        return NodesModule.createTypedNode(TagInterfaceApi.getNode(this.handle));
    }
}

module.exports.TagInterface = TagInterface;
module.exports.PredefinedTagKey = PredefinedTagKey;
