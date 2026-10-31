---
name: yt-dlp
description: 'Download video, audio and subtitles from YouTube, Vimeo and other sites with the yt-dlp CLI, for content the user may download (own uploads, Creative Commons, public domain); never circumvents DRM. Picks formats by resolution and codec (1080p H.264 MP4, audio-only M4A/MP3), fetches manual or auto subtitles in chosen languages as SRT without the video, downloads only a time range, batches playlists and channels with a download archive so re-runs skip finished items, and reports titles, durations, formats and subtitle languages without downloading; outputs checked with ffprobe. Use for "download this in 1080p as MP4", "just the audio as M4A", "get the Hungarian and English subtitles", "only 1:00 to 1:30", "download the playlist and skip what I have", "list the channel''s videos to a CSV", or a yt-dlp error like "Sign in to confirm". Not for editing files already on disk (ffmpeg, handbrake), a Markdown transcript (markitdown), recording a stream or screen (obs), or editing in Resolve (davinci-resolve).'
summary: "download video, audio and subtitles with yt-dlp — resolution and codec capped downloads, audio-only M4A/MP3, manual or auto subtitles as SRT, frame-accurate time-range clips, resumable playlist and channel batches with a download archive, metadata and format reports without downloading, ffprobe-verified outputs"
category: video
compatibility: "Built for yt-dlp 2026.10.26 (Homebrew) with FFmpeg 9.0.2 and deno 2.9.8 on macOS 27.2; Python 3.9+ for the helper scripts. Also runs on Linux with a pip or standalone install."
risk: low
tags:
    - yt-dlp
    - download
    - video
    - subtitles
    - youtube
license: GPL-3.0-only
metadata:
  version: "1.0.0"
  author: "Tamás Jablonkai"
---

# yt-dlp

yt-dlp is a headless CLI: there is no app to drive, only commands to get right.
The scripts below build those commands, print each one so it can be reused, and then
prove the result with ffprobe, because yt-dlp happily exits 0 with the wrong codec,
an Opus track in an MP4, a clip that starts three seconds early, or auto-captions
where the user asked for real subtitles. Verified against **yt-dlp 2026.10.26**
(Homebrew) with FFmpeg 9.0.2 and deno on macOS 27.2.

## Rights first

Use this for content the user may download: their own uploads, Creative Commons or
public-domain works, or material the site allows to be saved. Never work around
DRM (Netflix, Disney+, Widevine/FairPlay streams): yt-dlp refuses those, and so do
you. `--cookies-from-browser` is for the user's **own** logged-in account (their
private uploads, memberships they pay for), never for cookies someone else supplied.
When a request is clearly about redistributing someone else's paid content, say so
instead of downloading.

## Scripts

Paths are relative to this skill's directory.

| Script | Does |
|---|---|
| [scripts/ytdl.sh](scripts/ytdl.sh) `--check` | yt-dlp path, version and **install method with its update command**, ffmpeg/ffprobe, JS runtime. Run once first. Other arguments pass straight to yt-dlp. |
| [scripts/ytdl_info.py](scripts/ytdl_info.py) `URL… [--formats] [--subs --langs hu,en] [--items 1:20] [--csv F\|--json F]` | Metadata without downloading: title, duration, license, chapters; `--formats` adds the best height per codec (h264/vp9/av1) and audio formats; `--subs` lists manual vs auto languages. Playlists and channels give one row per entry (`--formats` then does a slower full read). |
| [scripts/ytdl_get.py](scripts/ytdl_get.py) `URL… --out DIR [options]` | Downloads, then verifies each file (height, codecs, container, audio-only, section length ±2 s, subtitle cue counts and languages). Prints the yt-dlp command to stderr and a JSON summary to stdout; exit 1 on any failed check. `--dry-run` shows the command only. |

`ytdl_get.py` options, by what the user asks for:

| The user says | Options |
|---|---|
| "1080p MP4", "H.264", "plays everywhere" | `--max-height 1080 --vcodec h264` (MP4 is the default container) |
| "best quality", "4K" | no cap; `--container mkv` keeps VP9/AV1 without fuss |
| "up to 1080p, H.264 if there is one" | add `--prefer`: soft `-S` sort instead of a hard filter |
| "just the audio", "as MP3" | `--audio m4a` (no re-encode on YouTube) or `--audio mp3` |
| "only 1:00–1:30" | `--section 1:00-1:30` (frame-accurate; `--keyframe-cut` copies instead and keeps hidden pre-roll) |
| "Hungarian and English subtitles, no video" | `--subs hu,en --subs-only` (manual subs; add `--auto-subs` to accept auto captions) |
| "the first 3 of the playlist" | `--items 1:3` |
| "skip what I already have", "resume later" | `--archive DIR/archive.txt` |
| "my private / members video" | `--cookies-from-browser safari` (asks for keychain access once) |
| anything else | append raw yt-dlp options after `--` |

