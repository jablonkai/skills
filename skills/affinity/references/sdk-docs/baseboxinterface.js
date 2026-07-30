'use strict';

const { BaseBoxInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class BaseBoxInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get isBaseBoxInterface() {
        return true;
    }

    get baseBox() {
        return BaseBoxInterfaceApi.getBaseBox(this.handle, true);
    }

    get constrainingBaseBox() {
        return BaseBoxInterfaceApi.getConstrainingBaseBox(this.handle, true);
    }

    getBaseBox(includeClips) {
        return BaseBoxInterfaceApi.getBaseBox(this.handle, includeClips);
    }

    getConstrainingBaseBox(includeClips) {
        return BaseBoxInterfaceApi.getConstrainingBaseBox(this.handle, includeClips);
    }

    get node() {
        return NodesModule.createTypedNode(BaseBoxInterfaceApi.getNode(this.handle));
    }
}

module.exports.BaseBoxInterface = BaseBoxInterface;
