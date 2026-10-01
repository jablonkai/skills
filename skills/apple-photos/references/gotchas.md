# Gotchas

All reproduced on Photos 12.0, macOS 27.0.1 and osxphotos 0.77.2 unless noted.

## Library and permissions

- **Two different "current libraries".** osxphotos without `--library` reads the
  *system* library. AppleScript writes to whatever library Photos *has open*. If
  they differ, a query from one library is written into the other. The write helpers
  compare the two (via `lsof`) and exit 3 when they differ.
- **Full Disk Access.** `~/Pictures/Photos Library.photoslibrary` is TCC-protected.
  Without Full Disk Access for the terminal or IDE, osxphotos fails with "Operation
  not permitted". Restart the app after granting it.
- **Automation permission** is per controlling app, so a new terminal asks again.
  Error -1743 means it was denied.
- `open -a Photos some-folder` doesn't open a library: Photos shows it as an **import
  source**. Only a real `.photoslibrary` bundle switches libraries.
- Shared albums can't be read by osxphotos on macOS 26 and later.

## Querying

- **`--to-date` is exclusive.** "10–17 May" is `--from-date 2023-05-10 --to-date
  2023-05-18`. With `--to-date 2023-05-17` everything shot on the 17th is silently
  dropped.
- Dates compare in the Mac's local timezone, but items keep their own offsets
  (`date` shows `+01:00` for a Lisbon photo). Near midnight, use full timestamps
  with an offset when it matters.
- **`--keyword` is case-sensitive**: `--keyword hiking` misses `Hiking`. Add `-i`.
  It's an exact match, so `hiking-boots` never matches.
- **`--place` is empty until Photos geocodes** the items, which happens in the
  background some time after import, and the names follow Photos' language. Fall back
  to a GPS box with `--query-eval`.
- The same flag repeated is OR, and different flags are AND. There's no NOT for
  keywords except `--no-keyword` (no keywords at all) or `--query-eval
  '"x" not in photo.keywords'`.
- `query` excludes Recently Deleted by default (`--deleted` includes it). Hidden
  items **are** included, while the Photos app hides them from its counts. Use
  `--not-hidden` to match what the user sees.
- `--json` is several KB per item. On libraries with 50k+ items use `--print` or
  `--count`.
- When zsh holds flags in an unquoted variable (`$L`), it doesn't word-split them.
  Use an array: `Q=(--keyword x); osxphotos query "${Q[@]}"`.

## Exporting

- **`DEST` must exist.** `osxphotos export` fails with "Path … does not exist".
- The default export writes the original **and** `NAME_edited.ext` for edited items.
  Choose explicitly with `--skip-edited` (originals) or `--skip-original-if-edited`.
- Sidecars are `NAME.jpg.xmp` unless `--sidecar-drop-ext`. Lightroom, Capture One
  and darktable expect `NAME.xmp`.
- `--update` only knows about files recorded in `DEST/.osxphotos_export.db`. Exporting
  to a new folder starts from scratch.
- `--cleanup` deletes every file in DEST that this run didn't export, including the
  user's own files. Never use it without asking.
- iCloud-only items (`ismissing`) are reported as missing, not exported, unless you
  pass `--download-missing`.

## Writing through AppleScript

- **App-level `albums` lists top-level albums only.** An album inside a folder is
  found through `folders[...].albums`. Two albums can share a name (one top-level, one
  in a folder), and Photos allows duplicate names even at the same level.
- **`import … skip check duplicates false` opens a modal "Import / Don't Import /
  Cancel" sheet** for duplicates and blocks every AppleScript call (-1712 timeout)
  until it's clicked. `ph-import.py` always skips Photos' check and dedupes by name and
  size itself.
- **`make new album|folder` can't be trusted to return the new object.** Shortly after
  a library opens, it creates the album but returns `missing value` or fails with
  -1700 "can't convert types". Retrying then creates a duplicate. Make it once, then
  find it by name (the helpers do this).
- **A library deleted and restored at the same path opens read-only**: every write
  (albums, favourites) is silently ignored. Restore backups to a new path, or check a
  write with a read-back before trusting it.
- Import ignores XMP sidecars. Metadata must be embedded in the files.
- AppleScript can't delete media items, only albums and folders. Removing an item
  from an album isn't in the dictionary either, so a wrongly filled album has to be
  deleted and rebuilt. Use `--dry-run` first.
- Smart Albums aren't in the AppleScript dictionary, so they can't be created there.
  Rebuild their rule as an osxphotos query instead.
- osxphotos reads a database snapshot. Albums and imports made through AppleScript
  showed up in the next osxphotos query immediately in testing, but an iCloud sync or
  a busy Photos can delay that. Re-query before concluding a write failed.
