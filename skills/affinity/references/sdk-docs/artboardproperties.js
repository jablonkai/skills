'use strict';

const { ArtboardPropertiesApi } = require('affinity:dom');
const { HandleObject } = require('/handleobject.js');
const { MarginsInterface } = require('/marginsinterface.js');

// cyclics:
const NodesModule = require('/nodes.js');
const PhysicalRootPropertiesInterfaceModule = require('/physicalrootpropertiesinterface.js');

class ArtboardProperties extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'ArtboardProperties';
    }

    get isArtboardProperties() {
        return true;
    }

    /**
    * @deprecated Use MarginsInterface.marginFill instead
    */
    get marginFill() {
        console.warn("Using deprecated ArtboardProperties get marginFill() function. Use MarginsInterface.marginFill instead.");
        return this.marginsInterface.marginFill;
    }
    
    get marginsInterface() {
        return new MarginsInterface(ArtboardPropertiesApi.getMarginsInterface(this.handle));
    }
    
    get physicalRootPropertiesInterface() {
        return new PhysicalRootPropertiesInterfaceModule.PhysicalRootPropertiesInterface(ArtboardPropertiesApi.getPhysicalRootPropertiesInterface(this.handle));
    }

    get node() {
        return NodesModule.createTypedNode(ArtboardPropertiesApi.getNode(this.handle));
    }
}

module.exports.ArtboardProperties = ArtboardProperties;
