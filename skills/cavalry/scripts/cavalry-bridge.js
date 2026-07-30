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
var STATUS_FILE = "/tmp/cavalry-bridge-status.json";

var seq = 0;
var server = new api.WebServer();

var callbacks = {
    onPost: function () {
        while (server.postCount() > 0) {
            var post = server.getNextPost();
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
