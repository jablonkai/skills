'use strict';

const { ArtboardPropertiesApi, EffectiveMarginBehaviour } = require('affinity:dom');
const { FillDescriptor } = require('./fills.js');
const { HandleObject } = require('./handleobject.js');
const { MarginsInterface } = require('./marginsinterface.js');

// cyclics:
const NodesModule = require('./nodes.js');
const PhysicalRootPropertiesInterfaceModule = require('./physicalrootpropertiesinterface.js');

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

    getMarginBox(behaviour) {
        return ArtboardPropertiesApi.getMarginBox(this.handle, behaviour);
    }

    get marginFill() {
        return new FillDescriptor(ArtboardPropertiesApi.getMarginFill(this.handle));
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
module.exports.EffectiveMarginBehaviour = EffectiveMarginBehaviour;
