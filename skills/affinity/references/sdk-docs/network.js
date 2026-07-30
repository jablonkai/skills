'use strict';

const { HttpRequestApi, HttpResponseApi, HttpStatusCode, RequestMethod } = require('affinity:network');
const { HandleObject } = require('./handleobject.js');

class HttpRequest extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'HttpRequest';
    }

    setTimeoutInSec(timeoutSec) {
        return HttpRequestApi.setTimeoutInSec(this.handle, timeoutSec);
    }
    
    setSuppressUserAgentHeader(suppress) {
        return HttpRequestApi.setSuppressUserAgentHeader(this.handle, suppress);
    }
    
    setEncodeHeaderValuesAsRfc2047(encodeAs2047) {
        return HttpRequestApi.setEncodeHeaderValuesAsRfc2047(this.handle, encodeAs2047);
    }
    
    setUseExpensiveNetwork(useExpensive) {
        return HttpRequestApi.setUseExpensiveNetwork(this.handle, useExpensive);
    }
    
    setUseConstrainedNetwork(useConstrained) {
        return HttpRequestApi.setUseConstrainedNetwork(this.handle, useConstrained);
    }
    
    setAvoidChunkedTransferEncoding(avoid) {
        return HttpRequestApi.setAvoidChunkedTransferEncoding(this.handle, avoid);
    }
    
    setHeaderValue(headerKey, headerVal) {
        return HttpRequestApi.setHeaderValue(this.handle, headerKey, headerVal);
    }
    
    getHeaderValue(headerKey) {
        return HttpRequestApi.getHeaderValue(this.handle, headerKey);
    }

    do() {
        var result = HttpRequestApi.do(this.handle);
		result.response = new HttpResponse(result.response);
		return result;
    }

    doAsync(callback) {
        if (typeof callback === 'function') {
            function wrapped(state, responseHandle, reason) {
                callback(state, new HttpResponse(responseHandle), reason);
            }
            return HttpRequestApi.doAsync(this.handle, wrapped);
        }
        return HttpRequestApi.doAsync(this.handle, callback);
    }
    
    static create(url, method) {
        return new HttpRequest(HttpRequestApi.create(url, method));
    }
}

class HttpResponse extends HandleObject {
    constructor(handle) {
        super(handle);
    }

    get [Symbol.toStringTag]() {
        return 'HttpResponse';
    }
    
    get statusCode() {
        return HttpResponseApi.getStatusCode(this.handle);
    }

    getHeaderValue(headerKey) {
        return HttpResponseApi.getHeaderValue(this.handle, headerKey);
    }

    get content() {
        return HttpResponseApi.getContent(this.handle);
    }
}

module.exports.HttpRequest = HttpRequest;
module.exports.HttpResponse = HttpResponse;
module.exports.RequestMethod = RequestMethod;
module.exports.HttpStatusCode = HttpStatusCode;
