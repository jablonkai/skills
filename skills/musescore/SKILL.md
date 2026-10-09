---
name: musescore
description: 'Write, engrave, convert and render sheet music with MuseScore Studio 4 headless (the mscore CLI) and MusicXML — lead sheets with chord symbols and lyrics, piano and ensemble arrangements with correct transposing parts; export PDF, PNG, SVG, MP3/WAV, MIDI, MusicXML and .mscz; batch-convert whole folders (MIDI to PDF scores, .mscz to MusicXML, scores to audio); transpose to a new key or interval and extract individual part PDFs; read score metadata. Use whenever the user wants sheet music, a score, notation, a lead sheet or jazz/Real Book-style chart, parts for players, or says "MuseScore", "MusicXML", "engrave", "convert these MIDI files to PDF scores", "transpose this score to Bb", "export the parts", "render the score to MP3" — even without naming MuseScore. Hungarian: "kotta", "írj kottát", "transzponáld", "szólamkivonat". Not for live-coded, generative or synthesized audio (use sonic-pi), audio or video transcoding (handbrake, compressor), DAW mixing, or plain-text tabs and chord charts.'
summary: "write, engrave and convert sheet music headless with MuseScore Studio 4 — MusicXML lead sheets and arrangements from a compact spec, PDF/PNG/SVG/MP3/MIDI export, folder batch conversion, transposition and part extraction, score-meta verified output"
category: audio
risk: low
tags:
    - musescore
    - musicxml
    - sheet-music
    - notation
    - transpose
metadata:
  version: "1.0.0"
---

# MuseScore headless engraving

MuseScore Studio 4's `mscore` binary imports MusicXML, MIDI, Guitar Pro and
its own `.mscz`/`.mscx`, and exports PDF, PNG, SVG, MP3/WAV/OGG/FLAC, MIDI,
MusicXML and `.mscz`, all **headless**: no window, no bridge, nothing left
running. So every task has the same shape: get a score file, run `mscore`
through a script, then verify the files.

```
scripts/musicxml-build.py  compact JSON spec -> MusicXML 4.0 (durations checked, transposing parts handled)
scripts/mscore-run.sh      one mscore call with a timeout; success = output file written, not rc
scripts/batch-convert.py   folder -> formats in one launch per output kind; OK/FAIL/SKIP + SUMMARY
scripts/transpose-parts.py transpose by key/interval -> .mscz + full score + one PDF per part
scripts/score-check.py     the oracle: --score-meta, MusicXML parse + XSD, PDF pages, audio length/silence
```

`SK=<this skill's directory>`. Run from the user's working directory.

## Setup check (once)

```bash
$SK/scripts/mscore-run.sh --which      # finds /Applications/MuseScore 4.app/... or $MSCORE_BIN
```

If it's missing, install MuseScore Studio 4 (Muse Hub or musescore.org, or
`brew install --cask musescore`). MP3 export works out of the box with the
bundled MS Basic soundfont, and MuseSounds is optional. `pdfinfo` (poppler), `ffprobe`/`ffmpeg`
and `xmllint` sharpen the checks, and `score-check.py` degrades gracefully without them.

**Exit codes lie.** mscore 4.x often aborts (rc 134, or a segfault) at
shutdown *after* writing every output, and it prints a crash-reporter wall
to stderr. And some failures write nothing at all (`-P`, an unsupported
format). Never judge a run by `$?`
from a bare `mscore` call. The scripts judge by the files on disk, so use them
or check the outputs yourself.

## Writing music: spec → MusicXML

Hand-written MusicXML goes wrong in quiet ways: a measure that's one eighth
short, a clarinet part written at concert pitch, a chord kind MuseScore
renders oddly. So write a compact JSON spec and let the builder emit the XML:

```json
{"title": "Evening Walk", "key": "F", "time": "4/4", "tempo": 96, "bars_per_line": 4,
 "parts": [{"name": "Melody", "instrument": "voice", "measures": [
   {"notes": "A4/q|Eve- G4/e|ning F4/e|walk A4/q C5/q", "chords": "F"},
   {"notes": "D5/h. r/q", "chords": "Gm7 C7@3"},
   "F5/q E5/q D5/q C5/q",
   {"notes": "F5/w", "chords": "F"}]}]}
```

```bash
python3 $SK/scripts/musicxml-build.py spec.json score.musicxml
```

- **Notes:** `PITCH/DUR`, where middle C is `C4`, `Bb3`, `F#5`, and `r` is a rest; `[C4,E4,G4]/h` is a chord.
  DUR is `w h q e s t`, with `.` for dotted, `3` for triplets (`C5/e3 D5/e3 E5/e3`), `~` to tie into the
  next note, and `|syl` for a lyric (`|Hel-` continues the word).
- **Chords:** `"chords": "F Dm7 Bb/D C7b9@3"`. Symbols without `@beat` are spread evenly
  across the bar, so `"F C7"` gives one per half bar.
- **Per measure:** `pickup`, `key`, `time`, `repeat_start`, `repeat_end`, `double`, `text`,
  `rehearsal`, `break` / `page_break`. Piano gets two staves, with `notes2` for the left hand.
- **Layout:** `"bars_per_line": 4` forces even systems. Use it for lead sheets: MuseScore's own
  spacing packs 5–6 bars a line and squeezes lyrics together.
