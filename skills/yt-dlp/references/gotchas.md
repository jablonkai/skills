# yt-dlp gotchas

Each of these produces a wrong result while yt-dlp exits 0, or wastes a retry.

## Updating

- **`yt-dlp -U` can't update a Homebrew install.** It reports the latest version,
  then refuses when one is newer ("You installed yt-dlp from a manual build or
  with a package manager; Use that to update"). Use `brew update && brew upgrade
  yt-dlp`; pip installs use `python3 -m pip install -U 'yt-dlp[default]'`.
  `ytdl.sh --check` prints the right one. `yt-dlp -U` is still a quick way to
  see whether a newer release exists.
- Most "Unable to extract", "Unsupported URL", HTTP 403, `nsig` or signature
  errors are a stale extractor. Update before debugging anything else. If stable
  is still broken a day later, the standalone binary can try
  `--update-to nightly`; Homebrew users wait for the next bottle or use pipx.
- YouTube needs a **JavaScript runtime** to solve its challenges. yt-dlp uses deno
  by default (a Homebrew dependency of the formula). Without one you get a warning
  and only a handful of low formats, or none.

## Format choice

- **`-S` only prefers.** `-S res:1080,vcodec:h264` returns AV1 or VP9 when no H.264
  stream exists, and a 720p file when no 1080p exists. When the user's requirement
  is hard ("must be H.264"), use a `-f` filter so a mismatch fails loudly with
  "Requested format is not available".
- `bv+ba` without `--merge-output-format` merges into whatever fits, often `.webm`
  or `.mkv`. Ask for `mp4` explicitly when the user said MP4.
- Pairing a VP9/AV1 video with the default best audio puts **Opus in MP4**. It is
  legal, but QuickTime and some TVs play it silent. With MP4, pick `ba[ext=m4a]`.
- **Scope films report odd heights.** A 2.39:1 "4K" film is 3840x1608 and its
  "1080p" is 1920x804. `height<=1080` is still the right cap; `res:1080` in `-S`
  compares the smaller dimension.
- `b` (single file) is often only 360p on YouTube. Without ffmpeg, `bv*+ba` can't
  merge and yt-dlp falls back to it. Check ffmpeg is installed.
- Live streams: `--live-from-start` or `--wait-for-video`; without them a running
  stream is recorded from "now" until it ends, which can take hours.

## Sections

- Without `--force-keyframes-at-cuts`, `--download-sections` copies from the
  previous keyframe. In MP4 the extra frames are hidden behind an edit list, so
  players start at the right moment, but the file still holds up to one GOP of
  pre-roll (0.5 s on a YouTube 1080p stream, several seconds on other sites)
  that editors, MKV/WebM and frame-exact tools show. Use the option whenever
  the clip goes into an edit or must start exactly; it re-encodes the clip
  (H.264), which on YouTube costs little extra time.
- A section download given the default output name collides with a later full
  download of the same video: yt-dlp sees `Title [id].mp4` and says "has already
  been downloaded". Put `%(section_start)d-%(section_end)d` in the name.
- The section is cut from the selected format. Choose the resolution first; a
  section doesn't make 4K any cheaper to re-encode.

## Subtitles

- **Manual vs auto.** `--write-subs` gets only uploaded subtitles;
  `--write-auto-subs` adds auto captions and machine translations (YouTube offers
  ~100 translated tracks). When the user says "subtitles" and a manual track
  exists, give the manual one; say so when only auto captions exist.
- **Language codes vary**: `en`, `en-US`, `en-GB`, `en-orig` (the original-language
  ASR track). `--sub-langs en` matches only `en` exactly. Use `'en.*'` to take any
  English variant, and check `--list-subs` before promising a language.
- `--convert-subs srt` needs ffmpeg and drops VTT styling and positioning. YouTube
  auto-captions in VTT contain rolling duplicate lines; SRT conversion cleans most
  of that but cue counts stay high.
- `--skip-download` with `--write-subs` still writes subtitles; `--print
  after_move:filepath` prints nothing for subtitle-only runs, since there is no
  media file to move. Look in the output folder instead.
- `--embed-subs` with MP4 converts to `mov_text`; most players show it, but it
  can't carry styling. MKV keeps SRT/ASS as they are.

## Batches and archives

- The archive records an item only **after it finished** (including
  post-processing). An interrupted download is retried on the next run, which
  is the point. Deleting a file does not remove its line, so it won't come back
  until the line is removed.
- The archive key is `extractor id`, not the URL or the filename. The same video
  through a different playlist URL is still skipped; the same video re-uploaded
  under a new id is not.
- Changing `-f` or `--audio-format` and re-running with the same archive skips
  everything. Use a separate archive per output type.
- `-I` indexes are the playlist's own order at the time of the run. A channel's
  "first 3" are the newest uploads and shift when the channel posts again.
- Hammering a site with big batches triggers "Sign in to confirm you're not a
  bot" or HTTP 429. Use `--sleep-requests 1 --sleep-interval 5`, and stop rather
  than retrying in a loop.

## "Sign in to confirm you're not a bot"

YouTube flags the **IP address** after a burst of requests (a few dozen in an
hour is enough), and then every request fails, whatever the options. Updating
yt-dlp doesn't help when it is already current. The ways out, from least to most
invasive:

1. **Wait.** The flag usually clears within hours. Tell the user and stop.
2. **Another network** (phone hotspot, VPN). The block is tied to the IP.
3. **A PO token provider plugin**, the route the yt-dlp wiki's *PO Token Guide*
   recommends. For example `bgutil-ytdlp-pot-provider` (`pip install` into the
   same Python as yt-dlp, plus its local token server). yt-dlp picks it up
   automatically, and no account is involved. Check with `-v` that the provider
   is listed.
4. **Cookies of a logged-in account**, `--cookies-from-browser safari`. Ask first,
   because it uses the user's identity. The yt-dlp wiki warns that accounts used
   for heavy automated downloading can get flagged, so suggest a secondary
   account rather than their main one. Safari needs Full Disk Access for the
   terminal.

Rotating `--extractor-args youtube:player_client=…` values doesn't get past
this block. They all fail the same way, so don't spend retries on them.

## Shell and files

- Quote URLs: zsh turns `?v=` into a glob ("no matches found") and `&` into a
  background job.
- Quote `-f`, `-S` and `-o` values; `[`, `]`, `*`, `>` and `|` are shell syntax.
- Titles can contain `/`, emoji and 200+ characters. yt-dlp sanitises `/`, but
  very long names fail on some filesystems: use `%(title).80B`.
- yt-dlp reads `~/.config/yt-dlp/config` (and `yt-dlp.conf` in the current folder)
  if present. When results differ from what the command says, run with
  `--ignore-config` or `-v` to see the effective options.
- `-v` prints versions, the JS runtime and the full command; include it when
  reporting a bug upstream.
