# Gotchas

- **A body rewrite deletes attachments.** Setting `note.body` rebuilds the note from the
  HTML, so attachments that aren't in the body (newer images, PDFs, scans, sketches) are
  gone. Inline data-URI images survive but come back as nameless, unexportable
  attachments. Even a file attachment that *is* in the body as
  `<img src="data:…">` comes back nameless and unsaveable after a rewrite (verified).
  `nt-write.py append/replace` refuses notes with file attachments unless `--reattach`
  (save, rewrite without them, re-add at the end), and always refuses notes with
  attachments it can't save. Don't bypass that with raw JXA.
- **A body rewrite flattens headings.** Writing back the HTML that `body` returned keeps
  a heading's `<b>` and font size but drops `face=".AppleSystemUIFontBold"`, so the note's
  existing `#`/`##` lines turn into big bold text (verified on macOS 27.2). `nt-write.py
  append` turns them back into `<h1>`/`<h2>` before the rewrite, and the reader also
  treats bold text of ≥ 17px as a heading, which covers notes rewritten earlier.
- **No real checklists.** Notes' tappable checkboxes are invisible to scripting. Reading
  them gives plain bullets without their state, and writing `class="checklist"` or
  `<input type=checkbox>` gives plain bullets. The helpers use ☐/☑ glyph bullets. For
  real checkboxes, the user has to convert the list in Notes (Format › Checklist).
- **`make new attachment` inserts twice** on Notes 4.13: the same id is listed twice and
  the plaintext has two U+FFFC markers. `add_attachment.js` deletes the extra copy.
- **Only images attach.** `make new attachment` with a PDF or any other non-image file
  returns without error and adds nothing.
- **Attachments land at the end.** No scripting call places an attachment mid-text.
- **Tables are missing from `plaintext`**: they show as U+FFFC. Search reads the table
  text from the body.
- **Locked notes**: `passwordProtected` is true, and `body`/`plaintext` are unreadable.
  They're skipped and reported.
- **Deleting folders** (only relevant to cleanup tooling; the skill never deletes): Notes
  silently ignores deleting a non-empty folder, and deleting its parent then orphans it
  to the account root. AppleScript `delete folder id …` is a no-op; JXA `N.delete()`
  works on an empty folder.
- **Title = first line.** Renaming means rewriting the first line of the body. `name` is
  writable, but it rewrites the body (with the same attachment risk).
- **Duplicate titles** are normal in Notes. Address notes by id when a title is
  ambiguous, and the helpers stop with the candidate ids.
- **Non-iCloud accounts** (Google, Exchange, Yahoo, "On My Mac" excepted) are
  IMAP-backed: tables, checklists and attachments aren't supported there. Write to an
  iCloud folder when the note has any of those.
- **"Recently Deleted"** is an ordinary folder to scripting. Search skips it unless
  `--include-deleted`. Its name is localized.
- **Localized errors**: `osascript` prints Hungarian or German messages. The helpers key
  on the error number.
- **Sandbox**: `save` into `~/Documents`, `~/Desktop` or iCloud Drive may fail. The
  helpers save into a temp dir and copy from there.
- **NoteStore SQLite** (`~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite`,
  gzip-compressed protobuf bodies) needs Full Disk Access and isn't used. The JXA path
  covers search, export and writes without it, and never risks touching the live database.
- **Sync**: writes go to the local store first. iCloud pushes them within seconds while
  Notes runs. Don't write the same note from two Macs at once.

## Security posture

There's no bridge and no listener: each helper call is a short `osascript` process with a
timeout, so #17/#32 (token, cross-origin) don't apply and #35 (stop path) is the timeout
or Ctrl-C. Writes are limited to create, append and an explicit replace. Nothing deletes
user content (the only `delete` removes the duplicate attachment the helper itself just
created). Note contents are passed through temp files in `$TMPDIR` that are removed
right after each call.
