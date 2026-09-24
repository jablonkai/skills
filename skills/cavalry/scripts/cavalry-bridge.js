// Cavalry Bridge — remote control for Cavalry
//
// Install: copy into the Cavalry Scripts folder (Help ▸ Show Scripts Folder),
// then run it from the Scripts menu. A small window confirms it is listening.
//
// Protocol: POST a JSON body to http://127.0.0.1:8731 :
//   {"path": "/abs/path/script.js", "id": "..."}  -> runs the file
//   {"code": "console.log('hi')",   "id": "..."}  -> executes the code
// Raw (non-JSON) bodies are executed as JavaScript directly.
//
// After every request the bridge writes STATUS_FILE with
// {seq, id, ok, error, at} so the caller can poll for completion (pair with
// cavalry-send.sh). A request that carries an "id" ([A-Za-z0-9_-]) also gets
// its own RESULTS_DIR/<id>.json, so concurrent callers never mistake — or
// miss — each other's jobs in the shared status file. A thrown exception comes back as "error" (message plus the
// line in the sent script). Console output stays in Cavalry's Log window —
// scripts must write any other results to files.

var VERSION = "2.0.0";
var PORT = 8731;
// The user's own Cavalry preferences folder, not /tmp: a fixed /tmp name can be
// pre-created by any other local user — as a symlink to write through, or with
// contents cavalry-send.sh would read as a successful run. The exact path is
// advertised in the GET /get reply below so the sender never has to guess it.
var STATUS_FILE = api.getPreferencesPath() + "/cavalry-bridge-status.json";
// Where the wrapped script reports a caught exception. exec() itself only
// returns a boolean, so the message has to travel through a file.
var ERROR_FILE = api.getPreferencesPath() + "/cavalry-bridge-error.txt";
var RESULTS_DIR = api.getPreferencesPath() + "/cavalry-bridge-results";
if (!api.filePathExists(RESULTS_DIR)) api.makeFolder(RESULTS_DIR);

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

// Run source inside an IIFE (nothing leaks between sends) wrapped in try/catch
// so a thrown error is reported with its message and line instead of a bare
// ok:false. The wrapper sits on the IIFE's first line, so the line numbers in
// the stack match the sent script. Syntax errors never reach the catch — exec
// just returns false — and are reported generically.
function run(source) {
    if (api.filePathExists(ERROR_FILE)) api.deleteFilePath(ERROR_FILE);
    var wrapped =
        "(function(){ try { (function(){ " + source + "\n})(); } catch (e) { " +
        "api.writeToFile(" + JSON.stringify(ERROR_FILE) + ", " +
        "String(e && e.stack ? e.stack : e), true); } })()";
    var ok = api.exec("cavalry.bridge", wrapped);
    var error = null;
    if (api.filePathExists(ERROR_FILE)) {
        error = api.readFromFile(ERROR_FILE);
        ok = false;
    } else if (!ok) {
        error = "script did not run — syntax error, or a permission prompt was declined (see Cavalry's Log window)";
    }
    return {ok: !!ok, error: error};
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
            var id = (req && req.id && /^[A-Za-z0-9_-]{1,64}$/.test(String(req.id)))
                ? String(req.id) : null;
            var result;
            if (req && req.path) {
                if (api.filePathExists(req.path)) {
                    console.log("Bridge: running " + req.path);
                    result = run(api.readFromFile(req.path));
                } else {
                    result = {ok: false, error: "no file at " + req.path};
                }
            } else {
                result = run((req && req.code) ? req.code : body);
            }
            seq++;
            var status = JSON.stringify(
                {seq: seq, id: id, ok: result.ok, error: result.error, at: Date.now()});
            api.writeToFile(STATUS_FILE, status, true);
            if (id) api.writeToFile(RESULTS_DIR + "/" + id + ".json", status, true);
            if (result.ok) console.log("Bridge: OK");
            else console.error("Bridge: FAILED — " + result.error);
        }
    }
};

server.listen("127.0.0.1", PORT);
// Static reply for GET /get — what `cavalry-send.sh --ping` probes, mirroring
// the /ping endpoints of the Blender and FreeCAD bridges. It also carries the
// status file path, which is how the sender discovers it.
server.setResultForGet(JSON.stringify(
    {ok: true, bridge: "cavalry", version: VERSION, cavalry: api.getCavalryVersion(),
     port: PORT, status: STATUS_FILE, results: RESULTS_DIR}));
server.addCallbackObject(callbacks);
server.setRealtime();

var label = new ui.Label("Bridge " + VERSION + " listening on 127.0.0.1:" + PORT);
label.setAlignment(1);
var layout = new ui.VLayout();
layout.addStretch();
layout.add(label);
layout.addStretch();
ui.setTitle("Cavalry Bridge");
ui.add(layout);
ui.show();
console.log("Cavalry Bridge " + VERSION + " listening on 127.0.0.1:" + PORT);
