# Subtitles

## Burn in or keep as a track?

| Need | Do |
|---|---|
| Social video, anything that must show text on every player | **burn in** (re-encode): `ff_recipe.py burnsubs` |
| Switchable languages, accessibility, keep quality | **soft track** (stream copy): `ff_recipe.py mux-subs` |

## Burn-in

Needs a build with **libass**. Homebrew `ffmpeg` has none, so use `ffmpeg-full`
(`/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg`, keg-only). `ff_recipe.py` picks the
right binary on its own, and `ff.sh --check` shows which builds can do it.

```
FF=/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg
$FF -i in.mp4 -vf "subtitles=subs.srt:force_style='FontName=Arial,FontSize=22,Outline=2,MarginV=40'" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy out.mp4
```

- **Style** with `force_style` (ASS fields): `FontName`, `FontSize` (relative to a
  288-px-high script canvas, not to video pixels: 22 ≈ 8% of the frame height),
  `PrimaryColour=&H00FFFFFF` (AABBGGRR), `OutlineColour`, `BackColour`,
  `BorderStyle=3` (opaque box), `Outline`, `Shadow`, `Alignment` (numpad: 2 bottom
  centre, 8 top centre), `MarginV`, `Bold=1`.
- **ASS files** keep their own styling: `subtitles=file.ass`, or `ass=file.ass`.
- **Embedded track**: `subtitles=in.mkv:si=0` (the input path again, with the
  subtitle stream index).
- **Encoding**: `:charenc=CP1250` (Central European), `CP1252`, `ISO-8859-2` for
  SRTs that aren't UTF-8. Mojibake (Ãµ, Å‘) means a wrong or missing charenc.
- **Fonts**: libass uses fontconfig and the system fonts. Accents (ő, ű) render
  when the font has them. Arial and Helvetica do. `fontsdir=/path` adds a folder.
- **Path escaping**: inside the filter, `:` `,` `'` `[` `]` `\` must be escaped.
  Copy the file to a simple temporary name instead of escaping (the recipe does).
- **Vertical/cropped versions**: burn the subtitles *before* reframing to keep the
  original layout, or *after* to size them for the new frame (a larger `FontSize`
  for 9:16).
- **Bitmap subtitles** (PGS from Blu-ray, VobSub): `-filter_complex "[0:v][0:s:0]overlay[v]"`.
  They don't need libass.

## Soft subtitle tracks

```
ffmpeg -i in.mp4 -i eng.srt -i hun.srt -map 0:v -map 0:a -map 1 -map 2 \
  -c:v copy -c:a copy -c:s mov_text \
  -metadata:s:s:0 language=eng -metadata:s:s:1 language=hun -disposition:s:0 default out.mp4
```
- MP4/MOV: `mov_text` only (SRT is converted, styling is lost). MKV: SRT/ASS/PGS
  are copied as they are (`-c:s copy`). WebM: `webvtt`.
- Language codes are ISO 639-2 (`eng`, `hun`, `deu`).
- Extract: `ffmpeg -i in.mkv -map 0:s:0 out.srt`. Convert: `ffmpeg -i in.srt out.vtt` / `out.ass`.
- Shift timing: `ffmpeg -itsoffset 1.5 -i in.srt -c copy shifted.srt`.
