'use strict';

const { Application } = require('/application.js');
const { LogFile, LogLevel } = require('/logging.js');

function main(path, append = true) {
    // The selected folder must be allowed in the application's Scripting settings.
    const outputPath = path || `${Application.userDesktopPath}/affinity-script.log`;
    const logFile = LogFile.create(outputPath, LogLevel.Info, append);

    logFile.start();
    try {
        console.debug("Excluded by the file's initial Info level");
        console.info("Writing this script's log records to", outputPath);
        console.warn("This warning is included");

        // This does not wait for records still queued by the sink.
        logFile.flush();

        logFile.logLevel = LogLevel.Error;
        console.warn("Excluded after changing the file level to Error");
        console.error("This error is included");
    }
    finally {
        logFile.stop();
    }
}

module.exports.main = main;
