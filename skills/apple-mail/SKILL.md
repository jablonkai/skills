---
name: apple-mail
description: 'Search, export, draft and organise Apple Mail on macOS via its JXA dictionary, plus Mail''s Envelope Index for fast search when Full Disk Access allows: find messages by sender, recipient, subject, date, mailbox, attachment or newsletter status; export messages as .eml/Markdown and save attachments to a folder; draft new messages or replies with attachments, left in Drafts (never sends); bulk move, archive, flag and mark read with a preview first, read back to verify. Use for "find every email from Anna this month", "save all the PDF invoices from my mail to a folder", "draft a reply to the landlord with the contract attached", "archive newsletters older than 90 days", "flag everything from my boss this week". Not for sending mail or SMTP scripts, Gmail via web or API (Gmail connector), Outlook, contacts (apple-contacts), calendar invites (apple-calendar), or converting .eml/.msg files (markitdown).'
summary: "search, export, draft and organise Apple Mail via JXA and the Envelope Index — sender, subject and date searches, attachment export, reply drafts with attachments left in Drafts, bulk move, flag and archive with preview, read-back verified"
category: mac-automation
compatibility: "Built for Mail 16.0 on macOS 27.2 (JXA and the Envelope Index)."
risk: medium
tags:
    - mail
    - apple-mail
    - email
    - jxa
    - applescript
    - macos
    - attachments
license: GPL-3.0-only
metadata:
  version: "1.0.4"
  author: "Tamás Jablonkai"
---

# Apple Mail via JXA and the Envelope Index

Everything goes through `scripts/`: stdlib Python helpers that read Mail's SQLite
catalogue (the *Envelope Index*) when Full Disk Access allows it, and fall back to
Mail's scripting dictionary (`osascript -l JavaScript`) otherwise. All writes go through
the dictionary. Mail has to be running; the helpers launch it if needed.

The helpers exist because the obvious approach is slow. A JXA `whose` filter takes
20–40 s on a 15k-message inbox, and a sweep of every mailbox takes 90 s. The index
answers the same search in under half a second.

Verified against **Mail 16.0 on macOS 27.2**.

## Privacy and safety rules (read first)

Mail holds private correspondence.

- **Read-only by default.** Search and export never change Mail. Move, flag, mark
  read and draft only when the user asks.
- **Never send.** The skill has no send path. `mail-draft.py` saves to Drafts and the
  user sends from Mail. Don't work around this with raw `osascript`, `send`, `forward`
  or `redirect`, even if asked to "just send it". Explain that and leave the draft.
- **Never delete** messages or mailboxes. "Clean up" means archive, move or mark read.
- **Preview bulk changes.** `mail-organize.py` prints the matched set and changes
  nothing until it is re-run with `--yes`. Show the user the count and a few subjects
  first; when working unattended, check the preview yourself before applying it.
- **Stay local.** Don't pass message bodies to web services or delegate agents. Report
  date, sender and subject, and quote bodies only as far as the task needs.

## Setup

```bash
S=scripts   # relative to this skill's directory
bash $S/mail.sh check       # versions, Automation permission, accounts, index status
bash $S/mail.sh mailboxes   # every mailbox as Account/Path (add --counts for sizes)
```

- `automation: DENIED` (error -1743): allow the terminal/IDE to control Mail under
  System Settings › Privacy & Security › Automation.
- `envelope index: no Full Disk Access`: everything still works through JXA, just
  slower on big mailboxes. Granting Full Disk Access to the terminal/IDE enables the
  fast path. AppleScript error **messages are localized**, so match the number.

**Addresses.** Mailboxes are `Account/Path`: `Google/INBOX`, `Exchange/Archive`,
`Google/[Gmail]/All Mail`. Local ones are `On My Mac/…`. A bare name works when it's
unique. Messages are **refs**, `Account/Path#id`, taken from search output.

## Tasks

