# Envelope Index (read-only fast path)

Mail's catalogue is `~/Library/Mail/V10/MailData/Envelope Index` (SQLite, WAL mode).
`V10` on macOS 27; the helpers take the highest `V*`. It needs **Full Disk Access** for
the process that reads it. Without it, `~/Library/Mail` returns "Operation not
permitted" and the helpers fall back to JXA.

Open it read-only: `sqlite3.connect("file:<path>?mode=ro", uri=True)`. Never write to it,
and don't copy it while Mail runs, because the `-wal` file holds recent changes.

## Tables used

| Table | Columns that matter |
|---|---|
| `messages` | `ROWID` (= JXA `message.id`), `mailbox` → `mailboxes.ROWID`, `sender` → `addresses.ROWID`, `subject` → `subjects.ROWID`, `subject_prefix` (`Re: `), `date_received`/`date_sent` (Unix seconds), `read`, `flagged`, `flag_color`, `deleted`, `global_message_id` → `message_global_data.ROWID`, `list_id_hash`, `unsubscribe_type`, `conversation_id` |
| `mailboxes` | `ROWID`, `url` (`imap://<account UUID>/<percent-encoded path>`, `ews://…`, `local://<UUID>/…`), `total_count`, `unread_count` |
| `addresses` | `ROWID`, `address`, `comment` (display name) |
| `subjects` | `ROWID`, `subject` |
| `recipients` | `message`, `address` → `addresses`, `type` (0 To, 1 Cc), `position` |
| `labels` | `message_id` (→ `messages.ROWID`), `mailbox_id` (Gmail labels: INBOX etc.) |
| `attachments` | `message`, `name`. **Incomplete**: rows can be missing, so confirm through JXA |
| `message_global_data` | `message_id_header` (`<…>`) |

## Mapping to JXA

- The account UUID in `mailboxes.url` equals JXA `account.id()`. Local mailboxes use
  their own UUID under `local://`.
- The URL path, percent-decoded and NFC-normalised, equals the JXA mailbox path
  (`[Gmail]/Összes levél`; the URL holds decomposed accents).
- A ref is `<account name>/<path>#<messages.ROWID>`. JXA resolves it with
  `mailbox.messages.byId(ROWID)`.

## Newsletter signal

`list_id_hash != 0` (a List-Id header) or `unsubscribe_type > 0` (List-Unsubscribe
present) marks list mail. `unsubscribe_type` NULL means it hasn't been computed, so the
helpers check those messages' headers through JXA.

## Gmail

Messages are stored once, in All Mail (`messages.mailbox`). Their other mailboxes come
from `labels`. A search scoped to `Google/INBOX` therefore matches on
`mailbox IN (…) OR ROWID IN (SELECT message_id FROM labels WHERE mailbox_id IN (…))`.
