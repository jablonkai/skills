# Gotchas

## Setup

- **The local API is off by default.** `403 Local API is not enabled` means the user
  must tick *Settings › Advanced › Allow other applications on this computer to
  communicate with Zotero*. Ask; don't flip `extensions.zotero.httpServer.localAPI.enabled`
  in `prefs.js` yourself. It's a privacy setting, and Zotero rewrites `prefs.js` on
  quit anyway.
- **Writes need a dialog click.** `authorize` blocks until the user answers in Zotero.
  If nobody is at the machine it times out; say so instead of retrying (Zotero allows
  5 dialogs per minute). Ask the user to choose *Always Allow*, or the key works for
  only one write.
- **Zotero must be running.** The API lives inside the app. `open -a Zotero` takes a
  few seconds before port 23119 answers; `check` polls nothing, so re-run it.
- **Zotero 6 and older** have no local API (there's no `/api/`), and Zotero 7–9 have
  it read-only. `add`/`undo` need Zotero 10+. `check` shows the version.

## Searching

- **Default quick search misses tags and abstracts.** `q=` without `qmode=everything`
  only looks at title, creators and year. A topic search that skips `--everything`
  and `--tag` finds a fraction of the relevant items.
- **`--everything` over-matches.** It also hits notes, abstracts and full-text PDFs,
  so a single word can pull in unrelated items. Judge each hit.
- **Collections don't include subcollections** in the API. Use `-r`.
- **Names are localized:** the library is called by its UI-language name
  (`Teljes könyvtár`, `Meine Bibliothek`). Collection names are the user's own.
- **Duplicate collection names** (two `Misc` under different parents) exit 3. Use the
  path (`Project/Misc`) or the key.

## Exports

- **Keys drift unless pinned.** Without Better BibTeX the `citationKey` field is
  empty, and each export regenerates `author_word_year`. Edit the title, and every
  `@key` in the user's paper breaks. Colliding keys get `a`/`b` suffixes per request,
  which change with the selection. `pin-keys` stores them (recipe "Pin, fix or set
  citation keys"). With BBT, keys are already stored.
- **CSL-JSON ids are URIs without BBT** (`http://zotero.org/users/local/…`), which
  Pandoc can't cite. The helper swaps in the BibTeX keys; raw API calls don't.
- **CSL-JSON includes child notes** as `type: document` entries with URI ids when you
  call the API directly. The helper removes them.
- **Better BibTeX** title-cases titles in its own export (`{{Knowledge}}`), even for
  Hungarian or German titles where that's wrong. The built-in exporter keeps case
  and protects only capitalised words.
- **Over 50 items:** the API takes ≤ 50 `itemKey`s per request. The helper batches
  and re-checks key uniqueness across batches. `bib` output is then sorted per
  chunk, and the helper warns about it.

## Adding

- **Invalid fields are silently moved to `extra`**, not rejected. If an added item
  looks odd, read it back.
- **DOI content negotiation** returns abstracts as JATS XML (`<jats:p>`). The helper
  strips tags. Crossref sometimes lacks abstracts, page numbers or issue numbers;
  that's the source, not a bug.
- **Dedupe is by DOI/ISBN only.** A paper already in the library *without* a DOI
  will be added again. If the user's library is messy, run `search "<title words>"`
  first.
- **`DELETE` is permanent** and bypasses the trash. The helper's `undo` uses
  `deleted: 1` (trash) instead. Don't purge on the user's behalf.

## Security posture

- The API is Zotero's own server, bound to `127.0.0.1:23119`. This skill adds no
  listener, bridge or background process. Stopping means closing Zotero; there's
  nothing of ours to stop.
- **Reads are unauthenticated once the local API is on.** Any local process (and any
  user on the machine who can reach localhost) can read the whole library, notes
  included. That's why enabling it is the user's call.
- **Browsers:** a cross-origin request with an `Origin` header got no data back in
  testing. Zotero's server is built to refuse browser pages, but don't rely on this
  for anything sensitive.
- **The write key** is unscoped: it can change every editable library, including
  group libraries. The helper keeps it in `~/.config/zotero-skill/key` (mode 0600),
  sends it only in the `Zotero-API-Key` header to 127.0.0.1, and never prints it.
  `deauthorize` deletes the file; *Clear Write Authorizations* in Zotero revokes it.
- **Outbound network** happens only on `add`, to doi.org and openlibrary.org, and
  sends just the DOI or ISBN. Style downloads go from Zotero to zotero.org.
- **Never write to `zotero.sqlite`.** Read-only access while Zotero is closed
  (`sqlite3 'file:…/zotero.sqlite?mode=ro&immutable=1'`) is the last resort for
  forensic questions only. Its schema is internal and changes between versions.
