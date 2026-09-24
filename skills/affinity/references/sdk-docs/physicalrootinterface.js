'use strict';

const { PhysicalRootInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('/handleobject.js');
const { PhysicalRootPropertiesInterface } = require('/physicalrootpropertiesinterface.js');

// cyclics:
const NodesModule = require('/nodes.js');

class PhysicalRootInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PhysicalRootInterface';
    }

    get physicalRootProperties() {
        const handle = PhysicalRootInterfaceApi.getPhysicalRootProperties(this.handle);
        return handle ? new PhysicalRootPropertiesInterface(handle) : null;
    }

    get node() {
        return NodesModule.createTypedNode(PhysicalRootInterfaceApi.getNode(this.handle));
    }
}

module.exports.PhysicalRootInterface = PhysicalRootInterface;
