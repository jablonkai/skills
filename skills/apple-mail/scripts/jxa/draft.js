// draft.js {replyTo?: ref, replyAll?, to:[], cc:[], bcc:[], subject?, body, attachments:[abs path], sender?}
//   -> {subject, to, cc, bcc, sender}
// Saves to Drafts and closes the compose object without sending. There is no send here.
//
// Replies use Mail's own reply() so the draft carries In-Reply-To/References, but on
// Mail 16 that object ignores `content = ...` writes. What works: add the attachments
// first, then insert the text with AppleScript's `make new paragraph at before first
// character` (JXA cannot express that location on a reply body). The quoted original is
// written by us, because reply() leaves the body empty when no window is opened.
function addrOf(s) { const m = /<([^>]+)>/.exec(s || ""); return (m ? m[1] : (s || "")).trim(); }
function asStr(s) {
  return s.split("\n").map(l => '"' + l.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"').join(" & linefeed & ");
}
function runAS(src) {
  const err = Ref();
  $.NSAppleScript.alloc.initWithSource(src).executeAndReturnError(err);
  return err[0] ? ObjC.deepUnwrap(err[0]) : null;
}
function attach(om, files) {
  for (const p of files) om.content.paragraphs.push(M.Attachment({ fileName: Path(p) }));
  if (files.length) delay(1 + 0.5 * files.length);
}

function run(argv) {
  const a = readArgs(argv[0]);
  const files = a.attachments || [];
  let om, sender = a.sender || null;
  if (a.replyTo) {
    const found = msgByRef(a.replyTo);
    const src = found.msg;
    om = M.reply(src, { openingWindow: false, replyToAll: !!a.replyAll });
    delay(1.5);
    if (!sender) {
      try {
        const acct = found.mb.ref.account(), mine = acct.emailAddresses();
        let name = "";
        try { name = acct.fullName(); } catch (e) {}
        if (mine.length) sender = name ? name + " <" + mine[0] + ">" : mine[0];
      } catch (e) {}   // local mailbox: keep Mail's default account
    }
    attach(om, files);
    const when = src.dateSent() || src.dateReceived();
    const quoted = (src.content() || "").replace(/\r/g, "").replace(/\s+$/, "")
      .split("\n").map(l => "> " + l).join("\n");
    const text = a.body.replace(/\s+$/, "") + "\n\nOn " + when.toString().replace(/ GMT.*$/, "") + ", "
      + src.sender() + " wrote:\n\n" + quoted + "\n\n";
    const ref = '(first outgoing message whose id is ' + om.id() + ')';
    let err = runAS('tell application "Mail" to tell content of ' + ref
      + ' to make new paragraph at before first character with data (' + asStr(text) + ')');
    if (err) err = runAS('tell application "Mail" to set content of ' + ref + ' to (' + asStr(text) + ')');
    if (err) throw new Error("could not write the reply body: " + JSON.stringify(err));
    delay(1);
    if (a.subject) om.subject = a.subject;
  } else {
    om = M.OutgoingMessage({ subject: a.subject || "", content: a.body, visible: false });
    M.outgoingMessages.push(om);
    attach(om, files);
  }
  if (sender) om.sender = sender;
  for (const x of a.to || []) om.toRecipients.push(M.ToRecipient({ address: addrOf(x) }));
  for (const x of a.cc || []) om.ccRecipients.push(M.CcRecipient({ address: addrOf(x) }));
  for (const x of a.bcc || []) om.bccRecipients.push(M.BccRecipient({ address: addrOf(x) }));
  om.save();
  delay(2);
  const r = { subject: om.subject(), to: om.toRecipients.address(), cc: om.ccRecipients.address(),
    bcc: om.bccRecipients.address(), sender: om.sender() };
  const before = M.outgoingMessages.length;
  om.close({ saving: "no" });
  delay(0.5);
  // close() sometimes leaves a windowless compose object behind (it is never sent and
  // goes away when Mail quits); report it instead of failing.
  r.leftoverComposeObjects = Math.max(0, M.outgoingMessages.length - (before - 1));
  return JSON.stringify(r);
}
