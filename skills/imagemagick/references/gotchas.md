# Gotchas

Each of these produces output that looks fine in a quick check and is still wrong.
Behaviour verified on ImageMagick 7.1.2-34 Q16-HDRI (Homebrew, macOS 27.2).

## Syntax and versions

- **IM6 vs IM7.** `convert in.jpg out.png` is IM6. On IM7 it still runs, with a
  deprecation warning and IM6 parsing quirks. On Windows, `convert` is a filesystem
  tool. Always use `magick`, and `magick mogrify|montage|compare|identify`. Old blog
  recipes also use `composite -dissolve`. In IM7 use `magick … -compose dissolve
  -define compose:args=40 -composite`, or the alpha-multiply form.
- **Settings vs operators.** `magick in.jpg out.jpg -quality 80` sets the quality
  *after* writing, so it has no effect. Put settings before the output, and `-font`
  before `-annotate`/`label:`.
- **Shell metacharacters in geometry.** `-resize 1600x1600>` without quotes redirects
  output to a file named `1600`. Quote the argument: `'1600x1600>'`.

## Overwriting

- **`mogrify` writes in place.** Without `-path OUTDIR` it rewrites the originals, with
  no undo. Even with `-format webp` and no `-path`, it writes next to the inputs, which
  mixes outputs into the source folder.
- **Same stem, different extensions.** `photo.jpg` and `photo.png` both become
  `photo.webp`, and the second one silently overwrites the first. `im_batch.py` refuses
  such collisions.

## Fonts

- **No fontconfig in Homebrew's build.** `magick -list font` prints nothing, so
  `-font Arial` and the default font both fail: `unable to read font ''`. `montage`
  labels fail the same way. Always pass a font file path.

## Orientation and colour

- **EXIF orientation.** A phone portrait is often stored landscape with
  `Orientation=6`. `-resize 1600x1600>` then measures the wrong edge, and `-strip`
  removes the tag, so the result displays sideways. Run `-auto-orient` first.
- **CMYK and wide-gamut sources.** `-colorspace sRGB` ignores the embedded ICC profile.
  On a CMYK JPEG the colours shift visibly (a purple came out 42/2/93 % instead of the
  profile-correct 45/17/47 %). Use `-profile sRGB.icc`. On an Adobe RGB file, a plain
  `-strip` leaves the numbers unchanged but drops the profile, so colours look
  desaturated in browsers.
- **Strip order.** `-strip -profile sRGB.icc` strips first. The image then has no source
  profile, so `-profile` merely *assigns* sRGB (a relabel, not a conversion). Convert
  first, then strip.
- **WebP has no CMYK.** Writing a CMYK JPEG straight to WebP makes IM convert naively.
  Do the profile conversion first.

## Trim, crop and canvas

- **`-trim` and off-white borders.** A single near-white speck stops the trim. With
  `-fuzz` too high (8 % on cream paper), it trims *into* the page. Use 2–4 % and check
  the resulting size.
- **Virtual canvas.** `-crop` and `-trim` keep the old page offset. PNG and GIF store it,
  and later `-extent`/`-composite` steps place things wrongly. Add `+repage`.
- **`-extent` without `-gravity center`** pads only right and bottom.
- **`-crop 3x3@`** makes *tiles*. `-crop 100x100` with no offset also tiles the whole
  image into many outputs (`out-0.png`, `out-1.png`, …). Add `+X+Y` for a single crop.

## Compositing

- **Logo opacity.** `-alpha set -channel A -evaluate multiply 0.4 +channel` scales the
  existing alpha. `-evaluate set 40%` sets *every* pixel's alpha to 40 %, so the logo's
  transparent background becomes a visible translucent box.
- **`-geometry` offsets are inward** from the gravity edge. `-gravity southeast -geometry
  +30+30` is 30 px from the right and the bottom, not past them.
- **Logo size.** A fixed `-resize 200x` logo looks tiny on 6000 px photos and huge on
  800 px ones. Scale it relative to each image (what `im_watermark.py --scale` does).

## Montage

- **`-label` is a setting.** `magick montage *.jpg -label '%f' …` puts the label after
  the files, so nothing gets labelled. Use `magick montage -label '%f' *.jpg …`.
- **Memory.** Montage decodes every input at full size. For big JPEGs, add `-define
  jpeg:size=600x600` (twice the tile) before the files.

## compare

- **AE is channel-averaged in 7.1.2.** A pixel that changed only in R and B counts as
  0.67. A 121-pixel change reported AE 80.67. For a true count, threshold the
  difference image and take the max across channels (what `im_compare.py` does).
- **SSIM is a distortion.** `-metric SSIM` prints 0 for identical images, the same as
  DSSIM. Similarity = 1 − value.
- **PSNR** prints dB with 120 for identical. The parenthesised value is dB/120.
- **Exit code 1 means "different", not an error.** Only 2 is an error. Don't wrap
  `compare` in `set -e` scripts without allowing 1.
- **Different sizes** are an error (`image widths or heights differ`). Resize one first,
  or use `-subimage-search` on purpose.

## Formats

- **`%Q` on PNG** is the zlib compression level, not a quality.
- **HEIC/AVIF** go through libheif. `-quality` maps to each encoder's own scale, so AVIF
  at 60 is not JPEG at 60. Compare the file sizes.
- **JPEG drops alpha.** Flatten with `-background white -alpha remove -alpha off` first,
  or transparent areas turn black.
- **Animated inputs.** `in.gif` has many frames. Without `[0]` you get many outputs
  (`out-0.png`, `out-1.png`, …), and `-coalesce` is needed before per-frame edits.
- **PDF input needs Ghostscript**, which this build lacks (`magick doc.pdf` fails).
  Render with poppler's `pdftoppm` first.
