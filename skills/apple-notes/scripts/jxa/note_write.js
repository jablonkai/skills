// note_write.js {mode:"create"|"append"|"replace", folderId?, noteId?, html}
//   -> {id, name, attachmentCount}
// create: pushes a new note into the folder and returns the one whose id is new.
ObjC.import("Foundation");
function readArgs(p) {
  return JSON.parse($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null).js);
}
function run(argv) {
  const a = readArgs(argv[0]);
  const N = Application("Notes");
  let n;
  if (a.mode === "create") {
    const f = N.folders.byId(a.folderId);
    const before = f.notes.length ? f.notes.id() : [];
    f.notes.push(N.Note({ body: a.html }));
    const id = f.notes.id().filter(x => before.indexOf(x) < 0)[0];
    n = N.notes.byId(id);
  } else {
    n = N.notes.byId(a.noteId);
    if (n.passwordProtected()) throw new Error("note is locked");
    n.body = a.mode === "append" ? n.body() + a.html : a.html;
  }
  return JSON.stringify({ id: n.id(), name: n.name(), attachmentCount: n.attachments.length });
}
