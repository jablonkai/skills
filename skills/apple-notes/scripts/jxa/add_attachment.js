// add_attachment.js {noteId, path} -> {added, name, attachmentCount}
// `make new attachment` lands at the end of the note (images only). Notes 4.13 inserts it twice (same
// id listed twice, two U+FFFC markers); deleting the extra copy leaves one intact file.
ObjC.import("Foundation");
function readArgs(p) {
  return JSON.parse($.NSString.stringWithContentsOfFileEncodingError(p, $.NSUTF8StringEncoding, null).js);
}
function run(argv) {
  const a = readArgs(argv[0]);
  const N = Application("Notes");
  const n = N.notes.byId(a.noteId);
  const before = n.attachments.length;
  const att = N.make({ new: "attachment", at: n, withData: Path(a.path) });
  delay(0.5);
  let after = n.attachments.length;
  if (after - before === 2) {
    N.delete(n.attachments[after - 1]);
    after = n.attachments.length;
  }
  // Non-image files (PDF, text, ...) are silently ignored by Notes 4.13: added is 0.
  let name = null;
  if (after > before) { try { name = att.name(); } catch (e) {} }
  return JSON.stringify({ added: after - before, name: name, attachmentCount: after });
}
