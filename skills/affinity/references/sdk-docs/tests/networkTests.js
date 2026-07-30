'use strict';
const {HttpRequest, HttpResponse, RequestMethod, HttpStatusCode} = require('/network');
const {ErrorCode} = require('affinity:common');

function RequestCB(reqState, response, reason) {
    console.assert(reqState.value === ErrorCode.OK.value);
    console.assert(response.statusCode.value === HttpStatusCode.Ok.value);
    console.assert(response.content);
    console.log("Test Ok");
}

async function HttpRequestGetTestAsync() {
    var req = HttpRequest.create("https://affinity.serif.com/en-gb/", RequestMethod.Get);
    await req.doAsync(RequestCB);
}

async function HttpRequestPostTestAsync() {
    var req = HttpRequest.create("https://httpbin.org/post", RequestMethod.Post);
    req.setHeaderValue("accept", "application/json");
    await req.doAsync(RequestCB);
}

function HttpRequestGetTest() {
    var req = HttpRequest.create("https://affinity.serif.com/en-gb/", RequestMethod.Get);
    var result = req.do();
    RequestCB(result.state, result.response, result.reason);
}
 
function HttpRequestPostTest() {
    var req = HttpRequest.create("https://httpbin.org/post", RequestMethod.Post);
    req.setHeaderValue("accept", "application/json");
	var result = req.do();
    RequestCB(result.state, result.response, result.reason);
 }

async function runTests() {
    console.log("GET async:");
    await HttpRequestGetTestAsync();
    console.log("POST async:");
    await HttpRequestPostTestAsync();
    console.log("GET sync:");
    HttpRequestGetTest();
    console.log("POST sync:");
    HttpRequestPostTest();
}


module.exports.runTests = runTests;
module.exports.HttpRequestGetTest = HttpRequestGetTest;