## Workflow

```bash
S=scripts
bash $S/ytdl.sh --check                                   # 1. once: versions, update command, JS runtime
python3 $S/ytdl_info.py URL --formats --subs --langs hu,en  # 2. what exists (skip for plain requests)
python3 $S/ytdl_get.py URL --out ~/Downloads/x [options]  # 3. download + verify
```

1. **Look before you choose** when the request names a resolution, codec or
   language: `ytdl_info.py --formats/--subs` shows whether H.264 1080p or a manual
   Hungarian track exists at all. If it doesn't, tell the user what does exist
   rather than silently delivering something else.
2. **Download with `ytdl_get.py`.** Use an explicit `--out` folder. The default
   filename is `Title [id].ext` (plus `NNN ` for playlist items and the range for
   clips), so names stay unique and re-runs recognise finished files.
3. **Read the JSON summary.** Report the files with resolution, codecs and duration;
   for subtitles the language and cue count; for archive runs how many were skipped.
   `failed_checks` non-empty means the job is not done: fix it, don't report success.

**When the requested combination doesn't exist** (YouTube serves H.264 only up to
1080p; 4K is VP9/AV1), there are two honest answers. Pick the one that fits the
user's constraint, and say which one you chose and why:

- *The device needs the codec*: download the best source with
  `--container mkv` (audio stays the original AAC/Opus), then re-encode only the
  video with ffmpeg (`-c:v libx264 -crf 18 -preset medium -c:a copy`, or `-c:a aac`
  only when the player can't take Opus). A 4K x264 encode takes tens of minutes,
  so mention that, and say the result is a second lossy generation and larger than
  the source.
- *The resolution can give*: `--max-height 2160 --vcodec h264` delivers the best
  native H.264 (1080p) in seconds, with no generation loss.

## When yt-dlp fails

Sites change constantly and an outdated yt-dlp is the usual cause of "Unable to
extract", "Unsupported URL", HTTP 403, nsig/signature errors, or missing formats.

1. **Update first, once**, with the command `ytdl.sh --check` printed. On Homebrew
   that is `brew upgrade yt-dlp`; `yt-dlp -U` only works for the standalone binary.
2. Retry the same command once. Still failing → read the error (the script prints a
   hint). "Sign in to confirm you're not a bot" means the IP is flagged: stop and
   offer the options in [gotchas.md](references/gotchas.md) (wait, another network,
   a PO token plugin, or cookies only after the user agrees). "Requested format is
   not available" means the hard filter matched nothing: check `--formats`.
3. Don't loop on retries or rotate tricks; report the error and the next step.

YouTube also needs a JavaScript runtime (deno, installed with the Homebrew formula).
Without one, `--check` says so and most formats disappear.

## Raw yt-dlp

For anything the scripts don't cover, write the command yourself after reading
[gotchas.md](references/gotchas.md). The essentials:

```bash
yt-dlp -f 'bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/b[height<=1080]' --merge-output-format mp4 URL  # hard cap
yt-dlp -S 'res:1080,vcodec:h264,acodec:aac' URL      # soft preference: falls back to VP9/AV1 silently
yt-dlp -x --audio-format mp3 -f ba URL               # audio only
yt-dlp --download-sections '*1:00-1:30' --force-keyframes-at-cuts URL
yt-dlp --skip-download --write-subs --sub-langs 'hu,en' --convert-subs srt URL
yt-dlp -I 1:3 --download-archive archive.txt -x --audio-format m4a PLAYLIST_URL
yt-dlp --flat-playlist --print '%(playlist_index)s\t%(id)s\t%(duration)s\t%(title)s' PLAYLIST_URL
```

Quote every URL (zsh treats `?` and `&` as globs/operators) and every `-f`/`-o`
value. `--print` implies `--simulate` unless the field has a stage prefix such as
`after_move:`.

## References

- [cli-reference.md](references/cli-reference.md): format selectors and filters,
  `-S` fields, output template fields and formatting, `--print` stages, item
  ranges, subtitle language patterns, sections, config files.
- [recipes.md](references/recipes.md): channel inventories, date filters,
  metadata and thumbnail embedding, chapter splits, SponsorBlock, polite batches,
  handing files on to ffmpeg or Resolve.
- [gotchas.md](references/gotchas.md): the update path, JS runtime, soft `-S`,
  keyframe sections, subtitle language codes, archive semantics, scope-format
  heights, container surprises, rate limits.

## Safety

Downloads go only into the folder the user names; nothing outside it is written
or deleted, and existing files are skipped rather than overwritten. Commands are
argument lists, so titles with quotes, slashes or accents are safe. Browser cookies
are read locally by yt-dlp and never printed or copied elsewhere.
