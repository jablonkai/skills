'use strict';

const { ArtboardInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const ArtboardPropertiesModule = require('./artboardproperties.js');
const NodesModule = require('./nodes.js');
const PhysicalRootInterfaceModule = require('./physicalrootinterface.js');

class ArtboardInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ArtboardInterface';
    }

    isSameObject(other) {
        return ArtboardInterfaceApi.isSameObject(this.handle, other.handle);
    }

    get isArtboardInterface() {
        return true;
    }

    get isArtboardEnabled() {
        return ArtboardInterfaceApi.isArtboardEnabled(this.handle);
    }

    get description() {
        return ArtboardInterfaceApi.getArtboardDescription(this.handle);
    }
    
    get baseBox() {
        return ArtboardInterfaceApi.getArtboardBaseBox(this.handle);
    }
    
    get spreadBaseBox() {
        return ArtboardInterfaceApi.getArtboardSpreadBaseBox(this.handle);
    }
    
    get topOfPageMargin() {
        return ArtboardInterfaceApi.getTopOfPageMargin(this.handle);
    }

    get artboardProperties() {
        return new ArtboardPropertiesModule.ArtboardProperties(ArtboardInterfaceApi.getArtboardProperties(this.handle));
    }

    get node() {
        return NodesModule.createTypedNode(ArtboardInterfaceApi.getNode(this.handle));
    }
    
    #physicalRootInterface;
    get physicalRootInterface() {
        if (!this.#physicalRootInterface)
            this.#physicalRootInterface = new PhysicalRootInterfaceModule.PhysicalRootInterface(ArtboardInterfaceApi.getPhysicalRootInterface(this.handle));
        return this.#physicalRootInterface;
    }
    
    get physicalRootProperties() {
        return this.physicalRootInterface.physicalRootProperties;
    }
    
    get pageCount() {
        return this.physicalRootProperties.pageCount;
    }

    setArtboardEnabled(enabled, preview) {
        const node = this.node;
        return node.document.setArtboardEnabled(enabled, node, preview);
    }

    set isArtboardEnabled(enabled) {
        this.setArtboardEnabled(enabled);
    }
}

module.exports.ArtboardInterface = ArtboardInterface;
