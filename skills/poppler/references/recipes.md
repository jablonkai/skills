# Raw-CLI recipes beyond the scripts

All verified with poppler 26.10.0 and qpdf 12.4.2. Check every output afterwards with
`qpdf --check OUT` and `qpdf --show-npages OUT`.

## Overlay / underlay (stamp, letterhead, watermark page)

```sh
# put page 1 of stamp.pdf on every page of doc.pdf (underlay: --underlay)
qpdf doc.pdf --overlay stamp.pdf --to=1-z --from=1 --repeat=1 -- out.pdf
```

`--from` picks the overlay pages and `--repeat` cycles them. The overlay is scaled to
fit each target page.

## Interleave scanned fronts and backs

```sh
qpdf --empty --collate --pages fronts.pdf backs.pdf z-1 -- book.pdf
```

`z-1` reverses the backs, as a stack scanned from the other side comes out backwards.

## Attachments

```sh
qpdf doc.pdf --add-attachment data.csv -- out.pdf     # key defaults to the file name
qpdf --list-attachments out.pdf
qpdf --show-attachment=data.csv out.pdf > data.csv    # extract
qpdf doc.pdf --remove-attachment=data.csv out.pdf
```

## Structure queries with qpdf JSON (v2)

```sh
qpdf --json=2 --json-key=pages doc.pdf          # per page: object, images, label, outlines
qpdf --json=2 --json-key=outlines doc.pdf       # bookmarks
qpdf --json=2 --json-key=acroform doc.pdf       # form fields
qpdf --json=2 --json-key=qpdf --json-object=trailer doc.pdf   # raw objects ("qpdf" key in v2)
```

## Word positions

```sh
pdftotext -tsv -f 2 -l 2 doc.pdf words.tsv     # level 5 rows = words: left top width height text
pdftotext -bbox-layout doc.pdf boxes.html      # blocks > lines > words with xMin/yMin/xMax/yMax
```

Coordinates are in points from the **top-left** of the page.

## Text from a region

```sh
# crop area in pixels at -r resolution (default 72 => points): x, y from top-left
pdftotext -f 1 -l 1 -x 300 -y 0 -W 300 -H 200 -layout doc.pdf -
```

## Rendering variants

```sh
pdftoppm -r 150 -png -scale-to 1200 doc.pdf thumbs/p     # fit in a 1200 px box
pdftoppm -jpeg -jpegopt quality=85 -r 200 -f 1 -l 1 -singlefile doc.pdf cover
pdftocairo -png -transp -r 300 -f 1 -l 1 -singlefile logo.pdf logo   # transparent background
pdftocairo -svg -f 3 -l 3 doc.pdf page3.svg                # vector, one page per call
pdftocairo -eps -f 1 -l 1 doc.pdf fig.eps
pdftoppm -gray -r 300 -tiff -tiffcompression lzw doc.pdf scan  # archival gray TIFF
```

## Shrink a PDF (lossless first)

```sh
qpdf --object-streams=generate --compress-streams=y --recompress-flate doc.pdf smaller.pdf
qpdf --optimize-images --object-streams=generate doc.pdf smaller.pdf  # lossy: images to JPEG where smaller
```

Compare sizes. qpdf doesn't downsample, so image-heavy files need Ghostscript or an editor.

## Metadata

`pdfinfo` reads the Info dictionary; `pdfinfo -meta` prints XMP. Neither poppler nor
qpdf has a simple "set title" flag. Edit with `qpdf --json` round-trip
(`--json-output` → edit `/Info` → `--json-input`) or `exiftool -Title="…" doc.pdf`.

## PDF/A check

veraPDF (if installed) validates PDF/A: `verapdf --format text doc.pdf`. Creating
PDF/A is outside this skill (libreoffice exports it from documents).
