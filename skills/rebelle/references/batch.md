# Motion IO batch rendering — CLI, data layers, video

Rebelle Motion IO is the animation build: it takes a JSON events file, runs it frame by
frame, and writes an image (and any other data layer you ask for) per frame. Condensed
from the official [Command Line Arguments](https://www.escapemotions.com/products/rebelle/motionio_doc/reference/command_line_arguments)
and [Import/Export data](https://www.escapemotions.com/products/rebelle/motionio_doc/reference/import_export_data)
pages plus behaviour verified on 8.3.0 / macOS.

## Command line

```bash
"/Applications/Rebelle 8 Motion IO.app/Contents/MacOS/Rebelle 8 Motion IO" \
  -batch-json /abs/path/events.json \
  -batch-out-rgba_canvas "/abs/out/frame_####.png" \
  -no-gui
```

| Argument | Meaning |
|---|---|
| `-batch-json PATH` | the events file; give it an absolute path |
| `-batch-start-frame-number N` | number the first output frame N |
| `-batch-dont-close-app-when-finished` | keep the app up afterwards (7.2.3+) |
| `-input FILE.reb` | open an existing artwork before the JSON runs — the reliable way to fix the canvas size (7.2.6+). Do not also send `NEW_ARTWORK`. |
| `-no-gui` | window still appears, but messages go to stderr instead of blocking dialogs |
| `-batch-out-TYPE PATH` | export a data layer per frame; `####` is the frame-number placeholder |
| `-batch-out-TYPE-options OPTS` | e.g. `tiled_mipmapped,colorconvert:sRGB:linear` |
| `-batch-in-TYPE PATH` | import a data layer per frame |
| `-batch-in-TYPE-function F` | `replace` (default), `add`, `subtract`, `multiply`, `min`, `max`, `average` |
| `-batch-in-TYPE-blending B` | rgba only, see the blending list below |
| `-batch-in-TYPE-multiplier F`, `-scaling F`, `-wait_for_file_timeout_seconds F` | per-layer import tuning |
| `-floating-license-server IP:PORT` | skip discovery, use this licence server |

Progress goes to stdout as `batch frame end: i/n`; `i == n` is the only completion
signal — the app does **not** exit on macOS. `scripts/rebelle-batch.sh` waits for that
line and stops the app.

Paths without an extension get a default one. Valid RGBA extensions: `png`, `exr`,
`tif`, `tiff`; `velocity` needs `exr`. Inside the JSON, prefer forward slashes.

## Data layers

| Layer | Channels / depth | Notes |
|---|---|---|
| `rgba`, `rgba_dry`, `rgba_wet` | 4 × 16-bit, 0..1 | `rgba` = dry + wet composited; export only |
| `rgba_canvas` | 4 × 8-bit (jpg/png/bmp/tif) | paper + all layers + bump shading — what a viewer expects. `scaling` doubles as NanoPixel export when RealShader+NanoPixel are on |
| `bump`, `bump_dry`, `bump_wet` | 1 × 16-bit, usually 0..10000 | impasto; wet bump flows with the water |
| `water` | 1 × 16-bit, 0..~10 | water per pixel |
| `wetness` | 1 × 8-bit, 0 or 1 | dry/wet flag |
| `velocity` | 2 × 16-bit, ~−1..1 | paint flow vector |
| `selection_mask`, `stencil_mask` | 1 × 8-bit grayscale | selection also gates CLEAR_LAYER/WET_LAYER/DRY |
| `reveal_mask` | 4 × 8-bit | brushes take colour from this image instead of the palette; Motion IO only |

`rgba`/`bump` are composites and cannot be imported. 16-bit output only lands in
`.exr`.

Import options: `colorconvert:FROM:TO` (default `linear`→`sRGB` on input, `sRGB`→
`linear` on output). Blending modes for rgba imports: `NORMAL`, `ADDITIVE`,
`SUBTRACTIVE`, `LINEAR_BURN`, `DARKEN`, `LIGHTEN`, `MULTIPLY`, `SCREEN`, `COLOR_DODGE`,
`COLOR_BURN`, `OVERLAY`, `HARD_LIGHT`, `SOFT_LIGHT`, `VIVID_LIGHT`, `LINEAR_LIGHT`,
`PIN_LIGHT`, `HARD_MIX`, `DIFFERENCE`, `EXCLUSION`, `HUE`, `SATURATION`, `COLOR`,
`LUMINOSITY`, `MIXBOX` (the Pigment mode).

`wait_for_file_timeout_seconds` is what makes a feedback loop possible: another program
generates the next frame's input from the previous frame's output while Rebelle waits.

## Frames to video

Exports carry transparency, so flatten before encoding if you want an opaque video:

```bash
# opaque, skipping the setup frames (Doc.first_content_frame)
ffmpeg -y -framerate 24 -start_number 2 -i out/frame_%04d.png \
       -vf "color=white[bg];[bg][0]scale2ref[bg][fg];[bg][fg]overlay,format=yuv420p" \
       -c:v libx264 -crf 18 out.mp4

# keep alpha (for compositing in DaVinci Resolve etc.)
ffmpeg -y -framerate 24 -start_number 2 -i out/frame_%04d.png -c:v qtrle out.mov
```

Motion IO also bundles its own ffmpeg at
`/Applications/Rebelle 8 Motion IO.app/Contents/MacOS/ffmpeg` if the system has none.

## Licensing

The EULA distinguishes painting from animation. Using the animation interfaces (Motion
IO or WebSocket-driven frame output) commercially at scale — the "Production Triggers"
in the agreement — needs a separate licence from Escape Motions; individual artists,
freelancers and small studios are covered without one. WebSocket-driven *animation* for
commercial use is explicitly a separate licence. Live painting, performances and
installations are fine. If a user's project looks like broadcast/streaming production,
point them at support@escapemotions.com rather than guessing.
