# Recipes

`Z="python3 scripts/zotero.py"` throughout. Every recipe starts with `$Z check`.

## Export a collection for a paper

```bash
$Z collections --table                       # find the exact collection
$Z export -c Thesis -f biblatex -o paper/refs.bib
```

- Hand back the file path, the entry count and the citation keys from the result. A
  non-empty `problems` list (exit 4) means something to fix or explain before the
  user compiles.
- Subcollections are **not** included unless you pass `-r`. If the collection has
  subcollections (`collections --table` shows them indented), ask or say which you
  chose.
- **Typst:** `#bibliography("refs.bib", style: "apa")` and `@hanLearningBothWeights2015`
  in the text. Typst (Hayagriva) reads BibLaTeX and BibTeX.
- **LaTeX + biber:** `\usepackage[backend=biber]{biblatex}`,
  `\addbibresource{refs.bib}`, `\cite{key}`.
- **LaTeX + bibtex/natbib:** export with `-f bibtex`, then `\bibliography{refs}`.
- **Pandoc:** `-f csljson -o refs.json`, then
  `pandoc paper.md --citeproc --bibliography refs.json --csl apa.csl`.
- To keep a file in sync while the user writes, use Better BibTeX's auto-export
  (`autoexport.add`, see the API reference) or simply re-run the export. Keys stay the
  same as long as they are pinned (BBT pins them; otherwise `pin-keys`).

## Summarise what the library has on a topic

```bash
$Z search pruning prune sparsity sparse "lottery ticket" --everything
$Z search --tag pruning
```

1. Union the results by `key`.
2. For each candidate, decide relevance from title, venue, tags and, if needed, the
   abstract:
   ```bash
   python3 -c 'import sys; sys.path.insert(0,"scripts"); from zotero import Zotero
   z=Zotero(); print(z.get_json("/items/KEY")["data"].get("abstractNote",""))'
   ```
3. Drop false friends (gardening books for "pruning", sleep in the
   "sleep(ms)" sense, …) and list them separately with the reason.
4. Present a table: authors, year, title, venue (journal or proceedings), item type,
   collection, key. Say how many items you searched and how you matched them.

## Reading list from DOIs

```bash
$Z add --doi 10.1038/nature14539 --doi 10.1145/3065386 --doi 10.1038/s41586-021-03819-2 \
       -c Reading --create-collection
$Z search -c Reading --table          # read back what's really there
```

- Report each DOI's `status`: `added`, `exists`, `exists, added to collection`, or
  `failed` with the error.
- If a DOI fails at doi.org (exit 3, `not found`), check it for a typo or a trailing
  period. Don't invent metadata.
- If the user wants them under a parent, use `-c "Thesis/Reading"`. The parent must
  exist; only the last level is created.
- If something went wrong, run `$Z undo` (or `--run <id>` from the `add` result).

## Bibliography for a document

```bash
$Z bib -c Thesis -s apa --output-format markdown > references.md
$Z bib -k KEY1,KEY2 -s ieee                          # numbered, sorted by the style
$Z cite -k KEY1 -s chicago-author-date               # (Han et al. 2015)
$Z bib --tag sleep -s modern-language-association --output-format html
```

For a non-English document pass `--locale de-DE`, `hu-HU`, …; it changes terms
("and" → "und"), not the titles.

## Books by ISBN

```bash
$Z add --isbn 978-0-262-04630-5 -c "Thesis/Background" --dry-run   # look first
$Z add --isbn 9780262046305 -c "Thesis/Background"
```

Open Library data is thinner than Crossref's: no editors and sometimes no place, and
the date is just the publish year. Mention that when it matters, and suggest the
user fix the item in Zotero if they need a perfect entry.

## Pin, fix or set citation keys

```bash
$Z pin-keys -c Thesis --dry-run     # which items have no stored key, and what they'd get
$Z pin-keys -c Thesis               # store them; `undo` clears them again
```

To give one item a specific key:

```bash
python3 - <<'EOF'
import sys; sys.path.insert(0, "scripts")
from zotero import Zotero
z = Zotero(need_key=True)
it = z.get_json("/items/2XNBDVKL")
z.write("PATCH", "/items/2XNBDVKL", {"citationKey": "han2015"}, it["version"])
EOF
```

Changing a key breaks existing `\cite{}` calls in the user's documents, so only do
it on request.
