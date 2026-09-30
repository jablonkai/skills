# Time in FCPXML

Every time is a rational number of seconds: `"8s"`, `"137/25s"`, `"180180/30000s"`.
Use `scripts/fcptime.py` (Fraction-based, `--selftest` covers the values below). Never
do the math in floats.

## Frame durations

| Rate | frameDuration (as FCP writes it) | Timecode counts at | Drop frame |
|---|---|---|---|
| 23.976 | `1001/24000s` | 24 | no |
| 24 | `100/2400s` | 24 | no |
| 25 | `100/2500s` | 25 | no |
| 29.97 | `1001/30000s` | 30 | yes (`;`) |
| 30 | `100/3000s` | 30 | no |
| 50 | `100/5000s` | 50 | no |
| 59.94 | `1001/60000s` | 60 | yes |
| 60 | `100/6000s` | 60 | no |

FCP writes integer-rate times reduced (`137/25s`, `1/25s`), and NTSC times on the
1001 timescale (`180180/30000s` = 180 frames at 29.97). Both forms parse the same way.
The builder writes them the way FCP does.

## Timecode

- Timecode counts frames at the rounded rate: at 23.976, `00:00:01:00` is 24 frames,
  which is **1.001 s**.
- Drop frame (29.97/59.94): frame numbers 00 and 01 (00–03 at 59.94) are skipped at the
  start of every minute except every tenth, so `00:01:00;00` does not exist and
  `00:01:00;02` is frame 1800. One hour DF is 107 892 frames.
- A sequence's timecode starts at `tcStart` (`3600s` = 01:00:00:00). Primary-spine
  offsets are in that same space, so the first item's `offset` equals `tcStart`.
- A clip's source timecode is its source time: `asset start` is the media's embedded
  timecode (0 without one), and the clip's `start` is an absolute source time.

```bash
python3 scripts/fcptime.py tc 2 --rate 25 --start 01:00:00:00    # 01:00:02:00
python3 scripts/fcptime.py tc "01:00:02;00" --rate 29.97 --to-time --start "01:00:00;00"
python3 scripts/fcptime.py time 450 --rate 29.97                 # 450450/30000s
```

## The grid rule

FCP conforms everything in a project to the **sequence** frame grid:

- `offset` and `duration` of every item, and
- the `start` of every clip. This applies even when the source has another rate, and it
  is measured in *absolute* asset time. A 29.97 clip with embedded timecode
  00:59:59;00 (asset start 107969862/30000 s) in a 25p project needs a start such as
  `89987/25s`, not asset start + 12/25 s.

Off-grid values are not rejected. FCP floors the start and **appends a one-frame copy
of the clip after the last item**, so the project comes out one frame longer. Verified
twice on 12.4. `fcpxml-verify.py` reports this as `grid`. The builder snaps (a start
rounds up to stay inside the media) and lists every change under `"adjusted"`.

A cross dissolve centred on a cut needs an even number of frames (half on each side).
The builder rounds an odd request up, e.g. 1 s at 25p becomes 26 frames.

## Speed changes

`<timeMap>` maps clip time to source time. FCP normalises it to span the asset. For a
half-speed clip it writes `timept time="16s" value="8s"` over an 8 s asset. When a
clip is retimed, source out ≠ source in + duration. `fcpxml-read.py` flags these
clips `retimed` and doesn't compute a source out for them.
