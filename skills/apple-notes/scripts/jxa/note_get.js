// note_get.js {id} -> {id, name, body, plaintext, folderId, created, modified, locked, attachmentCount, attachments:[{id,name,cid}]}
ObjC.import("Foundation");
function readArgs(p) {
  return JSON.parse($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null).js);
}
function run(argv) {
  const a = readArgs(argv[0]);
  const N = Application("Notes");
  const n = N.notes.byId(a.id);
  const locked = n.passwordProtected();
  const atts = n.attachments;
  const list = [];
  for (let i = 0; i < atts.length; i++) {
    const x = atts[i];
    list.push({ id: x.id(), name: x.name(), cid: x.contentIdentifier() });
  }
  return JSON.stringify({
    id: n.id(), name: n.name(), folderId: n.container().id(),
    created: n.creationDate(), modified: n.modificationDate(), locked: locked,
    body: locked ? "" : n.body(), plaintext: locked ? "" : n.plaintext(),
    attachmentCount: list.length, attachments: list
  });
}
