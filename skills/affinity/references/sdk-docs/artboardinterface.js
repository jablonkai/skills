'use strict';

const { ArtboardInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('/handleobject.js');

// cyclics:
const ArtboardPropertiesModule = require('/artboardproperties.js');
const BaselineGridInterfaceModule = require('/baselinegridinterface.js');
const NodesModule = require('/nodes.js');
const PhysicalRootInterfaceModule = require('/physicalrootinterface.js');

// monkey patches:
require('/geometry.js');

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

    get marginBox() {
        const properties = this.artboardProperties;
        if (!properties)
            return null;
        const box = this.spreadBaseBox;
        const marginsInterface = properties.marginsInterface;
        if (marginsInterface.useMargins) {
            const margins = marginsInterface.margins;
            box.x += margins.left;
            box.y += margins.top;
            box.width -= margins.left + margins.right;
            box.height -= margins.top + margins.bottom;
        }
        return box;
    }
    
    get topOfPageMargin() {
        return ArtboardInterfaceApi.getTopOfPageMargin(this.handle);
    }

    get artboardProperties() {
        const handle = ArtboardInterfaceApi.getArtboardProperties(this.handle);
        return handle ? new ArtboardPropertiesModule.ArtboardProperties(handle) : null;
    }

    get node() {
        return NodesModule.createTypedNode(ArtboardInterfaceApi.getNode(this.handle));
    }

    // physical root interface
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
        return this.physicalRootProperties?.pageCount ?? 0;
    }

    // baseline grid interface
    #baselineGridInterface;
    get baselineGridInterface() {
        if (!this.#baselineGridInterface)
            this.#baselineGridInterface = new BaselineGridInterfaceModule.BaselineGridInterface(ArtboardInterfaceApi.getBaselineGridInterface(this.handle));
        return this.#baselineGridInterface;
    }

    get baselineGridOptions() {
        return this.baselineGridInterface.baselineGridOptions;
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
