// Cavalry Bridge — remote control for Cavalry
//
// Install: copy into the Cavalry Scripts folder (Help ▸ Show Scripts Folder),
// then run it from the Scripts menu. A small window confirms it is listening.
//
// Protocol: POST a JSON body to http://127.0.0.1:8731 :
//   {"path": "/abs/path/script.js"}  -> runs the file
//   {"code": "console.log('hi')"}    -> executes the code
// Raw (non-JSON) bodies are executed as JavaScript directly.
//
// After every request the bridge writes STATUS_FILE with {seq, ok, at} so the
// caller can poll for completion (pair with cavalry-send.sh). Console output
// stays in Cavalry's Log window — scripts must write results to files.

var PORT = 8731;
// The user's own Cavalry preferences folder, not /tmp: a fixed /tmp name can be
// pre-created by any other local user — as a symlink to write through, or with
// contents cavalry-send.sh would read as a successful run. The exact path is
// advertised in the GET /get reply below so the sender never has to guess it.
var STATUS_FILE = api.getPreferencesPath() + "/cavalry-bridge-status.json";

var seq = 0;
var server = new api.WebServer();

// True when the request came from a browsing context on another origin. The
// bridge executes arbitrary JavaScript, so a page on any site the user visits
// could otherwise drive it with a CORS *simple* request (no preflight, and the
// opaque response is irrelevant — the code has already run). curl and
// cavalry-send.sh send neither header, so this costs them nothing.
function isCrossOrigin(post) {
    var headers = (post && post.headers) || [];
    for (var i = 0; i < headers.length; i++) {
        var name = String(headers[i].name || "").toLowerCase();
        var value = String(headers[i].value || "").toLowerCase();
        if (name === "origin" && value) return true;
        if (name === "sec-fetch-site" && value !== "same-origin" && value !== "none") return true;
    }
    return false;
}

var callbacks = {
    onPost: function () {
        while (server.postCount() > 0) {
            var post = server.getNextPost();
            if (isCrossOrigin(post)) {
                // Drop it without touching seq or STATUS_FILE — the request
                // never ran, so it must not look like a completed job.
                console.error("Bridge: cross-origin request rejected");
                continue;
            }
            var body = post.result;
            var req = null;
            try { req = JSON.parse(body); } catch (e) { req = null; }
            var ok = false;
            if (req && req.path) {
                if (api.filePathExists(req.path)) {
                    console.log("Bridge: running " + req.path);
                    ok = ui.runFileScript(req.path);
                } else {
                    console.error("Bridge: no file at " + req.path);
                }
            } else {
                var code = (req && req.code) ? req.code : body;
                ok = api.exec("cavalry.bridge", "(function(){ " + code + " \n})()");
            }
            seq++;
            api.writeToFile(STATUS_FILE,
                JSON.stringify({seq: seq, ok: !!ok, at: Date.now()}), true);
            console.log(ok ? "Bridge: OK" : "Bridge: FAILED");
        }
    }
};

server.listen("127.0.0.1", PORT);
// Static reply for GET /get — what `cavalry-send.sh --ping` probes, mirroring
// the /ping endpoints of the Blender and FreeCAD bridges. It also carries the
// status file path, which is how the sender discovers it.
server.setResultForGet(JSON.stringify(
    {ok: true, bridge: "cavalry", port: PORT, status: STATUS_FILE}));
server.addCallbackObject(callbacks);
server.setRealtime();

var label = new ui.Label("Bridge listening on 127.0.0.1:" + PORT);
label.setAlignment(1);
var layout = new ui.VLayout();
layout.addStretch();
layout.add(label);
layout.addStretch();
ui.setTitle("Cavalry Bridge");
ui.add(layout);
ui.show();
console.log("Cavalry Bridge listening on 127.0.0.1:" + PORT);
