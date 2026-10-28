# Recipes

`S` is this skill's `scripts/` directory.

## Cut to music in DaVinci Resolve
```bash
python3 $S/aubio_tool.py beats music.wav --out beats.csv
python3 $S/export_markers.py beats.csv --format resolve-json --select bars --out bars.json \
    --fps 25 --offset 0          # offset = where the music clip starts on the timeline, in s
```
Then use the davinci-resolve skill's helper. Pass `--fps` as the timeline frame rate,
so that same-frame merging matches Resolve:
```python
import json
for m in json.load(open("bars.json")):
    R.marker(m["seconds"], m["name"], m["color"], m["note"], m["duration"])
```
Without scripting, use `--format resolve-edl --fps 25 --tc-start 01:00:00:00`, then
Timeline ▸ Import ▸ Timeline Markers from EDL. The `--tc-start` value must equal the
timeline's start timecode.

For a faster cut, use `--select all`: downbeats come out red and the other beats
blue. For every second beat, use `--select every:2`.

## Cut to music in Final Cut Pro
```bash
python3 $S/export_markers.py beats.csv --format fcp-csv --select bars --out bars.fcp.csv
python3 <final-cut-pro>/scripts/fcpxml-edit.py project.fcpxml --markers bars.fcp.csv --out project-beats.fcpxml
```
`fcpxml-edit.py` snaps each marker to the frame grid and attaches it to the
primary-storyline clip under that time. Verified: 15 bar markers on a 30 s clip came
out DTD-valid. When building a new project with `fcpxml-build.py`, the same rows can
go into the spec's top-level `"markers": [{"at": sec, "name": …}]`.

## Trim the pauses out of a talk
```bash
python3 $S/aubio_tool.py quiet talk.mp4 --min-duration 1.0 --pad 0.15 \
    --out pauses.csv --keep-csv keep.csv
```
`keep.csv` lists the segments to keep. Turn them into one FFmpeg filter that keeps
audio and video in sync:
```bash
python3 - <<'EOF' > keep.filter
import csv
rows = list(csv.DictReader(open("keep.csv")))
sel = "+".join(f"between(t,{r['start_s']},{r['end_s']})" for r in rows)
print(f"[0:v]select='{sel}',setpts=N/FRAME_RATE/TB[v];[0:a]aselect='{sel}',asetpts=N/SR/TB[a]")
EOF
ffmpeg -i talk.mp4 -/filter_complex keep.filter -map "[v]" -map "[a]" talk-trimmed.mp4
```
`-/filter_complex FILE` reads the graph from a file; FFmpeg 9 removed the old
`-filter_complex_script`. Verified: 20 s → 16.92 s, audio and video equal length. For
audio only, drop the `[0:v]` chain and `-map "[v]"`.

For an edit the user will refine, export the pauses as markers instead:
`export_markers.py pauses.csv --format resolve-edl --color Red` gives one red marker per
pause, with its duration.

Report the threshold that was used and `total_quiet_s` / `kept_s`, so the user can
judge whether the cut is too aggressive.

## Melody to notes / MIDI
```bash
python3 $S/aubio_tool.py notes flute.wav --out notes.csv --midi flute.mid --midi-bpm 90
```
Give the sequence from the summary (`"sequence": ["C4", "D4", …]`) in the answer. The
musescore skill can engrave the MIDI file. Quantising to a meter is the user's call,
since note times stay in real seconds.

## Pitch / intonation
```bash
python3 $S/aubio_tool.py pitch vocal.wav --unit midi --out pitch.csv --min-hz 70 --max-hz 1100
```
The fractional part of each MIDI value is the deviation in semitones (0.1 = 10 cents).
Narrow `--min-hz/--max-hz` to the voice range to cut octave errors.

## Onsets and slicing a loop
```bash
python3 $S/aubio_tool.py onsets loop.wav --method hfc --minioi 0.05 --out onsets.csv
aubio cut -i loop.wav -m hfc -o slices/ --create-first     # one WAV per hit
```
The `strength` column (peak level after the onset) separates kicks and snares from
ghost notes. Filter the CSV on it before exporting markers.

## A known tempo, a tricky genre
- Drum & bass or footwork: `--bpm-hint 174` or `--bpm-range 150 190`.
- Ballad that reads as double time: `--bpm-range 50 100`.
- Waltz: `--meter 3`. 6/8: usually `--meter 2` at the dotted-quarter pulse, or
  `--meter 6`, depending on how the user counts.
