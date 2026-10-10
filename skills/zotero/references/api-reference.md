# Zotero local API reference

Everything here was probed against Zotero 10.0.6 (schema 44) unless marked otherwise.
The official docs are the [Local API page](https://www.zotero.org/support/dev/web_api/v3/local_api)
and the [Web API v3 basics](https://www.zotero.org/support/dev/web_api/v3/basics) it
mirrors.

## Contents
- [Base, auth, headers](#base-auth-headers)
- [Read endpoints](#read-endpoints)
- [Search parameters](#search-parameters)
- [Formats](#formats)
- [Writes](#writes)
- [Item JSON](#item-json)
- [Connector endpoints](#connector-endpoints)
- [Better BibTeX JSON-RPC](#better-bibtex-json-rpc)

## Base, auth, headers

| What | Value |
|------|-------|
| Base | `http://127.0.0.1:23119/api/users/0` (`0` = the local user; groups: `/api/groups/<id>`) |
| Enable | Settings › Advanced › *Allow other applications on this computer to communicate with Zotero* (pref `extensions.zotero.httpServer.localAPI.enabled`). Off returns `403 Local API is not enabled` |
| Reads | no auth, no rate limit, work offline, **not paginated** by default (`limit`/`start` still work, `Link` headers present) |
| Write key | `POST /api/local/authorize` with header `Zotero-Server-ID` and body `{"appName": "…"}`. This blocks until the user answers a dialog in Zotero, then returns `{"key": "<32 chars>", "remember": true\|false}`. `remember` is true when the user picked *Always Allow*; otherwise the key is single-use. Max 5 dialogs per minute (429). Revoke with Settings › Advanced › *Clear Write Authorizations* |
| Send key | `Zotero-API-Key: <key>` (or `Authorization: Bearer`, or `?key=`, which leaks into logs, so avoid it). Missing returns `401 API key required` |
| `Zotero-Server-ID` | returned on every response. Writes must echo it back, or get `428 Zotero-Server-ID not provided`. A mismatch on a read gets 412 |
| Versions | local object versions are unrelated to zotero.org versions; send `If-Unmodified-Since-Version: <version>` on PATCH/PUT/DELETE |
| Localized names | `itemType`/field names are the API's English ids, but library and collection names come back in the UI language (e.g. `Teljes könyvtár` = My Library) |

## Read endpoints

| Path | Returns |
|------|---------|
| `/items` | all items, including notes and attachments |
| `/items/top` | top-level items only (notes and attachments still appear if standalone) |
| `/items/<key>` / `/items/<key>/children` | one item / its notes and attachments |
| `/items/trash` | trashed items |
| `/collections`, `/collections/top`, `/collections/<key>/collections` | all / top-level / subcollections |
| `/collections/<key>/items[/top]` | items directly in that collection (**not** its subcollections) |
| `/collections/trash` | trashed collections |
| `/tags`, `/items/<key>/tags` | tags |
| `/searches`, `/searches/<key>/items` | saved searches; the second *executes* one (local-only feature) |
| `/items/<key>/fulltext` | indexed full text of an attachment |
| `/items/<key>/file/view/url` | `file://` URL of the attachment as text |

`meta.numItems` on a collection counts notes too.

## Search parameters

| Param | Effect |
|-------|--------|
| `q=` | quick search. Default `qmode=titleCreatorYear` matches only title, creators and year |
| `qmode=everything` | all fields + tags + notes + indexed full text. Needed to find a topic mentioned only in an abstract or tag |
| `tag=x` | exact tag; repeat for AND; `tag=a \|\| b` for OR; `tag=-x` excludes |
| `itemType=book` | type filter; `-note` excludes; `book \|\| thesis` OR |
| `itemKey=A,B,C` | up to 50 keys |
| `since=<version>` | changed since |
| `sort=dateAdded\|dateModified\|title\|creator\|date…`, `direction=asc\|desc` | ordering |
| `format=keys` | newline-separated keys (cheap) |

## Formats

`format=` on any item list or single item:

| Value | Notes |
|-------|-------|
| `json` (default) | `[{key, version, library, links, meta{creatorSummary, parsedDate, numChildren}, data{…}}]` |
| `keys` | plain keys |
| `bibtex`, `biblatex` | Zotero's built-in translators. Keys come from the item's `citationKey`. **Within one request** colliding keys get `a`, `b` suffixes. Notes are skipped |
| `csljson` | array of CSL items with `id` = `citation-key` when one is stored, **else the item URI**. **Child notes of exported items come back as extra `type: document` entries with a URI id**; the helper strips them |
| `ris` | one `TY … ER` record per item |
| `bib` | formatted bibliography as HTML (`<div class="csl-bib-body">…<div class="csl-entry">`). Sorted per the style. Params `style=<csl id>` (default `chicago-note-bibliography`), `locale=en-US`, `linkwrap=1` |
| `citation` | **400** as a format. Use `format=json&include=citation&style=…` instead; the result has `"citation": "(Smith, 2020)"` per item. `include=bib,citation,data` combine |
| `atom` | 501 locally |

Styles: ids from the [Zotero Style Repository](https://www.zotero.org/styles).
Installed ones live in `~/Zotero/styles/*.csl`. Others are downloaded from
zotero.org on first use; an unknown id gives `400 Invalid style`. Common ids: `apa`,
`chicago-author-date`, `chicago-notes-bibliography`, `modern-language-association`,
`ieee`, `nature`, `harvard-cite-them-right`, `elsevier-harvard`,
`american-medical-association`, `nlm-citation-sequence`, `vancouver`.

## Writes

All writes need the key and `Zotero-Server-ID`.

| Call | Body | Result |
|------|------|--------|
| `POST /items` | array (≤ 50) of item JSON | `{"successful": {"0": {key, version, …}}, "success": {"0": key}, "unchanged": {}, "failed": {"1": {code, message}}}`. Index = position in the array |
| `POST /collections` | `[{"name": "X", "parentCollection": "KEY"}]` | as above |
| `PATCH /items/<key>` | partial data, e.g. `{"collections": [...]}`, `{"deleted": 1}` (→ trash), `{"citationKey": "x"}` | 204 |
| `PATCH /collections/<key>` | `{"deleted": true}` → trash, `{"name": …}`, `{"parentCollection": …}` | 204 |
| `DELETE /items/<key>` | — | 204, **permanent** (bypasses the trash). Prefer `deleted: 1` |
| `DELETE /collections/<key>` | — | 204, permanent |

- **Fields invalid for the item type are not rejected.** Zotero moves them into
  `extra` as `Field Name: value` lines (e.g. `Publication Title: X` on a book), and
  the request still succeeds. Check what was stored when in doubt.
- Collection membership lives on the item (`data.collections`). To add an item to a
  collection, PATCH the item with the full new list.
- Writes appear in the UI immediately and sync on the next sync if sync is set up.

## Item JSON

```json
{"itemType": "journalArticle", "title": "…",
 "creators": [{"creatorType": "author", "firstName": "Ada", "lastName": "Lovelace"},
              {"creatorType": "editor", "name": "Single-field Org"}],
 "date": "2021-07-15", "publicationTitle": "Nature", "volume": "596", "issue": "7873",
 "pages": "583-589", "DOI": "10.1038/…", "ISSN": "0028-0836", "url": "…",
 "abstractNote": "…", "extra": "", "citationKey": "jumperHighlyAccurate2021",
 "tags": [{"tag": "protein"}], "collections": ["KEY"], "relations": {}}
```

Container field per type: `journalArticle.publicationTitle`,
`conferencePaper.proceedingsTitle`, `bookSection.bookTitle`, `preprint.repository`
(+ `archiveID`), `thesis.university` (+ `thesisType`), `report.institution`,
`book.publisher` (+ `place`, `ISBN`, `numPages`). `citationKey` is a native field in Zotero 10, and
every exporter uses it when set. **Plain Zotero leaves it empty.** The BibTeX/BibLaTeX
exporters then generate `lastname_firstword_year` per export, and CSL-JSON uses the
item URI (`http://zotero.org/users/local/…/items/KEY`) as `id`; the helper replaces
it with the BibTeX key. Better BibTeX fills the field with its own keys
(`lastnameTitleWordsYear`) and keeps them pinned.

## Connector endpoints

These are the browser connector's endpoints. They work **even with the local API
off**, and need no key.

| Endpoint | Use |
|----------|-----|
| `GET /connector/ping` | `X-Zotero-Version` header = running version |
| `POST /connector/getSelectedCollection` `{}` | the collection selected in the UI and all `targets` (`L1`, `C<id>`) |
| `POST /connector/import` (body: BibTeX/RIS text) | imports with Zotero's translators into the selected collection, returns 201 |
| `POST /connector/saveItems` | connector item JSON + `sessionID`; `POST /connector/updateSession {sessionID, target: "C12", tags}` moves the result |

They are meant for the browser extension and save into whatever the user has
selected, so use them only as a fallback.

## Better BibTeX JSON-RPC

`POST /better-bibtex/json-rpc` with `{"jsonrpc": "2.0", "method": …, "params": [...]}`.
Present only with the plugin (`No endpoint found` otherwise).

| Method | Params → result |
|--------|-----------------|
| `api.ready` | `[]` → `{zotero, betterbibtex}` versions |
| `item.citationkey` | `[["ITEMKEY", …]]` → `{ITEMKEY: citekey}` (group items: `"<libraryID>:KEY"`) |
| `item.export` | `[[citekeys], "Better BibLaTeX" \| "Better BibTeX" \| "Better CSL JSON", libraryID?]` → text |
| `item.search` | `["terms"]` → CSL-ish items with `citation-key` |
| `item.bibliography` | `[[citekeys], {contentType: "html"\|"text", id: "<style>", locale}]` → string |
| `collection.scanAUX` | `[collectionPath, auxPath]` → creates a collection from a LaTeX `.aux` |
| `autoexport.add` | `[collection, translator, path, displayOptions?, replace]` → keep a `.bib` in sync automatically |

With BBT installed, its keys are stored in the native `citationKey`, so the built-in
and BBT exporters agree. BBT's translators
title-case titles (wrong for non-English titles) and add `eprint`/`pubstate`.