- **Credits:** set `composer`/`lyricist` only to names the user gave. Never put in a
  placeholder or a guessed name.
- **Instruments:** name them (`flute`, `clarinet`, `alto sax`, `trumpet`, `horn`, `cello`,
  `guitar`, `double bass`, `piano`…). Write notes at **concert pitch**: the builder
  writes transposing parts at their written pitch and key, and octave instruments an
  octave up.
- A bar whose durations don't add up to the time signature is an **error with the
  measure number**. Fix the spec instead of padding it.

The full spec format and instrument table are in [references/musicxml.md](references/musicxml.md).
Hand-write or edit raw MusicXML (the element order rules, harmony
kinds, and what MuseScore ignores) only for things the builder can't express:
multiple voices on one staff, dynamics, articulations, slurs, drum kits. See
the same file for that too.

## Rendering and converting

```bash
$SK/scripts/mscore-run.sh -o score.pdf score.musicxml        # also .png .svg .mp3 .mid .musicxml .mscz
$SK/scripts/mscore-run.sh -o score.mscz score.musicxml       # keep a .mscz for further edits/transposes
```

PNG/SVG write one file per page: `-o page.png` → `page-1.png`, `page-2.png`…
Add `-T 20` to trim to the music and `-r 200` for the DPI. Audio takes `-b 192` (kbps) and
`--sound-profile "MuseScore Basic"`. All flags are in
[references/cli-reference.md](references/cli-reference.md).

**Folders:**

```bash
$SK/scripts/batch-convert.py midi_in/ scores_out/ --to pdf[,mp3,musicxml] [--ext mid,midi] [--flat]
```

The batch is recursive, mirrors sub-folders, handles spaces in names and only reads its inputs. Outputs that already exist are
skipped unless you pass `--overwrite`. It makes one launch for the score/image formats and one for audio: a job
entry that mixes the two crashes mscore 4.7. Any output missing after the job is retried
once on its own. Don't loop `mscore` per file in the shell.

## Transposing and parts

```bash
$SK/scripts/transpose-parts.py song.mscz out/ --to-key D            # or --interval M2 [--direction down]
$SK/scripts/transpose-parts.py song.mscz out/ --to-key Bb --formats pdf,musicxml --combined
$SK/scripts/transpose-parts.py song.mscz out/                       # no transposition: just score + parts
```

This writes `out/<name>-in-D.mscz`, the full-score files, and `out/<name>-in-D-<Part>.pdf`
per part. Each part is in its written key: a Bb clarinet part of a score in D shows E.
`--to-key` names the **concert** key and goes the *closest* way. When the user says "up" or
"down" (or the octave matters, e.g. for voices), use `--interval M2 --direction up` or pass
`--direction` explicitly. The JSON summary reports the resulting key from `--score-meta`. `--interval` takes M2, m3, P4, P5, TT, m7… (`--help-intervals`).
mscore's own `-P` (score + parts) writes nothing in 4.7. The script uses
`--score-parts-pdf` instead.

## Verify — every time

A file that exists isn't proof the music is right. After each job:

1. `python3 $SK/scripts/score-check.py [--xsd] out/*.pdf out/*.mp3 score.musicxml` → JSON
   per file: PDF pages; audio duration and peak dB (`silent: true` means the soundfont failed);
   `--score-meta` with title, measures (a pickup counts as one), concert `keysig` in fifths, timesig,
   tempo and per-part harmony/lyric counts; for MusicXML, the first pitches and chords per part and the XSD result.
   The exit status is 1 if any file failed.
2. Compare those numbers with the request: bar count, key (F = −1, D = 2, Bb = −2), chord
   count, parts, and an audio length of about `bars × beats × 60 / tempo` plus a short tail.
3. **Look at it:** `mscore-run.sh -T 20 -o look.png score.mscz` and Read `look-1.png`.
   Collisions, a wrong clef, chord symbols on the wrong beat and empty staves only show up here.

## Gotchas (the ones that bite first)

- **Exit codes:** see above. A crash-reporter dump lands in
  `~/Library/Application Support/MuseScore/MuseScore4/logs/dumps/` each time. It is harmless, and you can delete it.
- **Same-name outputs:** `-o` silently overwrites. The scripts never write over their input. Keep that rule
  when calling `mscore` directly.
- **MIDI import:** quantisation and voice splitting are MuseScore's guesses. Check the PNG;
  pass `-M ops.xml` (MIDI import operations) to steer them.
- **Transposing instruments:** `--score-meta` `keysig` is the concert key. The written key of a part
  shows up in its PDF or in the parsed MusicXML (`written_key_fifths`).
- **QML plugins** run only inside the GUI. There is no headless plugin runner in 4.x, so they don't fit this workflow.
- More: chord-kind rendering, MusicXML import quirks, sound profiles, page size and
  style files (`-S style.mss`) are in [references/gotchas.md](references/gotchas.md). Worked end-to-end
  examples are in [references/recipes.md](references/recipes.md).

## Hand-off

Report the files written (score, parts, audio), the checks you ran (bars, key, pages,
audio length, the PNG you looked at), and anything you approximated, such as MIDI quantisation or
missing articulations. A `.mscz` opens in MuseScore for hand edits, and MusicXML
opens in Sibelius, Finale, Dorico and most notation apps.
