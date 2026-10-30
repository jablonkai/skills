# CLI reference — poppler 26.10.0 and qpdf 12.4.2

The flags that matter, checked against the installed `-h` / `--help=` output. Full
help: `pdftotext -h`, `qpdf --help=all`, <https://qpdf.readthedocs.io>.

## poppler

All tools take `-f N -l M` (first/last page, 1-based) and `-upw`/`-opw` for passwords.
Those go on argv, so prefer decrypting with qpdf first; see [gotchas.md](gotchas.md).

| Tool | Key flags |
|---|---|
| `pdfinfo FILE` | `-f 1 -l N` per-page `size`/`rot` lines · `-box` Media/Crop/Bleed/Trim/ArtBox · `-meta` XMP · `-js` JavaScript · `-struct` tag tree · `-isodates` · `-rawdates` |
| `pdffonts FILE` | columns `name type encoding emb sub uni object ID`; `emb no` = not embedded; `[none]` name = Type 3 font; `-subst` shows substitutes |
| `pdftotext FILE OUT\|-` | `-layout` keeps columns · `-raw` content-stream order · `-fixed N` · `-bbox` / `-bbox-layout` XHTML word boxes · `-tsv` word table · `-cropbox` · `-x -y -W -H` crop area · `-enc UTF-8` · `-nopgbrk` no form feeds · `-eol unix` |
| `pdfimages FILE PREFIX` | `-list` table (page, num, type image/smask/stencil, size, enc, object ID) · `-all` native formats · `-j` JPEG only · `-png`/`-tiff` force · `-p` page number in names (`PREFIX-PPP-NNN.ext`) |
| `pdftoppm FILE PREFIX` | `-png`/`-jpeg`/`-tiff` · `-r DPI` (default 150) · `-scale-to N` / `-scale-to-x/-y` · `-singlefile` · `-gray` / `-mono` · `-cropbox` · `-jpegopt quality=90` · `-x -y -W -H` crop |
| `pdftocairo FILE OUT` | `-png -jpeg -tiff -pdf -svg -ps -eps` · `-r DPI` · `-transp` transparent PNG background · `-singlefile` · `-paper A4` (ps/pdf) · vector output for svg/pdf/ps |
| `pdfseparate IN out-%d.pdf` | one file per page; the pattern **must** contain `%d` |
| `pdfunite a.pdf b.pdf OUT` | simple concat; drops outlines/forms, no encrypted input |

### `pdfimages -list` columns

`page num type width height color comp bpc enc interp object ID x-ppi y-ppi size ratio`.
`type`: `image`, `smask` (soft mask = alpha of the previous image), `stencil` (1-bit
mask). `enc`: `jpeg` → `.jpg`, `jpx` → `.jp2`, `jbig2` → `.jb2e` (+ `.jb2g` globals),
`ccitt` → `.ccitt` (+ `.params`), `image` (raw/Flate) → `.png` with `-all`. The same
image placed twice is listed (and extracted) twice.

## qpdf

General form: `qpdf [options] INPUT [--pages …  --] OUTPUT`. `--replace-input` instead
of OUTPUT writes in place (avoid it until the result is checked).

| Task | Command |
|---|---|
| select pages | `qpdf in.pdf --pages . 1-3,7 -- out.pdf` (`.` = the primary input) |
| merge | `qpdf --empty --pages a.pdf b.pdf 1-3 c.pdf -- out.pdf` (`--empty` = no metadata from a primary) |
| rotate | `qpdf in.pdf --rotate=+90:1-3 out.pdf` (`+`/`-` relative; bare = absolute; `:range` optional) |
| split | `qpdf in.pdf --split-pages=N out-%d.pdf` → `out-1-2.pdf …` (zero-padded ranges; without `%d` inserted before `.pdf`) |
| collate | `qpdf --empty --collate --pages odd.pdf even.pdf z-1 -- out.pdf` (interleave scanned fronts/backs) |
| encrypt | `qpdf in.pdf --encrypt --user-password=U --owner-password=O --bits=256 [--print=none --modify=none --extract=n] -- out.pdf` |
| decrypt | `qpdf --decrypt --password-file=pw.txt in.pdf out.pdf` |
| linearise | `qpdf --linearize in.pdf out.pdf`; check `qpdf --check-linearization out.pdf` |
| repair | `qpdf damaged.pdf fixed.pdf` (reconstructs the xref, exit 3 with warnings) |
| check | `qpdf --check in.pdf` |
| page count | `qpdf --show-npages in.pdf` |
| encryption | `qpdf --is-encrypted` (exit 0 yes, 2 no) · `--requires-password` (0 yes, 2 no, 3 wrong/none needed) · `--show-encryption` (`R = 6` = AES-256) |
| JSON | `qpdf --json=2 --json-key=pages in.pdf` · `--json-key=qpdf --json-object=trailer` (v2 has no `objects` key) |
| smaller | `qpdf --object-streams=generate --compress-streams=y --recompress-flate --optimize-images in.pdf out.pdf` |

### Page ranges

`1,3,5-7` · `z` last · `r3` third from last · `5-1` counts down · `1-z,x3-4` excludes
from the preceding group · `:odd` / `:even` suffix picks every other page of the
*resulting* selection. No every-n-th for n > 2.

### Exit codes

`0` ok · `2` errors · `3` warnings (output written, usually fine; `--warning-exit-0` maps
it to 0). poppler tools: `0` ok, `1` open error, `2` output error, `3` permissions,
`99` other.

### Passwords without argv

- input password: `--password-file=FILE` (first line), or `@argfile` with a
  `--password=…` line — needed per file inside `--pages`, e.g.
  `qpdf --empty --pages a.pdf @pw.args 1-z b.pdf -- out.pdf`.
- encryption: put the whole `--encrypt … --` block in a 0600 argfile, one argument per
  line: `qpdf in.pdf @enc.args out.pdf`. Lines are taken literally (spaces are fine).
