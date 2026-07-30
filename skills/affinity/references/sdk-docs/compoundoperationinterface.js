'use strict';

const { CompoundOperationInterfaceApi } = require('affinity:dom');
const { CompoundOperation } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class CompoundOperationInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'CompoundOperationInterface';
    }

    get isCompoundOperationInterface() {
        return true;
    }

    get compoundOperation() {
        return CompoundOperationInterfaceApi.getCompoundOperation(this.handle);
    }

    get node() {
        return NodesModule.createTypedNode(CompoundOperationInterfaceApi.getNode(this.handle));
    }
}

module.exports.CompoundOperationInterface = CompoundOperationInterface;
module.exports.CompoundOperation = CompoundOperation;
