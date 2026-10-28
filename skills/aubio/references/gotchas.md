# aubio gotchas (0.4.9)

These were measured on synthetic audio with known ground truth on this machine. They
are why the skill goes through `scripts/aubio_tool.py` instead of raw aubio output.

## Beat and tempo
- **`aubio beat` drops beats.** On a clean 30 s click track at 120 bpm (60 beats) it
  printed 14 beats, all on the grid, with gaps of up to 8 s. The Python API shows the
  same sparse callbacks, while its `get_bpm()` is close (121.6). This is the tracker's
  output, not a parsing problem.
- **`aubio tempo` is wrong as a result.** It is the median gap of those sparse beats:
  67.23 bpm on the click track and 114.8 bpm on a 120 bpm drum groove. It doesn't
  always say `(uncertain)` when it is wrong.
- Onsets are reliable: 60 of 60 at ±5 ms on the same click track. So the script
  derives the tempo and grid from onsets.
- **Off-beat hi-hats cancel the beat.** With unweighted onsets, eighth-note hats sit
  at phase π of the beat pulse and pull the estimate off (122.8 instead of 120). The
  script weights onsets by peak level and also scores the subdivision.
- **Tempo octave.** A strict eighth-note pattern at 100 bpm fits 100 and 200 equally
  well. The script stays inside `--bpm-range` (70–180) and warns when the off-beats are
  as strong as the beats. Only the user or the genre can decide which one is right.
- **Downbeats** come from accent strength. With flat accents (a metronome, constant
  hats), the bar start is a guess, and the summary says so.

## Inputs and resampling
- **`-r` breaks tempo.** At `-r 22050` the click track reported 28.67 bpm. The script
  decodes to 44.1 kHz with FFmpeg and never passes `-r`.
- **Decoded compressed audio drifts.** aubio reads mp3, m4a and mp4 through its libav
  build, but the same click track as AAC gave 81.7 bpm against 67.2 bpm from the WAV.
  Always prep first (`aubio_tool.py` does this automatically) for reproducible numbers.
- Multichannel files are downmixed to mono in prep. To analyse one channel (such as a
  lavalier mic on the left), prep it yourself with `ffmpeg -af "pan=mono|c0=c0"` and
  pass that WAV.

## Quiet
- **The default `-s -70` is too low for real recordings.** With a −56 dBFS room-noise
  floor, `aubio quiet` reports no quiet region at all. At −60 dB or higher, the
  boundaries come out within 6 ms. `--silence auto` sets the threshold from the
  measured floor.
- Output is transitions only, and the last region has no end time. The script closes
  it at the file duration.
- There is no minimum-length filter, so a 0.2 s gap between words is reported like a
  3 s pause. The script's `--min-duration` handles that.
- Digital silence (exact zeros) measures as −inf. The script clamps the floor to
  −80 dB so that auto still works.

## Notes and pitch
- **Note starts are late** by 30–60 ms, because `notes` waits for a stable pitch.
  Snapping to the onset detector brings them to within ±5 ms. Ends are within ~10 ms.
- `notes` prints a lone timestamp on the first and last line.
- Repeated notes are separated only when there is an onset (re-attack) between them.
  A legato repeat with no level dip merges into one long note.
- `pitch` prints 0 for unvoiced frames. `yinfft` (the default) is the most robust;
  octave errors show up as isolated ±12 jumps in `--unit midi`.
- Both are monophonic. On chords or a full mix, the output follows whichever partial
  dominates and means nothing musically.

## Time resolution
One hop: 256/44100 ≈ 5.8 ms for onset, pitch, notes and quiet, and 11.6 ms for beat.
Marker exports round to the frame grid (40 ms at 25 fps), which is coarser than
anything above.
