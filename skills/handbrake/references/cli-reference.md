# HandBrakeCLI flag reference (1.11.2)

Checked against `HandBrakeCLI --help` from the Homebrew build of 1.11.2. The full help
is about 730 lines, so grep it instead of reading it:
`HandBrakeCLI --help 2>/dev/null | grep -A4 -- '--subtitle-burned'`. Flags differ
slightly between builds (the encoder list depends on how it was compiled), so check
`bash scripts/hb.sh --check` on a new machine.

## General

| Flag | Meaning |
|---|---|
| `-i FILE` / `-o FILE` | source, destination (required) |
| `--json` | scan info and progress as labelled JSON blocks on **stdout** (`Version: {…}`, `JSON Title Set: {…}`, `Progress: {…}`). The log goes to stderr |
| `-v[N]` | log verbosity (stderr) |
| `-Z NAME` | preset (case-sensitive). `-z` lists all of them |
| `--preset-import-file F…` | import presets from a JSON export (space-separated list or wildcard) |
| `--preset-export NAME --preset-export-file F` | write the effective settings of the current command line as a preset (combined with `-Z X`, this gives the resolved preset X) |
| `--queue-import-file F` | run a queue exported from the GUI |

## Source and titles

| Flag | Meaning |
|---|---|
| `-t N` | title (default 1). `-t 0` with `--scan` scans every title |
| `--scan` | scan only, encode nothing |
| `--main-feature` | pick the disc's main feature |
| `--min-duration S` / `--max-duration S` | ignore titles shorter/longer (default min 10 s) |
| `-c 1-3` | chapters. `--angle N`: DVD/BD angle |
| `--start-at seconds:N` / `--stop-at seconds:N` | partial encode (also `frames:`, `pts:` on a 90 kHz clock) |

## Container

| Flag | Meaning |
|---|---|
| `-f av_mp4\|av_mov\|av_mkv\|av_webm` | container (default: from the `-o` extension) |
| `-m` / `--no-markers` | chapter markers |
| `-O` | MP4 fast start (web streaming) |
| `--keep-metadata` | copy the source's common metadata |
| `--align-av` | pad the start so audio and video start together |

## Video

| Flag | Meaning |
|---|---|
| `-e ENC` | `x265 x265_10bit x265_12bit vt_h265 vt_h265_10bit x264 x264_10bit vt_h264 svt_av1 svt_av1_10bit VP9 VP9_10bit VP8 vt_prores dnxhr dnxhr_10bit ffv1 mpeg4 mpeg2 theora` |
| `-q Q` | constant quality (RF). Lower = better and bigger |
| `-b KBPS` | average bitrate instead of `-q`. `--multi-pass` (plus `-T` turbo first pass) |
| `--encoder-preset P` | speed/efficiency trade-off (`--encoder-preset-list x265`: ultrafast…placebo; SVT-AV1: 0–13) |
| `--encoder-tune T`, `--encoder-profile P`, `--encoder-level L` | each has a `-list` variant |
| `-x k=v:k=v` | raw encoder options |
| `-r FPS`, `--vfr` / `--cfr` / `--pfr` | frame rate and its mode |

## Picture

| Flag | Meaning |
|---|---|
| `-X W` / `-Y H` | maximum width/height: scales down, never up |
| `-w W` / `-l H` | exact storage size (**height is `-l`**, and `-h` is help) |
| `--non-anamorphic` | square pixels (PAR 1:1) |
| `--keep-display-aspect` | keep the source's display aspect ratio when sizing |
| `--auto-anamorphic` / `--loose-anamorphic` / `--custom-anamorphic` | anamorphic modes (presets default to auto) |
| `--crop-mode auto\|conservative\|none\|custom`, `--crop T:B:L:R` | crop. Auto removes black bars |
| `--modulus N` | storage size multiple (2, 4, 8, 16) |
| `--comb-detect`, `--decomb`, `-d`/`--deinterlace`, `--denoise`/`--nlmeans`, `--deblock`, `--rotate` | filters |

## Audio (per selected track, comma-separated)

| Flag | Meaning |
|---|---|
| `-a 1,3` | source tracks by 1-based number, `none` for no audio. Default: the first track |
| `--audio-lang-list eng,hun` + `--all-audio` / `--first-audio` | select by ISO 639-2 language (`any` matches all) |
| `-E ENC,ENC` | one encoder per selected track: `ca_aac ca_haac opus ac3 eac3 mp3 flac16 flac24 alac16 alac24 vorbis pcm16 pcm24 truehd`, or `copy`, `copy:aac`, `copy:ac3`, … |
| `--audio-copy-mask aac,ac3,…` | codecs that `copy` may pass through |
| `--audio-fallback ENC` | encoder used when copying is impossible |
| `-B KBPS`, `-6 mono\|stereo\|dpl2\|5point1\|…`, `-R HZ`, `--gain DB`, `-D DRC` | bitrate, mixdown, sample rate, gain, dynamic range compression |
| `-A NAME` | track names |

The Homebrew macOS build lists `ca_aac` (Core Audio) and **no `av_aac`**, so the
default AAC encoder is `ca_aac`. Presets written on another OS that name `av_aac`
are mapped to the available AAC encoder.

## Subtitles

| Flag | Meaning |
|---|---|
| `-s 2,3` | source subtitle tracks by 1-based number. `none`. `scan` = foreign-audio search pass |
| `--subtitle-lang-list L` + `--all-subtitles` / `--first-subtitle` | select by language |
| `--subtitle-burned[=N]` | burn the N-th track **of the `-s` list** (not the source number). Default N = 1 |
| `--subtitle-default[=N]` | flag the N-th `-s` track as default. `none` clears it |
| `-F[=N]` / `--subtitle-forced` | only the forced captions of the track |
| `-N LANG` + `--native-dub` | native-language behaviour (subtitles, or dub if available) |
| `--srt-file a.srt,b.srt`, `--srt-lang eng,hun`, `--srt-codeset UTF-8`, `--srt-burn[=N]`, `--srt-default[=N]` | add external SRT files |
| `--ssa-file …` (same family) | external SSA/ASS |

## Exit codes seen on 1.11.2

| Situation | Exit |
|---|---|
| Success | 0 |
| Missing input, no title found, unknown preset name | 2 |
| Interrupted with SIGINT | 1, with a broken partial output left behind |
| **Unknown option** | **0**, nothing written, `unknown option (...)` on stderr |
