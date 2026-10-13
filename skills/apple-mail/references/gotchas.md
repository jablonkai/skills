# Gotchas

## Permissions
- **Automation** (Privacy & Security › Automation › Mail) is required for everything.
  The first call shows the prompt. Error -1743 means it's denied.
- **Full Disk Access** is optional and only speeds up search. After granting it, quit and
  reopen the terminal/IDE, because the grant only applies to new processes.

## Speed
- Never use `whose` on a big mailbox: 21 s for `sender contains` and 41 s for a date
  filter on 15k messages. Bulk property arrays plus Python filtering take under 1 s.
- Per-mailbox `container()` walks cost about 100 ms each. Use the bulk `container.name()` chain.
- A sweep of every mailbox's `dateReceived` (85k messages) takes about 90 s. Scope with
  `--mailbox`/`--account`, or let the index do it.

## Data quirks
- Some mailboxes throw -1728 when their messages are read (Exchange "Notes"). The
  search skips them with a warning.
- `M.signatures` throws -1728 here. Don't rely on it.
- **Attachment elements are unreliable.** Two attachments of one message can share an
  `id`, `fileSize` comes back swapped between them, and `mimeType` throws -10000. Use
  names only, and take bytes from `message.source()` (what `mail-export.py` does).
- `content` of a reply starts with the quoted text; a new draft's content starts with a
  newline. Compare text after normalising whitespace.
- Mailbox names are localized (`Piszkozatok` = Drafts, `Összes levél` = All Mail,
  `Kuka` = Trash, `Importálás` = Import) and may arrive NFD-decomposed. Normalise to NFC.
- The Gmail INBOX holds no messages of its own in JXA terms. Its messages report
  `mailbox()` = All Mail.

## Writes
- `M.delete(mailbox)` fails with -10000. Mailboxes can be created and renamed by
  script, but only removed in the UI.
- Deleting a draft (cleanup) moves it to the account's Trash.
- `save()` on an outgoing message is asynchronous. Wait about 2 s before closing, then
  look the draft up in Drafts by subject (the newest id wins).
- `close({saving: "no"})` on a saved outgoing message sometimes leaves a windowless
  compose object in `M.outgoingMessages`. `close`, `delete` and `visible = true` can't
  remove it. It is never sent and disappears when Mail quits. `mail-draft.py` warns
  when this happens. Never call `send()` on anything in `outgoingMessages`.
- Mail 16's `M.reply()` object ignores `content = ...` (with or without
  `openingWindow`), and adding an attachment after setting text wipes the text. What
  works is to attach first, then run the AppleScript `tell content of (first outgoing
  message whose id is N) to make new paragraph at before first character with data (...)`.
  JXA can't express that location (-1719). Use `linefeed` for line breaks, because
  `return` collapses them. Mail's reply sets In-Reply-To/References itself, but it
  doesn't quote the original when no window opens, so the helper writes the quote.
- Moving a message gives it a new `id` in the target. Look it up there by `messageId`.
- Moves into Exchange/IMAP mailboxes take a few seconds to show up in the target. The
  organize helper retries its read-back.

## Security posture
- No bridge, no port, no daemon. Each call is a short `osascript` or SQLite read.
- Nothing is sent: there's no send, forward-and-send, redirect or bounce code path.
- The index is opened `mode=ro` and never copied out of `~/Library/Mail`.
