// details.js {refs:[ref], headers?, content?, sourceDir?} -> [{ref, to, cc, attachments, headers?, content?, source?}]
// sourceDir: write each message's raw RFC 822 source to <sourceDir>/<id>.eml (keeps stdout small).
function run(argv) {
  const a = readArgs(argv[0]);
  const cache = allMailboxes(null);
  const out = [];
  for (const ref of a.refs) {
    try {
      const m = msgByRef(ref, cache).msg;
      const r = { ref: ref, id: m.id(), messageId: m.messageId(), date: iso(m.dateReceived()),
        from: m.sender(), subject: m.subject(), replyTo: m.replyTo(),
        to: m.toRecipients.address(), cc: m.ccRecipients.address(),
        read: m.readStatus(), flagged: m.flaggedStatus(), flagIndex: m.flagIndex() };
      const at = m.mailAttachments;
      // Only name + downloaded: Mail's attachment elements can share one id, so fileSize
      // comes back paired with the wrong name and mimeType throws -10000. Sizes and bytes
      // come from the message source instead (mail-export.py).
      r.attachments = at.name().map(n => ({ name: n }));
      if (r.attachments.length) {
        let dl = [];
        try { dl = at.downloaded(); } catch (e) {}
        r.attachments.forEach((x, i) => { x.downloaded = dl[i] !== false; });
      }
      if (a.headers) r.headers = m.allHeaders();
      if (a.content) r.content = m.content();
      if (a.sourceDir) {
        const p = a.sourceDir + "/" + r.id + ".eml";
        writeText(p, m.source());
        r.source = p;
      }
      out.push(r);
    } catch (e) { out.push({ ref: ref, error: e.errorNumber || String(e) }); }
  }
  return JSON.stringify(out);
}
