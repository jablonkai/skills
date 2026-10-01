# Recipes

`NK=<skill>/scripts/nk.py`. Every recipe ends with a render and a verify. The frame
counts printed by `nk.py render` are already checked against the disk, and `verify` is
for a second look or for files rendered elsewhere.

## 1. FG over BG with a grade → EXR

```bash
python3 $NK template fg_over_bg -o shots/sh010/comp_v001.nk \
  --plate FG=plates/sh010/fg.1001.png --plate BG=plates/sh010/bg.####.exr \
  --set OUT=renders/sh010/comp_v001/comp.####.exr \
  --set GRADE_GAIN=0.8 --set GRADE_GAMMA=1.1
python3 $NK render shots/sh010/comp_v001.nk
```

- `--plate` accepts `####`, `%04d` or any one frame of the sequence, and detects
  first/last/size. The range and format follow BG.
- Grade knobs: `GRADE_GAIN` (white), `GRADE_LIFT` (black), `GRADE_GAMMA`,
  `GRADE_MULTIPLY`, `GRADE_OFFSET` (add), `GRADE_BLACKPOINT`, `GRADE_WHITEPOINT`. For a
  colour cast, use a quoted 4-vector: `--set "GRADE_GAIN={1.1 1.0 0.9 1}"`.
- Move or scale the FG with `FG_X`, `FG_Y` and `FG_SCALE`. A premultiplied EXR FG needs
  `--set FG_PREMULTIPLIED=true`.
- Need more than the template offers (a second grade, a blur, an edge matte)? Copy the
  generated `.nk` and edit the text. Wiring rules are in `nk-format.md`.

## 2. Batch render a folder

```bash
python3 $NK batch shots/ -r                  # every .nk/.nknc, sorted, one Nuke at a time
python3 $NK batch shots/ -r --json > batch_report.json
```

- Each script renders all its enabled Writes over its own Root range, or its Write
  `use_limit` range. `-F` overrides the range for all of them.
- A failing Write (for example an h264 MOV under NC) is reported by script and Write
  name, and the batch continues. The exit code is 1 if anything failed.
- To find problems without rendering: `for f in shots/**/*.nk; do python3 $NK check "$f"; done`.

## 3. Slate + burn-in template

```bash
python3 $NK template slate_burnin -o review/sh020_v003.nk \
  --plate PLATE=plates/sh020/sh020.####.exr \
  --set SHOT=sh020 --set VERSION=v003 --set PROJECT="Night Run" \
  --set ARTIST=tamas --set "NOTE=temp sky, first grade" \
  --set OUT=review/sh020_v003/sh020.####.png
python3 $NK render review/sh020_v003.nk
```

- The output is one slate frame at `PLATE_FIRST-1` (a text card plus a thumbnail of the
  mid frame), then each plate frame with burn-ins:
  - top band: shot, version, date
  - bottom band: project and 4-digit frame number
- For a ProRes review movie instead of PNGs: `--set OUT_TYPE=mov --set OUT=review/sh020_v003.mov`.
  The MOV codec defaults to ProRes 422 HQ. h264 is not available under NC.
- To make a reusable per-show template, copy `assets/templates/slate_burnin.nk`, keep the
  `@@PLACEHOLDERS@@`, and pass the copy's path instead of the name.
  `nk.py template --list` documents the placeholders of the bundled ones.

## 4. Swap the plate in an existing script

Without editing the file, override at render time:

```bash
python3 $NK render comp_v003.nk \
  --set BG.file=/plates/sh030/bg.####.exr --set BG.first=1001 --set BG.last=1060 \
  --set BG.origfirst=1001 --set BG.origlast=1060 \
  --set root.first_frame=1001 --set root.last_frame=1060 \
  --set Write_EXR.file=/renders/sh030/comp.####.exr
```

This works for a plate of the **same size**. Scripts generated from the templates bake the
plate's scale factor (`scale {{1920/3840}}`) and a Crop to format. A larger swapped-in
plate is therefore silently **cropped**, not scaled: a 4K plate in a 1080 template keeps
only its bottom-left quarter. When the size changes, re-run `nk.py template` with the new
`--plate`.

To keep a new script, `sed` the `file` line in the `.nk` text, or turn the script into a
template by replacing the paths with `@@PLATE@@` and friends.

## 5. Roto matte

Put `Roto { inputs 0  output alpha  name Matte }` in the `.nk`, wire it as a mask
(`inputs 1+1` on a Grade, or as A in a `Merge2 operation mask`), and add the shapes with
a hook. Example in `python-api.md`:

```bash
python3 $NK render comp.nk --py shapes.py
```

## 6. Plates over 1920×1080

The NC cap applies to what a Write receives.

- The templates already scale via `@@KEY_FIT_W@@`/`@@KEY_FIT_H@@`.
- In hand-written scripts, put `Reformat { type scale  scale {{1920/3840}} }` (or
  `type "to format"` with a ≤1080p `format`) before every Write.
- Add `Crop { box {0 0 1920 1080}  reformat true  crop false }` if a transform could push
  the bbox outside the frame.

## 7. Checking pixels

The frame count is checked by `nk.py`. For "is the grade/comp right", sample pixels with
ffmpeg:

```bash
ffmpeg -v error -i comp.1010.exr -vf "crop=8:8:100:100,format=gbrpf32le" -f rawvideo - | \
  python3 -c "import sys,struct; d=sys.stdin.buffer.read(); v=struct.unpack('<%df'%(len(d)//4), d); n=len(v)//3; print([sum(v[i*n:(i+1)*n])/n for i in range(3)])"
```

- The planes come out in G, B, R order for `gbrpf32le`.
- To eyeball a frame, convert it to a PNG contact sheet:
  `ffmpeg -i out.%04d.png -vf "select=not(mod(n\,12)),scale=480:-1,tile=4x2" -frames:v 1 sheet.png`.
