'use strict';

const { ExportableInterfaceApi } = require('affinity:dom');
const { ExportConfig } = require('./exportconfig.js');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class ExportableInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ExportableInterface';
    }

    get exportConfig() {
        const exportConfigHandle = ExportableInterfaceApi.getExportConfig(this.handle);
        return exportConfigHandle ? new ExportConfig(exportConfigHandle) : null;
    }

    get node() {
        return NodesModule.createTypedNode(ExportableInterfaceApi.getNode(this.handle));
    }
}

module.exports.ExportableInterface = ExportableInterface;
