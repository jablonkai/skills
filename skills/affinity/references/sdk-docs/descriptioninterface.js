'use strict';

const { DescriptionInterfaceApi } = require('affinity:dom');
const { Colour } = require('./colours.js');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class DescriptionInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'DescriptionInterface';
    }

    get userDescription() {
        return DescriptionInterfaceApi.getUserDescription(this.handle);
    }

    get description() {
        return DescriptionInterfaceApi.getDescription(this.handle, true);
    }

    get defaultDescription() {
        return DescriptionInterfaceApi.getDefaultDescription(this.handle);
    }

    get defaultDescriptionForDisplay() {
        return DescriptionInterfaceApi.getDefaultDescriptionForDisplay(this.handle);
    }

    getTagColour(inferFromAncestors) {
        let colourHandle = DescriptionInterfaceApi.getTagColour(this.handle, inferFromAncestors);
        if (colourHandle)
            return new Colour(colourHandle);
        else
            return null;
    }

    get tagColour() {
        return this.getTagColour(false);
    }

    getDescription(descriptionOnEmpty) {
        return DescriptionInterfaceApi.getDescription(this.handle, descriptionOnEmpty);
    }

    get node() {
        return NodesModule.createTypedNode(DescriptionInterfaceApi.getNode(this.handle));
    }

    // mutating helpers
    setUserDescription(description, preview) {
        const node = this.node;
        return node.document.setLayerDescription(description, node, preview);
    }

    setTagColour(colour, preview) {
        const node = this.node;
        return node.document.setTagColour(colour, node, preview);
    }

    // mutating async helpers
    setUserDescriptionAsync(description, callback, preview) {
        const node = this.node;
        return node.document.setLayerDescriptionAsync(description, node, callback, preview);
    }

    setTagColourAsync(colour, callback, preview) {
        const node = this.node;
        return node.document.setTagColourAsync(colour, node, callback, preview);
    }

    // mutating property helpers
    set userDescription(description) {
        this.setUserDescription(description);
    }

    set tagColour(colour) {
        this.setTagColour(colour);
    }
}

module.exports.DescriptionInterface = DescriptionInterface;
