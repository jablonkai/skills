# Recipes

`S=scripts` (relative to the skill). Add `--library PATH` everywhere when the
target isn't the system library.

## Find things

```bash
osxphotos query --year 2024 --person "Anna" --count
osxphotos query --no-location --year 2021 --quiet --print "{original_name} {created}"
osxphotos query --keyword beach -i --favorite --quiet --print "{uuid}" > uuids.txt
osxphotos persons --json      # name → count; report only aggregates unless asked
osxphotos places --json
osxphotos albums --json
osxphotos query --not-in-album --only-photos --count
osxphotos query --regex "Screenshot" "{original_name}" --count   # or --query-eval photo.screenshot
```

Top people in one year, as counts only:

```bash
osxphotos query --year 2024 --quiet --print "{person}" | grep -v '^_$' | sort | uniq -c | sort -rn | head
```

## Place filters

1. Try `--place "Lisbon"` (it matches Photos' geocoded names, in Photos' language).
2. If that gives 0 or suspiciously few results, geocoding hasn't run or the names are
   localised. Use a GPS box:
   `--query-eval 'photo.location[0] is not None and abs(photo.location[0]-LAT)<D and abs(photo.location[1]-LON)<D'`.
   0.3° is about 33 km of latitude. Shrink it to about 0.1 for one city.
3. Items without GPS can't be placed. Mention how many in-range items have no
   location (`--no-location` with the same dates) so the user can decide.

## Exports

```bash
mkdir -p "$DEST"
# Edited version where one exists, otherwise the original, by year/month, incremental
osxphotos export "$DEST" --favorite --skip-original-if-edited \
  --directory "{created.year}/{created.mm}" --update --report "$DEST/export-report.csv"
# Originals and sidecars for Lightroom/darktable (NAME.xmp next to NAME.jpg)
osxphotos export "$DEST" --album "Portfolio" --skip-edited --sidecar XMP --sidecar-drop-ext
# One folder per album (items in several albums are copied into each)
osxphotos export "$DEST" --directory "{folder_album}" --update
# JPEG copies for sharing, without Live Photo videos or RAW halves
osxphotos export "$DEST" --album "Share" --skip-original-if-edited --convert-to-jpeg --skip-live --skip-raw
python3 $S/ph-verify-export.py "$DEST" --sidecar xmp -- --album "Portfolio"
```

- **Live Photos** export as `IMG_1234.HEIC` plus `IMG_1234.mov`. Skip the video with
  `--skip-live`.
- **RAW+JPEG pairs** export both files. Use `--skip-raw` or `--skip-raw-jpeg`.
- **iCloud "Optimise Mac Storage"**: items with `ismissing` have no original on disk
  and are reported as `missing`. Run `ph-stats.py` to see how many (`icloud_only`).
  `--download-missing` (needs Photos running, slow) fetches them. Add `--use-photokit`
  for the faster PhotoKit path, which needs Terminal.app, not iTerm2.
- **Big exports**: run with `--update` in the background. Ctrl-C is safe, and the
  same command resumes.

## Albums

```bash
python3 $S/ph-album.py --name "Hiking" -- --keyword hiking -i
python3 $S/ph-album.py --name "Lisbon 2023" --folder "Trips" -- --from-date 2023-05-10 --to-date 2023-05-18 --place Lisbon
python3 $S/ph-album.py --name "Best of 2024" --dry-run -- --year 2024 --favorite
```

- The summary JSON contains `matched`, `already_in_album`, `added`, `album_count`,
  and `not_matching_query` (items left in the album that the query doesn't match. They
  are never removed: tell the user).
- Smart Albums can't be created by AppleScript. A regular album is a snapshot, so
  re-run the same command later to top it up.

## Import

```bash
python3 $S/ph-import.py ~/Scans --album "Scans" --recursive --dry-run
python3 $S/ph-import.py ~/Scans --album "Scans" --recursive
```

Photos reads dates, GPS and keywords from EXIF, IPTC and XMP inside the files. It
**ignores XMP sidecars** on import.

## Statistics

```bash
python3 $S/ph-stats.py                     # per year
python3 $S/ph-stats.py --by month -- --year 2024
python3 $S/ph-stats.py --json -- --album "Trips"
osxphotos info                             # library totals incl. trash and shared
```
