---
name: imagemagick
description: 'Batch-process raster images with the ImageMagick 7 CLI (magick, mogrify, montage, compare): resize, crop, pad and convert images or whole folders into a new folder without touching originals (HEIC/iPhone photos to JPEG, WebP, AVIF, no upscaling, auto-orient), logo or text watermarks, labelled contact sheets, square, story and OG versions with blurred-background padding, trimmed borders, frames and rounded corners, sRGB conversion and EXIF/GPS stripping for the web, and screenshot diffs with an exact changed-pixel count. Use for "resize this folder to 1600 px as WebP", "convert these HEICs to JPEG", "watermark every photo with my logo", "make a contact sheet", "Instagram square and story versions", "strip GPS before upload", "how different are these two screenshots". Not for retouching or painting (gimp, krita), ML edits (pixelmator-pro), PSD layers (photocraft), raw development (lightcraft), SVG/vector (inkscape), the Photos library (apple-photos), video or GIFs from video (ffmpeg), or PDF pages (poppler).'
summary: "batch-process images with the ImageMagick 7 CLI — folder resize and WebP/AVIF/HEIC/JPEG conversion without touching originals, logo and text watermarks, labelled contact sheets, blurred-pad social sizes, trim, borders and rounded corners, sRGB and metadata strip, compare diffs, identify-verified outputs"
category: design-automation
compatibility: "Built for ImageMagick 7.1.2-34 Q16-HDRI (Homebrew) on macOS 27.2; Python 3.9+ for the helper scripts. Also runs with ImageMagick 7 on Linux."
risk: low
tags: [imagemagick, magick, mogrify, montage, resize, webp, avif, watermark, contact-sheet, batch]
license: GPL-3.0-only
metadata:
  version: "1.0.0"
  author: "Tamás Jablonkai"
---

# Batch image work with ImageMagick 7

Headless command-line only: no app, no bridge. Every operation is one `magick` process.
The bundled scripts cover the jobs people ask for most, and they **verify every
output**: size, format, colourspace, untouched originals. Verified against
**ImageMagick 7.1.2-34 Q16-HDRI** on macOS 27.2.

```sh
S=<this skill>/scripts
bash $S/im.sh --check     # magick version, WebP/AVIF/HEIC write support, the font file to use
```

Always use IM7 syntax, `magick …`. Never use bare `convert`: on IM7 it is a deprecated
shim, and on Windows it is a disk tool. `mogrify`, `montage`, `compare` and `identify`
run as `magick mogrify` and so on.

## Ground rules

- **Never write over the originals.** Write into a new folder. `magick mogrify` without
  `-path OUTDIR` rewrites the files in place. The scripts refuse an output folder that
  holds an input, and they checksum the inputs before and after.
- **Text needs a font *file*.** Homebrew's ImageMagick has no fontconfig, so
  `magick -list font` is empty and `-font Arial` or the default font fails with
  `unable to read font`. Pass `-font /System/Library/Fonts/Supplemental/Arial.ttf`
  (`im.sh --check` prints the one to use).
- **`-auto-orient` first.** Phone photos are often stored sideways with an EXIF
  Orientation tag. Resize before orienting, or strip before orienting, and portraits
  come out sideways.
- **Colour-manage, then strip.** For files with an ICC profile (Adobe RGB, Display P3,
  CMYK), convert with `-profile "/System/Library/ColorSync/Profiles/sRGB Profile.icc"`.
  `-colorspace sRGB` ignores the embedded profile and turns CMYK colours visibly wrong.
  `-strip` drops the profile too, so it comes *after* the conversion.

## Scripts

Each prints a JSON report with `"ok"` and exits 0 only when its checks pass. The report
is your verification: read it, and quote its numbers to the user.

| Script | Does |
|---|---|
| `im_batch.py IN… --out DIR` | resize (`--max PX` long edge, `--width`, `--height`, `--exact WxH --fit pad\|crop\|stretch`), convert (`--format webp\|avif\|heic\|jpeg\|png\|tiff`, `--quality`, `--lossless`), `--srgb`, `--strip`, `--suffix`, `--recursive`. Never upscales unless `--upscale`. Skips non-images (e.g. `.AAE` sidecars) and lists them. `--recursive` mirrors subfolders. Same-stem files (`IMG_0001.HEIC` + `IMG_0001.PNG`) are both kept, the second as `IMG_0001_png.jpg`. |
| `im_watermark.py IN… --out DIR --logo F \| --text T` | `--gravity southeast`, `--opacity 0.4`, `--scale` (× shorter side), `--margin`, `--stroke` for text. Checks that only the mark box changed. |
| `im_montage.py IN… OUT.jpg --cols 4` | labelled contact sheet in name order. `--tile 300x300`, `--label '%f'\|'%t'\|none`, `--title`, `--spacing`. Checks the grid and the label strips. |
| `im_social.py IN… --out DIR --preset square --preset story` | fixed sizes with `--fill blur` (default), `color` or `crop`. Presets: square 1080², portrait 1080×1350, story/reel 1080×1920, og 1200×630, landscape, x, youtube. `--size WxH` for others. Checks that the subject is intact. |
| `im_inspect.py FILE_OR_DIR… [--json]` | format, display size, colourspace, depth, alpha, quality, ICC name, EXIF/GPS, orientation |
| `im_compare.py A B [--diff D.png] [--fuzz 3%] [--metric PIXELS\|RMSE\|PSNR\|SSIM --threshold X]` | the oracle: exact differing-pixel count and bbox, RMSE/MAE/PSNR dB/SSIM, a red-on-faded diff image |

