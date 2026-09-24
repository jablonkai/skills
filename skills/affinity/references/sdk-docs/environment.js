'use strict';

const { EnvironmentApi, EnvironmentPermission, HeapStatistics } = require('affinity:application');
const { EnumerationResult, LogLevel } = require('affinity:common');
const { ConfigurationItem } = require('./configuration.js');

let environmentPermissions = null;
let environmentConfiguration = null;

class Environment {
    static get [Symbol.toStringTag]() {
        return 'Environment';
    }

    static toString() {
        return Environment[Symbol.toStringTag];
    }

    static postTask(func) {
        EnvironmentApi.postTask(func);
    }

    static quit() {
        EnvironmentApi.quit();
    }

    static get sdkVersionStr() {
        return EnvironmentApi.getSDKVersionStr();
    }

    static get v8VersionStr() {
        return EnvironmentApi.getV8VersionStr();
    }

    static hasPermission(environmentPermission) {
        return EnvironmentApi.hasPermission(environmentPermission);
    }

    static get configuration() {
        if (environmentConfiguration == null) {
            const h = EnvironmentApi.getConfiguration();
            if (h) {
                environmentConfiguration = new ConfigurationItem(h);
            }
        }
        return environmentConfiguration;
    }

    static enumerateFileSystemRoots(callback) {
        return EnvironmentApi.enumerateFileSystemRoots(callback);
    }

    static get fileSystemRoots() {
        const res = [];
        Environment.enumerateFileSystemRoots((root) => { res.push(root); return EnumerationResult.Continue; });
        return res;
    }

    static getHeapStatistics() {
        return EnvironmentApi.getHeapStatistics();
    }

    static get logLevel() {
        return EnvironmentApi.getLogLevel();
    }

    static set logLevel(level) {
        EnvironmentApi.setLogLevel(level);
    }

    static get permissions() {
        if (environmentPermissions == null) {
            environmentPermissions = Object.fromEntries(EnvironmentPermission.keys.map(perm => 
                [
                    perm.charAt(0).toLowerCase() + perm.slice(1),
                    Environment.hasPermission(EnvironmentPermission[perm])
                ]));
            Object.freeze(environmentPermissions);
        }
        return environmentPermissions;
    }
}

module.exports.Environment = Environment;
module.exports.EnvironmentPermission = EnvironmentPermission;
module.exports.LogLevel = LogLevel;
module.exports.HeapStatistics = HeapStatistics;
