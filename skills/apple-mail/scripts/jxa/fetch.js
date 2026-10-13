// fetch.js {keys:[mailbox key], since?:ISO} -> {messages:[...], skipped:[{key,error}]}
// Bulk property arrays per mailbox: one Apple event per property, not per message.
// `whose` filters are 50-100x slower on big mailboxes, so filtering happens in Python.
function run(argv) {
  const a = readArgs(argv[0]);
  const cache = allMailboxes(null);
  const out = [], skipped = [];
  const since = a.since ? new Date(a.since) : null;
  for (const key of a.keys) {
    let mb;
    try { mb = findMailbox(key, cache); } catch (e) { skipped.push({ key: key, error: String(e) }); continue; }
    try {
      const ms = mb.ref.messages;
      const dates = ms.dateReceived();
      if (!dates.length) continue;
      const ids = ms.id(), senders = ms.sender(), subjects = ms.subject();
      const mids = ms.messageId(), read = ms.readStatus(), flagged = ms.flaggedStatus();
      for (let i = 0; i < ids.length; i++) {
        if (since && dates[i] && dates[i] < since) continue;
        out.push({ ref: mb.key + "#" + ids[i], id: ids[i], mailbox: mb.key, messageId: mids[i],
          date: iso(dates[i]), from: senders[i], subject: subjects[i], read: read[i], flagged: flagged[i] });
      }
    } catch (e) { skipped.push({ key: key, error: e.errorNumber || String(e) }); }
  }
  return JSON.stringify({ messages: out, skipped: skipped });
}
