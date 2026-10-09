---
name: apple-photos
description: 'Query, export and organise the Apple Photos library on macOS: osxphotos for read-only searches by date, year, place, GPS area, people, keywords and albums, per-year statistics, and exports of originals or edited versions with XMP/JSON sidecars as resumable --update runs; Photos'' AppleScript for creating albums from a query and importing files. Read-only and local by default. Use for "export all photos from our Lisbon trip in May 2023 with XMP sidecars", "make an album of everything tagged hiking", "how many photos did I take each year", "which people appear most in my library", "import this folder into Photos into an album", "back up my Photos originals by year", or Hungarian "exportáld a nyaralás képeit a Fotókból". Not for editing pixels or retouching (use gimp or krita), Lightroom or other catalogs, converting or resizing image files outside Photos, video transcoding (use handbrake), iCloud web or shared albums, or bulk metadata rewrites unless the user explicitly asks.'
summary: "query, export and organise the Apple Photos library with osxphotos and AppleScript — searches by date, place, people and keywords, yearly statistics, original or edited exports with XMP sidecars, albums from a query, and file import"
category: mac-automation
risk: medium
tags:
    - photos
    - osxphotos
    - applescript
    - macos
    - export
metadata:
  version: "1.0.0"
---

# Apple Photos via osxphotos and AppleScript

Two surfaces, split by direction:

- **Reads go through [`osxphotos`](https://github.com/RhetTbull/osxphotos)** (MIT,
  Python CLI). It reads a snapshot of the library's SQLite database, so Photos doesn't
  need to run, and it never writes to the library during `query`, `export`, `info`,
  `albums`, `keywords`, `persons` or `places`.
- **Writes go through Photos' AppleScript dictionary** (JXA): creating albums, adding
  items, importing files. AppleScript always acts on **the library Photos has open**,
  so the write helpers check which library that is before they change anything.

Verified against **Photos 12.0 on macOS 27.0.1 with osxphotos 0.77.2**.

## Privacy rules (read first)

The library is personal data: faces, names, places, private photos.

- **Read-only by default.** Write to the library only when the user asks for an album
  or an import. Never delete, and never edit dates, titles, keywords or locations.
  Never run `osxphotos timewarp`, `batch-edit`, `push-exif`, `add-locations`, `sync`
  or `import` unless the user names that operation.
- **Stay local.** Don't upload photos or send library contents (names, people, places,
  thumbnails) to any web service.
- **Report aggregates** (counts, years, album sizes). List individual names, people or
  locations only when the user asked for them.
- Exports write only into the folder the user names. Don't use `--cleanup`: it deletes
  files in the destination.

## Setup

```bash
S=scripts   # paths are relative to this skill's directory
bash $S/photos.sh --check     # osxphotos path/version, Photos version, readable?, open library, automation
```

- **osxphotos missing** (exit 2): `uv tool install --python 3.13 osxphotos`. It needs
  Python 3.10–3.14, and the macOS system Python is 3.9, which is why uv is used.
- **Default library "NOT readable"**: the terminal or IDE that runs the agent needs
  **Full Disk Access** (System Settings › Privacy & Security). Restart it after
  granting. Libraries outside `~/Pictures` are usually readable without it.
- **Automation denied** (error -1743): allow the terminal to control Photos under
  Privacy & Security › Automation. macOS asks for this on the first write.
- Another library: pass `--library PATH` to every read. `osxphotos list` finds libraries.

## Workflow

1. **Query and count before acting.** Run `osxphotos query … --count`, then spot-check
   with `--print "{original_name} {created} {place.name}"`. Tell the user the number
   before a large export or an album write.
2. **Export** with `osxphotos export`, or **write** with `ph-album.py` / `ph-import.py`.
3. **Verify by read-back**: `ph-verify-export.py` for exports, and the JSON summaries of
   the album and import helpers. They re-read Photos after writing.

