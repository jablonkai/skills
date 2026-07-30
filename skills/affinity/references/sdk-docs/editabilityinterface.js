'use strict';

const { EditabilityInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class EditabilityInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'EditabilityInterface';
    }

    get isEditable() {
        return EditabilityInterfaceApi.isEditable(this.handle);
    }

    get isLocalEditable() {
        return EditabilityInterfaceApi.isLocalEditable(this.handle);
    }

    get isMasterEditable() {
        return EditabilityInterfaceApi.isMasterEditable(this.handle);
    }

    get node() {
        return NodesModule.createTypedNode(EditabilityInterfaceApi.getNode(this.handle));
    }
}

module.exports.EditabilityInterface = EditabilityInterface;