## Recipes

```sh
# folder -> max 1600 px long edge, WebP, sRGB, no metadata, into a new folder
python3 $S/im_batch.py photos/ --out web/ --max 1600 --format webp --quality 82 --srgb --strip

# HEIC from the phone -> JPEG
python3 $S/im_batch.py ~/Desktop/heic/ --out jpg/ --format jpeg --quality 85 --srgb

# logo bottom-right at 40 %, about 15 % of the shorter side
python3 $S/im_watermark.py photos/ --out marked/ --logo logo.png --gravity southeast --opacity 0.4

# 4-column contact sheet with file names
python3 $S/im_montage.py photos/ contact.jpg --cols 4 --tile 300x300

# Instagram square + story with a blurred background instead of cropping
python3 $S/im_social.py beach.jpg --out social/ --preset square --preset story

# what differs between two screenshots
python3 $S/im_compare.py before.png after.png --diff diff.png
```

One-off edits are a single `magick` command. Verify each with
`python3 $S/im_inspect.py OUT`, or with `im_compare.py` against the source.

```sh
F=/System/Library/Fonts/Supplemental/Arial.ttf

# trim a near-white scanner border, then +repage. Keep fuzz LOW (2-4 %) and check the size:
# off-white paper is only ~6-10 % from white, so -fuzz 8% eats into the page itself
magick scan.png -fuzz 3% -trim +repage trimmed.png && magick identify -format '%wx%h\n' trimmed.png

# 20 px border, then 24 px rounded corners with transparency (PNG keeps alpha, JPEG cannot)
magick trimmed.png -bordercolor '#333' -border 20 \
  \( +clone -alpha extract -fill black -colorize 100% -fill white \
     -draw "roundrectangle 0,0 %[fx:w-1],%[fx:h-1] 24,24" \) \
  -alpha off -compose CopyOpacity -composite rounded.png

# web export of one file with an ICC profile
magick in.jpg -auto-orient -profile "/System/Library/ColorSync/Profiles/sRGB Profile.icc" -strip -quality 85 out.jpg

# in-place-style folder batch done safely
magick mogrify -path out/ -auto-orient -resize '1600x1600>' -format webp -quality 82 photos/*.jpg

# text caption with a background box
magick in.jpg -gravity south -font "$F" -pointsize 48 -fill white -undercolor '#0008' -annotate +0+40 ' Caption ' out.jpg
```

Geometry: `1600x1600>` = shrink only, `1600x1600^` = cover, `1080x1080!` = exact
(distorts), `50%` = scale. Quote `>`, `^` and `!` in the shell. More operators,
`-define` keys and `identify -format` escapes:
[references/cli-reference.md](references/cli-reference.md). Extra recipes (GIF frames,
sprite sheets, size targets, PDF pages): [references/recipes.md](references/recipes.md).

## Verify before you report

- Read the script's report. `ok: false`, a `problems` entry or `originals_unchanged:
  false` means the job isn't done.
- After a hand-written command: `im_inspect.py OUT` for size, format, colourspace and
  EXIF. Use `im_compare.py SRC OUT` when only part of the image should have changed.
  Compare the output count against the input count.
- Tell the user the numbers: how many files, the sizes, and where they went. Also list
  any skipped non-image files.

## Pitfalls that look right but aren't

Full list with explanations: [references/gotchas.md](references/gotchas.md).

- **`compare -metric AE` is not a pixel count** in 7.1.2. It averages over the channels,
  so a pixel that changed in 2 of 3 channels counts as 0.67. `-metric SSIM` returns a
  *distortion* (0 = identical). Use `im_compare.py`.
- **`montage -label`** is a setting: it has to come *before* the files, or the tiles get
  no labels.
- **`-trim` without `-fuzz`** stops at the first off-white speck, and too much fuzz
  trims into light paper. Use 2–4 %, then check the size. Without `+repage`, the old
  canvas offset survives into PNG/GIF.
- **Opacity on a logo:** `-channel A -evaluate multiply 0.4` keeps the transparent parts
  transparent. `-evaluate set 40%` or `-alpha set` on a flattened logo paints a
  translucent box.
- **`-resize 1600x1600`** without `>` enlarges small images, and a bare `-extent`
  without `-gravity center` pads only to the right and bottom.
- **Settings vs operators:** `-quality`, `-define` and `-font` must be set before the
  output or the text they affect. `-resize` acts on the images read so far.
