# yt-dlp CLI reference

Checked against `yt-dlp --help` of 2026.10.26. Only the options this skill relies
on; `yt-dlp --help` and the README's "FORMAT SELECTION" and "OUTPUT TEMPLATE"
sections have the rest.

## Format selection (`-f`)

A selector picks one format, or a video and an audio format to merge.

| Selector | Meaning |
|---|---|
| `b` | best single file with video **and** audio |
| `bv` / `bv*` | best video-only / best format that has video (may include audio) |
| `ba` / `ba*` | best audio-only / best format that has audio |
| `bv*+ba` | merge best video with best audio (needs ffmpeg) |
| `A/B/C` | first selector that matches anything |
| `22`, `137+140` | explicit format ids from `-F` |

Filters go in brackets right after a selector and can be chained:

| Filter | Example |
|---|---|
| numeric `< <= > >= = !=` | `[height<=1080]`, `[fps<=30]`, `[filesize<500M]`, `[tbr>1000]` |
| string `= ^= $= *= ~=` | `[vcodec^=avc1]` (starts with), `[ext=m4a]`, `[vcodec~='^(hvc1\|hev1)']` (regex), `[language^=hu]` |
| `?` after the operator | keep formats where the field is unknown: `[height<=?1080]` |

Codec ids as sites report them: H.264 `avc1`, HEVC `hvc1`/`hev1`, AV1 `av01`,
VP9 `vp9`/`vp09`, AAC `mp4a`, Opus `opus`.

A hard 1080p H.264 MP4 with AAC, falling back to a single file:

```bash
-f 'bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/bv*[height<=1080][vcodec^=avc1]+ba/b[height<=1080]'
--merge-output-format mp4
```

`-F` lists every format; `-f … --print format_id,resolution,vcodec,acodec`
with `--simulate` shows what a selector would pick.

## Format sorting (`-S`)

`-S` reorders the candidates the selector chooses from. It **prefers**, it never
excludes: `-S vcodec:h264` still returns AV1 when no H.264 exists.

