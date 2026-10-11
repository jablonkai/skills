# Recipes

```bash
S=scripts
```

## Back up every note as Markdown

```bash
for acct in iCloud; do
  python3 $S/nt-export.py --folder "$acct/Notes" --out ~/NotesBackup/$acct
done
python3 $S/nt-verify.py export --dir ~/NotesBackup/iCloud --folder iCloud/Notes
```

Export each top-level folder separately (`notes.sh check` lists them). A re-run skips
`.md` files that already exist; `--force` refreshes them.

## Search, then export the hits

```bash
python3 $S/nt-search.py --text "Kestrel" --json > /tmp/hits.json
python3 $S/nt-export.py --ids-from /tmp/hits.json --out ~/Export/kestrel
```

Hits from different folders are written to `<Account>_<Folder>/` subdirectories.

## Daily log: append to one note

```bash
printf '## %s\n\n- [ ] call Anna\n- shipped the release\n' "$(date +%F)" > /tmp/today.md
python3 $S/nt-write.py append --note "iCloud/Journal/Work log" --md /tmp/today.md --dry-run
python3 $S/nt-write.py append --note "iCloud/Journal/Work log" --md /tmp/today.md
```

If it exits 3 (the log has photos or PDFs), start a new note per month instead:
`nt-write.py create --folder iCloud/Journal --title "Work log 2026-10" --md /tmp/today.md`.

## A folder of Markdown files → notes

```bash
for f in ~/notes-md/*.md; do
  python3 $S/nt-write.py create --folder "iCloud/Imported" --make-folder --md "$f" \
    --title "$(basename "$f" .md)" || echo "CHECK: $f"
done
```

`--title` is used only when the file has no leading heading. Front matter (for example
from an earlier export) is stripped.

## Notes changed this week, by folder

```bash
python3 $S/nt-search.py --since "$(date -v-7d +%F)" --json |
  python3 -c 'import json,sys,collections; r=json.load(sys.stdin)["results"]; print(collections.Counter(x["folder"] for x in r))'
```

## Convert without Notes

```bash
python3 $S/notes_md.py to-html note.md > note.html   # preview what would be sent (images inlined)
python3 $S/notes_md.py to-md body.html               # Notes HTML (e.g. saved from JXA) → Markdown
```
