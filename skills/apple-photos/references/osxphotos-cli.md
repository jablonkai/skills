# osxphotos CLI reference

Checked against `--help` of **osxphotos 0.77.2** on macOS 27 / Photos 12. Only the
flags this skill relies on are listed. `osxphotos help <command>` has the rest.

Every command takes `--library PATH`. Without it, osxphotos opens the **system**
library, which is not necessarily the one Photos has open (see
[gotchas.md](gotchas.md)).

## Read-only commands

| Command | Use |
|---|---|
| `query [filters] --count` | how many items match |
| `query [filters] --print TEMPLATE --quiet` | one line per item, cheap. Prefer it over `--json` on big libraries |
| `query [filters] --json` | full records, several KB per item. Fields are below |
| `info` | library totals: photos, videos, hidden, trash, missing, cloud |
| `albums` / `keywords` / `persons` / `places` | name → count, `--json` available |
| `list` | Photos libraries found on this Mac |
| `export DEST [filters] [options]` | copies files out. The library is untouched |
| `dump`, `labels`, `orphans`, `compare` | read-only diagnostics |

**Commands that write to the library** (use only on explicit request): `import`,
`batch-edit`, `timewarp`, `push-exif` (rewrites original files), `add-locations`,
`sync`, and `query/export --add-to-album`.

## Query filters (shared by `query` and `export`)

| Flag | Meaning |
|---|---|
| `--from-date D` / `--to-date D` | created on/after D / **before** D (exclusive). ISO 8601, with or without time and timezone |
| `--year 2023` | calendar year (repeatable) |
| `--keyword K` | exact keyword. Case-sensitive unless `-i`/`--ignore-case`. Repeat for OR |
| `--person P`, `--album A`, `--folder F` | exact name. Repeat for OR |
| `--place TEXT` | substring of Photos' reverse-geocoded place names (empty until Photos has geocoded) |
| `--location` / `--no-location` | has GPS / doesn't |
| `--favorite`, `--hidden`, `--not-hidden`, `--edited`, `--not-edited` | flags |
| `--only-photos` / `--only-movies` | media type |
| `--not-in-album`, `--missing`, `--cloudasset`, `--shared` | state |
| `--deleted` / `--deleted-only` | include or only Recently Deleted. Excluded by default |
| `--uuid U` / `--uuid-from-file F` | exact items |
| `--regex REGEX TEMPLATE` | regex over any rendered template, e.g. `--regex "^IMG_2" "{original_name}"` |
| `--query-eval EXPR` | Python expression over `photo` (a PhotoInfo), e.g. `photo.location[0] is not None and photo.width > 4000`. Repeat for AND |

Different flags AND together. Repeating the same flag ORs its values.

## Export options

| Flag | Effect |
|---|---|
| `DEST` | must already exist (`mkdir -p` first) |
| `--skip-edited` | originals only |
| `--skip-original-if-edited` | the edited version where there is one, otherwise the original |
| *(default)* | the original, plus `NAME_edited.ext` for edited items (`--edited-suffix` changes it) |
| `--sidecar XMP` / `JSON` / `exiftool` | sidecar per file, named `NAME.ext.xmp`. `--sidecar-drop-ext` gives `NAME.xmp`. Repeat for several kinds |
| `--exiftool` | writes metadata into the exported files. Needs `exiftool` on PATH |
| `--favorite-rating`, `--person-keyword`, `--album-keyword` | extra metadata in sidecars/exiftool |
| `--directory TEMPLATE` | subfolders, e.g. `"{created.year}/{created.mm}"`, `"{album}"`, `"{folder_album}"` |
| `--filename TEMPLATE` | file names, e.g. `"{created.strftime,%Y%m%d_%H%M%S}_{original_name}"` |
| `--update` | export only new or changed items. Tracks state in `DEST/.osxphotos_export.db` |
| `--dry-run`, `--limit N` | try without writing / cap the count |
| `--report FILE.csv\|.json` | per-file result log |
| `--skip-live`, `--skip-raw`, `--skip-raw-jpeg`, `--skip-bursts` | drop paired components |
| `--convert-to-jpeg` | HEIC/PNG/RAW → JPEG copies |
| `--download-missing [--use-photokit]` | fetch iCloud-only originals through Photos. Slow, and needs Photos running |
| `--cleanup` | **deletes** files in DEST that are not in this export. Don't use without explicit consent |

Name collisions get ` (1)` suffixes.

## Templates (for `--print`, `--directory`, `--filename`)

`{uuid}`, `{original_name}` (no extension), `{photo.original_filename}`,
`{created}` (date), `{created.year}`, `{created.mm}`, `{created.dd}`,
`{created.strftime,%Y-%m-%d %H:%M}`, `{place.name}`, `{place.country_code}`,
`{album}`, `{folder_album}`, `{keyword}`, `{person}`, `{title}`, `{descr}`,
`{photo.<attr>}` for any PhotoInfo attribute. A boolean renders as the attribute name
when true and `_` when false (e.g. `{photo.favorite}` → `favorite` or `_`). A missing
value also renders as `_`. Multi-valued fields (`{keyword}`, `{album}`) expand to one
output per value in `--directory`.

## `query --json` fields used most

`uuid`, `original_filename`, `filename`, `date` (ISO with offset), `date_added`,
`ismovie`, `isphoto`, `favorite`, `hidden`, `intrash`, `hasadjustments`, `keywords`,
`persons`, `albums`, `album_info[].folder_names`, `latitude`, `longitude`, `place`
(dict, `{}` until geocoded), `title`, `description`, `path` (None when not on disk),
`ismissing`, `iscloudasset`, `live_photo`, `has_raw`, `original_filesize`, `width`,
`height`, `uti`, `labels` (ML labels), `score`.
