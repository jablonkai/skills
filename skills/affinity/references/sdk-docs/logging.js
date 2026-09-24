'use strict';

const { LogFileApi, LogLevel } = require('affinity:common');
const { HandleObject } = require('/handleobject.js');

class LogFile extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'LogFile';
    }

    static create(path, logLevel, append = false) {
        return new LogFile(LogFileApi.create(path, logLevel, append));
    }

    get logLevel() {
        return LogFileApi.getLogLevel(this.handle);
    }

    set logLevel(value) {
        LogFileApi.setLogLevel(this.handle, value);
    }

    start() {
        LogFileApi.start(this.handle);
    }

    flush() {
        LogFileApi.flush(this.handle);
    }

    stop() {
        LogFileApi.stop(this.handle);
    }
}

module.exports.LogFile = LogFile;
module.exports.LogLevel = LogLevel;
