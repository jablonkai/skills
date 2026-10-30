# ImageMagick 7 CLI reference

The flags that matter for batch work, checked against 7.1.2-34. Full docs:
<https://imagemagick.org/script/command-line-options.php>.

## Command shape

```
magick [input-settings] INPUT [operators…] [output-settings] OUTPUT
magick mogrify -path OUTDIR [operators…] FILES…      # one output per input
magick montage [settings] FILES… [layout] OUTPUT
magick compare -metric M A B DIFF|null:
magick identify -format '…' FILE
```

IM7 applies operators in order, to the images read so far. A **setting** (`-quality`,
`-font`, `-gravity`, `-background`, `-label`, `-define`) stays in force until it is
changed. Set it before the operator or the output it affects. `FILE[0]` reads only the
first frame or page. `FILE[1600x1600]` resizes while reading.

## Geometry

| Form | Meaning |
|---|---|
| `1600x1600` | fit inside, keep aspect (enlarges small images) |
| `1600x1600>` | shrink only, never enlarge |
| `1600x1600<` | enlarge only |
| `1080x1080^` | cover: the smaller side reaches the box (pair with `-extent`) |
| `1080x1080!` | exact size, ignores aspect (distorts) |
| `1600` / `x1600` | width only / height only |
| `50%` | scale |
| `2000000@` | at most that many pixels |
| `WxH+X+Y` | size plus offset, for `-crop`, `-extent`, `-geometry` |

Shells treat `>`, `<`, `!` and `^` specially. Quote the whole argument.

## Size and canvas

| Operator | Use |
|---|---|
| `-resize G` | quality resample (Lanczos/Mitchell). The default choice. |
| `-thumbnail G` | `-resize` plus a metadata strip, for small previews |
| `-sample G` / `-scale G` | nearest-neighbour / box; pixel art, fast previews |
| `-extent WxH` | pad or cut the canvas to WxH, anchored by `-gravity`, filled with `-background` |
| `-crop WxH+X+Y +repage` | cut a region; `+repage` drops the virtual canvas offset |
| `-trim +repage` | remove a uniform border; add `-fuzz N%` for near-uniform |
| `-border N` / `-bordercolor C` | frame on all sides (`-border 20x10` for horizontal x vertical) |
| `-splice WxH` / `-shave WxH` | add / remove rows and columns at the gravity edge |
| `-auto-orient` | apply EXIF Orientation to the pixels and reset the tag |
| `-rotate 90`, `-flip`, `-flop` | rotate CW, mirror vertically / horizontally |
| `-define jpeg:size=WxH` | (before input) let libjpeg decode at reduced size, much faster |

## Compositing

```sh
magick base.jpg \( logo.png -resize 240x -alpha set -channel A -evaluate multiply 0.4 +channel \) \
  -gravity southeast -geometry +30+30 -compose over -composite out.jpg
```

- `-gravity` places the overlay. `-geometry +X+Y` offsets it *inward* from that edge.
- `-compose` modes: `over` (normal), `multiply`, `screen`, `CopyOpacity` (use the
  second image as the alpha mask), `difference` (for diffs), `dissolve` (with
  `-define compose:args=40`).
- `\( … \)` is an image-list sub-stack (`(` `)` without escaping from Python argv).
- `mpr:NAME` is an in-memory register: `-write mpr:src +delete` … `mpr:src`.

## Text

`-font FILE -pointsize N -fill C [-stroke C -strokewidth N] [-undercolor C]` and then:

- `-annotate +X+Y 'text'`: draws on the current image (gravity-aware)
- `label:'text'`: makes a new image sized to the text (`-background none` for a transparent one)
- `caption:'text'` with `-size Wx`: word-wrapped to a width

Without fontconfig, `-font` must be a file path (`.ttf`, `.otf`, `.ttc`).

## Colour

| Option | Use |
|---|---|
| `-profile sRGB.icc` | convert from the embedded profile to sRGB (lcms). If the image has no profile, the first `-profile` *assigns* one. |
| `-colorspace sRGB` | maths conversion, **ignores embedded profiles**. Only right for untagged images. |
| `-colorspace Gray` | greyscale |
| `-strip` | remove EXIF, XMP, IPTC, comments and ICC. Do it after the profile conversion. |
| `+profile '!icc,*'` | remove every profile except ICC (keeps colour, drops EXIF) |
| `-set profile FILE` | attach a profile without converting |

macOS profiles live in `/System/Library/ColorSync/Profiles/` (`sRGB Profile.icc`,
`AdobeRGB1998.icc`, `Display P3.icc`, `Generic CMYK Profile.icc`).

## Encoders

| Format | Options |
|---|---|
| JPEG | `-quality 1-100` (82-90 typical), `-sampling-factor 4:2:0`, `-interlace JPEG` (progressive), `-define jpeg:extent=200kb` (target file size) |
| WebP | `-quality` (lossy), `-define webp:lossless=true`, `-define webp:method=6` (slower, smaller), `-define webp:alpha-quality=N` |
| AVIF / HEIC | `-quality` (50-70 typical for AVIF), `-define heic:speed=0-9` (lower = slower and smaller) |
| PNG | `-quality 95` = zlib level 9 with adaptive filtering. `PNG8:out.png` = palette, `PNG24:`/`PNG32:` force depth and alpha. |
| GIF | `-layers optimize`, `-loop 0`, `-delay` in 1/100 s, `-colors 128` |
| TIFF | `-compress zip\|lzw\|none` |

Force a format regardless of the extension with a prefix: `webp:out.bin`.

## identify -format escapes

`%f` file name, `%t` name without extension, `%e` extension, `%m` format, `%w`/`%h`
pixel size, `%[colorspace]`, `%z` depth, `%A` alpha (`True`/`False`/`Blend`), `%Q`
quality (JPEG/WebP; zlib level for PNG), `%b` file size, `%n` frames, `%[orientation]`,
`%[profiles]` (e.g. `exif,icc`), `%[icc:description]`, `%[EXIF:*]` (all EXIF keys),
`%[EXIF:GPS*]`, `%@` trim bounding box, `%[pixel:p{X,Y}]` one pixel, `%[fx:mean]`,
`%[fx:standard_deviation]`, `%[distortion]` (after `-compare`). Use `FILE[0]` for
multi-frame files, or you get one line per frame.

## compare

```sh
magick compare -metric RMSE a.png b.png diff.png    # stderr: "raw (normalised)"; exit 0 same, 1 differ, 2 error
magick a.png b.png -metric RMSE -compare -format '%[distortion]' info:   # normalised value on stdout
```

7.1.2 metrics: `RMSE`, `MAE`, `PSNR` (dB, 120 = identical, normalised = dB/120),
`SSIM` and `DSSIM` (both are **distortions**: 0 = identical), `AE` (channel-averaged:
not a pixel count), `NCC`, `PHASH`. `-fuzz N%` makes small differences count as equal.
`-highlight-color`/`-lowlight-color` style the diff image. Both images must be the same
size; `-subimage-search` finds a small image inside a large one.

## mogrify

`magick mogrify -path OUTDIR -format webp [operators] *.jpg` writes `OUTDIR/NAME.webp`.
Without `-path` it **overwrites the inputs**, or writes next to them when `-format`
changes the extension. It has no parentheses or multi-image composition, so use a
`magick` loop (or the scripts) for overlays.

## Limits

`magick -list resource` shows the memory, disk and pixel-area limits. Huge images (more
than ~16k px a side) can hit `width or height exceeds limit` from `policy.xml`. Use
`-limit memory 2GiB -limit disk 8GiB` per command, or `-define registry:temporary-path=DIR`.
