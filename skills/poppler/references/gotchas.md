# Gotchas — behaviour verified on poppler 26.10.0 / qpdf 12.4.2

Each item looks right on the first try and isn't.

## Passwords

- **argv leaks.** `pdftotext -upw secret`, `qpdf --password=secret` and
  `--encrypt secret …` are visible to every user via `ps` and stay in shell history.
  qpdf reads `--password-file=F` and `@argfile` (one argument per line, taken literally).
  poppler has no file option, so decrypt with qpdf into a private temp file first.
- **Owner-only encryption is not a lock.** A file with only an owner password opens in
  any viewer (`pdfinfo` works) and `qpdf --decrypt` removes it with no password. It
  carries permission flags only.
- **qpdf rejects an empty owner password** next to a user password with AES-256
  (`--allow-insecure` overrides). It *accepts* an owner password equal to the user
  password, which hands full permissions to anyone who can open the file. Generate a
  random owner password and store it.
- **`--encrypt` needs its terminator** `--`, and with the flag form (`--user-password=`)
  you can't mix in the old positional form (`positional and dashed encryption
  arguments may not be mixed`).
- Operations on an encrypted primary input **keep the encryption** in the output.
  Use `--decrypt` when the user wants an open file.

## Pages

- **`pdfunite`** concatenates naively: outlines, links, form fields and named
  destinations are lost, and encrypted inputs fail. `qpdf --empty --pages` keeps them
  where it can.
- **`pdfseparate in.pdf out.pdf`** fails for more than one page: the pattern must contain `%d`.
- **`:odd` / `:even`** apply to the selection: `4-9:odd` is 4, 6, 8, not the odd page
  numbers. There's no every-n-th syntax; build the list (`select --every N`).
- **Exclusions bind to the previous group**: `1-10,x3,x5-6`. A leading `x` with no
  group before it selects nothing.
- **`--rotate=90`** (no sign) sets an absolute rotation and **`+90`** adds to the current
  one. The qpdf manual says you almost always want the signed form.
- **Merging mixed page sizes** keeps each page's size. Nothing is scaled. Report it
  (`pdf_inspect.py`) if the user expects uniform pages.

## Text

- **Default `pdftotext`** (no `-layout`) reflows columns into reading order guesses.
  Two-column pages interleave unless `-layout` is used. `-raw` gives content-stream
  order, which is often scrambled.
- Output `OUT` defaults to `IN.txt` next to the input: pass `-` for stdout.
- Pages are separated by **form feeds** (`\f`); `-nopgbrk` drops them.
- **Empty text** means no text layer (a scan). It isn't an error from poppler's point of
  view: exit 0, empty output.

## Images

- **`-j`** writes JPEGs as-is and converts everything else to PPM/PBM. **`-all`** keeps
  JPEG, JPEG 2000, JBIG2 and CCITT native and writes the rest as PNG.
- **Soft masks are separate files.** An RGBA image is stored as an RGB image plus an
  `smask`; `pdfimages -all` writes both (the mask as gray PNG). Count `type=image` rows
  as "images"; merge mask + colour with ImageMagick
  (`magick col.png mask.png -compose CopyOpacity -composite out.png`) if the user wants
  transparency back.
- **Repeated placements** of one image object are listed and extracted once per
  placement. Deduplicate by `object ID` if needed.
- Extracted images are at their **native resolution**, not the size shown on the page.
  `x-ppi`/`y-ppi` in `-list` give the effective placement resolution.

## Rendering

- **Names are padded** to the page count's width (`p-01.png` … `p-12.png`, but `p-1.png`
  for a 3-page file). `-singlefile` with one page per call gives exact names.
- **Pixels = ceil(points × DPI / 72).** A4 at 300 DPI is 2481 × 3508. `/Rotate 90`/`270` swaps
  width and height. Default rendering uses the **CropBox**. `pdfinfo` page sizes are
  the CropBox too; use `pdfinfo -box` to see MediaBox/TrimBox/BleedBox.
- `pdftoppm` has no SVG/PDF output. Use `pdftocairo -svg` (one page per call;
  multi-page SVG isn't a thing).

## qpdf exit codes

`3` = warnings and **the output was written**. A repaired file typically exits 3 while
qpdf rebuilds the xref, and then `qpdf --check fixed.pdf` exits 0. Treating 3 as failure
throws away good repairs; treating 2 as success ships broken files.
