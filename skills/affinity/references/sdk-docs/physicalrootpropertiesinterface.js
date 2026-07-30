'use strict';

const { PhysicalRootPropertiesInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');
const PageBoxInterfaceModule = require('./pageboxinterface.js');

class PhysicalRootPropertiesInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PhysicalRootPropertiesInterface';
    }

    get pageCount() {
        return PhysicalRootPropertiesInterfaceApi.getPageCount(this.handle);
    }

    get pageBoxInterface() {
        return new PageBoxInterfaceModule.PageBoxInterface(PhysicalRootPropertiesInterfaceApi.getPageBoxInterface(this.handle));
    }

    get node() {
        return NodesModule.createTypedNode(PhysicalRootPropertiesInterfaceApi.getNode(this.handle));
    }
}

module.exports.PhysicalRootPropertiesInterface = PhysicalRootPropertiesInterface;
