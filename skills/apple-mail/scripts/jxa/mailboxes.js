// mailboxes.js {account?, counts?} -> [{account, accountId, path, key, count?, unread?, error?}]
function run(argv) {
  const a = readArgs(argv[0]);
  const out = [];
  for (const m of allMailboxes(a.account || null)) {
    const r = { account: m.account, accountId: m.accountId, path: m.path, key: m.key };
    if (a.counts) {
      try { r.count = m.ref.messages.length; r.unread = m.ref.unreadCount(); }
      catch (e) { r.error = e.errorNumber || String(e); }
    }
    out.push(r);
  }
  return JSON.stringify(out);
}
