---
name: aubio
description: 'Analyse audio with the aubio CLI: BPM and a beat grid with bar numbers, onsets, monophonic pitch and notes (CSV or MIDI), and quiet regions in music, voice or a video soundtrack, with FFmpeg normalising each input. Bundled scripts correct aubio 0.4.9''s sparse beats and wrong tempo and report confidence and half/double-time ambiguity; beats, onsets and pauses export as DaVinci Resolve marker JSON or EDL, Final Cut Pro marker CSV, or plain CSV. Use for "what BPM is this track", "beat times of song.wav as CSV", "a marker on every bar for my Resolve timeline", "find pauses longer than a second in this lecture", "which notes does this melody play, export MIDI", "detect onsets in this drum loop", or any mention of aubio. Not for making sound or click tracks (sonic-pi, supercollider), transcoding or loudness normalising (handbrake, compressor), editing the timeline itself (davinci-resolve, final-cut-pro; when its markers must come from the music, run this first), notation (musescore), or speech-to-text.'
summary: "analyse audio with the aubio CLI — corrected BPM and beat grids, onsets, pitch and note extraction to CSV or MIDI, silence detection, exported as Resolve marker JSON/EDL or FCPXML marker CSV"
category: audio
compatibility: "Built for aubio 0.4.9 (Homebrew, Python 3.14, numpy 2.5) and FFmpeg 9.0.2 on macOS 27 (arm64)."
risk: low
tags:
    - aubio
    - bpm
    - beat-detection
    - onset
    - pitch
    - silence
    - audio-analysis
    - markers
metadata:
  version: "1.0.1"
  author: "Tamás Jablonkai"
---

# aubio audio analysis

aubio (free, GPL-3.0) detects onsets, beats, tempo, pitch, notes and silence in audio
files from the command line. Everything here is headless and one-shot: file in,
numbers out. There is no app or session to manage. The source file is only read and
never changed. Verified against **aubio 0.4.9** (Homebrew) and **FFmpeg 9.0.2** on
macOS 27 (arm64).

Use the bundled scripts rather than raw `aubio` calls. In 0.4.9 the raw CLI is wrong
in ways that look plausible:

- `aubio beat` drops most beats. It found 14 of 60 on a clean click track.
- `aubio tempo` takes the median of those gaps, so it can report 67 bpm for a 120 bpm
  track.
- `aubio quiet`'s default −70 dB threshold misses every pause that sits above a room
  noise floor.
- `aubio notes` starts every note 30–60 ms late.

The scripts fix each of these and print the evidence as JSON.

| File | What it is |
|------|-----------|
| [scripts/aubio_tool.py](scripts/aubio_tool.py) | `prep`, `beats`, `onsets`, `quiet`, `notes`, `pitch` → CSV, plus a JSON summary on stdout |
| [scripts/export_markers.py](scripts/export_markers.py) | Turns any of those CSVs into Resolve JSON or EDL, FCP marker CSV, or plain CSV |
| [references/cli-reference.md](references/cli-reference.md) | Every raw `aubio` subcommand: options, defaults, output format |
| [references/recipes.md](references/recipes.md) | Cut-to-music in Resolve and FCP, trimming the pauses out of a talk, melody to MIDI, slicing a loop |
| [references/gotchas.md](references/gotchas.md) | **Read before trusting a raw aubio number** or debugging an odd result |

Both scripts are stdlib Python 3.9+. They need `aubio`, `ffmpeg` and `ffprobe` on PATH
(`brew install aubio ffmpeg`).

## Workflow

1. **Pass the file as it is.** Each subcommand decodes it with FFmpeg to 44.1 kHz mono
   WAV in a temp dir first, so mp3, m4a, flac and video files (mp4, mov) all work.
   Don't use aubio's `-r` or its own decoding: both change the results (see gotchas).
2. **Run the subcommand** for the task, with `--out` set to the CSV the user wants.
3. **Read the JSON summary** before answering. It carries the confidence values and
   `warnings`; pass those on to the user rather than reporting bare numbers.
4. **Export** to the editor format the user needs, if any.

```bash
S=scripts   # relative to this skill's directory
python3 $S/aubio_tool.py beats song.mp3 --out beats.csv            # BPM + beat grid
python3 $S/aubio_tool.py quiet talk.m4a --min-duration 1 --out pauses.csv
python3 $S/aubio_tool.py notes melody.wav --out notes.csv --midi melody.mid
python3 $S/aubio_tool.py onsets loop.wav --out onsets.csv
python3 $S/aubio_tool.py pitch vocal.wav --unit midi --out pitch.csv
python3 $S/export_markers.py beats.csv --format resolve-json --select bars --out bars.json
```