| Field | Meaning |
|---|---|
| `res:1080` | prefer the largest resolution not above 1080 |
| `vcodec:h264` / `acodec:aac` | prefer this codec (and those "better" than it in yt-dlp's order) |
| `ext:mp4:m4a` | prefer containers for video:audio |
| `fps`, `hdr:12`, `size`, `br`, `proto`, `lang` | other sort keys |
| `+size` | a `+` reverses the order (smallest first) |

`-t mp4` is a preset alias for `--merge-output-format mp4 --remux-video mp4
-S vcodec:h264,lang,quality,res,fps,hdr:12,acodec:aac`; `-t mkv`, `-t mp3`,
`-t aac` exist too. Handy for "something that plays", not a guarantee.

## Output template (`-o`)

Default `%(title)s [%(id)s].%(ext)s`. `-P/--paths DIR` sets the base folder;
`-o` may contain `/` for subfolders.

| Syntax | Result |
|---|---|
| `%(title)s`, `%(id)s`, `%(ext)s`, `%(uploader)s`, `%(channel)s` | plain fields |
| `%(playlist_index)03d`, `%(playlist_title)s`, `%(playlist_count)s` | playlist fields (empty outside playlists) |
| `%(upload_date>%Y-%m-%d)s` | date formatting |
| `%(title).80B` | truncate to 80 bytes (long titles hit filename limits) |
| `%(field\|default)s` | default when the field is missing |
| `%(field&text\|)s` | `text` only when the field exists (`{}` inside = the value) |
| `%(section_start)d`, `%(section_end)d` | clip boundaries with `--download-sections` |

`-o 'subtitle:subs/%(title)s.%(ext)s'` and `-o 'thumbnail:…'` set per-type
templates. `--restrict-filenames` gives ASCII names without spaces;
`--windows-filenames` only removes characters Windows forbids.

## Metadata without downloading

| Command | Gives |
|---|---|
| `-j` / `--dump-json` | one JSON object per video (implies `--simulate`) |
| `-J` / `--dump-single-json` | one object; playlists contain `entries` |
| `--flat-playlist` | entries without visiting each video (fast; id, title, duration, url) |
| `--print FIELDS` | e.g. `--print '%(id)s %(duration_string)s %(title)s'` |
| `--print-to-file TEMPLATE FILE` | append to a file instead of stdout |
| `-F`, `--list-subs` | human-readable format and subtitle tables |

`--print` stages: `video:` (default, before download, implies `--simulate`),
`pre_process:`, `after_filter:`, `before_dl:`, `post_process:`, `after_move:`
(final path known: `--print after_move:filepath`), `after_video:`, `playlist:`.
A stage later than `video:` keeps the download running.

## Playlists and batches

| Option | Notes |
|---|---|
| `-I 1:3`, `-I 1,4,7`, `-I -5:`, `-I ::2` | items by 1-based index; negatives count from the end; `start:stop:step` |
| `--download-archive FILE` | appends `extractor id` per **finished** item; listed ids are skipped |
| `--break-on-existing` | stop at the first archived item (fast incremental channel syncs) |
| `--lazy-playlist` | process entries as they arrive (huge channels) |
| `-a FILE` / `--batch-file` | one URL per line, `#` comments |
| `--max-downloads N` | stop after N downloads |
| `--dateafter 20260101`, `--datebefore` | upload-date window |
| `--match-filters 'duration>60 & !is_live'` | skip entries by field |

## Audio extraction

`-x --audio-format FMT` with FMT one of `best aac alac flac m4a mp3 opus vorbis
wav`. `--audio-quality 0` (best VBR) … `10`, or a bitrate like `192K`. When the
downloaded stream already is the target codec it is remuxed, not re-encoded,
so pair `-x --audio-format m4a` with `-f 'ba[ext=m4a]/ba'`.

## Subtitles

| Option | Notes |
|---|---|
| `--write-subs` | manual (uploaded) subtitles |
| `--write-auto-subs` | auto-generated captions (YouTube ASR and machine translations) |
| `--sub-langs 'hu,en'` | comma list of regexes; `all`; `-live_chat` excludes |
| `--sub-format 'srt/vtt/best'` | preferred source format |
| `--convert-subs srt\|vtt\|ass\|lrc` | convert after download (ffmpeg); styling is lost |
| `--embed-subs` | mux into MP4/MKV/WebM as soft tracks |
| `--list-subs` | show both tables, manual and automatic |
| `--skip-download` | subtitles/metadata only |

Files land as `NAME.LANG.EXT`, e.g. `Sintel [eRsGyueVLvQ].hu.srt`.

## Sections

`--download-sections '*START-END'`: times as `SS`, `MM:SS` or `HH:MM:SS(.ms)`,
`inf` for the end, negative values count from the end (`'*-30-inf'` = last 30 s).
Without `*` the value is a chapter-title regex (`--download-sections intro`).
Repeat the option for several clips. `--force-keyframes-at-cuts` re-encodes at
the boundaries so the clip starts exactly where asked.

## Network, auth and config

| Option | Notes |
|---|---|
| `--cookies-from-browser safari\|chrome\|firefox\|brave\|edge[:PROFILE]` | the user's own logged-in session; Safari/Chrome ask for keychain access |
| `--sleep-requests 1`, `--sleep-interval 5 --max-sleep-interval 15` | pacing for large batches |
| `--limit-rate 5M`, `-N 4` (`--concurrent-fragments`) | bandwidth and fragment concurrency |
| `--js-runtimes deno\|node\|bun\|quickjs[:PATH]` | JS runtime for YouTube challenges (deno enabled by default) |
| `--extractor-args 'youtube:player_client=default,web_safari'` | per-extractor tweaks; only when an error message suggests one |
| `--ignore-config` | skip `~/.config/yt-dlp/config` and other config files (reproducible runs) |
| `-U`, `--update-to nightly` | self-update; standalone binary only |
