---
name: zotero
description: 'Search, export, cite and add to a Zotero library from the command line through the running Zotero app''s local API: find items by topic, tag, author or collection and summarise their metadata, export a collection to BibTeX, BibLaTeX, CSL-JSON or RIS for LaTeX, Typst or Pandoc with validated citation keys, render bibliographies and in-text citations in any CSL style (APA, Chicago, IEEE, MLA …), and add papers by DOI or books by ISBN to a collection without duplicates, with undo. Uses Better BibTeX when installed. Use for "export my Thesis collection to refs.bib", "what do I have in Zotero on transformer pruning", "APA bibliography of my sleep papers", "add these three DOIs to my Reading collection", "cite these in IEEE style", "make a .bib from my reference manager for Typst". Not for Mendeley, EndNote or JabRef, fixing a .bib with no Zotero library involved, searching arXiv or Google Scholar for new papers, converting PDFs (markitdown), or writing the paper itself.'
summary: "search, export and grow a Zotero library via its local API — topic and collection searches with metadata summaries, BibTeX/BibLaTeX/CSL-JSON export for LaTeX and Typst, CSL-styled citations and bibliographies, adding papers by DOI and books by ISBN with undo"
category: research
risk: medium
tags:
    - zotero
    - bibtex
    - citations
    - csl
    - references
    - research
metadata:
  version: "1.0.0"
---

# Zotero from the command line

Zotero (free, AGPL) is a reference manager. Since Zotero 7 the desktop app serves
the user's library on `http://127.0.0.1:23119/api/` in the same shape as the
zotero.org web API, and from Zotero 10 that local API also accepts writes. This
skill drives that API through one helper. There's no account, no web API key and no
sync involved. Verified against **Zotero 10.0.6** with **Better BibTeX 9.0.71** on
macOS 27.

- [scripts/zotero.py](scripts/zotero.py): the helper (stdlib Python 3.9+). It prints
  JSON on stdout (or the exported text with `-o -`) and errors as JSON on stderr. Exit
  codes: **0** ok, **1** setup problem (not running, local API off, no write key),
  **2** Zotero or network error, **3** not found or ambiguous (for example a
  collection name), **4** the export failed validation.
- [references/api-reference.md](references/api-reference.md): local API endpoints and
  parameters, export formats, CSL styles, the write and authorize protocol, the
  connector endpoints, and Better BibTeX JSON-RPC. Read it when a task needs
  something the helper doesn't do.
- [references/recipes.md](references/recipes.md): worked flows for LaTeX/Typst/Pandoc
  exports, literature summaries, reading lists by DOI, bibliographies for a document.
- [references/gotchas.md](references/gotchas.md): **read it before a search comes up
  short, a key looks wrong, or a write fails.** It also covers the security posture.

## 1. Check first

```bash
Z="python3 scripts/zotero.py"   # paths are relative to this skill's directory
$Z check
```

| `check` says | Do |
|---|---|
| `running: false` | `open -a Zotero` (or `brew install --cask zotero`), wait a few seconds, re-check |
| `localApi: false` | **Ask the user** to tick *Settings › Advanced › Allow other applications on this computer to communicate with Zotero*. It's their privacy decision (any local program can then read the library), so don't edit `prefs.js` behind their back |
| `writeKey: false` | Reads work. Before `add`, `pin-keys` or `undo`, run `$Z authorize`. It opens a dialog in Zotero that the **user** must approve, so tell them to look at Zotero. The key is stored in `~/.config/zotero-skill/key` (0600) |
| `betterBibtex: true` | `export --bbt` is available (see below) |

Never write to `~/Zotero/zotero.sqlite`: Zotero holds it open, and editing it behind
the app's back corrupts the library. The local API is the only write path.

## 2. Find things

```bash
$Z collections --table                     # tree with keys and item counts
$Z search pruning sparsity --everything --table
$Z search --tag sleep --tag ultrarunning   # repeated --tag = AND
$Z search -c Thesis -r                     # a collection incl. subcollections
```

- Collections can be named by name, path (`skill-eval/Thesis`) or key. An ambiguous
  name exits 3 and lists the candidates, so pick one rather than guessing.
- Each positional term is a separate quick search, and the results are OR'ed.
- Output rows hold `key, type, title, creators, year, venue, citationKey, DOI, ISBN,
  tags, collections`. Notes and attachments are never returned.

