# Notes scripting dictionary (JXA)

Confirmed with `sdef /System/Applications/Notes.app` on Notes 4.13 / macOS 27.0.1.

| Class | Elements | Properties (r = read-only) |
|---|---|---|
| application | accounts, folders, notes, attachments | `defaultAccount`, `defaultFolder`, `selection` |
| account | folders, notes | `name`, `id` (r), `upgraded` (r), `defaultFolder` |
| folder | folders, notes | `name`, `id` (r), `shared` (r), `container` (r: account or folder) |
| note | attachments | `name`, `body` (HTML, writable), `plaintext` (r), `id` (r), `container` (r), `creationDate` (r), `modificationDate` (r), `passwordProtected` (r), `shared` (r) |
| attachment | — | `name` (r), `id` (r), `contentIdentifier` (r), `URL` (r), `container` (r: note) |

Commands: `show`, `open note location`, plus the standard `make`, `delete`, `save`
(attachments) and `move`.

## Patterns

```javascript
const N = Application("Notes");
// Folder lists are flat: account.folders includes nested folders; container() is the parent.
const fs = N.accounts.byName("iCloud").folders;
fs.name(); fs.id(); fs[3].container().id();

// Batch property reads: one Apple event per property for a whole folder.
const ns = N.folders.byId(fid).notes;
ns.name(); ns.id(); ns.plaintext(); ns.modificationDate(); ns.passwordProtected();

// Global lookups by id work for nested folders and for notes in any folder.
N.notes.byId("x-coredata://…/ICNote/p123");

// Create: push into a folder, then find the new id (push returns no usable specifier).
f.notes.push(N.Note({ body: "<div><h1>Title</h1></div><div>text</div>" }));

// File attachment: lands at the END of the note; Notes 4.13 inserts it twice → delete the extra.
N.make({ new: "attachment", at: note, withData: Path("/abs/file.png") });

// Save an attachment: write to a temp dir (Notes is sandboxed), then move with Python.
N.save(att, { in: Path("/tmp/x/file.png") });
```

## Ids

- Notes `x-coredata://<store-uuid>/ICNote/p<n>`, folders `…/ICFolder/p<n>`, attachments
  `…/ICAttachment/p<n>`. They're stable while the note exists, but they're local to this Mac
  (the same iCloud note has a different id on another Mac).
- Attachment ids change when a body rewrite re-creates them.

## Errors (match the number; the text is localized)

| Number | Meaning |
|---|---|
| -1743 | Automation not permitted for this terminal/IDE |
| -1728 | Object not found (stale id, renamed folder) |
| -1712 | Apple event timed out (a dialog in Notes, a sync stall) |
| -10000 | Handler failed, e.g. `save` on a table or on a nameless image attachment |
| -600 | Notes not running and couldn't be launched |
