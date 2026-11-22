/*
BSD 3-Clause License

Copyright (c) 2026, Canva Pty Ltd.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

Neither the name of the copyright holder nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

'use strict';

const { TextFlowApi, TextFlowOverflowInfoApi, TextFlowOverflowState } = require('affinity:dom');
const { HandleObject } = require('/handleobject.js');

const OverflowPosition = Object.freeze({
    None: -1, // No position available
});

class TextFlowOverflowInfo extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TextFlowOverflowInfo';
    }

    get state() {
        return TextFlowOverflowInfoApi.getState(this.handle);
    }

    get position() {
        return TextFlowOverflowInfoApi.getPosition(this.handle);
    }
}

class TextFlow extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TextFlow';
    }

    get frameCount() {
        return TextFlowApi.getFrameCount(this.handle);
    }

    get isEmpty() {
        return TextFlowApi.isEmpty(this.handle);
    }

    get ignoreTextWraps() {
        return TextFlowApi.ignoreTextWraps(this.handle);
    }

    get isMultiFrameTextFlow() {
        return TextFlowApi.isMultiFrameTextFlow(this.handle);
    }

    get hideOverflow() {
        return TextFlowApi.hideOverflow(this.handle);
    }

    // This function call may take a long time
    getOverflowInfo() {
        return new TextFlowOverflowInfo(TextFlowApi.getOverflowInfo(this.handle));
    }

    getOverflowInfoAsync(callback) {
        if (typeof callback === 'function') {
            function wrappedCallback(error, overflowInfo) {
                callback(error, error ? null : new TextFlowOverflowInfo(overflowInfo));
            }
            return TextFlowApi.getOverflowInfoAsync(this.handle, wrappedCallback);
        }
        return TextFlowApi.getOverflowInfoAsync(this.handle, callback);
    }

    getDocumentPageIndex(frameIndex) {
        return TextFlowApi.getDocumentPageIndex(this.handle, frameIndex);
    }

    getDocumentSpreadIndex(frameIndex) {
        return TextFlowApi.getDocumentSpreadIndex(this.handle, frameIndex);
    }
}

module.exports.OverflowPosition = OverflowPosition;
module.exports.TextFlow = TextFlow;
module.exports.TextFlowOverflowInfo = TextFlowOverflowInfo;
module.exports.TextFlowOverflowState = TextFlowOverflowState;
