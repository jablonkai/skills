'use strict';

const { OSApi } = require('affinity:os');

class OS {
    static get [Symbol.toStringTag]() {
        return 'OS';
    }

    static get arch() {
        return OSApi.getArchitecture();
    }

    static get Eol() {
        return OSApi.getEol();
    }

    static get machine() {
        return OSApi.getMachine();
    }

    static get platform() {
        return OSApi.getPlatform();
    }

    static get release() {
        return OSApi.getRelease();
    }

    static get osName() {
        return OSApi.getOSName();
    }

    static get osVersion() {
        return OSApi.getOSVersion();
    }
}

module.exports.OS = OS;