**A topic search needs judgement, not one query.** Zotero's quick search matches title,
creator and year by default. It does **not** match tags or abstracts. So:

1. Search the topic word **and** its synonyms and stems with `--everything`, which
   adds every field, tags, notes and indexed full text. For example
   `pruning prune sparsity "lottery ticket"`.
2. Add `--tag` searches for any matching tags you see in the results.
3. Read titles, venues and tags (fetch `abstractNote` via the API for borderline
   items), and **drop false friends**. A gardening book tagged `pruning` is not
   about neural-network pruning. Say what you dropped and why.

## 3. Export for LaTeX, Typst or Pandoc

```bash
$Z export -c Thesis -f biblatex -o refs.bib        # bibtex | biblatex | csljson | ris
$Z export --tag sleep -f csljson -o refs.json      # Pandoc / citeproc
$Z export -c Thesis -r --bbt -f biblatex -o refs.bib
```

- The export comes from Zotero's own translators. Notes are excluded, and the entry
  count is checked against the item count. The file is also checked for balanced
  braces, unique keys and a title in every entry. The result JSON lists the citation
  keys and any `problems`, and a problem means exit 4.
- **Citation keys.** Zotero 10 has a `citationKey` field. Better BibTeX fills and pins
  it (`hanLearningBothWeights2015`). Without BBT it stays empty, and the exporter
  generates `han_learning_2015` on the fly. That key is deterministic but **changes
  if the title, first author or year is edited**. When the user is about to cite from
  the file, offer `$Z pin-keys -c Thesis` (needs the write key, undoable). It stores
  the current keys so they never drift. Give the user the key list from the result.
- Typst reads both BibTeX and BibLaTeX: `#bibliography("refs.bib")`, then `@key`.
  For biber or Typst prefer `biblatex`; for classic `bibtex` + natbib use `bibtex`.
- `--bbt` switches to Better BibTeX's translators, which give richer fields (arXiv
  `eprint`, …). BBT title-cases titles, including non-English ones, so check those.
  Use it when the user asks for BBT or already uses BBT output.

## 4. Citations and bibliographies

```bash
$Z bib -c Thesis -s apa                                 # plain text, one entry per paragraph
$Z bib --tag sleep -s chicago-author-date --output-format markdown
$Z cite -k 2XNBDVKL,73WG8K9C -s ieee                    # in-text citation per item
```

Zotero renders the citations itself, with the same citeproc-js engine its
word-processor plugins use. `--style` is a CSL id. The common ones are
installed; others (e.g. `american-sociological-association`) are fetched from
zotero.org on first use. A bad id exits 2 with `Invalid style`. `--locale`
(default `en-US`) sets the language of terms like "and" and "edited by".

## 5. Add papers and books

```bash
$Z add --doi 10.1038/nature14539 --doi 10.1145/3065386 -c Reading --create-collection
$Z add --isbn 9780262046305 -c "Thesis/Background" --tag to-read
$Z add --doi … --dry-run          # resolve and show the metadata, write nothing
$Z undo                           # trash what the last add created, unlink what it linked
```

- DOIs are resolved via doi.org (Crossref/DataCite CSL-JSON), and ISBNs via Open
  Library. `doi:`/URL prefixes and ISBN hyphens are accepted.
- **No duplicates:** an item whose DOI or ISBN is already in the library is not
  re-created. It is added to the target collection instead (status
  `exists, added to collection`).
- `--create-collection` creates a missing collection, including a nested one under an
  existing parent. Without it, a missing collection exits 3, so check
  `collections` before guessing at a name.
- Every write is journaled in `~/.config/zotero-skill/journal.jsonl`. `undo [--run
  ID]` moves the created items and collections to Zotero's trash and removes
  collection links it added. `history` shows the journal.
- After adding, read the result back (`search -c Reading`) and report the titles,
  because a DOI can resolve to a different work than the user expected.

## 6. Anything else

Read [references/api-reference.md](references/api-reference.md) and call the local
API directly. For example, you can edit fields with `PATCH /items/<key>`, list saved
searches, or get full text with `/items/<key>/fulltext`. Reuse the helper's
`Zotero` class (`from zotero import Zotero` with `scripts/` on `sys.path`). It handles
`Zotero-Server-ID`, the stored key and errors. Writes need
`If-Unmodified-Since-Version` from a fresh GET.
