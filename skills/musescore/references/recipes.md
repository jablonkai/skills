# Recipes

`SK` is the skill directory. Every recipe ends with a check, because a run that worked is
not a score that's right.

## Lead sheet → PDF + MP3

```json
{"title": "Blue Hour", "key": "Bb", "time": "4/4", "tempo": 120,
 "parts": [{"name": "Lead", "instrument": "voice", "measures": [
  {"notes": "D5/q F5/q G5/h", "chords": "Bbmaj7"},
  {"notes": "F5/q. Eb5/e D5/h", "chords": "Cm7 F7"},
  {"notes": "Bb4/h~ Bb4/e C5/e D5/q", "chords": "Bbmaj7 G7"},
  {"notes": "C5/w", "chords": "Cm7 F7"},
  {"notes": "D5/q F5/q Bb5/h", "chords": "Bbmaj7", "double": true},
  {"notes": "A5/q G5/q F5/h", "chords": "Ebmaj7 Ab7"},
  {"notes": "G5/e3 F5/e3 Eb5/e3 D5/q C5/h", "chords": "Dm7 G7"},
  {"notes": "Bb4/w", "chords": "Cm7 F7"}]}]}
```

```bash
python3 $SK/scripts/musicxml-build.py blue.json blue.musicxml
$SK/scripts/mscore-run.sh -o blue.mscz blue.musicxml
$SK/scripts/mscore-run.sh -o blue.pdf blue.mscz
$SK/scripts/mscore-run.sh -o blue.mp3 blue.mscz
$SK/scripts/mscore-run.sh -T 20 -o look.png blue.mscz      # then Read look-1.png
python3 $SK/scripts/score-check.py --xsd blue.musicxml blue.pdf blue.mp3
```

Expect measures 8, keysig −2, timesig 4/4, tempo 120, has_harmonies, and harmony count = the number of
symbols. The MP3 should run 8 × 4 × 60/120 = 16 s plus ~3 s of tail, and `silent` should be false.

For a lead sheet with lyrics, put `|syllable` on each note. For a 2-chorus form use
`repeat_start`/`repeat_end`, and pass `--unroll-repeats` when exporting audio.

## Folder of MIDI files → engraved PDFs

```bash
$SK/scripts/batch-convert.py midi/ pdf/ --to pdf --ext mid,midi
find pdf -name '*.pdf' -print0 | xargs -0 python3 $SK/scripts/score-check.py --no-meta | grep -E '"(file|pages|ok)"'
```

The output tree mirrors `midi/`. Rerunning skips files that are already done (`--overwrite` to redo).
Spot-check one PNG (`mscore-run.sh -o look.png midi/some.mid`): MIDI import quantises
and splits voices by itself, and that's where a batch quietly goes wrong. To add audio
or MusicXML in the same pass: `--to pdf,musicxml,mp3`.

## Transpose a score and export parts

```bash
$SK/scripts/transpose-parts.py quartet.mscz out/ --to-key D            # C → D, closest direction
$SK/scripts/transpose-parts.py quartet.mscz out/ --interval M2 --direction up --formats pdf,musicxml
python3 $SK/scripts/score-check.py out/quartet-up-M2.mscz out/*.pdf
```

Check that the summary's `concert_key_after.keysig` equals the target, that there's one PDF per
entry in `parts`, and that each has ≥ 1 page. For a pitch check, parse the exported MusicXML
(`score-check.py out/x.musicxml` → `first_pitches`). Transposing parts show their
written pitch there. Compare against the source's `first_pitches` with the same part's
transposition in mind.

Parts only, with no transposition: `transpose-parts.py score.mscz parts/`.

## Ensemble arrangement from scratch

Write one spec with several parts at concert pitch. The builder handles clefs and transposition:

```json
{"title": "Chorale", "key": "G", "time": "3/4", "tempo": 72, "parts": [
 {"name": "Flute", "measures": ["D5/h. ", "B4/h A4/q", "G4/h."]},
 {"name": "Clarinet in Bb", "measures": ["B4/h. ", "G4/h F#4/q", "D4/h."]},
 {"name": "Cello", "measures": ["G2/h. ", "E3/h D3/q", "G2/h."]}]}
```

Then render as in the lead-sheet recipe and transpose or extract parts as above. The
clarinet part comes out written in A major, which is correct for a Bb instrument in G.

## Convert between notation formats

```bash
$SK/scripts/mscore-run.sh -o song.musicxml song.mscz     # for Sibelius/Finale/Dorico
$SK/scripts/mscore-run.sh -o song.mscz song.musicxml     # into MuseScore
$SK/scripts/batch-convert.py library/ export/ --to musicxml --ext mscz
```

## Edit an existing score's XML

For small edits like a title, a tempo or a single note, round-trip through MusicXML:

```bash
$SK/scripts/mscore-run.sh -o work.musicxml song.mscz
# edit work.musicxml (keep the element order; validate with score-check.py --xsd)
$SK/scripts/mscore-run.sh -o song-edited.mscz work.musicxml
```

The round trip keeps notes, chords, lyrics, instruments and most layout. MuseScore-only
properties (some style settings, playback tweaks) may reset. When those matter,
edit `<name>.mscx` inside the `.mscz` zip directly instead.