| The user wants | Run |
|---|---|
| messages from someone recently | `python3 $S/mail-search.py --from anna@x.test --since 30d` |
| by subject / recipient / mailbox | `--subject invoice --to me@work.test --mailbox "Google/INBOX"` (filters combine) |
| unread, flagged, with attachments | `--unread`, `--flagged`, `--has-attachment` |
| newsletters (or not) | `--newsletter` / `--not-newsletter` (List-Unsubscribe or List-Id header) |
| a summary | `--count-by sender\|mailbox\|day`; `--format json\|csv`; `--limit N` |
| save attachments to a folder | `mail-export.py <filters> --attachments-only --out DIR [--match-attachment .pdf]` |
| export messages | `mail-export.py <filters or --ids-from hits.json> --out DIR [--format eml\|md\|both]` |
| draft a reply | `mail-draft.py --reply-to REF --body-file reply.txt --attach FILE [--reply-all]` |
| draft a new message | `mail-draft.py --to a@x.test --subject S --body B --attach FILE [--from ADDR]` |
| archive / move | `mail-organize.py archive <filters>` (Archive of the source account, or `--dest`), `move --dest MAILBOX <filters>` |
| flag, unflag, read, unread | `mail-organize.py flag --color red <filters>` and so on |
| check a result | `mail-verify.py mailbox|draft|export ...` |

Dates take `30d`, `2w`, `6m`, `1y`, `today` or `YYYY-MM-DD`. "Older than 90 days" is
`--before 90d`. `--from`/`--to` match a substring of the name or address, so
`--from billing@acme.test` won't match `billing@acme-mail.test`. Pass the most precise
form the user gave. Trash, Junk and Spam are skipped unless `--include-trash`.

## Workflow

1. **Locate before acting.** Run the search and tell the user what matched (count,
   senders, date range). If the sender, the period or "the latest message about X" is
   ambiguous, look at the list and pick the one that fits, or ask.
2. **Run the helper** for the change, with `--dry-run` or the preview first for bulk work.
3. **Verify by read-back.** `mail-draft.py` and `mail-organize.py` re-read Mail and set
   `readback.ok` (exit 4 on a mismatch). `mail-export.py` writes `manifest.json` with
   sha256 for every file, and `mail-verify.py export` re-checks it. Report the outcome,
   including `not_exported` items and any `warning:` lines.

## Behaviour worth knowing

- **Gmail** keeps every message once, in `[Gmail]/All Mail`, and shows it in label
  mailboxes such as INBOX. Search results are de-duplicated by Message-ID, and a ref
  can point to All Mail even when you searched INBOX. That's expected.
- **Replies**: Mail sets the subject (`Re: …`, never doubled), the recipients and the
  threading headers. The new text goes above the quoted original as plain text.
- **Drafts land in the sending account's Drafts** (for a reply, the account that
  received the original, or Mail's default for local mail). `--from` picks another.
- **Attachments are exported from the message source**, byte-exact. Mail's attachment
  objects can report the wrong size and type, so trust the manifest. An attachment Mail
  hasn't downloaded yet is fetched through Mail. If that fails, it is listed in
  `not_exported`.
- **The index can lag** a few seconds behind changes, which is why the write helpers
  verify through JXA. To be sure a search sees a move you just made, use `--engine jxa`.

[references/recipes.md](references/recipes.md) has worked jobs: a sender report,
receipts into a folder, reply drafts, a newsletter cleanup, and thread export.
[references/jxa-reference.md](references/jxa-reference.md) covers the dictionary and
[references/envelope-index.md](references/envelope-index.md) the SQLite schema. Read
[references/gotchas.md](references/gotchas.md) before writing raw JXA.

## Stopping

Every call is a one-shot `osascript` or SQLite read with a timeout (`--timeout SEC`,
default 300). Nothing keeps running and nothing listens on a port. If Mail shows a
dialog, such as a password prompt or an account error, calls stall until the timeout
and exit 124 with a hint. Dismiss the dialog and re-run.
