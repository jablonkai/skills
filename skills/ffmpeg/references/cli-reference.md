# ffmpeg / ffprobe CLI reference

Checked against `ffmpeg -h full` on FFmpeg 9.0.2. Option position matters:
an option applies to the **next** `-i` (input options) or the **next output file**
(output options).

## Command shape

```
ffmpeg [global] [input opts] -i IN1 [input opts] -i IN2 ... [output opts] OUT1 [output opts] OUT2
```
Global: `-hide_banner -nostdin -y|-n -loglevel error|warning|info -stats -progress pipe:1 -stats_period 1`.

## Stream selection (`-map`)

| Spec | Means |
|---|---|
| `-map 0` | every stream of input 0 |
| `-map 0:v:0` | first video stream of input 0 |
| `-map 0:a` / `0:a?` | all audio (the `?` makes it optional, so it doesn't fail when there is none) |
| `-map 0:m:language:hun` | streams tagged Hungarian |
| `-map -0:d` | negative: drop data streams (timecode, GPS) |
| `-map "[v]"` | a labelled filtergraph output |
| `-map 1:a:0` | audio from the second input (audio replacement) |

Per-stream options take the same specifiers: `-c:a:1 aac`, `-b:a:0 192k`,
`-filter:a:0 loudnorm=...`, `-metadata:s:a:0 language=hun`,
`-disposition:s:0 default`. Later, more specific options override earlier ones
for the streams they match (`-c copy -c:a:0 aac` = copy all, re-encode the first audio).

## Codecs

`-c copy` (all), `-c:v copy -c:a aac`, `-vn/-an/-sn/-dn` drop a stream type.
Encoder options: `ffmpeg -h encoder=libx264`. Lists: `-encoders`, `-decoders`,
`-filters`, `-pix_fmts`, `-h filter=xfade`.

## Seeking and length

| Option | Where | Effect |
|---|---|---|
| `-ss T` | before `-i` | fast input seek. Copy: nearest keyframe before T. Re-encode: frame-accurate |
| `-ss T` | after `-i` | decode and discard up to T (slow) |
| `-t D` | either | duration |
| `-to T` | either | end position (input: input time; output: output time) |
| `-sseof -10` | before `-i` | seek relative to the end |
| `-itsoffset 0.2` | before `-i` | shift that input's timestamps (A/V sync fixes) |

Time format: `90`, `1:30`, `00:01:30.250`, `1500ms`.

## Concat

Demuxer (lossless, identical parameters):
```
printf "file '%s'\n" /abs/a.mp4 /abs/b.mp4 > list.txt
ffmpeg -f concat -safe 0 -i list.txt -map 0 -c copy -movflags +faststart out.mp4
```
Per-entry `inpoint`/`outpoint` lines can trim inside the list, but only on
keyframes for copy. Filter (re-encode, any sources):
`[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]` after normalising size, fps, SAR,
sample rate and layout.

## Progress and monitoring

`-progress pipe:1 -nostats` prints `key=value` blocks (`out_time_us`, `frame`,
`fps`, `speed`, `progress=continue|end`) every `-stats_period` seconds. Percent =
out_time_us / 1e6 / duration. `ff_lib.run_ffmpeg` parses it. `q` on stdin or
SIGINT stops ffmpeg gracefully and finalises the file (MP4 is playable up to that
point). SIGKILL leaves an unplayable MP4 with no moov atom.

## Metadata and chapters

`-map_metadata 0` (global tags), `-map_chapters 0`, `-metadata title="…"`,
`-metadata:s:a:0 language=eng`, `-movflags +use_metadata_tags` (keep custom MOV tags),
creation time: `-metadata creation_time=2026-10-01T10:00:00Z`.

## ffprobe

```
ffprobe -v error -of json -show_format -show_streams IN            # everything
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,pix_fmt -of csv=p=0 IN
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 IN
ffprobe -v error -select_streams v:0 -show_entries packet=pts_time,flags -of csv=p=0 IN | grep K   # keyframes
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames IN          # exact frame count (decodes)
```
`ff_probe.py` wraps these: summary, `--json`, `--keyframes [--near T]`,
`--loudness`, and `--expect key=value,...` as a pass/fail check.

## Measurements

- Loudness: `-af ebur128=peak=true -f null -` (summary I, LRA, true peak) or
  `loudnorm=print_format=json`.
- Black frames / silence: `-vf blackdetect=d=0.5:pix_th=0.1`, `-af silencedetect=n=-50dB:d=1`.
- Quality vs source: `[0:v][1:v]libvmaf` (built in), `psnr`, `ssim`.
- Scene changes: `-vf "select='gt(scene,0.4)',showinfo" -f null -`.
