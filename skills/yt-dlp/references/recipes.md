# yt-dlp recipes

Beyond what `ytdl_get.py` options cover. Quote every URL.

## Inventories

```bash
# every video of a channel (uploads tab) as TSV, no downloads
yt-dlp --flat-playlist --print '%(playlist_index)s\t%(id)s\t%(duration_string)s\t%(title)s' \
  'https://www.youtube.com/@Channel/videos' > channel.tsv

# the same as CSV with formats per video (slow: one full read per entry)
python3 scripts/ytdl_info.py 'https://www.youtube.com/@Channel/videos' --items 1:50 --formats --csv channel.csv

# total runtime of a playlist
yt-dlp --flat-playlist --print duration 'PLAYLIST_URL' | awk '{s+=$1} END {printf "%d:%02d:%02d\n", s/3600, s%3600/60, s%60}'
```

Channel URLs: `/@name/videos`, `/@name/shorts`, `/@name/streams` are separate
tabs; `/@name` alone gives the tab list.

## Date and content filters

```bash
yt-dlp --dateafter 20260101 --match-filters 'duration>120 & !is_live' -I 1:200 --download-archive a.txt URL
yt-dlp --match-filters 'title~=(?i)interview' URL      # title regex
```

`--dateafter` needs each entry's upload date, so it visits every video; pair it
with `--break-on-existing` or `--break-match-filters` on large channels.

## Metadata, thumbnails, chapters

```bash
yt-dlp --embed-metadata --embed-thumbnail --embed-chapters -f 'bv*+ba' --merge-output-format mp4 URL
yt-dlp --write-thumbnail --convert-thumbnails jpg --skip-download URL
yt-dlp --write-info-json --skip-download URL                 # full metadata to NAME.info.json
yt-dlp --split-chapters -o 'chapter:%(title)s/%(section_number)02d %(section_title)s.%(ext)s' URL
```

Audio for a music library: `-x --audio-format mp3 --audio-quality 0
--embed-metadata --embed-thumbnail --parse-metadata 'title:%(artist)s - %(title)s'`.

## SponsorBlock

```bash
yt-dlp --sponsorblock-remove sponsor,selfpromo URL       # cut segments (re-encodes around cuts)
yt-dlp --sponsorblock-mark all --embed-chapters URL      # mark as chapters instead
```

## Polite large batches

```bash
yt-dlp -a urls.txt --download-archive archive.txt \
  --sleep-requests 1 --sleep-interval 5 --max-sleep-interval 15 \
  --limit-rate 8M -o '%(uploader)s/%(upload_date>%Y-%m-%d)s %(title).80B [%(id)s].%(ext)s'
```

Run it again to resume. Archive lines are only written for finished items.

## Private content of the user's own account

```bash
yt-dlp --cookies-from-browser safari 'https://www.youtube.com/watch?v=UNLISTED_OR_PRIVATE'
yt-dlp --cookies-from-browser 'chrome:Profile 1' URL
yt-dlp --cookies-from-browser firefox --cookies cookies.txt URL   # export once to a file for reuse
```

Safari needs Full Disk Access for the terminal; Chrome asks for the keychain.
Treat an exported `cookies.txt` like a password: keep it out of repositories and
delete it after the job.

## Handing off to other skills

| Next step | Skill |
|---|---|
| exact cuts, joins, loudness, burn-in of the downloaded SRT | ffmpeg |
| batch shrink to H.265 | handbrake |
| timeline with the clip, subtitles from the SRT | davinci-resolve |
| Markdown transcript for notes or an LLM | markitdown |

Download the highest quality the next step needs, once. Re-encode afterwards
with ffmpeg rather than letting yt-dlp re-encode (`--recode-video`) during
download, so one source file can serve several outputs.
