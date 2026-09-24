'use strict';

const { EnumerationResult } = require('affinity:common');
const { TextFrameInterfaceApi } = require('affinity:dom');
const { HandleObject } = require('/handleobject.js');

// cyclics:
const NodesModule = require('/nodes.js');

// monkey patches:
require('/geometry.js');

class TextFrameInterface extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'TextFrameInterface';
    }

    get canHideOverflow() {
        return TextFrameInterfaceApi.canHideOverflow(this.handle);
    }

    get canUseBaselineGrid() {
        return TextFrameInterfaceApi.canUseBaselineGrid(this.handle);
    }

    get canUseTextWraps() {
        return TextFrameInterfaceApi.canUseTextWraps(this.handle);
    }

    get hasScaledText() {
        return TextFrameInterfaceApi.hasScaledText(this.handle);
    }

    get ignoreBaselineGrid() {
        return TextFrameInterfaceApi.ignoreBaselineGrid(this.handle);
    }

    get ignoreTextWraps() {
        return TextFrameInterfaceApi.ignoreTextWraps(this.handle);
    }

    get isMultiFrameTextFlow() {
        return TextFrameInterfaceApi.isMultiFrameTextFlow(this.handle);
    }

    get isTextFlowBack() {
        return TextFrameInterfaceApi.isTextFlowBack(this.handle);
    }

    get isTextFlowFront() {
        return TextFrameInterfaceApi.isTextFlowFront(this.handle);
    }

    get isWrappingText() {
        return TextFrameInterfaceApi.isWrappingText(this.handle);
    }

    get textBegin() {
        return TextFrameInterfaceApi.getTextBegin(this.handle);
    }

    get textFlowIndex() {
        return TextFrameInterfaceApi.getTextFlowIndex(this.handle);
    }

    enumerateTextFlowNodes(callback) {
        if (typeof callback === 'function') {
            function wrapped(nodeHandle) {
                return callback(NodesModule.createTypedNode(nodeHandle));
            }
            return TextFrameInterfaceApi.enumerateTextFlowNodes(this.handle, wrapped);
        }
        return TextFrameInterfaceApi.enumerateTextFlowNodes(this.handle, callback);
    }

    get textFlowNodes() {
        const nodes = [];
        this.enumerateTextFlowNodes(node => {
            nodes.push(node);
            return EnumerationResult.Continue;
        });
        return nodes;
    }

    get scalarStoryToDomainTransform() {
        return TextFrameInterfaceApi.getScalarStoryToDomainTransform(this.handle);
    }

    get storyToDomainTransform() {
        return TextFrameInterfaceApi.getStoryToDomainTransform(this.handle);
    }

    get textRenderScale() {
        return TextFrameInterfaceApi.getTextRenderScale(this.handle);
    }

    get textUiScale() {
        return TextFrameInterfaceApi.getTextUiScale(this.handle);
    }

    get node() {
        return NodesModule.createTypedNode(TextFrameInterfaceApi.getNode(this.handle));
    }

    get spreadNode() {
        return NodesModule.createTypedNode(TextFrameInterfaceApi.getSpreadNode(this.handle));
    }
}

module.exports.TextFrameInterface = TextFrameInterface;
