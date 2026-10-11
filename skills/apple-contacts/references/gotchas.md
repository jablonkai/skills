# Gotchas

## Permissions

- The framework needs Contacts access for the app that runs the script (Terminal, VS
  Code, …). The first framework call asks; afterwards only System Settings › Privacy &
  Security › Contacts can change it. `contacts.sh check` shows the state.
- AppleScript steps (notes, the read fallback, saving noted contacts) also need
  Automation permission for `osascript` to control Contacts. A `-1743` error means it was
  refused: System Settings › Privacy & Security › Automation.
- The first AppleScript step launches Contacts (about 6 s). Later ones are fast.

## Notes, and why noted contacts are saved through AppleScript

- Without Apple's `com.apple.developer.contacts.notes` entitlement, the framework
  silently drops the note key from a fetch; reading `.note` then raises
  `CNPropertyNotFetchedException`. So notes are read and written with AppleScript.
- The same limit blocks *saving*: updating a contact that has a note, or adding it to or
  removing it from a group, fails in CoreData with `Cocoa error 134092` (it can't load the
  note to re-index the card). Deleting such a contact works. Deleting a group whose
  members have notes fails the same way unless they are removed first.
- `ct_lib.save()` handles all of this: it looks up which targets have notes and sends
  their update/membership operations through AppleScript, after the framework part. If
  you ever write a save by hand, expect 134092 on any card with a note.
- `cn vcard` output has no NOTE line; `ct-export.py` splices notes in. vCard
  import reads NOTE from the file text and writes it after the save.

## Linked cards and counts

- Contacts links cards for the same person across accounts (an Exchange card and a
  Google card). The framework's unified view merges them: here 328 cards → 292 contacts.
  AppleScript sees the 328 cards. Duplicate reports run on the unified view, so linked
  cards are not reported as duplicates.
- A unified contact's `containers` lists every account its cards are in.

## Accounts

- New contacts and groups go to one account (container). The system default can be
  iCloud, which syncs to the user's phone, so name the account in your answer.
- A contact can join only a group in its own account. When an existing contact matches
  an import but lives in another account, it is reported under `notInGroup` instead.
- Exchange "folders" can show up as extra containers whose id ends in `:ABGroup`.
- Group names are unique only within an account; pass `--account` when two accounts
  have a group with the same name.

## Matching people

- Emails match case-insensitively. Phones match on digits, last 9 compared, so
  `+36 30 555 0101`, `06 30 555 0101` and `0036305550101` are the same number; numbers
  under 7 digits are never used as evidence.
- Names match with accents, case, punctuation and word order ignored, so `Kovács János`
  and `Janos Kovacs` are the same name. A single word (a first name only) is never
  treated as a duplicate.
- Import treats an entry as existing on the same email, or the same name plus the same
  phone, or the same name when the entry has no email or phone at all. Two people who
  share only a name are both kept.

## CSV

- Encoding: UTF-8 (with or without BOM) or UTF-16; delimiter `,`, `;` or tab, sniffed.
- `Name` alone is split on the last space (`Anna Nagy` → given Anna, family Nagy) or on a
  comma (`Nagy, Anna`). Prefer separate first/last columns for Hungarian-order names.
- `Title` is ambiguous (Outlook uses it for Mr./Dr., others for the job) and is ignored
  with a warning; rename the column to `Job Title` or `Prefix`.
- Birthdays: `YYYY-MM-DD`, `YYYY.MM.DD.`, `DD.MM.YYYY` (day first) or `--MM-DD`.

## Security posture

- No listener and no daemon: every helper is a one-shot process with a timeout, so there
  is no network surface, nothing to authenticate (#17, #32) and nothing to stop (#35).
- Read-only by default (#22). Writes create or change only what was asked; deletes need
  `--yes`; deleting a group keeps the people; duplicates are reported, never merged.
- Contact data stays on the Mac. Don't pass it to delegate agents or web services.
- `cn` is compiled from source in this skill on first use. Its cache directory holds
  only the binary.