| The user says | Do |
|---|---|
| "photos from 10–17 May 2023" | `--from-date 2023-05-10 --to-date 2023-05-18`. **`--to-date` is exclusive**, so add a day for an inclusive end |
| "taken in Lisbon" | `--place Lisbon` only works after Photos has geocoded the items (it can be empty on new imports). Reliable: a GPS box, `--query-eval 'photo.location[0] is not None and abs(photo.location[0]-38.72)<0.3 and abs(photo.location[1]+9.14)<0.3'` (≈30 km). Try `--place`, and fall back to the box if the count is 0 or too small |
| "tagged hiking" | `--keyword hiking -i`. Without `-i`, matching is case-sensitive and misses `Hiking`. It's always an exact keyword match, so `hiking-boots` is excluded either way |
| "with Anna" / "in album X" | `--person "Anna"` / `--album "X"`. Repeating the same flag ORs its values; different flags AND together |
| "originals" / "edited versions" / "both" | `--skip-edited` / `--skip-original-if-edited` / the default (it exports the original plus `NAME_edited.ext` for edited items) |
| "with XMP sidecars" | `--sidecar XMP` writes `NAME.jpg.xmp`. Add `--sidecar-drop-ext` for `NAME.xmp` (what Lightroom and darktable expect) |
| "by year/month folders" | `--directory "{created.year}/{created.mm}"` |
| "incremental backup" | `--update` (re-runs export only new or changed items, tracked in `DEST/.osxphotos_export.db`) |
| "photos only" / "videos only" | `--only-photos` / `--only-movies` |

## Recipes

```bash
# Trip export: originals + XMP sidecars, resumable, then verify
mkdir -p "$DEST"     # export fails if DEST does not exist
Q=(--from-date 2023-05-10 --to-date 2023-05-18 --query-eval 'photo.location[0] is not None and abs(photo.location[0]-38.72)<0.3 and abs(photo.location[1]+9.14)<0.3')
osxphotos query "${Q[@]}" --count
osxphotos export "$DEST" "${Q[@]}" --skip-edited --sidecar XMP --update
python3 $S/ph-verify-export.py "$DEST" --sidecar xmp -- "${Q[@]}"

# Album from a query: reuses an existing album, adds only what's missing
python3 $S/ph-album.py --name "Hiking" --dry-run -- --keyword hiking -i
python3 $S/ph-album.py --name "Hiking" -- --keyword hiking -i

# Statistics per year (or --by month), read-only
python3 $S/ph-stats.py                       # photos, videos, favourites, edited, located, hidden, iCloud-only
python3 $S/ph-stats.py -- --person "Anna"    # narrowed by any query args

# Import a folder into an album; already-imported files are skipped
python3 $S/ph-import.py ~/Scans --album "Scans" --dry-run
python3 $S/ph-import.py ~/Scans --album "Scans"
```

Every script takes `--library PATH`. With the album and import helpers it must match
the library Photos has open, or they exit 3. The query goes after `--` and uses
osxphotos query syntax.

- [references/osxphotos-cli.md](references/osxphotos-cli.md): query, export and
  template flags, the `query --json` fields, and the read-only subcommands.
- [references/applescript.md](references/applescript.md): the Photos dictionary, JXA
  snippets, ids, folders, and errors.
- [references/recipes.md](references/recipes.md): more worked jobs, including people,
  top-N reports, Live Photos and RAW, iCloud-only originals, and folder layouts.
- [references/gotchas.md](references/gotchas.md): **read before writing raw commands.**

## Stopping and resuming

- **Exports**: Ctrl-C stops osxphotos. Re-running the same `export … --update` into
  the same folder continues where it stopped and skips files it already wrote.
- **`ph-album.py`** adds in batches of 200 and **`ph-import.py`** in batches of 100.
  `--timeout SEC` or Ctrl-C stop between batches and print what was done (exit 124 or
  130). Re-running finishes the job without duplicates.
- A Photos modal dialog (for example a duplicate-import prompt or a library upgrade)
  blocks every AppleScript call until someone dismisses it. The helpers time out with
  a hint instead of hanging.

## Safety

- osxphotos reads a copy of the database. Read commands never modify the library.
- Album writes are idempotent. Items that are in the album but not in the query are
  reported, never removed. An ambiguous album name (two albums with the same name)
  stops with an error.
- Imports bypass Photos' own duplicate prompt, which would block automation. They
  skip files whose original name and size are already in the library unless
  `--allow-duplicates` is passed.
- Commands are built as argument lists, never through a shell. Nothing listens on a
  port. Everything stays on this Mac.
