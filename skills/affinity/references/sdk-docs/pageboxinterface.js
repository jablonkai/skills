'use strict';

const { PageBoundingBoxType, PageBoxInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('./handleobject.js');

// cyclics:
const NodesModule = require('./nodes.js');

class PageBoxInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'PageBoxInterface';
    }

    getPageBoundingBox(pageBoundingBoxType) {
        return PageBoxInterfaceApi.getPageBoundingBox(this.handle, pageBoundingBoxType);
    }
}

module.exports.PageBoundingBoxType = PageBoundingBoxType;
module.exports.PageBoxInterface = PageBoxInterface;
