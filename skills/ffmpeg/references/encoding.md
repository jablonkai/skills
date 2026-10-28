# Encoders and quality settings

Available in Homebrew FFmpeg 9.0.2 (`ff.sh --check` shows the live list):
libx264, libx265, libsvtav1, libvpx-vp9, h264/hevc/prores_videotoolbox, prores_ks,
aac, aac_at, libopus, libmp3lame, flac, pcm_*. Not built in: libfdk_aac, libaom-av1
(use libsvtav1), NVENC/QSV (not on a Mac).

## Choosing

| Goal | Encoder | Quality knob | Notes |
|---|---|---|---|
| Plays everywhere | `libx264 -pix_fmt yuv420p` | `-crf 18–23` (lower = better; 18 ≈ visually lossless) | `-preset slow` ≈ 10% smaller than `medium`, at 2x the time |
| Smaller, modern devices | `libx265 -tag:v hvc1` | `-crf 22–28` | ~40% smaller than x264 at the same quality. 10-bit: `-pix_fmt yuv420p10le` |
| Smallest / web AV1 | `libsvtav1` | `-crf 28–38`, `-preset 4–8` | preset 6 is a good balance. Safari needs Apple silicon / iOS 17+ |
| Web, open | `libvpx-vp9 -b:v 0` | `-crf 28–36` | `-row-mt 1` for speed. WebM + Opus |
| Fast on a Mac | `h264_videotoolbox` / `hevc_videotoolbox` | `-q:v 50–70` (**higher = better**) | 5–10x faster. Larger files. No `-crf`. `-tag:v hvc1` for HEVC |
| Edit master | `prores_ks -profile:v 3 -vendor apl0` | profile: 0 proxy, 1 LT, 2 422, 3 HQ, 4 4444, 5 XQ | `-pix_fmt yuv422p10le`, or `yuva444p10le` for 4444 with alpha. MOV + PCM audio |
| Fast ProRes | `prores_videotoolbox -profile:v 3` | same profile numbers | hardware ProRes on Apple silicon |
| Archive, lossless | `libx264 -qp 0` or `ffv1 -level 3` (MKV) | — | huge |

Bitrate targets instead of quality (streaming caps, size budgets): `-b:v 8M
-maxrate 10M -bufsize 16M`. Exact size: two-pass x264
(`-pass 1 -an -f null /dev/null && -pass 2`). Bitrate = target_bits / duration.

## Platform targets

| Target | Settings |
|---|---|
| YouTube 1080p | H.264 High, `-crf 18`, `-pix_fmt yuv420p`, `-g` half the fps (closed GOP), AAC 320k 48 kHz, `+faststart` |
| Instagram/TikTok Reels | 1080x1920, H.264, 30 fps, `-crf 20`, AAC 128–256k, ≤ 90 s for Reels |
| Web embed | H.264 `-crf 23 -preset slow`, `-movflags +faststart`. Optional VP9/AV1 alternative |
| Apple devices | HEVC `-tag:v hvc1` or H.264. Avoid 4:2:2 and 4:4:4 |
| Editors (Resolve/FCP/Premiere) | ProRes 422 / HQ MOV, or DNxHR `-c:v dnxhd -profile:v dnxhr_hq -pix_fmt yuv422p` (MOV/MXF), constant frame rate |
| Proxies | ProRes Proxy at half resolution, or H.264 540p `-crf 23 -preset veryfast -g 1`-ish short GOPs for scrubbing |

## Audio

| Codec | Settings |
|---|---|
| AAC (native) | `-c:a aac -b:a 192k` (stereo). `aac_at` (AudioToolbox) sounds slightly better at low rates |
| Opus | `-c:a libopus -b:a 96k–128k` (WebM/MKV/MP4) |
| MP3 | `-c:a libmp3lame -q:a 2` (VBR ~190k) |
| PCM | `-c:a pcm_s16le` / `pcm_s24le` (MOV/WAV) |
| FLAC | `-c:a flac` |

Downmix: `-ac 2`. Resample: `-ar 48000`. Mono → stereo: `-ac 2`. Pick a channel:
`-af "pan=mono|c0=FL"`.

## Hardware decode

`-hwaccel videotoolbox` before `-i` speeds up HEVC/ProRes decoding. Combine with
`scale_vt` to keep frames on the GPU. Software filters need
`hwdownload,format=nv12`. It is rarely worth it for short jobs.

## Things to check after an encode

`ff_probe.py OUT --expect vcodec=hevc,size=1920x1080,pix_fmt=yuv420p,duration=…`.
For quality-sensitive deliveries, measure VMAF against the source:
`ffmpeg -i out.mp4 -i src.mov -lavfi "[0:v][1:v]libvmaf" -f null -` (≥ 93 ≈
transparent for most viewers).