Exit codes: 0 means ok. 1 means nothing usable was found, such as no onsets or no
notes, and the reason is printed as JSON on stderr. 2 means a tool or usage error.

## Beats and tempo (`beats`)

The script detects onsets, weights each one by its loudness, and searches 70–180 bpm
for the pulse the onsets agree on. It then fits a beat grid to the onsets by least
squares and numbers bars from the strongest beat class. CSV columns:
`index,time_s,bar,beat,matched`. `matched` is 1 when a real onset lies within 30 ms of
that grid beat.

Summary fields to read and report:

- `bpm`: two decimals; also `bpm_rounded`. `aubio_tempo_raw` is aubio's own figure,
  kept only for comparison. Don't report it as the answer.
- `confidence`: the share of grid beats backed by an onset. Above ~0.8 the grid is
  solid. Below 0.6, say the result is unreliable.
- `mode`: `grid` (steady tempo, the default fit) or `follow` (drifting tempo, picked
  automatically when it explains clearly more beats). For a live recording that speeds
  up, report `bpm_start_end` as well as the average.
- `alternatives`: how well the half-time and double-time readings fit.
- `warnings`: half-time or double-time is plausible, the downbeat is a guess, or the
  fit is poor. When `uncertain` is true, state the caveat in your answer.

Tempo octave (90 vs 180) is a musical judgement, not something the data can settle.
When the user knows the tempo or genre, pass `--bpm-hint 174`, which searches ±8 %
around it, or `--bpm-range LO HI`. Bar numbering follows `--meter` (default 4). When
the downbeat warning appears and bars matter, ask for or pass `--first-downbeat SEC`.

## Quiet regions (`quiet`)

`--silence auto` (the default) measures the file's noise floor and loud level with
FFmpeg and sets the threshold between them. The summary shows `noise_floor_db`,
`loud_level_db` and the `threshold_db` it used. `--min-duration` (default 1 s) drops
shorter pauses and counts them in `shorter_regions_skipped`. `--pad 0.15` shrinks
every region on both sides, so a cut keeps a breath. `--keep-csv keep.csv` also writes
the non-quiet segments, which is what a trim needs (see recipes). Pass a fixed level
(`--silence -45`) only when the user names one, or when auto warns about low contrast.

## Notes and pitch (`notes`, `pitch`)

Both are **monophonic**: one voice or instrument line at a time. Chords and full mixes
give garbage, so say so rather than presenting the output.

- `notes` CSV: `index,midi,name,start_s,end_s,duration_s,freq_hz`. Starts are snapped
  to the onset detector, which is accurate to a few ms. `--midi out.mid` writes a
  type-0 MIDI file (`--midi-bpm` sets its tempo; times stay in seconds).
- `pitch` drops unvoiced frames (aubio writes 0 Hz for those) and anything outside
  `--min-hz/--max-hz`. `--unit midi` gives fractional MIDI numbers, useful for
  intonation. The summary has the median note and the 5–95 % range.

## Markers for editors (`export_markers.py`)

The input is any CSV from `aubio_tool.py`; the script detects its kind from the
columns.

| `--format` | Goes to | How the user or agent loads it |
|-----------|---------|-------------------------------|
| `resolve-json` | davinci-resolve skill | `for m in json.load(f): R.marker(m["seconds"], m["name"], m["color"], m["note"], m["duration"])` |
| `resolve-edl` | DaVinci Resolve, no scripting | Timeline ▸ Import ▸ Timeline Markers from EDL (`--fps`, `--tc-start` must match the timeline) |
| `fcp-csv` | final-cut-pro skill | `fcpxml-edit.py project.fcpxml --markers markers.csv --out new.fcpxml` |
| `csv` | anything else | `seconds,name,duration_s` |

- `--select bars` puts one marker per bar. `every:2` puts one on every other beat.
  The default `all` puts one on every beat, with downbeats in `--downbeat-color`.
- `--offset SEC` applies when the music doesn't start at the timeline start. For
  example, a song placed at 00:00:10:00 needs `--offset 10`.
- Markers that round to the same frame are merged and counted in `merged_same_frame`,
  because Resolve refuses a second marker on a frame.
- Quiet regions and notes become markers with a duration.

## Checking the result

Before reporting, check each of these:

- The CSV row count matches the summary (`beats`, `count`).
- For beats, the spacing between rows matches 60/`bpm`.
- `confidence` and `warnings` appear in your answer.
- For markers, the export summary's `markers` count is what the user asked for. For
  example, a 3-minute song at 120 bpm in 4/4 has about 90 bars.
- When the user gave a known value (a BPM, a pause they remember), compare against it
  and say whether it matches.
