// save_attachments.js {ref, items:[{index, path}]} -> [{path, ok, error?}]
// Mail's own save: downloads IMAP parts that are not local yet.
function run(argv) {
  const a = readArgs(argv[0]);
  const m = msgByRef(a.ref).msg;
  const at = m.mailAttachments;
  return JSON.stringify(a.items.map(it => {
    try { at[it.index].save({ in: Path(it.path) }); return { path: it.path, ok: true }; }
    catch (e) { return { path: it.path, ok: false, error: e.errorNumber || String(e) }; }
  }));
}
