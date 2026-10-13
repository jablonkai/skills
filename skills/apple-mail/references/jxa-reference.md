# Mail JXA reference (Mail 16, macOS 27)

`const M = Application("Mail")`. Read the dictionary with `sdef /System/Applications/Mail.app`.

## Object model

| Class | Key properties / elements |
|---|---|
| `account` (`imap account`, `pop account`, `iCloud account`) | `name`, `id` (UUID, same as in Envelope Index URLs), `emailAddresses`, `enabled`, `mailboxes` (flat: all nested ones) |
| `mailbox` | `name`, `container` (parent mailbox; throws or returns the account at the top), `account`, `messages`, `mailboxes` (children), `unreadCount` |
| `message` | `id` (integer, = Envelope Index `messages.ROWID`), `messageId` (RFC Message-ID without `<>`), `sender`, `subject`, `dateReceived`, `dateSent`, `readStatus`, `flaggedStatus`, `flagIndex` (-1 none, 0 red … 6 gray), `junkMailStatus`, `deletedStatus`, `replyTo`, `toRecipients`/`ccRecipients`/`bccRecipients` (`address`, `name`), `mailAttachments` (`name`, `downloaded`, `save`), `content`, `source`, `allHeaders`, `mailbox` |
| `outgoing message` | `subject`, `content`, `sender`, `visible`, recipients, `save()`, `close()` |
| `rule` | `name`, `enabled`, `ruleConditions`, … (one rule here; rarely needed) |

Application-level shortcuts: `M.inbox`, `M.draftsMailbox`, `M.sentMailbox`,
`M.junkMailbox`, `M.trashMailbox`, `M.outbox` are the unified mailboxes. Their messages
report their real mailbox through `message.mailbox()`. `M.mailboxes` holds the local
"On My Mac" mailboxes (flat, nested ones included).

## Fast reads: bulk properties

```js
const ms = M.accounts.byName("Google").mailboxes.byName("INBOX").messages;
const ids = ms.id(), from = ms.sender(), subj = ms.subject(), date = ms.dateReceived();
```

That is one Apple event per property, about 0.4 s for 15k messages. The same query
through `ms.whose({sender: {_contains: "x"}})` takes 20 s or more. Paths come from
bulk `coll.container.name()`, then `coll.container.container.name()` and so on; see
`bulkPaths` in `scripts/jxa/_common.js`.

## Lookups by id

`mailbox.messages.byId(49674)` resolves in about 0.2 s, but only in the message's own
mailbox. For Gmail that's `[Gmail]/All Mail` (localized, e.g. `[Gmail]/Összes levél`).
`messages.whose({id: n})` is no faster.

## Writes

```js
M.move(msg, { to: targetMailbox });        // also across accounts
msg.flaggedStatus = true; msg.flagIndex = 0; // red
msg.readStatus = true;
M.duplicate(msg, { to: mb });               // copy, keeps dates and attachments

// draft: new
const om = M.OutgoingMessage({ subject: "S", content: "Body", visible: false });
M.outgoingMessages.push(om);
om.toRecipients.push(M.ToRecipient({ address: "a@x.test" }));
om.content.paragraphs.push(M.Attachment({ fileName: Path("/abs/file.pdf") }));
delay(1); om.save(); delay(2); om.close({ saving: "no" });

// draft: reply (content can't be assigned; see gotchas.md)
const r = M.reply(msg, { openingWindow: false, replyToAll: false });
r.content.paragraphs.push(M.Attachment({ fileName: Path("/abs/file.pdf") }));   // attachments first
// then, via AppleScript (NSAppleScript from JXA, see scripts/jxa/draft.js):
//   tell content of (first outgoing message whose id is <r.id()>) to make new paragraph
//     at before first character with data ("New text" & linefeed & ...)
r.save();
```

`save()` stores the draft in the sender account's Drafts. `close({saving:"no"})` after
a save leaves the saved draft in place. `send()` exists, but this skill never calls it.

Local mailboxes: `M.make({new: "mailbox", withProperties: {name: "X"}})` creates one;
`mb.name = "Y"` renames. `M.delete(mailbox)` fails with -10000, so remove mailboxes in
the Mail UI. `M.importMailMailbox({at: Path("/x/Name.mbox")})` imports an mbox folder
(a directory with an `mbox` file inside) under On My Mac › Import (`Importálás` here).
