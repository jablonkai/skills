# Filtergraphs and recipes

## Syntax in one screen

```
-vf  "scale=1280:-2,fps=30"                     # simple chain: one input, one output
-filter_complex "[0:v]split[a][b];[a]...[bg];[b]...[fg];[bg][fg]overlay[v]" -map "[v]" -map 0:a
```

- `,` chains filters, `;` separates chains, and `[label]` names pads. Inputs are
  `[N:v]` / `[N:a]` / `[N:v:1]`. A labelled output must be `-map`ped.
- Options are `filter=key=value:key=value`. Expressions like `(W-w)/2` and `min(ih,720)`
  are evaluated per frame. A `,` inside an expression must be escaped (`\,`) or
  quoted: `select='not(mod(n\,30))'`.
- `overlay`: `W/H` = main, `w/h` = overlay. `scale` inside `scale2ref`/`overlay`
  uses `iw/ih` for the input.
- Always quote the whole graph for the shell, and pass it as one argv element when
  building commands in code.
- Long graphs: `-/filter_complex graph.txt` reads the graph from a file, so there
  is no shell quoting at all. (The old `-filter_complex_script` is **gone in 9.0**
  and fails with "Unrecognized option". The `-/` prefix works for any option, e.g.
  `-/vf`.)

## Recipes (ff_recipe.py builds these)

**Fit into a box without cropping (letterbox / pillarbox)**
```
scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setsar=1
```
**Fill a box by cropping (centre)**
```
scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1
```
**9:16 with blurred fill**
```
[0:v]split[bg][fg];
[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=40,eq=brightness=-0.08[bgb];
[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fgs];
[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v]
```
`boxblur=20:5` is faster than `gblur` for 4K.

**Watermark / logo** (PNG with alpha, 15% of the width, bottom-right, 85% opacity)
```
-i in.mp4 -loop 1 -i logo.png -filter_complex
"[1:v]scale=288:-1,format=rgba,colorchannelmixer=aa=0.85[l];[0:v][l]overlay=W-w-32:H-h-32:shortest=1,format=yuv420p[v]"
-map "[v]" -map 0:a? -c:a copy
```
`-loop 1` on a still image plus `shortest=1` stops at the end of the video.
Timed: `overlay=...:enable='between(t,5,10)'`.

**Crossfade chain** (`xfade` + `acrossfade`)
```
[0:v][1:v]xfade=transition=fade:duration=1:offset=5[v1];
[v1][2:v]xfade=transition=fade:duration=1:offset=10[v];
[0:a][1:a]acrossfade=d=1[a1];[a1][2:a]acrossfade=d=1[a]
```
- `offset` is the time **in the output so far** at which the fade starts:
  offset_k = (d0 + … + d_{k−1}) − k·D. With 6 s clips and 1 s fades the offsets
  are 5, 10, and the total is 16 s.
- Both inputs must have the same size, frame rate, pixel format and time base, or
  you get "First input link main timebase do not match" or a corrupted fade. Normalise
  each one: `scale,pad,setsar=1,fps=30,format=yuv420p,settb=AVTB`.
- `acrossfade` overlaps by `d`, so audio length = video length. Clips without
  audio need `anullsrc` of the right length, or the chain stalls.
- Transitions: `fade dissolve wipeleft wiperight slideup slidedown circleopen
  radial fadeblack fadewhite pixelize zoomin` (see `ffmpeg -h filter=xfade`).

**GIF with a proper palette**
```
-ss 10 -t 5 -i in.mp4 -filter_complex
"fps=15,scale=480:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=sierra2_4a"
-loop 0 out.gif
```
`stats_mode=diff` plus `paletteuse=diff_mode=rectangle` suits mostly static
screen recordings. `dither=bayer:bayer_scale=3` gives smaller files. Keep it at
≤ 15 fps and ≤ 480–640 px, because GIF size grows fast. WebM/MP4 loops are 10x smaller.

**Contact sheet** (N evenly spaced frames, fast on long files)
```
-ss t1 -i in -ss t2 -i in ...  # one input seek per tile, tk = D·(k+0.5)/N
[0:v]trim=end_frame=1,setpts=PTS-STARTPTS,scale=480:-2[t0]; ... concat=n=16:v=1:a=0,tile=4x4:padding=6:margin=6
-frames:v 1 -update 1 sheet.png
```
The single-input form, `fps=N/D,scale=..,tile=4x4`, decodes the whole file. That
is fine for short clips and slow for an hour of 4K. `thumbnail` picks a
representative frame per batch, and `select='gt(scene,0.4)'` picks scene changes.

**Speed change**
```
-filter:v "setpts=PTS/4,fps=30" -filter:a "atempo=2,atempo=2"   # 4x
-filter:v "setpts=PTS*2" -filter:a "atempo=0.5"                  # half speed
```
Smooth slow motion: `minterpolate=fps=60:mi_mode=mci` (slow).

**Frame grabs**: `-ss 12.5 -i in -frames:v 1 -update 1 grab.png`. One frame
every 10 s: `-vf fps=1/10 -fps_mode vfr grabs/f_%04d.png`.

**drawtext** (ffmpeg-full only): `drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial.ttf:text='%{pts\:hms}':x=20:y=20:fontsize=36:fontcolor=white:box=1:boxcolor=black@0.5`.
Burn-in timecode: `drawtext=timecode='00\:00\:00\:00':rate=25:...`.

**Other common ones**: `crop=w:h:x:y`, `transpose=1` (90° clockwise), `hflip`,
`eq=brightness=0.05:contrast=1.1:saturation=1.2`, `lut3d=file.cube`,
`deshake`/`vidstabdetect`+`vidstabtransform` (ffmpeg-full), `yadif` (deinterlace),
`hqdn3d` (denoise), `fade=t=in:st=0:d=1`, `afade=t=out:st=55:d=2`,
`amix=inputs=2:duration=first:weights='1 0.3'`, `sidechaincompress` (ducking).
