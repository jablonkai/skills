# More recipes

Raw `magick` commands for jobs the scripts don't wrap. Each was run against
7.1.2-34. `F` is a font file (`bash scripts/im.sh --check` prints one).

```sh
F=/System/Library/Fonts/Supplemental/Arial.ttf
```

## Square thumbnails (cover and crop)

```sh
magick in.jpg -auto-orient -resize 400x400^ -gravity center -extent 400x400 -strip thumb.jpg
# whole folder, safely:
magick mogrify -path thumbs/ -auto-orient -thumbnail 400x400^ -gravity center -extent 400x400 *.jpg
```

## Hit a file-size target

```sh
magick in.jpg -resize 1600x -define jpeg:extent=200kb out.jpg     # JPEG only; searches the quality
```

For WebP/AVIF, try a few `-quality` values and keep the largest that fits.

## Caption, banner and text effects

```sh
# caption on a translucent box at the bottom
magick in.jpg -gravity south -font "$F" -pointsize 48 -fill white -undercolor '#0008' -annotate +0+40 ' Caption ' out.jpg
# word-wrapped text block as its own image
magick -size 800x -background none -font "$F" -pointsize 32 -fill black caption:'Long text that wraps…' block.png
# outlined text that reads on any background
magick in.jpg -gravity center -font "$F" -pointsize 120 -fill white -stroke black -strokewidth 4 -annotate +0+0 'SALE' out.jpg
```

## Sprite sheets and strips

```sh
magick a.png b.png c.png -resize x100 +append strip.png   # side by side (-append = stacked)
magick montage icons/*.png -tile 8x -geometry 64x64+0+0 -background none sprites.png
```

## Animated GIF / frames

```sh
magick -delay 50 frames/*.png -resize 400x400 -loop 0 -layers optimize anim.gif   # 0.5 s per frame
magick anim.gif -coalesce frame_%02d.png     # coalesce first, or later frames are partial deltas
```

To make a GIF from a *video*, use ffmpeg (palettegen/paletteuse). It is far better.

## Favicons

```sh
magick logo.png -background none -gravity center -extent 512x512 -define icon:auto-resize=256,64,32,16 favicon.ico
```

## Transparency

```sh
magick in.png -fuzz 6% -transparent white out.png             # knock out a flat background colour
magick in.png -background white -alpha remove -alpha off out.jpg   # flatten onto white before JPEG
magick in.png -alpha extract mask.png                          # alpha channel as greyscale
```

ML background removal on photos is not an ImageMagick job (pixelmator-pro, or `rembg`).

## Colour and tone

```sh
magick in.jpg -colorspace Gray out.jpg
magick in.jpg -auto-level out.jpg                 # stretch contrast to full range
magick in.jpg -modulate 100,130 out.jpg           # brightness 100 %, saturation 130 %
magick in.jpg -sepia-tone 80% out.jpg
magick in.jpg -profile "/System/Library/ColorSync/Profiles/Display P3.icc" out-p3.jpg   # tag/convert to P3
```

## Before and after side by side, with labels

```sh
magick \( before.jpg -resize 800x \) \( after.jpg -resize 800x \) -background white \
  -font "$F" -pointsize 28 -gravity north -splice 0x40 -annotate +0+5 '%t' +append compare.jpg
```

## PDF pages

This build has no Ghostscript, so `magick file.pdf` fails. Render with poppler first
(`pdftoppm -r 200 -png in.pdf page`, see the poppler skill), then process the PNGs with
magick. Going the other way, `magick *.jpg out.pdf` (images into a PDF) works without
Ghostscript.

## Montage variations

```sh
# polaroid-ish frames and shadow
magick montage photos/*.jpg -font "$F" -label '%t' -tile 5x -geometry 240x240+10+10 -shadow -background '#eee' sheet.jpg
# no labels, tight grid
magick montage photos/*.jpg -tile 6x -geometry 200x200+2+2 grid.jpg
```

## Batch with a shell loop (when mogrify can't composite)

```sh
mkdir -p out
for f in photos/*.jpg; do
  magick "$f" -auto-orient \( logo.png -resize 200x \) -gravity southeast -geometry +20+20 -composite "out/$(basename "$f")"
done
```
