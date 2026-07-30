'use strict';

const { ConstraintType, PictureFrameInterfaceApi, SpatialAnchor } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class PictureFrameInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PictureFrameInterface';
    }

    get enabled() {
        return PictureFrameInterfaceApi.isEnabled(this.handle);
    }

    get description() {
        return PictureFrameInterfaceApi.getDescription(this.handle);
    }
    
    get hasFrameContents() {
        return PictureFrameInterfaceApi.hasFrameContents(this.handle);
    }
    
    get frameContents() {
        return PictureFrameInterfaceApi.getFrameContents(this.handle);
    }
    
    get anchor() {
        return PictureFrameInterfaceApi.getAnchor(this.handle);
    }
    
    get isClearFillOnPopulate() {
        return PictureFrameInterfaceApi.isClearFillOnPopulate(this.handle);
    }
    
    get originalContentRectangle() {
        return PictureFrameInterfaceApi.getOriginalContentRectangle(this.handle);
    }
    
    get dataMergeFieldId() {
        return PictureFrameInterfaceApi.getDataMergeFieldId(this.handle);
    }
    
    calculateAnchor(node, hint) {
        return PictureFrameInterfaceApi.calculateAnchor(this.handle, node.handle, hint);
    }
    
    calculateConstraints(node, hint) {
        return PictureFrameInterfaceApi.calculateConstraints(this.handle, node.handle, hint);
    }

    get node() {
        return NodesModule.createTypedNode(PictureFrameInterfaceApi.getNode(this.handle));
    }
}

module.exports.ConstraintType = ConstraintType;
module.exports.PictureFrameInterface = PictureFrameInterface;
module.exports.SpatialAnchor = SpatialAnchor;
